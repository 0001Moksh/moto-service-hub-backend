from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

# ==================== Auth Schemas ====================

class EmailRequest(BaseModel):
    email: EmailStr


class OTPRequest(BaseModel):
    email: EmailStr
    otp: str


class PasswordRequest(BaseModel):
    email: EmailStr
    password: str


class AadhaarDataRequest(BaseModel):
    email: EmailStr


class AadhaarDataVerification(BaseModel):
    email: EmailStr
    name: str
    gender: str
    dob: str  # DD/MM/YYYY
    aadhaar_number: str


class CustomerSignupComplete(BaseModel):
    email: EmailStr
    password: str
    phone_number: str
    name: str
    gender: str
    dob: str
    aadhaar_number: str


class CustomerSigninRequest(BaseModel):
    email: EmailStr
    password: str


# ==================== Customer Response Schemas ====================

class CustomerResponse(BaseModel):
    customer_id: int
    mail: str
    phone_number: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    aadhaar_number: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class SigninResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    customer: Optional[CustomerResponse] = None


class SignupStep1Response(BaseModel):
    success: bool
    message: str
    email: str
    step: str = "otp_sent"


class SignupStep2Response(BaseModel):
    success: bool
    message: str
    email: str
    step: str = "password_required"


class SignupStep3Response(BaseModel):
    success: bool
    message: str
    email: str
    step: str = "phone_required"


class SignupStep4Response(BaseModel):
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


class SignupCompleteResponse(BaseModel):
    success: bool
    message: str
    customer: Optional[CustomerResponse] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
