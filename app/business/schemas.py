from datetime import datetime, timezone
from typing import Optional, List

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

class BranchNearMeItem(BaseModel):
    id: int
    business_id: int
    business_name: str  # JOIN ile business tablosundan
    location: PointSchema | None

    model_config = ConfigDict(from_attributes=True)

class BranchNearMeResponseList(BaseModel):
    success: bool
    message: str | None = None
    branches: list[BranchNearMeItem] | None = None


class BranchListItem(BaseModel):
    id: int
    business_id: int
    business_name: str  # JOIN ile business tablosundan
    location: PointSchema | None
    distance: float

    model_config = ConfigDict(from_attributes=True)

class BranchListResponse(BaseModel):
    success: bool
    message: str
    branches: list[BranchListItem] | None = None

class BranchDetailSchema(BaseModel):
    # Şube (Branch)
    id: int
    address_text: str
    phone: str
    location: PointSchema | None
    is_active: bool
    # Business
    business_id: int
    business_name: str
    business_description: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class CustomBranchDetailResponse(BaseModel):
    success: bool
    message: str
    data: BranchDetailSchema | None = None


class BranchUpdateSchema(BaseModel):
    address_text: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[PointSchema] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

class CustomBranchUpdateResponse(BaseModel):
    success: bool
    message: str
    branch: Optional[BranchCreateResponse] = None


class BusinessDetailResponse(BaseModel):
    """
    Bir işletmenin kendi detaylarını ve şubelerinin listesini içeren ana model.
    """
    id: int
    owner_id: int
    name: str
    description: str
    is_active: bool
    branches: List[BranchCreateResponse]

    model_config = ConfigDict(from_attributes=True)
class CustomBusinessDetailResponse(BaseModel):
    success: bool
    message: str
    business: BusinessDetailResponse | None = None

class BranchSearchResponseList(BaseModel):
    """
    /branches/search endpoint'i için yanıt
    """
    success: bool
    message: str | None = None
    branches: list[BranchNearMeItem] | None = None


class CustomSuccessResponse(BaseModel):
    """
    Başarılı silme veya benzeri işlemler için genel yanıt modeli.
    """
    success: bool
    message: str


class MyBranchInfo(BaseModel):
    """
    'Benim İşletmelerim' listesinde her bir branch için gösterilecek özet bilgi.
    """
    id: int
    address_text: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MyBusinessListItem(BaseModel):
    """
    'Benim İşletmelerim' listesindeki her bir işletmeyi temsil eden model.
    İşletmenin temel bilgilerini ve sahip olduğu şubelerin listesini içerir.
    """
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    branches: List[MyBranchInfo] = [] # İşletmeye ait şubelerin listesi

    model_config = ConfigDict(from_attributes=True)


class MyBusinessListResponse(BaseModel):
    """
    /my-businesses endpoint'inin ana yanıt modeli.
    """
    success: bool
    businesses: List[MyBusinessListItem] = []
