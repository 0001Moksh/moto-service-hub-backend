from fastapi import APIRouter, HTTPException, UploadFile, File
import logging

from app.core.database import supabase
from app.schemas.vehicle import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    RCExtractionResponse, RCDataVerification, VehicleAddCompleteResponse
)
from app.utils.file_handler import save_upload_file, delete_file
from app.utils.groq_service import extract_rc_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vehicle", tags=["Vehicle"])

# In-memory storage for RC extraction progress
rc_progress = {}


# ==================== Upload RC & Extract Data ====================

@router.post("/add/step1-upload-rc", response_model=RCExtractionResponse)
async def add_vehicle_step1_upload_rc(customer_id: int, file: UploadFile = File(...)):
    """Step 1: Customer uploads RC and data is extracted"""
    try:
        # Verify customer exists
        customer_response = supabase.table("customer").select("*").eq("customer_id", customer_id).execute()
        if not customer_response.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_email = customer_response.data[0]["mail"]
        
        # Save file
        saved = save_upload_file(file, f"rc/{customer_email}")
        if not saved["success"]:
            raise HTTPException(status_code=400, detail=saved["error"])
        
        # Extract data using Groq
        extraction = extract_rc_data(saved["file_path"])
        
        if not extraction.get("success"):
            delete_file(saved["file_path"])
            raise HTTPException(status_code=400, detail=extraction.get("error", "Failed to extract data"))
        
        # Store extraction in memory (don't insert to DB yet - wait for Step 2)
        # This avoids duplicate key issues if same reg_number is uploaded again
        extracted_data = extraction["data"]
        rc_progress[customer_id] = {
            "customer_id": customer_id,
            "rc_image": saved["file_path"],
            "rc_data": extracted_data,
            "step": 1
        }
        
        logger.info(f"RC data extracted for customer {customer_id}")
        
        return RCExtractionResponse(
            success=True,
            message="RC data extracted successfully. Please verify the information.",
            extracted_data=extraction["data"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading RC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Verify RC Data & Save Vehicle ====================

@router.post("/add/step2-verify-rc", response_model=VehicleAddCompleteResponse)
async def add_vehicle_step2_verify_rc(request: RCDataVerification):
    """Step 2: Customer verifies/edits RC data and saves vehicle"""
    try:
        customer_id = request.customer_id
        
        # Check extraction progress
        if customer_id not in rc_progress:
            raise HTTPException(status_code=400, detail="Please upload RC first")
        
        # Prepare all vehicle data with verified values
        vehicle_data = {
            "customer_id": customer_id,
            "reg_number": request.reg_number,
            "owner_name": request.owner_name,
            "fuel": request.fuel,
            "vehicle_class": request.vehicle_class,
            "manufacturer": request.manufacturer,
            "color": request.color,
            "body_type": request.body_type,
            "chassis_no": request.chassis_no,
            "engine_no": request.engine_no,
            "model_no": request.model_no,
            "registration_date": request.registration_date,
            "manufacture_date": request.manufacture_date,
            "refid_validity": request.refid_validity
        }
        # Remove None values
        vehicle_data = {k: v for k, v in vehicle_data.items() if v is not None}
        
        try:
            # Check if vehicle with this reg_number already exists
            existing = supabase.table("vehicle").select("*").eq("reg_number", request.reg_number).execute()
            
            if existing.data:
                # Vehicle exists, update it
                vehicle_id = existing.data[0]["vehicle_id"]
                response = supabase.table("vehicle").update(vehicle_data).eq("vehicle_id", vehicle_id).execute()
                logger.info(f"Vehicle record updated in DB for customer {customer_id}")
            else:
                # Vehicle doesn't exist, insert it
                response = supabase.table("vehicle").insert(vehicle_data).execute()
                if response.data:
                    logger.info(f"Vehicle record created in DB for customer {customer_id}")
            
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to add vehicle")
            
            vehicle = response.data[0]
        except HTTPException:
            raise
        except Exception as db_error:
            logger.error(f"Error saving vehicle in DB: {db_error}")
            raise HTTPException(status_code=500, detail=str(db_error))
        
        # Clean up progress
        del rc_progress[customer_id]
        
        logger.info(f"Vehicle added for customer {customer_id}")
        
        return VehicleAddCompleteResponse(
            success=True,
            message="Vehicle added successfully!",
            vehicle=VehicleResponse(**vehicle)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying RC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Create Vehicle Directly ====================

@router.post("/create", response_model=VehicleResponse)
async def create_vehicle(vehicle: VehicleCreate):
    """Create vehicle directly (without RC extraction)"""
    try:
        # Verify customer exists if provided
        if vehicle.customer_id:
            customer_response = supabase.table("customer").select("*").eq("customer_id", vehicle.customer_id).execute()
            if not customer_response.data:
                raise HTTPException(status_code=404, detail="Customer not found")
        
        response = supabase.table("vehicle").insert(vehicle.dict()).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create vehicle")
        
        logger.info(f"✅ Vehicle created: {vehicle.reg_number}")
        
        return VehicleResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vehicle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Get Vehicle ====================

@router.get("/get/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int):
    """Get vehicle details"""
    try:
        response = supabase.table("vehicle").select("*").eq("vehicle_id", vehicle_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return VehicleResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vehicle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== List Customer Vehicles ====================

class VehicleListResponse:
    vehicles: list[VehicleResponse]
    total: int


@router.get("/list/{customer_id}")
async def list_customer_vehicles(customer_id: int):
    """Get all vehicles for a customer"""
    try:
        response = supabase.table("vehicle").select("*").eq("customer_id", customer_id).execute()
        
        vehicles = [VehicleResponse(**v) for v in response.data]
        
        return {
            "success": True,
            "total": len(vehicles),
            "vehicles": vehicles
        }
    
    except Exception as e:
        logger.error(f"Error listing vehicles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Update Vehicle ====================

@router.put("/update/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: int, vehicle: VehicleUpdate):
    """Update vehicle details"""
    try:
        # Remove None values
        update_data = {k: v for k, v in vehicle.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table("vehicle").update(update_data).eq("vehicle_id", vehicle_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        logger.info(f"✅ Vehicle {vehicle_id} updated")
        
        return VehicleResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Delete Vehicle ====================

@router.delete("/delete/{vehicle_id}")
async def delete_vehicle(vehicle_id: int):
    """Delete vehicle"""
    try:
        response = supabase.table("vehicle").delete().eq("vehicle_id", vehicle_id).execute()
        
        logger.info(f"✅ Vehicle {vehicle_id} deleted")
        
        return {
            "success": True,
            "message": "Vehicle deleted successfully",
            "vehicle_id": vehicle_id
        }
    
    except Exception as e:
        logger.error(f"Error deleting vehicle: {e}")
        raise HTTPException(status_code=500, detail=str(e))
