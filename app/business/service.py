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


def business_near_me(location: Point, radius: int, db: Session):
    """
    Takes in a Point(float longtitude, float latitude) and the radius and
    returns a list of businesses near the point.
    """
    branches_orm = crud.business_near_point(point=location, radius=radius, db=db)
    if not branches_orm:
        return None

    result_list = []
    for branch in branches_orm:
        formatted_data = _calculate_is_open_and_format_branch(branch)
        result_list.append(BranchNearMeItem.model_validate(formatted_data))

    return result_list


def branch_list(location: Point, limit: int, db: Session):
    branches_with_distance = crud.find_nearest_businesses_ordered(lat=location.y, lon=location.x, limit=limit, db=db)
    if not branches_with_distance:
        return None

    result_list = []
    for branch, distance in branches_with_distance:
        formatted_data = _calculate_is_open_and_format_branch(branch)
        formatted_data['distance'] = distance
        result_list.append(BranchListItem.model_validate(formatted_data))

    return result_list


def get_branch_details(db: Session, branch_id: int):
    branch_orm = crud.get_branch_by_id(db=db, branch_id=branch_id)
    if not branch_orm or not branch_orm.is_active or not branch_orm.business.is_active:
        return None

    formatted_data = _calculate_is_open_and_format_branch(branch_orm)
    return BranchDetailSchema.model_validate(formatted_data)

def edit_branch(db: Session, branch_id: int, update_data: BranchUpdateSchema, current_user: User):
    """
    Bir şubeyi düzenlemek için iş mantığını ve yetkilendirmeyi yönetir.
    """
    db_branch = crud.get_branch_by_id(db, branch_id)

    if not db_branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    if db_branch.business.owner_id != current_user.userid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this branch")
    # Yetki varsa düzenlemeyi yap ve bildir
    return crud.update_branch(db, db_branch, update_data)

def get_my_businesses(db: Session, current_user: User):
    """
    Oturum açmış kullanıcının sahip olduğu işletmeleri listelemek için iş mantığını yönetir. Auth gerekli
    """
    businesses = crud.get_businesses_by_owner_id(db, owner_id=current_user.userid)
    return businesses



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
    if not branches:
        return None

    result_list = []
    for branch in branches:
        formatted_data = _calculate_is_open_and_format_branch(branch)
        result_list.append(BranchNearMeItem.model_validate(formatted_data))

    return result_list

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


def _calculate_is_open_and_format_branch(branch: Branch):
    """
    Bir Branch ORM nesnesi alır, anlık 'is_open' durumunu hesaplar
    ve Pydantic şemasına uygun bir dict döndürür.
    """
    now_utc = datetime.now(timezone.utc)
    current_weekday = now_utc.weekday()  # Monday is 0, Sunday is 6
    previous_weekday = (current_weekday - 1) % 7
    current_time = now_utc.time()

    is_open = False

    # IS_OPEN Calculation
    for hour in branch.opening_hours:
        hour_weekday = hour.day_of_week.value

        # Skip if this day is not relevant
        if hour_weekday != current_weekday and hour_weekday != previous_weekday:
            continue

        # Case 1: Normal hours on current day (opens <= closes)
        if hour_weekday == current_weekday and hour.opens <= hour.closes:
            if hour.opens <= current_time < hour.closes:
                is_open = True
                break

        # Case 2: Overnight hours starting today (opens > closes)
        elif hour_weekday == current_weekday and hour.opens > hour.closes:
            if current_time >= hour.opens:
                is_open = True
                break

        # Case 3: Overnight hours from previous day
        elif hour_weekday == previous_weekday and hour.opens > hour.closes:
            if current_time < hour.closes:
                is_open = True
                break

    # Format opening hours for API response
    formatted_opening_hours = [
        {
            "day_of_week": hour.day_of_week.name.lower(),
            "opens": hour.opens.strftime("%H:%M:%S"),
            "closes": hour.closes.strftime("%H:%M:%S")
        } for hour in branch.opening_hours
    ]
    # Format branch data for API response
    branch_data = {
        'id': branch.id,
        'business_id': branch.business_id,
        'business_name': branch.business.name,
        'is_open': is_open,
        'address_text': branch.address_text,
        'phone': branch.phone,
        'is_active': branch.is_active,
        'business_description': branch.business.description,
        'created_at': branch.created_at,
        'opening_hours': formatted_opening_hours,
        'location': None
    }

    if branch.location:
        shapely_point = to_shape(branch.location)
        branch_data['location'] = PointSchema(latitude=shapely_point.y, longitude=shapely_point.x)

    return branch_data
