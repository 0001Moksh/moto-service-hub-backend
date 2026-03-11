from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import logging

# Load environment variables before importing supabase
from dotenv import load_dotenv
load_dotenv('.env.local')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Moto Service Hub - CRUD Test",
    description="Testing CRUD operations with Supabase Database",
    version="1.0.0"
)

# Supabase initialization
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in .env.local")

# Import and create Supabase client
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as client_error:
    logger.error(f"Failed to initialize Supabase: {client_error}")
    # Try alternative initialization method
    import supabase as sp
    supabase = sp.Client(SUPABASE_URL, SUPABASE_KEY)

# ==================== Pydantic Models ====================

class AdminCreate(BaseModel):
    mail: str
    password: str

class AdminUpdate(BaseModel):
    mail: Optional[str] = None
    password: Optional[str] = None

class CustomerCreate(BaseModel):
    mail: str
    password: str
    phone_number: Optional[str] = None

class CustomerUpdate(BaseModel):
    mail: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None

class VehicleCreate(BaseModel):
    customer_id: Optional[int] = None
    reg_number: str
    owner_name: Optional[str] = None
    fuel: Optional[str] = None
    manufacturer: Optional[str] = None

class VehicleUpdate(BaseModel):
    reg_number: Optional[str] = None
    owner_name: Optional[str] = None
    fuel: Optional[str] = None
    manufacturer: Optional[str] = None

# ==================== Admin Endpoints ====================

@app.get("/test/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Moto Service Hub CRUD Testing API is running",
        "supabase_connected": True
    }

@app.post("/test/admin/create", tags=["Admin"])
async def create_admin(admin: AdminCreate):
    """Create a new admin record"""
    try:
        response = supabase.table("admin").insert({
            "mail": admin.mail,
            "password": admin.password
        }).execute()
        
        return {
            "success": True,
            "message": "Admin created successfully",
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error creating admin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/test/admin/list", tags=["Admin"])
async def list_admins():
    """Get all admin records"""
    try:
        response = supabase.table("admin").select("*").execute()
        
        return {
            "success": True,
            "message": "Admins retrieved successfully",
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error listing admins: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/test/admin/{admin_id}", tags=["Admin"])
async def get_admin(admin_id: int):
    """Get a specific admin by ID"""
    try:
        response = supabase.table("admin").select("*").eq("admin_id", admin_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        return {
            "success": True,
            "message": "Admin retrieved successfully",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting admin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/test/admin/{admin_id}", tags=["Admin"])
async def update_admin(admin_id: int, admin: AdminUpdate):
    """Update an admin record"""
    try:
        update_data = {k: v for k, v in admin.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table("admin").update(update_data).eq("admin_id", admin_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        return {
            "success": True,
            "message": "Admin updated successfully",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating admin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/test/admin/{admin_id}", tags=["Admin"])
async def delete_admin(admin_id: int):
    """Delete an admin record"""
    try:
        response = supabase.table("admin").delete().eq("admin_id", admin_id).execute()
        
        return {
            "success": True,
            "message": "Admin deleted successfully",
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error deleting admin: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== Customer Endpoints ====================

@app.post("/test/customer/create", tags=["Customer"])
async def create_customer(customer: CustomerCreate):
    """Create a new customer record"""
    try:
        response = supabase.table("customer").insert({
            "mail": customer.mail,
            "password": customer.password,
            "phone_number": customer.phone_number
        }).execute()
        
        return {
            "success": True,
            "message": "Customer created successfully",
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/test/customer/list", tags=["Customer"])
async def list_customers():
    """Get all customer records"""
    try:
        response = supabase.table("customer").select("*").execute()
        
        return {
            "success": True,
            "message": "Customers retrieved successfully",
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/test/customer/{customer_id}", tags=["Customer"])
async def get_customer(customer_id: int):
    """Get a specific customer by ID"""
    try:
        response = supabase.table("customer").select("*").eq("customer_id", customer_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            "success": True,
            "message": "Customer retrieved successfully",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/test/customer/{customer_id}", tags=["Customer"])
async def update_customer(customer_id: int, customer: CustomerUpdate):
    """Update a customer record"""
    try:
        update_data = {k: v for k, v in customer.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table("customer").update(update_data).eq("customer_id", customer_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            "success": True,
            "message": "Customer updated successfully",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/test/customer/{customer_id}", tags=["Customer"])
async def delete_customer(customer_id: int):
    """Delete a customer record"""
    try:
        response = supabase.table("customer").delete().eq("customer_id", customer_id).execute()
        
        return {
            "success": True,
            "message": "Customer deleted successfully",
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error deleting customer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== Vehicle Endpoints ====================

@app.post("/test/vehicle/create", tags=["Vehicle"])
async def create_vehicle(vehicle: VehicleCreate):
    """Create a new vehicle record"""
    try:
        response = supabase.table("vehicle").insert({
            "customer_id": vehicle.customer_id,
            "reg_number": vehicle.reg_number,
            "owner_name": vehicle.owner_name,
            "fuel": vehicle.fuel,
            "manufacturer": vehicle.manufacturer
        }).execute()
        
        return {
            "success": True,
            "message": "Vehicle created successfully",
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error creating vehicle: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/test/vehicle/list", tags=["Vehicle"])
async def list_vehicles():
    """Get all vehicle records"""
    try:
        response = supabase.table("vehicle").select("*").execute()
        
        return {
            "success": True,
            "message": "Vehicles retrieved successfully",
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error listing vehicles: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/test/vehicle/{vehicle_id}", tags=["Vehicle"])
async def get_vehicle(vehicle_id: int):
    """Get a specific vehicle by ID"""
    try:
        response = supabase.table("vehicle").select("*").eq("vehicle_id", vehicle_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {
            "success": True,
            "message": "Vehicle retrieved successfully",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vehicle: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/test/vehicle/{vehicle_id}", tags=["Vehicle"])
async def update_vehicle(vehicle_id: int, vehicle: VehicleUpdate):
    """Update a vehicle record"""
    try:
        update_data = {k: v for k, v in vehicle.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        response = supabase.table("vehicle").update(update_data).eq("vehicle_id", vehicle_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {
            "success": True,
            "message": "Vehicle updated successfully",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/test/vehicle/{vehicle_id}", tags=["Vehicle"])
async def delete_vehicle(vehicle_id: int):
    """Delete a vehicle record"""
    try:
        response = supabase.table("vehicle").delete().eq("vehicle_id", vehicle_id).execute()
        
        return {
            "success": True,
            "message": "Vehicle deleted successfully",
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error deleting vehicle: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== Raw Query Testing ====================

@app.get("/test/query/{table_name}", tags=["Testing"])
async def test_raw_query(table_name: str):
    """Test raw query on any table (up to 100 records)"""
    try:
        response = supabase.table(table_name).select("*").limit(100).execute()
        
        return {
            "success": True,
            "table": table_name,
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        logger.error(f"Error querying {table_name}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
