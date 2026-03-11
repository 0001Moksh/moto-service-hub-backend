from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# ==================== Vehicle Schemas ====================

class VehicleBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    customer_id: Optional[int] = None
    reg_number: str
    owner_name: Optional[str] = None
    fuel: Optional[str] = None
    manufacturer: Optional[str] = None
    color: Optional[str] = None
    body_type: Optional[str] = None
    chassis_no: Optional[str] = None
    engine_no: Optional[str] = None
    model_no: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    reg_number: Optional[str] = None
    owner_name: Optional[str] = None
    fuel: Optional[str] = None
    manufacturer: Optional[str] = None
    color: Optional[str] = None
    body_type: Optional[str] = None
    chassis_no: Optional[str] = None
    engine_no: Optional[str] = None
    model_no: Optional[str] = None


class VehicleResponse(VehicleBase):
    vehicle_id: int
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class RCExtractionResponse(BaseModel):
    success: bool
    message: str
    extracted_data: dict
    step: str = "verify_rc_data"


class RCDataVerification(BaseModel):
    customer_id: int
    reg_number: str
    owner_name: Optional[str] = None
    fuel: Optional[str] = None
    vehicle_class: Optional[str] = None
    manufacturer: Optional[str] = None
    color: Optional[str] = None
    body_type: Optional[str] = None
    chassis_no: Optional[str] = None
    engine_no: Optional[str] = None
    model_no: Optional[str] = None
    registration_date: Optional[str] = None
    manufacture_date: Optional[str] = None
    refid_validity: Optional[str] = None


class VehicleAddCompleteResponse(BaseModel):
    success: bool
    message: str
    vehicle: Optional[VehicleResponse] = None
