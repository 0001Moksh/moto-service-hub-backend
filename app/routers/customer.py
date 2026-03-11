from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
from datetime import timedelta

from app.core.database import supabase
from app.schemas.customer import (
    EmailRequest, OTPRequest, PasswordRequest, AadhaarDataVerification,
    CustomerSignupComplete, CustomerSigninRequest,
    SignupStep1Response, SignupStep2Response, SignupStep3Response,
    SignupStep4Response, AadhaarExtractionResponse, SignupCompleteResponse,
    SigninResponse, CustomerResponse
)
from app.utils.otp import generate_otp, store_otp, verify_otp
from app.utils.email import send_otp_email, send_welcome_email
from app.utils.auth import hash_password, verify_password, create_access_token, verify_token
from app.utils.file_handler import save_upload_file, delete_file
from app.utils.groq_service import extract_aadhaar_data
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/customer", tags=["Customer"])

# In-memory storage for signup progress (use Redis in production)
signup_progress = {}


# ==================== Step 1: Email Signup ====================

@router.post("/signup/step1", response_model=SignupStep1Response)
async def signup_step1(request: EmailRequest):
    """Step 1: Customer enters email and OTP is sent"""
    try:
        email = request.email
        
        # Check if email already exists
        existing = supabase.table("customer").select("*").eq("mail", email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate and store OTP
        otp = generate_otp(settings.OTP_LENGTH)
        store_otp(email, otp, settings.OTP_EXPIRY_MINUTES)
        
        # Send OTP email
        email_sent = send_otp_email(email, otp)
        if not email_sent:
            logger.warning(f"Failed to send OTP email to {email}, but OTP is stored")
        
        # Store signup progress (don't create DB record yet - need password first)
        signup_progress[email] = {"step": 1, "email": email}
        
        logger.info(f"OTP sent to {email}")
        
        return SignupStep1Response(
            success=True,
            message="OTP sent to your email. Check your inbox.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup step 1: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 2: OTP Verification ====================

@router.post("/signup/step2", response_model=SignupStep2Response)
async def signup_step2(request: OTPRequest):
    """Step 2: Customer verifies OTP"""
    try:
        email = request.email
        otp = request.otp
        
        # Verify OTP
        if not verify_otp(email, otp):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        # Update signup progress
        if email in signup_progress:
            signup_progress[email]["step"] = 2
        else:
            signup_progress[email] = {"step": 2, "email": email}
        
        logger.info(f"OTP verified for {email}")
        
        return SignupStep2Response(
            success=True,
            message="OTP verified successfully. Now set your password.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup step 2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 3: Password Setup ====================

@router.post("/signup/step3", response_model=SignupStep3Response)
async def signup_step3(request: PasswordRequest):
    """Step 3: Customer sets password"""
    try:
        email = request.email
        password = request.password
        
        # Validate password
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check if OTP was verified
        if email not in signup_progress or signup_progress[email]["step"] < 2:
            raise HTTPException(status_code=400, detail="Please verify OTP first")
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create customer record in database with email and password (NOW that we have both)
        try:
            customer_data = {
                "mail": email,
                "password": hashed_password
            }
            db_response = supabase.table("customer").insert(customer_data).execute()
            if db_response.data:
                logger.info(f"Customer record created in DB for {email}")
        except Exception as db_error:
            logger.warning(f"Could not create customer record in DB: {db_error}")
        
        # Store password in memory for session
        signup_progress[email]["password"] = hashed_password
        signup_progress[email]["step"] = 3
        
        logger.info(f"Password set for {email}")
        
        return SignupStep3Response(
            success=True,
            message="Password set successfully. Now add your phone number.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup step 3: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 4: Phone Number ====================

class PhoneRequest(EmailRequest):
    phone_number: str


@router.post("/signup/step4", response_model=SignupStep4Response)
async def signup_step4(request: PhoneRequest):
    """Step 4: Customer adds phone number"""
    try:
        email = request.email
        phone_number = request.phone_number
        
        # Validate
        if not phone_number or len(phone_number) < 10:
            raise HTTPException(status_code=400, detail="Valid phone number required")
        
        if email not in signup_progress or signup_progress[email]["step"] < 3:
            raise HTTPException(status_code=400, detail="Please complete previous steps")
        
        # Update customer record in database
        try:
            supabase.table("customer").update({
                "phone_number": phone_number
            }).eq("mail", email).execute()
            logger.info(f"Phone number saved in DB for {email}")
        except Exception as db_error:
            logger.warning(f"Could not save phone number in DB: {db_error}")
        
        # Store phone in memory
        signup_progress[email]["phone_number"] = phone_number
        signup_progress[email]["step"] = 4
        
        logger.info(f"Phone number set for {email}")
        
        return SignupStep4Response(
            success=True,
            message="Phone number saved. Now upload your Aadhaar card for verification.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup step 4: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 5: Aadhaar Upload & Extraction ====================

@router.post("/signup/step5-upload-aadhaar", response_model=AadhaarExtractionResponse)
async def signup_step5_upload_aadhaar(email: str, file: UploadFile = File(...)):
    """Step 5: Customer uploads Aadhaar card and data is extracted"""
    try:
        if email not in signup_progress or signup_progress[email]["step"] < 4:
            raise HTTPException(status_code=400, detail="Please complete previous steps")
        
        # Save file
        saved = save_upload_file(file, f"aadhaar/{email}")
        if not saved["success"]:
            raise HTTPException(status_code=400, detail=saved["error"])
        
        # Extract data using Groq
        extraction = extract_aadhaar_data(saved["file_path"])
        
        if not extraction.get("success"):
            delete_file(saved["file_path"])
            raise HTTPException(status_code=400, detail=extraction.get("error", "Failed to extract data"))
        
        # Update customer record in database
        try:
            supabase.table("customer").update({
                "aadhaar_image": saved["file_path"]
            }).eq("mail", email).execute()
            logger.info(f"Aadhaar image saved in DB for {email}")
        except Exception as db_error:
            logger.warning(f"Could not save aadhaar in DB: {db_error}")
        
        # Store extracted data in memory
        signup_progress[email]["aadhaar_image"] = saved["file_path"]
        signup_progress[email]["aadhaar_data"] = extraction["data"]
        signup_progress[email]["step"] = 5
        
        logger.info(f"✅ Aadhaar data extracted for {email}")
        
        return AadhaarExtractionResponse(
            success=True,
            message="Aadhaar data extracted successfully. Please verify the information.",
            email=email,
            extracted_data=extraction["data"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup step 5: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 6: Verify & Save ====================

@router.post("/signup/step6-verify-aadhaar", response_model=SignupCompleteResponse)
async def signup_step6_verify_aadhaar(request: AadhaarDataVerification):
    """Step 6: Customer verifies/edits Aadhaar data and completes signup"""
    try:
        email = request.email
        
        if email not in signup_progress or signup_progress[email]["step"] < 5:
            raise HTTPException(status_code=400, detail="Please upload Aadhaar first")
        
        # Update customer record with final data
        customer_data = {
            "name": request.name,
            "gender": request.gender,
            "dob": request.dob,
            "aadhaar_number": request.aadhaar_number
        }
        
        try:
            response = supabase.table("customer").update(customer_data).eq("mail", email).execute()
            
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to update customer")
            
            customer = response.data[0]
            logger.info(f"Customer signup completed and saved to DB for {email}")
        except Exception as db_error:
            logger.error(f"Error updating customer in DB: {db_error}")
            raise HTTPException(status_code=500, detail=str(db_error))
        
        # Send welcome email
        send_welcome_email(email, request.name)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email, "customer_id": customer.get("customer_id", email)},
            expires_delta=access_token_expires
        )
        
        # Clean up progress
        del signup_progress[email]
        
        logger.info(f"Customer signup completed for {email}")
        
        return SignupCompleteResponse(
            success=True,
            message="Signup completed successfully! Welcome to Moto Service Hub.",
            customer=CustomerResponse(**customer),
            access_token=access_token
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup step 6: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Signin ====================

@router.post("/signin", response_model=SigninResponse)
async def signin(request: CustomerSigninRequest):
    """Customer signin with email and password"""
    try:
        email = request.email
        password = request.password
        
        # Get customer
        response = supabase.table("customer").select("*").eq("mail", email).execute()
        
        if not response.data:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        customer = response.data[0]
        
        # Verify password
        if not verify_password(password, customer["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email, "customer_id": customer["customer_id"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Customer signed in: {email}")
        
        return SigninResponse(
            success=True,
            message="Signin successful",
            access_token=access_token,
            customer=CustomerResponse(**customer)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Customer Profile ====================

@router.get("/profile/{customer_id}", response_model=CustomerResponse)
async def get_customer_profile(customer_id: int):
    """Get customer profile"""
    try:
        response = supabase.table("customer").select("*").eq("customer_id", customer_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
