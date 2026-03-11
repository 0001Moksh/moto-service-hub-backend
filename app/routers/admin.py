from fastapi import APIRouter, HTTPException
import logging
from datetime import timedelta

from app.core.database import supabase
from app.core.config import settings
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.email import send_email
from app.schemas.owner import ApproveShopRequest, ApproveShopResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ==================== Admin Login ====================

class AdminLoginRequest:
    admin_key: str


@router.post("/login")
async def admin_login(admin_key: str):
    """Admin login with admin key"""
    try:
        # Verify admin key
        if admin_key != settings.ADMIN_KEY:
            raise HTTPException(status_code=401, detail="Invalid admin key")
        
        # Get admin record
        admin_response = supabase.table("admin").select("*").eq("mail", settings.ADMIN_EMAIL).execute()
        
        if not admin_response.data:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        admin = admin_response.data[0]
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin["mail"], "admin_id": admin["admin_id"], "role": "admin"},
            expires_delta=access_token_expires
        )
        
        logger.info(f"✅ Admin logged in")
        
        return {
            "success": True,
            "message": "Admin login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "admin": {
                "admin_id": admin["admin_id"],
                "mail": admin["mail"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Dashboard Stats ====================

@router.get("/stats")
async def get_admin_stats():
    """Get dashboard statistics"""
    try:
        # Get counts
        customers_response = supabase.table("customer").select("count").execute()
        vehicles_response = supabase.table("vehicle").select("count").execute()
        bookings_response = supabase.table("booking").select("count").execute()
        services_response = supabase.table("service").select("count").execute()
        
        return {
            "success": True,
            "stats": {
                "total_customers": len(customers_response.data) if customers_response.data else 0,
                "total_vehicles": len(vehicles_response.data) if vehicles_response.data else 0,
                "total_bookings": len(bookings_response.data) if bookings_response.data else 0,
                "total_services": len(services_response.data) if services_response.data else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== List All Customers ====================

@router.get("/customers")
async def list_all_customers(limit: int = 100, offset: int = 0):
    """List all customers"""
    try:
        response = supabase.table("customer").select("*").limit(limit).offset(offset).execute()
        
        return {
            "success": True,
            "total": len(response.data),
            "customers": response.data
        }
    
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== List All Vehicles ====================

@router.get("/vehicles")
async def list_all_vehicles(limit: int = 100, offset: int = 0):
    """List all vehicles"""
    try:
        response = supabase.table("vehicle").select("*").limit(limit).offset(offset).execute()
        
        return {
            "success": True,
            "total": len(response.data),
            "vehicles": response.data
        }
    
    except Exception as e:
        logger.error(f"Error listing vehicles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Shop Request Management ====================

@router.get("/shop-requests")
async def list_shop_requests(status: str = None, limit: int = 100, offset: int = 0):
    """List shop requests (all or filtered by status: pending/approved/rejected)"""
    try:
        if status:
            response = supabase.table("request_shop").select("*").eq("status", status).limit(limit).offset(offset).execute()
        else:
            response = supabase.table("request_shop").select("*").limit(limit).offset(offset).execute()
        
        return {
            "success": True,
            "total": len(response.data),
            "requests": response.data
        }
    
    except Exception as e:
        logger.error(f"Error listing shop requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shop-requests/{request_id}")
async def get_shop_request(request_id: int):
    """Get a specific shop request"""
    try:
        response = supabase.table("request_shop").select("*").eq("request_id", request_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Shop request not found")
        
        return {
            "success": True,
            "request": response.data[0]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shop request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve-shop", response_model=ApproveShopResponse)
async def approve_shop(request: ApproveShopRequest):
    """Approve a shop request and create owner account"""
    try:
        request_id = request.request_id
        
        # Get the shop request
        response = supabase.table("request_shop").select("*").eq("request_id", request_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Shop request not found")
        
        shop_request = response.data[0]
        
        if shop_request["status"] != "pending":
            raise HTTPException(status_code=400, detail="Only pending requests can be approved")
        
        # Check if owner already exists
        existing_owner = supabase.table("owner").select("*").eq("mail", shop_request["mail"]).execute()
        if existing_owner.data:
            raise HTTPException(status_code=400, detail="Owner already exists")
        
        # Create owner account
        owner_data = {
            "mail": shop_request["mail"],
            "owner_name": shop_request["owner_name"],
            "gender": shop_request["gender"],
            "dob": shop_request["dob"],
            "aadhaar_number": shop_request["aadhaar_number"],
            "password": shop_request["password"]
        }
        
        try:
            owner_response = supabase.table("owner").insert(owner_data).execute()
            
            if not owner_response.data:
                raise HTTPException(status_code=500, detail="Failed to create owner account")
            
            owner = owner_response.data[0]
            owner_id = owner["owner_id"]
            
        except Exception as db_error:
            logger.error(f"Error creating owner account: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        # Create shop record
        shop_data = {
            "owner_id": owner_id,
            "shop_name": shop_request["shop_name"],
            "shop_location": shop_request["shop_location"],
            "phone_number": shop_request["phone_number"]
        }
        
        try:
            shop_response = supabase.table("shop").insert(shop_data).execute()
            
            if not shop_response.data:
                # Rollback owner creation
                supabase.table("owner").delete().eq("owner_id", owner_id).execute()
                raise HTTPException(status_code=500, detail="Failed to create shop record")
            
        except Exception as db_error:
            # Rollback owner creation
            supabase.table("owner").delete().eq("owner_id", owner_id).execute()
            logger.error(f"Error creating shop record: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        # Update request_shop status to approved
        try:
            supabase.table("request_shop").update({"status": "approved"}).eq("request_id", request_id).execute()
        except Exception as update_error:
            logger.error(f"Error updating request status: {update_error}")
        
        # Send approval email
        approval_email_subject = "Your Shop Owner Account Has Been Approved!"
        approval_email_body = f"""
Dear {shop_request['owner_name']},

Congratulations! Your shop owner application has been approved.

Shop Details:
- Shop Name: {shop_request['shop_name']}
- Location: {shop_request['shop_location']}
- Phone: {shop_request['phone_number']}

You can now sign in to your owner portal at:
{settings.FRONTEND_URL or 'https://yourdomain.com'}/owner/signin

Use your email and password to login and start managing your shop.

Best regards,
Moto Service Hub Team
"""
        
        try:
            send_email(shop_request["mail"], approval_email_subject, approval_email_body)
        except Exception as email_error:
            logger.warning(f"Failed to send approval email: {email_error}")
        
        logger.info(f"Shop request {request_id} approved. Owner account created for {shop_request['mail']}")
        
        return ApproveShopResponse(
            success=True,
            message="Shop request approved successfully. Owner account created and email sent.",
            owner_id=owner_id,
            request_id=request_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving shop request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject-shop")
async def reject_shop(request_id: int, reason: str = ""):
    """Reject a shop request"""
    try:
        # Get the shop request
        response = supabase.table("request_shop").select("*").eq("request_id", request_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Shop request not found")
        
        shop_request = response.data[0]
        
        if shop_request["status"] != "pending":
            raise HTTPException(status_code=400, detail="Only pending requests can be rejected")
        
        # Update request status
        supabase.table("request_shop").update({"status": "rejected"}).eq("request_id", request_id).execute()
        
        # Send rejection email
        rejection_email_subject = "Shop Owner Application Status"
        rejection_email_body = f"""
Dear {shop_request['owner_name']},

Thank you for applying to become a shop owner on Moto Service Hub.

Unfortunately, your application has been rejected.
Reason: {reason if reason else 'Not specified'}

If you have any questions, please contact our support team.

Best regards,
Moto Service Hub Team
"""
        
        try:
            send_email(shop_request["mail"], rejection_email_subject, rejection_email_body)
        except Exception as email_error:
            logger.warning(f"Failed to send rejection email: {email_error}")
        
        logger.info(f"Shop request {request_id} rejected for {shop_request['mail']}")
        
        return {
            "success": True,
            "message": "Shop request rejected. Email notification sent.",
            "request_id": request_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting shop request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

