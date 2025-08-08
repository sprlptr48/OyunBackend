from datetime import datetime, timezone
import logging
from typing import Optional

from fastapi import HTTPException
from geoalchemy2.functions import ST_MakePoint
from geoalchemy2.shape import to_shape
from shapely import Point
from sqlalchemy.orm import Session
from starlette import status

from app.auth.models import User
from app.business import crud
from app.business.crud import business_near_point, find_nearest_businesses_ordered
from app.business.models import Business, Branch
from app.business.schemas import BusinessCreateResponse, BusinessCreateSchema, PointSchema, BranchNearMeResponseList, \
    BranchListResponse, BranchListItem, BranchNearMeItem, BranchDetailSchema, BranchUpdateSchema, CustomSuccessResponse


def create_business(business_data: BusinessCreateSchema, db: Session) -> Business | None:
    try:
        db_business = Business(**business_data.model_dump())
        db.add(db_business)
        db.commit()
        db.refresh(db_business)
        return db_business
    except Exception as e:
        # Always rollback in case of an error to prevent a broken transaction
        db.rollback()
        logging.error(f"Error creating business: {e}")
        # Raise an HTTPException to provide a clear error message to the client
        return None


def create_branch(branch_data, db):
    try: # TODO: Frontend için WKT mi iyi yoksa Point(float, float) mı?
        # Location verisini WKT formatına dönüştürmek için ST_MakePoint
        location_point = ST_MakePoint(branch_data.location.longitude, branch_data.location.latitude)
        # Diğer veriler model_dump ile
        branch_data_dict = branch_data.model_dump(exclude={"location"})
        # location'ı düzeltilmiş değerle güncelle
        db_branch = Branch(**branch_data_dict, location=location_point)
        db.add(db_branch)
        db.commit()
        db.refresh(db_branch)
        return db_branch
    except Exception as e:
        # Always rollback in case of an error to prevent a broken transaction
        db.rollback()
        logging.error(f"Error creating business: {e}")
        # Raise an HTTPException to provide a clear error message to the client
        return None


def business_near_me(location: Point, radius, db):
    """
    Takes in a Point(float longtitude, float latitude) and the radius and
    returns a list of businesses near the point.
    """
    # TODO: Frontend için WKT mi iyi yoksa Point(float, float) mı?

    branches = business_near_point(location, radius, db)
    if not branches:
        return None

    # Convert to response schema
    branch_responses = []
    for branch in branches:
        location_schema = None
        if branch.location:
            shapely_point = to_shape(branch.location)
            location_schema = PointSchema(
                latitude=shapely_point.y,
                longitude=shapely_point.x
            )

        # Yeni, yalın şemayı kullanarak yanıt oluşturuluyor
        branch_response = BranchNearMeItem(
            id=branch.id,
            business_id=branch.business_id,
            business_name=branch.business.name,  # İlişki üzerinden isme erişim
            location=location_schema
        )
        branch_responses.append(branch_response)
    return branch_responses


def branch_list(location: Point, limit, db):
    branches_with_distance = find_nearest_businesses_ordered(location.y, location.x, limit, db)
    if not branches_with_distance:
        return None

    branches_list = []
    for branch, distance in branches_with_distance:
        location_schema = None
        if branch.location:
            shapely_point = to_shape(branch.location)
            location_schema = PointSchema(
                latitude=shapely_point.y,
                longitude=shapely_point.x
            )

        branch_response = BranchListItem(
            id=branch.id,
            business_id=branch.business_id,
            business_name=branch.business.name,
            location=location_schema,
            distance=distance
        )
        branches_list.append(branch_response)

    return branches_list

def get_branch_details(db: Session, branch_id: int):
    """
    Şube detaylarını alır ve yanıt şemasına uygun hale getirir.
    """
    branch = crud.get_branch_with_details_by_id(db, branch_id)

    if not branch:
        return None

    # Konum verisini Pydantic şemasına dönüştür
    location_schema = None
    if branch.location:
        shapely_point = to_shape(branch.location)
        location_schema = PointSchema(
            latitude=shapely_point.y,
            longitude=shapely_point.x
        )

    return BranchDetailSchema(
        id=branch.id,
        address_text=branch.address_text,
        phone=branch.phone,
        location=location_schema,
        is_active=branch.is_active,
        business_id=branch.business.id,
        business_name=branch.business.name,
        business_description=branch.business.description,
        created_at=branch.created_at
    )


def edit_branch(db: Session, branch_id: int, update_data: BranchUpdateSchema, current_user: User):
    """
    Bir şubeyi düzenlemek için iş mantığını ve yetkilendirmeyi yönetir.
    """
    db_branch = crud.get_branch_by_id(db, branch_id)
    if not db_branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )

    if db_branch.business.owner_id != current_user.userid: #sahibi değilse
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this branch"
        )

    # yetki varsa güncelleme işlemini yap.
    updated_branch = crud.update_branch(db, db_branch, update_data)
    return updated_branch


def get_business_details(db: Session, business_id: int):
    """
    İşletme detaylarını getir (şubeleriyle birlikte)
    """
    business = crud.get_business_with_branches_by_id(db, business_id)

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business with the specified ID not found."
        )


    return business


def search_for_branches(db: Session, keyword: str, lat: Optional[float], lon: Optional[float], radius: Optional[int]) \
        -> list[BranchNearMeItem]:
    """
    Arama parametrelerini işler, CRUD'u çağırır ve sonucu formatlar.
    """
    point = None
    if lat is not None and lon is not None:
        point = Point(lon, lat)

    branches = crud.search_branches(db, keyword=keyword, point=point, radius=radius)
    # Sonuçları Pydantic şemasına dönüştür.
    branch_responses = []
    for branch in branches:
        location_schema = None
        if branch.location:
            shapely_point = to_shape(branch.location)
            location_schema = PointSchema(
                latitude=shapely_point.y,
                longitude=shapely_point.x
            )
        branch_responses.append(
            BranchNearMeItem(
                id=branch.id,
                business_id=branch.business_id,
                business_name=branch.business.name,
                location=location_schema
            )
        )
    return branch_responses

def remove_branch(db: Session, branch_id: int, current_user: User) -> CustomSuccessResponse :
    """
    Bir şubeyi silmek için iş mantığını ve yetkilendirmeyi yönetir.
    """
    # Şube var mı? (get_branch_by_id)
    db_branch = crud.get_branch_by_id(db, branch_id)
    if not db_branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    #Bu kullanıcı bu şubeyi silebilir mi?
    if db_branch.business.owner_id != current_user.userid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this branch"
        )
    #Yetki varsa, sil.
    crud.delete_branch(db, db_branch)
    return CustomSuccessResponse(success=True, message="Branch deleted")
