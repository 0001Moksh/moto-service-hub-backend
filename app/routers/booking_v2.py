"""
Scalable Booking System - Database-Backed Sessions
Supports unlimited concurrent users without conflicts
Uses PostgreSQL booking_session table for persistent, multi-user booking workflows
"""

from fastapi import APIRouter, HTTPException
from uuid import UUID, uuid4
import logging
from datetime import datetime, timedelta

from app.core.database import supabase
from app.schemas.booking import (
    BookingSessionCreate, BookingSessionResponse, BookingSession,
    BookingStep1Request, BookingStep1Response, VehicleForBooking,
    BookingStep2Request, BookingStep2Response,
    BookingStep3Request, BookingStep3Response, ShopForBooking,
    BookingStep4Request, BookingStep4Response, BookingResponse,
    BookingConfirmationResponse, AvailableTimeSlotResponse, TimeSlot,
    BookingSummary, VehicleBookingsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/booking", tags=["Booking"])


# ==================== Booking Session Management ====================

@router.post("/session/create", response_model=BookingSessionResponse)
async def create_booking_session(request: BookingSessionCreate):
    """Create a new booking session for a customer"""
    try:
        session_id = uuid4()
        
        # Verify vehicle exists
        vehicle_response = supabase.table("vehicle").select("*").eq("vehicle_id", request.vehicle_id).execute()
        if not vehicle_response.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Create session in database
        session_data = {
            "session_id": str(session_id),
            "vehicle_id": request.vehicle_id,
            "customer_id": request.customer_id,
            "current_step": 1,
            "status": "in_progress",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        response = supabase.table("booking_session").insert(session_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create booking session")
        
        logger.info(f"✅ Booking session created: {session_id} for vehicle {request.vehicle_id}")
        
        return BookingSessionResponse(
            success=True,
            session_id=session_id,
            message="Booking session created successfully. Proceed with vehicle selection."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_booking_session(session_id: UUID):
    """Get booking session details"""
    try:
        response = supabase.table("booking_session").select("*").eq("session_id", str(session_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Booking session not found or expired")
        
        session = response.data[0]
        
        # Check if session has expired
        expires_at = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
        if expires_at < datetime.now(expires_at.tzinfo):
            raise HTTPException(status_code=410, detail="Booking session has expired")
        
        return BookingSession(
            session_id=UUID(session["session_id"]),
            vehicle_id=session["vehicle_id"],
            shop_id=session.get("shop_id"),
            issue_from_customer=session.get("issue_from_customer"),
            current_step=session["current_step"],
            status=session["status"],
            created_at=session.get("created_at"),
            updated_at=session.get("updated_at")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving booking session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 1: Select Vehicle ====================

@router.post("/step1-select-vehicle", response_model=BookingStep1Response)
async def booking_step1_select_vehicle(request: BookingStep1Request):
    """Step 1: Customer selects a vehicle for booking"""
    try:
        session_id = request.session_id
        vehicle_id = request.vehicle_id
        
        # Get session
        session_response = supabase.table("booking_session").select("*").eq("session_id", str(session_id)).execute()
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Booking session not found")
        
        session = session_response.data[0]
        
        # Verify vehicle exists
        vehicle_response = supabase.table("vehicle").select("*").eq("vehicle_id", vehicle_id).execute()
        if not vehicle_response.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        vehicle = vehicle_response.data[0]
        
        # Update session to step 1
        update_data = {
            "vehicle_id": vehicle_id,
            "current_step": 1,
            "updated_at": datetime.now().isoformat()
        }
        
        supabase.table("booking_session").update(update_data).eq("session_id", str(session_id)).execute()
        
        logger.info(f"✅ Session {session_id}: Vehicle {vehicle_id} selected")
        
        return BookingStep1Response(
            success=True,
            message="Vehicle selected successfully. Now describe the issues.",
            session_id=session_id,
            vehicle_id=vehicle_id,
            vehicle=VehicleForBooking(
                vehicle_id=vehicle["vehicle_id"],
                reg_number=vehicle.get("reg_number"),
                manufacturer=vehicle.get("manufacturer"),
                model_no=vehicle.get("model_no"),
                color=vehicle.get("color"),
                body_type=vehicle.get("body_type")
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in booking step 1: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 2: Add Issue Description ====================

@router.post("/step2-add-issue", response_model=BookingStep2Response)
async def booking_step2_add_issue(request: BookingStep2Request):
    """Step 2: Customer adds issue descriptions"""
    try:
        session_id = request.session_id
        vehicle_id = request.vehicle_id
        issue_from_customer = request.issue_from_customer
        
        # Get session
        session_response = supabase.table("booking_session").select("*").eq("session_id", str(session_id)).execute()
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Booking session not found")
        
        session = session_response.data[0]
        
        # Verify session is in correct step
        if session["current_step"] < 1:
            raise HTTPException(status_code=400, detail="Please select a vehicle first")
        
        # Validate issues
        if not issue_from_customer or len(issue_from_customer) == 0:
            raise HTTPException(status_code=400, detail="Please provide at least one issue description")
        
        for issue in issue_from_customer:
            if not issue or len(issue.strip()) < 5:
                raise HTTPException(status_code=400, detail="Each issue description must be at least 5 characters")
        
        # Update session with issues and move to step 2
        update_data = {
            "vehicle_id": vehicle_id,
            "issue_from_customer": issue_from_customer,
            "current_step": 2,
            "updated_at": datetime.now().isoformat()
        }
        
        supabase.table("booking_session").update(update_data).eq("session_id", str(session_id)).execute()
        
        logger.info(f"✅ Session {session_id}: Added {len(issue_from_customer)} issue(s)")
        
        return BookingStep2Response(
            success=True,
            message="Issues recorded. Now select a shop.",
            session_id=session_id,
            vehicle_id=vehicle_id,
            issue_from_customer=issue_from_customer
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in booking step 2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 3: Select Shop ====================

@router.get("/available-shops", tags=["Booking - Shop Selection"])
async def get_available_shops():
    """Get list of all available shops"""
    try:
        response = supabase.table("shop").select("shop_id, shop_name, shop_location, phone_number").execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No shops available")
        
        shops = []
        for shop in response.data:
            shops.append({
                "shop_id": shop.get("shop_id"),
                "shop_name": shop.get("shop_name"),
                "shop_location": shop.get("shop_location"),
                "phone_number": shop.get("phone_number"),
                "rating": 4.5
            })
        
        return {
            "success": True,
            "total_shops": len(shops),
            "shops": shops
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available shops: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step3-select-shop", response_model=BookingStep3Response)
async def booking_step3_select_shop(request: BookingStep3Request):
    """Step 3: Customer selects a shop"""
    try:
        session_id = request.session_id
        vehicle_id = request.vehicle_id
        shop_id = request.shop_id
        
        # Get session
        session_response = supabase.table("booking_session").select("*").eq("session_id", str(session_id)).execute()
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Booking session not found")
        
        session = session_response.data[0]
        
        # Verify session has completed step 2
        if session["current_step"] < 2:
            raise HTTPException(status_code=400, detail="Please add issue description first")
        
        # Verify shop exists
        shop_response = supabase.table("shop").select("*").eq("shop_id", shop_id).execute()
        if not shop_response.data:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        shop = shop_response.data[0]
        
        # Update session with shop selection
        update_data = {
            "vehicle_id": vehicle_id,
            "shop_id": shop_id,
            "current_step": 3,
            "updated_at": datetime.now().isoformat()
        }
        
        supabase.table("booking_session").update(update_data).eq("session_id", str(session_id)).execute()
        
        logger.info(f"✅ Session {session_id}: Shop {shop_id} selected")
        
        return BookingStep3Response(
            success=True,
            message="Shop selected. Now choose a date and time for service.",
            session_id=session_id,
            vehicle_id=vehicle_id,
            shop=ShopForBooking(
                shop_id=shop.get("shop_id"),
                shop_name=shop.get("shop_name"),
                shop_location=shop.get("shop_location"),
                phone_number=shop.get("phone_number"),
                rating=4.5
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in booking step 3: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Available Time Slots ====================

@router.get("/available-slots/{shop_id}/{booking_date}", response_model=AvailableTimeSlotResponse)
async def get_available_slots(shop_id: int, booking_date: str):
    """Get available time slots for a specific shop and date"""
    try:
        # Verify shop exists
        shop_response = supabase.table("shop").select("*").eq("shop_id", shop_id).execute()
        if not shop_response.data:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        shop = shop_response.data[0]
        
        # Generate time slots (9 AM to 5 PM, hourly)
        slots = []
        start_hour = 9
        end_hour = 17
        slot_duration = 1
        
        current_datetime = datetime.now()
        requested_date = datetime.strptime(booking_date, "%Y-%m-%d")
        
        if requested_date.date() < current_datetime.date():
            raise HTTPException(status_code=400, detail="Cannot book for past dates")
        
        for hour in range(start_hour, end_hour):
            # Check if slot is booked using timestamp comparison
            slot_start = f"{booking_date}T{hour:02d}:00:00"
            slot_end = f"{booking_date}T{hour+slot_duration:02d}:00:00"
            
            booking_check = supabase.table("booking").select("*").eq("shop_id", shop_id).gte("service_at", slot_start).lt("service_at", slot_end).execute()
            
            is_available = len(booking_check.data) == 0
            
            slots.append(TimeSlot(
                date=booking_date,
                start_time=f"{hour:02d}:00",
                end_time=f"{hour+slot_duration:02d}:00",
                available=is_available
            ))
        
        return AvailableTimeSlotResponse(
            success=True,
            shop_id=shop_id,
            shop_name=shop.get("shop_name"),
            date=booking_date,
            slots=slots
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 4: Book Time Slot ====================

@router.post("/step4-book-timeslot", response_model=BookingStep4Response)
async def booking_step4_book_timeslot(request: BookingStep4Request):
    """Step 4: Customer books a time slot and completes the booking"""
    try:
        session_id = request.session_id
        vehicle_id = request.vehicle_id
        shop_id = request.shop_id
        issue_from_customer = request.issue_from_customer
        booking_date = request.date  # YYYY-MM-DD
        time_slot = request.time_slot  # HH:MM-HH:MM
        booking_trust = request.booking_trust
        
        # Get session
        session_response = supabase.table("booking_session").select("*").eq("session_id", str(session_id)).execute()
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Booking session not found")
        
        session = session_response.data[0]
        
        # Verify session has completed step 3
        if session["current_step"] < 3:
            raise HTTPException(status_code=400, detail="Please select a shop first")
        
        # Parse date and time slot
        try:
            # Parse date (YYYY-MM-DD)
            booking_datetime = datetime.strptime(booking_date, "%Y-%m-%d")
            
            # Parse time slot (HH:MM-HH:MM)
            if "-" not in time_slot:
                raise ValueError("Time slot must be in format HH:MM-HH:MM")
            
            start_time_str = time_slot.split("-")[0].strip()  # HH:MM
            start_hour, start_minute = start_time_str.split(":")
            
            # Combine date and time
            service_datetime = booking_datetime.replace(hour=int(start_hour), minute=int(start_minute), second=0, microsecond=0)
            
            if service_datetime < datetime.now():
                raise HTTPException(status_code=400, detail="Cannot book for past date/time")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date/time format. Use date as YYYY-MM-DD and time_slot as HH:MM-HH:MM. Error: {str(e)}")
        
        # Check slot availability using timestamp comparison
        service_hour = start_hour.lstrip('0') or '0'
        slot_start = f"{booking_date}T{int(service_hour):02d}:00:00"
        slot_end = f"{booking_date}T{int(service_hour)+1:02d}:00:00"
        
        slot_check = supabase.table("booking").select("*").eq("shop_id", shop_id).gte("service_at", slot_start).lt("service_at", slot_end).execute()
        
        if slot_check.data:
            raise HTTPException(status_code=400, detail="This time slot is already booked. Please choose another.")
        
        # Get available mechanic
        mechanic_response = supabase.table("mechanic").select("mechanic_id").eq("shop_id", shop_id).limit(1).execute()
        mechanic_id = mechanic_response.data[0]["mechanic_id"] if mechanic_response.data else 1
        
        # Create booking record with full service_at datetime
        service_at_iso = service_datetime.isoformat()
        booking_data = {
            "vehicle_id": vehicle_id,
            "shop_id": shop_id,
            "mechanic_id": mechanic_id,
            "issue_from_customer": issue_from_customer,
            "booking_trust": booking_trust,
            "service_at": service_at_iso,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table("booking").insert(booking_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create booking")
        
        booking = response.data[0]
        
        # Update session status to completed and store date/time_slot
        supabase.table("booking_session").update({
            "current_step": 4,
            "status": "completed",
            "date": booking_date,
            "time_slot": time_slot,
            "updated_at": datetime.now().isoformat()
        }).eq("session_id", str(session_id)).execute()
        
        logger.info(f"✅ Session {session_id}: Booking {booking['booking_id']} created successfully for {booking_date} {time_slot}")
        
        return BookingStep4Response(
            success=True,
            message="✅ Booking confirmed successfully! Waiting for mechanic acceptance.",
            session_id=session_id,
            booking=BookingResponse(
                booking_id=booking.get("booking_id", 0),
                vehicle_id=booking.get("vehicle_id"),
                shop_id=booking.get("shop_id"),
                mechanic_id=booking.get("mechanic_id"),
                issue_from_customer=booking.get("issue_from_customer", []),
                booking_trust=booking.get("booking_trust", False),
                status=booking.get("status"),
                created_at=booking.get("created_at"),
                service_at=booking.get("service_at"),
                cancelled_description=booking.get("cancelled_description")
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in booking step 4: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Booking Confirmation ====================

@router.get("/confirmation/{booking_id}", response_model=BookingConfirmationResponse)
async def get_booking_confirmation(booking_id: int):
    """Get booking confirmation details"""
    try:
        booking_response = supabase.table("booking").select("*").eq("booking_id", booking_id).execute()
        if not booking_response.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking = booking_response.data[0]
        
        vehicle_response = supabase.table("vehicle").select("*").eq("vehicle_id", booking["vehicle_id"]).execute()
        vehicle = vehicle_response.data[0] if vehicle_response.data else {}
        
        shop_response = supabase.table("shop").select("*").eq("shop_id", booking["shop_id"]).execute()
        shop = shop_response.data[0] if shop_response.data else {}
        
        return BookingConfirmationResponse(
            success=True,
            message="Booking confirmed",
            booking_id=booking["booking_id"],
            vehicle_id=booking["vehicle_id"],
            shop_id=booking["shop_id"],
            shop_name=shop.get("shop_name", "Unknown"),
            vehicle_reg_number=vehicle.get("reg_number", "Unknown"),
            service_at=booking["service_at"],
            issue_from_customer=booking.get("issue_from_customer", []),
            booking_trust=booking.get("booking_trust", False),
            status=booking["status"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking confirmation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Vehicle Bookings ====================

@router.get("/vehicle/{vehicle_id}", response_model=VehicleBookingsResponse)
async def get_vehicle_bookings(vehicle_id: int):
    """Get all bookings for a vehicle"""
    try:
        bookings_response = supabase.table("booking").select("*").eq("vehicle_id", vehicle_id).order("service_at", desc=True).execute()
        
        bookings_data = []
        for booking in bookings_response.data:
            vehicle_response = supabase.table("vehicle").select("*").eq("vehicle_id", booking["vehicle_id"]).execute()
            vehicle = vehicle_response.data[0] if vehicle_response.data else {"reg_number": "Unknown"}
            
            shop_response = supabase.table("shop").select("*").eq("shop_id", booking["shop_id"]).execute()
            shop = shop_response.data[0] if shop_response.data else {"shop_name": "Unknown"}
            
            bookings_data.append(BookingSummary(
                booking_id=booking["booking_id"],
                vehicle_reg_number=vehicle.get("reg_number"),
                shop_name=shop.get("shop_name"),
                service_at=booking["service_at"],
                status=booking["status"],
                issue_count=len(booking.get("issue_from_customer", []))
            ))
        
        return VehicleBookingsResponse(
            success=True,
            vehicle_id=vehicle_id,
            total_bookings=len(bookings_data),
            bookings=bookings_data
        )
    
    except Exception as e:
        logger.error(f"Error getting vehicle bookings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Cancel Booking ====================

@router.delete("/cancel/{booking_id}")
async def cancel_booking(booking_id: int, cancelled_description: str = ""):
    """Cancel a booking"""
    try:
        booking_response = supabase.table("booking").select("*").eq("booking_id", booking_id).execute()
        if not booking_response.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking = booking_response.data[0]
        
        if booking["status"] in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel a {booking['status']} booking")
        
        supabase.table("booking").update({
            "status": "cancelled",
            "cancelled_description": cancelled_description
        }).eq("booking_id", booking_id).execute()
        
        logger.info(f"✅ Booking {booking_id} cancelled")
        
        return {
            "success": True,
            "message": "Booking cancelled successfully",
            "booking_id": booking_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))
