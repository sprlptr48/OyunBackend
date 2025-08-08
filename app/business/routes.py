import logging
from typing import Optional

import geoalchemy2.types
from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.shape import to_shape
from shapely import Point
from sqlalchemy.orm import Session
from starlette import status

from . import service
from .models import *
from .schemas import BusinessCreateResponse, BusinessCreateSchema, CustomBusinessCreationResponse, BranchCreateSchema, \
    CustomBranchCreationResponse, BranchCreateResponse, PointSchema, BranchNearMeResponseList, BranchListResponse, \
    CustomBranchDetailResponse, CustomBranchUpdateResponse, BranchUpdateSchema, CustomBusinessDetailResponse, \
    BusinessDetailResponse, BranchSearchResponseList
from ..auth.models import User
from ..auth.service import get_current_user
from ..core.database import get_db

logger = logging.getLogger('uvicorn.error')
business_router = APIRouter(prefix="/business", tags=["Auth"])

@business_router.post("/create", response_model=CustomBusinessCreationResponse)
def create_business_endpoint(business_data: BusinessCreateSchema, db: Session = Depends(get_db)):
    result = service.create_business(business_data, db)
    if not result:
        return CustomBusinessCreationResponse(success=False, message="Business Creation Fail")
    return CustomBusinessCreationResponse(
        success=True, message="Business Created", business=BusinessCreateResponse.model_validate(result.__dict__))

@business_router.post("/create-branch")
def create_branch_endpoint(branch_data: BranchCreateSchema, db: Session = Depends(get_db)):
    result = service.create_branch(branch_data, db)
    if not result:
        return CustomBranchCreationResponse(success=False, message="Branch Creation Fail")

    # WKBElement'i PointSchema'ya dönüştürme
    shapely_point = to_shape(result.location)
    location_schema = PointSchema(
        latitude=shapely_point.y,
        longitude=shapely_point.x
    )

    # Yanıt modelini oluştururken dönüştürülmüş location'ı kullanma
    branch_response_data = result.__dict__.copy()
    branch_response_data['location'] = location_schema

    return CustomBranchCreationResponse(
        success=True,
        message="Branch Created",
        branch=BranchCreateResponse.model_validate(branch_response_data)
    )

# LAT: Kuzey güney LON: Doğu-Batı
@business_router.get("/near-me")
def business_near_me_endpoint(lat: float, lon: float, radius: int, db: Session = Depends(get_db)):
    """
    Takes in a Point(float longtitude, float latitude) and the radius and
    returns a list of businesses near the point.
    """
    location = Point(lon, lat)
    result = service.business_near_me(location, radius, db)

    if not result:
        return BranchNearMeResponseList(success=False, message="None Found")

    return BranchNearMeResponseList(
        success=True,
        message="Branches found",
        branches=result
    )

@business_router.get("/list")
def branch_list_endpoint(lat: float, lon: float, limit: int, db: Session = Depends(get_db)):
    """
    Takes in latitude and longitude and returns a list of businesses nearby,
    sorted from closest to farthest.
    """
    location = Point(lon, lat)
    result = service.branch_list(location, limit, db)

    if not result:
        return BranchListResponse(success=False, message="None Found")

    return BranchListResponse(
        success=True,
        message="Branches found",
        branches=result
    )

@business_router.get("/branch/{branch_id}", response_model=CustomBranchDetailResponse)
def get_branch_detail_endpoint(branch_id: int, db: Session = Depends(get_db)):
    """
    Belirli bir şubenin ve bağlı olduğu işletmenin detaylı bilgilerini getirir.
    Bu endpoint herkese açıktır.
    """
    branch_details = service.get_branch_details(db, branch_id)

    if not branch_details:
        return CustomBranchDetailResponse(
            success=False,
            message="Branch details not found",
            data=None
        )

    return CustomBranchDetailResponse(
        success=True,
        message="Branch details retrieved",
        data=branch_details
    )


@business_router.put("/branches/{branch_id}",response_model=CustomBranchUpdateResponse)
def update_branch_endpoint(branch_id: int, branch_data: BranchUpdateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Mevcut bir şubeyi günceller.
    - Kimlik doğrulaması (Authentication) gerektirir.
    - Kullanıcı, şubenin ait olduğu işletmenin sahibi olmalıdır (Authorization).
    """
    try:
        updated_branch = service.edit_branch(
            db=db,
            branch_id=branch_id,
            update_data=branch_data,
            current_user=current_user
        )
        shapely_point = to_shape(updated_branch.location)
        location_schema = PointSchema(
            latitude=shapely_point.y,
            longitude=shapely_point.x
        )
        branch_response_data = updated_branch.__dict__.copy()
        branch_response_data['location'] = location_schema

        return CustomBranchUpdateResponse(
            success=True,
            message="Branch updated successfully",
            branch=BranchCreateResponse.model_validate(branch_response_data)
        )
    except HTTPException as e:
        # Servis katmanından gelen HTTP hatalarını doğrudan yansıt
        raise e
    except Exception as e:
        # Beklenmedik bir hata oluşursa logla ve 500 hatası dön
        logger.error(f"Error updating branch {branch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )



@business_router.get("/{business_id}", response_model=CustomBusinessDetailResponse)
def get_business_detail_endpoint(business_id: int, db: Session = Depends(get_db)):
    """
    Belirli bir işletmenin tüm detaylarını ve şubelerini döndürür.
    Bu endpoint herkese açıktır, kimlik doğrulaması gerektirmez.
    """
    try:
        business_orm = service.get_business_details(db, business_id)

        serialized_branches = []
        for branch in business_orm.branches:
            location_schema = None
            if branch.location is not None:
                shapely_point = to_shape(branch.location)
                location_schema = PointSchema(
                    latitude=shapely_point.y,
                    longitude=shapely_point.x
                )

            branch_data = branch.__dict__
            branch_data['location'] = location_schema
            serialized_branches.append(BranchCreateResponse.model_validate(branch_data))

        business_data = business_orm.__dict__
        business_data['branches'] = serialized_branches

        final_business_response = BusinessDetailResponse.model_validate(business_data)

        return CustomBusinessDetailResponse(
            success=True,
            message="Business details fetched successfully",
            business=final_business_response
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching details for business {business_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )

@business_router.get("/branches/search", response_model=BranchSearchResponseList)
def search_branches_endpoint(keyword: str, lat: Optional[float] = None, lon: Optional[float] = None, radius: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Anahtar kelime ve opsiyonel lokasyon ile şube arar.
    - **keyword**: İşletme adı veya adreste aranacak metin.
    - **lat, lon**: Arama yapılacak merkez noktanın enlem ve boylamı.
    - **radius**: Merkez noktadan itibaren aranacak alanın metre cinsinden yarıçapı.
    """
    results = service.search_for_branches(
        db=db,
        keyword=keyword,
        lat=lat,
        lon=lon,
        radius=radius
    )
    if not results:
        return BranchSearchResponseList(success=True, message="No branches found matching your criteria.", branches=[])
    return BranchSearchResponseList(
        success=True,
        message=f"{len(results)} branches found.",
        branches=results
    )
