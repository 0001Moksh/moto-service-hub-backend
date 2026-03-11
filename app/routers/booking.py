from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime, timedelta

from app.core.database import supabase
from app.schemas.booking import (
    BookingStep1Request, BookingStep1Response, VehicleForBooking,
    BookingStep2Request, BookingStep2Response,
    BookingStep3Request, BookingStep3Response, ShopForBooking,
    BookingStep4Request, BookingStep4Response, BookingResponse,
    BookingConfirmationResponse, AvailableTimeSlotResponse, TimeSlot,
    BookingSummary, VehicleBookingsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/booking", tags=["Booking"])

# In-memory storage for booking progress (use Redis in production)
booking_progress = {}


# ==================== Step 1: Select Vehicle ====================

@router.post("/step1-select-vehicle", response_model=BookingStep1Response)
async def booking_step1_select_vehicle(request: BookingStep1Request):
    """Step 1: Customer selects a vehicle for booking"""
    try:
        vehicle_id = request.vehicle_id
        
        # Verify vehicle exists
        vehicle_response = supabase.table("vehicle").select("*").eq("vehicle_id", vehicle_id).execute()
        if not vehicle_response.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        vehicle = vehicle_response.data[0]
        
        # Store booking progress
        booking_progress[vehicle_id] = {
            "step": 1,
            "vehicle_id": vehicle_id,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Vehicle {vehicle_id} selected for booking")
        
        return BookingStep1Response(
            success=True,
            message="Vehicle selected successfully. Now describe the issues.",
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
        vehicle_id = request.vehicle_id
        issue_from_customer = request.issue_from_customer
        
        # Verify vehicle has been selected
        if vehicle_id not in booking_progress or booking_progress[vehicle_id]["step"] < 1:
            raise HTTPException(status_code=400, detail="Please select a vehicle first")
        
        # Validate issues
        if not issue_from_customer or len(issue_from_customer) == 0:
            raise HTTPException(status_code=400, detail="Please provide at least one issue description")
        
        # Validate each issue
        for issue in issue_from_customer:
            if not issue or len(issue.strip()) < 5:
                raise HTTPException(status_code=400, detail="Each issue description must be at least 5 characters")
        
        # Update booking progress
        booking_progress[vehicle_id]["step"] = 2
        booking_progress[vehicle_id]["issue_from_customer"] = issue_from_customer
        
        logger.info(f"Vehicle {vehicle_id} added {len(issue_from_customer)} issue(s)")
        
        return BookingStep2Response(
            success=True,
            message="Issues recorded. Now select a shop.",
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
        # Get all shops from the shop table
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
                "rating": 4.5  # Default rating - can be calculated from booking reviews
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
        vehicle_id = request.vehicle_id
        shop_id = request.shop_id
        
        # Verify vehicle has completed step 2
        if vehicle_id not in booking_progress or booking_progress[vehicle_id]["step"] < 2:
            raise HTTPException(status_code=400, detail="Please add issue description first")
        
        # Verify shop exists (query shop table directly)
        shop_response = supabase.table("shop").select("*").eq("shop_id", shop_id).execute()
        if not shop_response.data:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        shop = shop_response.data[0]
        
        # Update booking progress
        booking_progress[vehicle_id]["step"] = 3
        booking_progress[vehicle_id]["shop_id"] = shop_id
        
        logger.info(f"Vehicle {vehicle_id} selected shop {shop_id}")
        
        return BookingStep3Response(
            success=True,
            message="Shop selected. Now choose a date and time for service.",
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
        # Verify shop exists (query shop table)
        shop_response = supabase.table("shop").select("*").eq("shop_id", shop_id).execute()
        if not shop_response.data:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        shop = shop_response.data[0]
        
        # Generate sample time slots (9 AM to 5 PM)
        slots = []
        start_hour = 9
        end_hour = 17
        slot_duration = 1  # 1 hour slots
        
        current_datetime = datetime.now()
        requested_date = datetime.strptime(booking_date, "%Y-%m-%d")
        
        # Don't allow booking in the past
        if requested_date.date() < current_datetime.date():
            raise HTTPException(status_code=400, detail="Cannot book for past dates")
        
        for hour in range(start_hour, end_hour):
            slot_time = f"{hour:02d}:00"
            
            # Check if this slot is already booked
            service_at_check = f"{booking_date}T{slot_time}:00"
            booking_check = supabase.table("booking").select("*").eq("shop_id", shop_id).ilike("service_at", f"{booking_date}T{hour:02d}%").execute()
            
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
        vehicle_id = request.vehicle_id
        shop_id = request.shop_id
        issue_from_customer = request.issue_from_customer
        service_at = request.service_at
        booking_trust = request.booking_trust
        
        # Verify vehicle has completed step 3
        if vehicle_id not in booking_progress or booking_progress[vehicle_id]["step"] < 3:
            raise HTTPException(status_code=400, detail="Please select a shop first")
        
        progress = booking_progress[vehicle_id]
        if progress["shop_id"] != shop_id:
            raise HTTPException(status_code=400, detail="Data mismatch. Please start over.")
        
        # Validate service_at format (ISO 8601)
        try:
            service_datetime = datetime.fromisoformat(service_at.replace('Z', '+00:00'))
            if service_datetime < datetime.now():
                raise HTTPException(status_code=400, detail="Cannot book for past date/time")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")
        
        # Check if time slot is already booked
        slot_check = supabase.table("booking").select("*").eq("shop_id", shop_id).eq("vehicle_id", vehicle_id).ilike("service_at", f"{service_at.split('T')[0]}T{service_at.split('T')[1][:2]}%").execute()
        
        if slot_check.data:
            raise HTTPException(status_code=400, detail="This time slot is already booked. Please choose another.")
        
        # Get a mechanic from the shop to assign to this booking
        # For initial booking, assign the first available mechanic from the shop
        mechanic_response = supabase.table("mechanic").select("mechanic_id").eq("shop_id", shop_id).limit(1).execute()
        mechanic_id = mechanic_response.data[0]["mechanic_id"] if mechanic_response.data else None
        
        if not mechanic_id:
            logger.warning(f"No mechanic found for shop {shop_id}, using default mechanic_id=1")
            mechanic_id = 1  # Fallback, will be updated later
        
        # Create booking record with 'pending' status (waiting for mechanic acceptance)
        booking_data = {
            "vehicle_id": vehicle_id,
            "shop_id": shop_id,
            "mechanic_id": mechanic_id,
            "issue_from_customer": issue_from_customer,
            "booking_trust": booking_trust,
            "service_at": service_at,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            response = supabase.table("booking").insert(booking_data).execute()
            
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to create booking")
            
            booking = response.data[0]
            logger.info(f"✅ Booking created: {booking['booking_id']}")
        
        except Exception as db_error:
            logger.error(f"Error creating booking in DB: {db_error}")
            raise HTTPException(status_code=500, detail=str(db_error))
        
        # Clean up progress
        del booking_progress[vehicle_id]
        
        return BookingStep4Response(
            success=True,
            message="✅ Booking confirmed successfully! Waiting for mechanic acceptance.",
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
        # Get booking details
        booking_response = supabase.table("booking").select("*").eq("booking_id", booking_id).execute()
        if not booking_response.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking = booking_response.data[0]
        
        # Get vehicle details
        vehicle_response = supabase.table("vehicle").select("*").eq("vehicle_id", booking["vehicle_id"]).execute()
        vehicle = vehicle_response.data[0] if vehicle_response.data else {}
        
        # Get shop details
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
        # Get all bookings for vehicle
        bookings_response = supabase.table("booking").select("*").eq("vehicle_id", vehicle_id).order("service_at", desc=True).execute()
        
        bookings_data = []
        for booking in bookings_response.data:
            # Get vehicle details
            vehicle_response = supabase.table("vehicle").select("*").eq("vehicle_id", booking["vehicle_id"]).execute()
            vehicle = vehicle_response.data[0] if vehicle_response.data else {"reg_number": "Unknown"}
            
            # Get shop details
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
        # Get booking
        booking_response = supabase.table("booking").select("*").eq("booking_id", booking_id).execute()
        if not booking_response.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking = booking_response.data[0]
        
        # Check if booking can be cancelled (not completed or already cancelled)
        if booking["status"] in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel a {booking['status']} booking")
        
        # Update booking status
        response = supabase.table("booking").update({
            "status": "cancelled",
            "cancelled_description": cancelled_description
        }).eq("booking_id", booking_id).execute()
        
        logger.info(f"Booking {booking_id} cancelled")
        
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

