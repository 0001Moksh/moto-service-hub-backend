from pydantic import BaseModel, EmailStr
from typing import Optional

# ==================== Owner Signup Schemas ====================

class EmailRequest(BaseModel):
    email: EmailStr


class OTPRequest(BaseModel):
    email: EmailStr
    otp: str


class PasswordRequest(BaseModel):
    email: EmailStr
    password: str


class AadhaarDataVerification(BaseModel):
    email: EmailStr
    owner_name: str
    gender: str
    dob: str  # DD/MM/YYYY
    aadhaar_number: str


class ShopDetailsRequest(BaseModel):
    email: EmailStr
    shop_name: str
    shop_location: str
    phone_number: str


# ==================== Request Shop Schema ====================

class RequestShopResponse(BaseModel):
    request_id: int
    owner_name: str
    shop_name: str
    shop_location: str
    phone_number: str
    email: str
    aadhaar_number: str
    status: str
    
    class Config:
        from_attributes = True


# ==================== Owner Response Schemas ====================

class OwnerResponse(BaseModel):
    owner_id: int
    owner_name: str
    mail: str
    phone_number: str
    gender: Optional[str] = None
    dob: Optional[str] = None
    aadhaar_number: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class OwnerSignupStep1Response(BaseModel):
    success: bool
    message: str
    email: str
    step: str = "otp_sent"


class OwnerSignupStep2Response(BaseModel):
    success: bool
    message: str
    email: str
    step: str = "password_required"


class OwnerSignupStep3Response(BaseModel):
    success: bool
    message: str
    email: str
    step: str = "aadhaar_upload_required"


class AadhaarExtractionResponse(BaseModel):
    success: bool
    message: str
    email: str
    extracted_data: dict
    step: str = "verify_aadhaar_data"


class OwnerSignupStep5Response(BaseModel):
    success: bool
    message: str
    email: str
    step: str = "shop_details_required"


class RequestShopSubmitResponse(BaseModel):
    success: bool
    message: str
    request_id: int
    status: str = "pending"


class OwnerSigninRequest(BaseModel):
    email: EmailStr
    password: str


class OwnerSigninResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    owner: Optional[OwnerResponse] = None


# ==================== Admin Approval Schemas ====================

class ApproveShopRequest(BaseModel):
    request_id: int
    action: str  # "approve" or "reject"
    rejection_reason: Optional[str] = None


class ApproveShopResponse(BaseModel):
    success: bool
    message: str
    status: str
