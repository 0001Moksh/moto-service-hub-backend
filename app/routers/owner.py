from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
from datetime import timedelta

from app.core.database import supabase
from app.schemas.owner import (
    EmailRequest, OTPRequest, PasswordRequest, AadhaarDataVerification,
    ShopDetailsRequest, RequestShopResponse, OwnerResponse,
    OwnerSignupStep1Response, OwnerSignupStep2Response, OwnerSignupStep3Response,
    AadhaarExtractionResponse, OwnerSignupStep5Response, RequestShopSubmitResponse,
    OwnerSigninRequest, OwnerSigninResponse
)
from app.utils.otp import generate_otp, store_otp, verify_otp
from app.utils.email import send_otp_email, send_welcome_email
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.file_handler import save_upload_file, delete_file
from app.utils.groq_service import extract_aadhaar_data
from app.core.config import settings
from app.schemas.mechanic import MechanicInviteRequest, MechanicInviteResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/owner", tags=["Owner"])

# In-memory storage for signup progress
owner_signup_progress = {}


# ==================== Step 1: Email Signup ====================

@router.post("/signup/step1", response_model=OwnerSignupStep1Response)
async def signup_step1(request: EmailRequest):
    """Step 1: Owner enters email and OTP is sent"""
    try:
        email = request.email
        
        # Check if email already exists in owner or request_shop
        existing_owner = supabase.table("owner").select("*").eq("mail", email).execute()
        existing_request = supabase.table("request_shop").select("*").eq("mail", email).execute()
        
        if existing_owner.data:
            raise HTTPException(status_code=400, detail="Email already registered as owner")
        if existing_request.data and existing_request.data[0]["status"] == "approved":
            raise HTTPException(status_code=400, detail="This email is already approved as owner")
        
        # Generate and store OTP
        otp = generate_otp(settings.OTP_LENGTH)
        store_otp(email, otp, settings.OTP_EXPIRY_MINUTES)
        
        # Send OTP email
        email_sent = send_otp_email(email, otp)
        if not email_sent:
            logger.warning(f"Failed to send OTP email to {email}, but OTP is stored")
        
        # Store signup progress
        owner_signup_progress[email] = {"step": 1, "email": email}
        
        logger.info(f"OTP sent to {email}")
        
        return OwnerSignupStep1Response(
            success=True,
            message="OTP sent to your email. Check your inbox.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in owner signup step 1: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 2: OTP Verification ====================

@router.post("/signup/step2", response_model=OwnerSignupStep2Response)
async def signup_step2(request: OTPRequest):
    """Step 2: Owner verifies OTP"""
    try:
        email = request.email
        otp = request.otp
        
        # Verify OTP
        if not verify_otp(email, otp):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        # Update signup progress
        if email in owner_signup_progress:
            owner_signup_progress[email]["step"] = 2
        else:
            owner_signup_progress[email] = {"step": 2, "email": email}
        
        logger.info(f"OTP verified for {email}")
        
        return OwnerSignupStep2Response(
            success=True,
            message="OTP verified successfully. Now set your password.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in owner signup step 2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 3: Password Setup ====================

@router.post("/signup/step3", response_model=OwnerSignupStep3Response)
async def signup_step3(request: PasswordRequest):
    """Step 3: Owner sets password"""
    try:
        email = request.email
        password = request.password
        
        # Validate password
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check if OTP was verified
        if email not in owner_signup_progress or owner_signup_progress[email]["step"] < 2:
            raise HTTPException(status_code=400, detail="Please verify OTP first")
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Store password in memory
        owner_signup_progress[email]["password"] = hashed_password
        owner_signup_progress[email]["step"] = 3
        
        logger.info(f"Password set for {email}")
        
        return OwnerSignupStep3Response(
            success=True,
            message="Password set successfully. Now upload your Aadhaar card.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in owner signup step 3: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 4: Aadhaar Upload & Extraction ====================

@router.post("/signup/step4-upload-aadhaar", response_model=AadhaarExtractionResponse)
async def signup_step4_upload_aadhaar(email: str, file: UploadFile = File(...)):
    """Step 4: Owner uploads Aadhaar card and data is extracted"""
    try:
        if email not in owner_signup_progress or owner_signup_progress[email]["step"] < 3:
            raise HTTPException(status_code=400, detail="Please complete previous steps")
        
        # Save file
        saved = save_upload_file(file, f"aadhaar/owner/{email}")
        if not saved["success"]:
            raise HTTPException(status_code=400, detail=saved["error"])
        
        # Extract data using Groq
        extraction = extract_aadhaar_data(saved["file_path"])
        
        if not extraction.get("success"):
            delete_file(saved["file_path"])
            raise HTTPException(status_code=400, detail=extraction.get("error", "Failed to extract data"))
        
        # Store extracted data in memory
        owner_signup_progress[email]["aadhaar_image"] = saved["file_path"]
        owner_signup_progress[email]["aadhaar_data"] = extraction["data"]
        owner_signup_progress[email]["step"] = 4
        
        logger.info(f"Aadhaar data extracted for {email}")
        
        return AadhaarExtractionResponse(
            success=True,
            message="Aadhaar data extracted successfully. Please verify the information.",
            email=email,
            extracted_data=extraction["data"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in owner signup step 4: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 5: Verify Aadhaar Data ====================

@router.post("/signup/step5-verify-aadhaar", response_model=OwnerSignupStep5Response)
async def signup_step5_verify_aadhaar(request: AadhaarDataVerification):
    """Step 5: Owner verifies/edits Aadhaar data"""
    try:
        email = request.email
        
        if email not in owner_signup_progress or owner_signup_progress[email]["step"] < 4:
            raise HTTPException(status_code=400, detail="Please upload Aadhaar first")
        
        # Store verified aadhaar data
        owner_signup_progress[email]["owner_name"] = request.owner_name
        owner_signup_progress[email]["gender"] = request.gender
        owner_signup_progress[email]["dob"] = request.dob
        owner_signup_progress[email]["aadhaar_number"] = request.aadhaar_number
        owner_signup_progress[email]["step"] = 5
        
        logger.info(f"Aadhaar data verified for {email}")
        
        return OwnerSignupStep5Response(
            success=True,
            message="Aadhaar data verified. Now enter your shop details.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in owner signup step 5: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 6: Shop Details & Submit Request ====================

@router.post("/signup/step6-submit-request", response_model=RequestShopSubmitResponse)
async def signup_step6_submit_request(request: ShopDetailsRequest):
    """Step 6: Owner enters shop details and submits approval request"""
    try:
        email = request.email
        
        if email not in owner_signup_progress or owner_signup_progress[email]["step"] < 5:
            raise HTTPException(status_code=400, detail="Please complete previous steps")
        
        # Get all stored data
        owner_data = owner_signup_progress[email]
        
        # Create request_shop record for admin approval
        shop_request_data = {
            "mail": email,
            "owner_name": owner_data.get("owner_name"),
            "gender": owner_data.get("gender"),
            "dob": owner_data.get("dob"),
            "aadhaar_number": owner_data.get("aadhaar_number"),
            "password": owner_data.get("password"),
            "shop_name": request.shop_name,
            "shop_location": request.shop_location,
            "phone_number": request.phone_number,
            "status": "pending"
        }
        
        try:
            response = supabase.table("request_shop").insert(shop_request_data).execute()
            
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to submit shop request")
            
            request_record = response.data[0]
            request_id = request_record["request_id"]
            
            logger.info(f"Shop request submitted for {email} with request_id {request_id}")
            
            # Send confirmation email and admin notification
            # TODO: Send email to admin with approval link
            
        except Exception as db_error:
            logger.error(f"Error submitting shop request: {db_error}")
            raise HTTPException(status_code=500, detail=str(db_error))
        
        # Clean up progress
        del owner_signup_progress[email]
        
        return RequestShopSubmitResponse(
            success=True,
            message="Shop request submitted successfully! Admin will review and send approval via email.",
            request_id=request_id,
            status="pending"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in owner signup step 6: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Owner Signin ====================

@router.post("/signin", response_model=OwnerSigninResponse)
async def signin(request: OwnerSigninRequest):
    """Owner signin with email and password (after approval)"""
    try:
        email = request.email
        password = request.password
        
        # Get owner (only approved owners)
        response = supabase.table("owner").select("*").eq("mail", email).execute()
        
        if not response.data:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        owner = response.data[0]
        
        # Verify password
        if not verify_password(password, owner["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email, "owner_id": owner["owner_id"], "role": "owner"},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Owner signed in: {email}")
        
        return OwnerSigninResponse(
            success=True,
            message="Signin successful",
            access_token=access_token,
            owner=OwnerResponse(**owner)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in owner signin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Owner Profile ====================

@router.get("/profile/{owner_id}", response_model=OwnerResponse)
async def get_owner_profile(owner_id: int):
    """Get owner profile"""
    try:
        response = supabase.table("owner").select("*").eq("owner_id", owner_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        return OwnerResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting owner profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Owner: Invite Mechanic ====================

@router.post("/invite-mechanic", response_model=MechanicInviteResponse)
async def invite_mechanic(shop_id: int, request: MechanicInviteRequest):
    """Owner invites a mechanic to their shop"""
    try:
        # Get shop
        shop_response = supabase.table("shop").select("*").eq("shop_id", shop_id).execute()
        
        if not shop_response.data:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        shop = shop_response.data[0]
        
        # Check if mechanic already exists in shop
        existing = supabase.table("mechanic").select("*").eq("mail", request.mechanic_email).eq("shop_id", shop_id).execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail="Mechanic already exists in this shop")
        
        # Delegate to mechanic router
        from app.routers import mechanic as mechanic_router
        
        # Generate invitation token and send email directly
        import uuid
        invitation_token = str(uuid.uuid4())
        
        mechanic_router.mechanic_invitations[invitation_token] = {
            "shop_id": shop_id,
            "mechanic_email": request.mechanic_email,
            "mechanic_name": request.mechanic_name,
            "created_at": __import__('datetime').datetime.now()
        }
        
        # Send invitation email
        invitation_link = f"{settings.FRONTEND_URL}/mechanic/signup?token={invitation_token}"
        
        from app.utils.email import send_email
        
        email_subject = f"Mechanic Invitation from {shop['shop_name']}"
        email_body = f"""
Dear {request.mechanic_name},

You have been invited to join {shop['shop_name']} as a mechanic.

Shop Details:
- Name: {shop['shop_name']}
- Location: {shop['shop_location']}
- Phone: {shop['phone_number']}

To accept this invitation and complete your signup, click the link below:
{invitation_link}

This link will expire in 7 days.

Best regards,
Moto Service Hub Team
"""
        
        try:
            send_email(request.mechanic_email, email_subject, email_body)
        except Exception as email_error:
            logger.warning(f"Failed to send invitation email: {email_error}")
        
        logger.info(f"Mechanic invitation sent to {request.mechanic_email} for shop {shop_id}")
        
        return MechanicInviteResponse(
            success=True,
            message="Mechanic invitation sent successfully",
            invitation_token=invitation_token
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting mechanic: {e}")
        raise HTTPException(status_code=500, detail=str(e))
