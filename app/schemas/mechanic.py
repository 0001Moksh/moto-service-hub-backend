from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ==================== Mechanic Invitation ====================

class MechanicInviteRequest(BaseModel):
    """Owner invites a mechanic"""
    mechanic_email: EmailStr
    mechanic_name: str = Field(..., min_length=2, max_length=100)


class MechanicInviteResponse(BaseModel):
    """Response after inviting mechanic"""
    success: bool
    message: str
    mechanic_id: Optional[int] = None
    invitation_token: str


# ==================== Mechanic Signup Flow ====================

class MechanicSignupStep1Request(BaseModel):
    """Step 1: Accept invitation with token"""
    invitation_token: str


class MechanicSignupStep1Response(BaseModel):
    """Step 1: Accepted invitation, ready for password setup"""
    success: bool
    message: str
    mechanic_email: str
    mechanic_name: str


class MechanicSignupStep2Request(BaseModel):
    """Step 2: Set password"""
    invitation_token: str
    password: str = Field(..., min_length=8, max_length=100)


class MechanicSignupStep2Response(BaseModel):
    """Step 2: Password set, ready for Aadhaar upload"""
    success: bool
    message: str
    mechanic_email: str


class AadhaarExtractionResponse(BaseModel):
    """Aadhaar extraction response"""
    success: bool
    message: str
    mechanic_email: str
    extracted_data: Optional[dict] = None


class MechanicSignupStep3Request(BaseModel):
    """Step 3: Verify Aadhaar data"""
    invitation_token: str
    mechanic_name: str
    gender: str = Field(..., min_length=1, max_length=50)
    dob: str = Field(..., min_length=1, max_length=20)
    aadhaar_number: str = Field(..., min_length=10, max_length=20)


class MechanicSignupStep3Response(BaseModel):
    """Step 3: Aadhaar verified, signup complete"""
    success: bool
    message: str
    mechanic_email: str
    mechanic_id: Optional[int] = None


# ==================== Mechanic Authentication ====================

class MechanicSigninRequest(BaseModel):
    """Mechanic signin"""
    email: EmailStr
    password: str


class MechanicDetail(BaseModel):
    """Mechanic details in response"""
    mechanic_id: int
    shop_id: int
    mechanic_email: str
    mechanic_name: str
    gender: str
    dob: str
    aadhaar_number: str
    phone_number: Optional[str] = None
    status: str = "active"


class MechanicSigninResponse(BaseModel):
    """Mechanic signin response"""
    success: bool
    message: str
    access_token: str
    mechanic: MechanicDetail


# ==================== Get Mechanic Profile ====================

class MechanicProfileResponse(BaseModel):
    """Mechanic profile"""
    success: bool
    mechanic: MechanicDetail


# ==================== Owner Actions on Mechanics ====================

class ListMechanicsResponse(BaseModel):
    """List all mechanics for owner's shop"""
    success: bool
    total: int
    mechanics: list[MechanicDetail]


class RemoveMechanicRequest(BaseModel):
    """Remove mechanic from shop"""
    mechanic_id: int
