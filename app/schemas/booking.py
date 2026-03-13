from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


# ==================== Booking Session Management ====================

class BookingSessionCreate(BaseModel):
    """Create a new booking session"""
    vehicle_id: int
    customer_id: Optional[int] = None


class BookingSession(BaseModel):
    """Booking session details"""
    session_id: UUID
    vehicle_id: int
    shop_id: Optional[int] = None
    issue_from_customer: Optional[list[str]] = None
    current_step: int
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BookingSessionResponse(BaseModel):
    """Response containing session info"""
    success: bool
    session_id: UUID
    message: str


# ==================== Vehicle Selection (Step 1) ====================

class BookingStep1Request(BaseModel):
    session_id: UUID  # Now track by session instead of vehicle_id
    vehicle_id: int


class VehicleForBooking(BaseModel):
    vehicle_id: int
    reg_number: str
    manufacturer: Optional[str] = None
    model_no: Optional[str] = None
    color: Optional[str] = None
    body_type: Optional[str] = None


class BookingStep1Response(BaseModel):
    success: bool
    message: str
    session_id: UUID
    vehicle_id: int
    vehicle: VehicleForBooking
    step: str = "issue_description_required"


# ==================== Issue Description (Step 2) ====================

class BookingStep2Request(BaseModel):
    session_id: UUID
    vehicle_id: int
    issue_from_customer: list[str]  # Array of issue descriptions


class BookingStep2Response(BaseModel):
    success: bool
    message: str
    session_id: UUID
    vehicle_id: int
    issue_from_customer: list[str]
    step: str = "shop_selection_required"


# ==================== Shop Selection (Step 3) ====================

class ShopForBooking(BaseModel):
    shop_id: int
    shop_name: str
    shop_location: str
    phone_number: Optional[str] = None
    rating: Optional[float] = None


class BookingStep3Request(BaseModel):
    session_id: UUID
    vehicle_id: int
    shop_id: int


class BookingStep3Response(BaseModel):
    success: bool
    message: str
    session_id: UUID
    vehicle_id: int
    shop: ShopForBooking
    step: str = "timeslot_selection_required"


# ==================== Time Slot Selection & Booking Completion (Step 4) ====================

class TimeSlot(BaseModel):
    slot_id: Optional[int] = None
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    available: bool = True


class BookingStep4Request(BaseModel):
    session_id: UUID
    vehicle_id: int
    shop_id: int
    issue_from_customer: list[str]
    date: str  # YYYY-MM-DD (from available-slots endpoint)
    time_slot: str  # HH:MM-HH:MM format (e.g., "14:00-15:00")
    booking_trust: Optional[bool] = False


class BookingResponse(BaseModel):
    booking_id: int
    vehicle_id: int
    shop_id: int
    mechanic_id: Optional[int] = None
    issue_from_customer: list[str]
    booking_trust: bool
    status: str  # "confirmed", "pending", "completed", "cancelled"
    created_at: Optional[str] = None
    service_at: str
    cancelled_description: Optional[str] = None


class BookingStep4Response(BaseModel):
    success: bool
    message: str
    session_id: UUID
    booking: Optional[BookingResponse] = None
    step: str = "booking_confirmed"


# ==================== Booking Confirmation ====================

class BookingConfirmationResponse(BaseModel):
    success: bool
    message: str
    booking_id: int
    vehicle_id: int
    shop_id: int
    shop_name: str
    vehicle_reg_number: str
    service_at: str
    issue_from_customer: list[str]
    booking_trust: bool
    status: str


# ==================== Available Time Slots ====================

class AvailableTimeSlotResponse(BaseModel):
    success: bool
    shop_id: int
    shop_name: str
    date: str
    slots: list[TimeSlot]


# ==================== Get Vehicle Bookings ====================

class BookingSummary(BaseModel):
    booking_id: int
    vehicle_reg_number: str
    shop_name: str
    service_at: str
    status: str
    issue_count: int


class VehicleBookingsResponse(BaseModel):
    success: bool
    vehicle_id: int
    total_bookings: int
    bookings: list[BookingSummary]
