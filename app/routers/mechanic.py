from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
from datetime import timedelta
from typing import Optional
import uuid
import json

from app.core.database import supabase
from app.schemas.mechanic import (
    MechanicInviteRequest, MechanicInviteResponse,
    MechanicSignupStep1Request, MechanicSignupStep1Response,
    MechanicSignupStep2Request, MechanicSignupStep2Response,
    MechanicSignupStep3Request, MechanicSignupStep3Response,
    AadhaarExtractionResponse, MechanicSigninRequest, MechanicSigninResponse,
    MechanicProfileResponse, ListMechanicsResponse, MechanicDetail, RemoveMechanicRequest
)
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.file_handler import save_upload_file, delete_file
from app.utils.groq_service import extract_aadhaar_data
from app.utils.email import send_email
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mechanic", tags=["Mechanic"])

# In-memory storage for invitations and signup progress
mechanic_invitations = {}  # token -> {shop_id, owner_id, mechanic_email, mechanic_name, created_at, expires_at}
mechanic_signup_progress = {}  # invitation_token -> {step, email, name, shop_id, ...}


# ==================== Mechanic Invitation (from Owner) ====================

@router.post("/invite", response_model=MechanicInviteResponse)
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
        
        # Generate invitation token
        invitation_token = str(uuid.uuid4())
        
        # Store invitation
        mechanic_invitations[invitation_token] = {
            "shop_id": shop_id,
            "mechanic_email": request.mechanic_email,
            "mechanic_name": request.mechanic_name,
            "created_at": __import__('datetime').datetime.now()
        }
        
        # Send invitation email
        invitation_link = f"{settings.FRONTEND_URL}/mechanic/signup?token={invitation_token}"
        
        email_subject = f"Mechanic Invitation from {shop['shop_name']}"
        email_body = f"""
Dear {request.mechanic_name},

You have been invited to join {shop['shop_name']} as a mechanic.

Shop Details:
- Name: {shop['shop_name']}
- Location: {shop['shop_location']}

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
            message="Invitation sent successfully to mechanic",
            invitation_token=invitation_token
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting mechanic: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Mechanic Signup Flow ====================

@router.post("/signup/step1", response_model=MechanicSignupStep1Response)
async def mechanic_signup_step1(request: MechanicSignupStep1Request):
    """Step 1: Mechanic accepts invitation"""
    try:
        invitation_token = request.invitation_token
        
        # Verify token exists and not expired
        if invitation_token not in mechanic_invitations:
            raise HTTPException(status_code=400, detail="Invalid or expired invitation token")
        
        invitation = mechanic_invitations[invitation_token]
        
        # Initialize signup progress
        mechanic_signup_progress[invitation_token] = {
            "step": 1,
            "mechanic_email": invitation["mechanic_email"],
            "mechanic_name": invitation["mechanic_name"],
            "shop_id": invitation["shop_id"]
        }
        
        logger.info(f"Mechanic {invitation['mechanic_email']} accepted invitation")
        
        return MechanicSignupStep1Response(
            success=True,
            message="Invitation accepted. Now set your password.",
            mechanic_email=invitation["mechanic_email"],
            mechanic_name=invitation["mechanic_name"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mechanic signup step 1: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signup/step2", response_model=MechanicSignupStep2Response)
async def mechanic_signup_step2(request: MechanicSignupStep2Request):
    """Step 2: Mechanic sets password"""
    try:
        invitation_token = request.invitation_token
        password = request.password
        
        # Validate password
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
        # Check signup progress
        if invitation_token not in mechanic_signup_progress:
            raise HTTPException(status_code=400, detail="Invalid invitation or signup not started")
        
        progress = mechanic_signup_progress[invitation_token]
        
        if progress["step"] < 1:
            raise HTTPException(status_code=400, detail="Please accept invitation first")
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create mechanic record in database
        mechanic_data = {
            "shop_id": progress["shop_id"],
            "mail": progress["mechanic_email"],
            "password": hashed_password
        }
        
        try:
            response = supabase.table("mechanic").insert(mechanic_data).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create mechanic record")
            
            mechanic = response.data[0]
            mechanic_id = mechanic["mechanic_id"]
            
            # Update progress
            progress["mechanic_id"] = mechanic_id
            progress["password_hash"] = hashed_password
            progress["step"] = 2
            
            logger.info(f"Mechanic {progress['mechanic_email']} created in database with ID {mechanic_id}")
            
        except Exception as db_error:
            logger.error(f"Error creating mechanic record: {db_error}")
            raise HTTPException(status_code=500, detail=str(db_error))
        
        return MechanicSignupStep2Response(
            success=True,
            message="Password set successfully. Now upload your Aadhaar card.",
            mechanic_email=progress["mechanic_email"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mechanic signup step 2: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signup/step3-upload-aadhaar", response_model=AadhaarExtractionResponse)
async def mechanic_signup_step3_upload_aadhaar(invitation_token: str, phone_number: Optional[str] = None, file: UploadFile = File(...)):
    """Step 3: Mechanic uploads Aadhaar card"""
    try:
        if invitation_token not in mechanic_signup_progress:
            raise HTTPException(status_code=400, detail="Invalid invitation or signup not started")
        
        progress = mechanic_signup_progress[invitation_token]
        
        if progress["step"] < 2:
            raise HTTPException(status_code=400, detail="Please set password first")
        
        # Save file
        mechanic_email = progress["mechanic_email"]
        saved = save_upload_file(file, f"aadhaar/mechanic/{mechanic_email}")
        
        if not saved["success"]:
            raise HTTPException(status_code=400, detail=saved["error"])
        
        # Extract data using Groq
        extraction = extract_aadhaar_data(saved["file_path"])
        
        if not extraction.get("success"):
            delete_file(saved["file_path"])
            raise HTTPException(status_code=400, detail=extraction.get("error", "Failed to extract data"))
        
        # Store in progress
        progress["aadhaar_image"] = saved["file_path"]
        progress["aadhaar_data"] = extraction["data"]
        progress["phone_number"] = phone_number  # Store phone number during upload
        progress["step"] = 3
        
        logger.info(f"Aadhaar data extracted for mechanic {mechanic_email}")
        
        return AadhaarExtractionResponse(
            success=True,
            message="Aadhaar data extracted successfully. Please verify the information.",
            mechanic_email=mechanic_email,
            extracted_data=extraction["data"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mechanic signup step 3 upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signup/step3-verify-aadhaar", response_model=MechanicSignupStep3Response)
async def mechanic_signup_step3_verify_aadhaar(request: MechanicSignupStep3Request):
    """Step 3: Mechanic verifies Aadhaar data"""
    try:
        invitation_token = request.invitation_token
        
        if invitation_token not in mechanic_signup_progress:
            raise HTTPException(status_code=400, detail="Invalid invitation or signup not started")
        
        progress = mechanic_signup_progress[invitation_token]
        
        if progress["step"] < 3:
            raise HTTPException(status_code=400, detail="Please upload Aadhaar first")
        
        mechanic_id = progress.get("mechanic_id")
        
        if not mechanic_id:
            raise HTTPException(status_code=400, detail="Mechanic record not found")
        
        # Update mechanic with Aadhaar data
        update_data = {
            "name": request.mechanic_name,
            "gender": request.gender,
            "dob": request.dob,
            "aadhaar_number": request.aadhaar_number
        }
        
        # Add phone number if provided during upload
        if progress.get("phone_number"):
            update_data["phone_number"] = progress["phone_number"]
        
        try:
            response = supabase.table("mechanic").update(update_data).eq("mechanic_id", mechanic_id).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to update mechanic record")
            
            logger.info(f"Mechanic {mechanic_id} verified and activated with Aadhaar number {request.aadhaar_number}")
            
        except Exception as db_error:
            logger.error(f"Error updating mechanic record: {db_error}")
            raise HTTPException(status_code=500, detail=str(db_error))
        
        # Clean up progress and invitation
        del mechanic_signup_progress[invitation_token]
        del mechanic_invitations[invitation_token]
        
        return MechanicSignupStep3Response(
            success=True,
            message="Aadhaar verified! Your account is now active. You can now sign in.",
            mechanic_email=progress["mechanic_email"],
            mechanic_id=mechanic_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mechanic signup step 3 verify: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Mechanic Signin ====================

@router.post("/signin", response_model=MechanicSigninResponse)
async def mechanic_signin(request: MechanicSigninRequest):
    """Mechanic signin with email and password"""
    try:
        email = request.email
        password = request.password
        
        # Get mechanic
        response = supabase.table("mechanic").select("*").eq("mail", email).execute()
        
        if not response.data:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        mechanic = response.data[0]
        
        # Verify password
        if not verify_password(password, mechanic["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email, "mechanic_id": mechanic["mechanic_id"], "role": "mechanic"},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Mechanic signed in: {email}")
        
        return MechanicSigninResponse(
            success=True,
            message="Signin successful",
            access_token=access_token,
            mechanic=MechanicDetail(
                mechanic_id=mechanic["mechanic_id"],
                shop_id=mechanic["shop_id"],
                mechanic_email=mechanic["mail"],
                mechanic_name=mechanic.get("name", ""),
                gender=mechanic.get("gender", ""),
                dob=mechanic.get("dob", ""),
                aadhaar_number=mechanic.get("aadhaar_number", ""),
                phone_number=mechanic.get("phone_number"),
                status=mechanic.get("status", "active")
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mechanic signin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Mechanic Profile ====================

@router.get("/profile/{mechanic_id}", response_model=MechanicProfileResponse)
async def get_mechanic_profile(mechanic_id: int):
    """Get mechanic profile"""
    try:
        response = supabase.table("mechanic").select("*").eq("mechanic_id", mechanic_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Mechanic not found")
        
        mechanic = response.data[0]
        
        return MechanicProfileResponse(
            success=True,
            mechanic=MechanicDetail(
                mechanic_id=mechanic["mechanic_id"],
                shop_id=mechanic["shop_id"],
                mechanic_email=mechanic["mail"],
                mechanic_name=mechanic.get("name", ""),
                gender=mechanic.get("gender", ""),
                dob=mechanic.get("dob", ""),
                aadhaar_number=mechanic.get("aadhaar_number", ""),
                phone_number=mechanic.get("phone_number"),
                status=mechanic.get("status", "active")
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mechanic profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Owner: List Shop Mechanics ====================

@router.get("/shop/{owner_id}/mechanics", response_model=ListMechanicsResponse)
async def list_shop_mechanics(owner_id: int, limit: int = 100, offset: int = 0):
    """Owner: List all mechanics in their shop"""
    try:
        # Get owner's shop
        shop_response = supabase.table("shop").select("shop_id").eq("owner_id", owner_id).execute()
        
        if not shop_response.data:
            raise HTTPException(status_code=404, detail="Shop not found for owner")
        
        shop_id = shop_response.data[0]["shop_id"]
        
        # Get mechanics
        response = supabase.table("mechanic").select("*").eq("shop_id", shop_id).limit(limit).offset(offset).execute()
        
        mechanics = [
            MechanicDetail(
                mechanic_id=m["mechanic_id"],
                shop_id=m["shop_id"],
                mechanic_email=m["mail"],
                mechanic_name=m.get("name", ""),
                gender=m.get("gender", ""),
                dob=m.get("dob", ""),
                aadhaar_number=m.get("aadhaar_number", ""),
                phone_number=m.get("phone_number"),
                status=m.get("status", "active")
            )
            for m in response.data
        ]
        
        return ListMechanicsResponse(
            success=True,
            total=len(mechanics),
            mechanics=mechanics
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing mechanics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Owner: Remove Mechanic ====================

@router.delete("/remove")
async def remove_mechanic(owner_id: int, request: RemoveMechanicRequest):
    """Owner: Remove mechanic from shop"""
    try:
        mechanic_id = request.mechanic_id
        
        # Get mechanic
        mechanic_response = supabase.table("mechanic").select("*").eq("mechanic_id", mechanic_id).execute()
        
        if not mechanic_response.data:
            raise HTTPException(status_code=404, detail="Mechanic not found")
        
        mechanic = mechanic_response.data[0]
        
        # Verify owner owns the shop
        shop_response = supabase.table("shop").select("*").eq("shop_id", mechanic["shop_id"]).eq("owner_id", owner_id).execute()
        
        if not shop_response.data:
            raise HTTPException(status_code=403, detail="Not authorized to remove this mechanic")
        
        # Delete mechanic
        supabase.table("mechanic").delete().eq("mechanic_id", mechanic_id).execute()
        
        logger.info(f"Mechanic {mechanic_id} removed from shop")
        
        return {
            "success": True,
            "message": "Mechanic removed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing mechanic: {e}")
        raise HTTPException(status_code=500, detail=str(e))
