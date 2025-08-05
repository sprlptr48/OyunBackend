from datetime import datetime, timezone
from pydantic import ConfigDict, BaseModel

class BusinessCreateSchema(BaseModel):
    owner_id: int
    name: str
    description: str
    #business_type_id: ?
    is_active: bool | None = None
    created_at: datetime | None = None
class BusinessCreateResponse(BusinessCreateSchema):
    id: int
    created_at: datetime
class CustomBusinessCreationResponse(BaseModel):
    success: bool
    message: str
    business: BusinessCreateResponse | None = None

class PointSchema(BaseModel):
    latitude: float
    longitude: float

class BranchCreateSchema(BaseModel):
    business_id: int
    address_text: str
    phone: str
    location: PointSchema
    is_active: bool
    created_at: datetime | None = None

class BranchCreateResponse(BranchCreateSchema):
    id: int

class CustomBranchCreationResponse(BaseModel):
    success: bool
    message: str
    branch: BranchCreateResponse | None = None

