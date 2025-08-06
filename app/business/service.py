from datetime import datetime, timezone
import logging

from anyio import create_udp_socket
from geoalchemy2.functions import ST_MakePoint
from geoalchemy2.shape import to_shape
from shapely import Point
from sqlalchemy.orm import Session

from app.business.crud import business_near_point, find_nearest_businesses_ordered
from app.business.models import Business, Branch
from app.business.schemas import BusinessCreateResponse, BusinessCreateSchema, PointSchema, BranchNearMeResponseList, \
    BranchNearMeResponse, BranchListResponse, BranchListItem


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

        branch_response = BranchNearMeResponse(
            id=branch.id,
            business_id=branch.business_id,
            address_text=branch.address_text,
            phone=branch.phone,
            location=location_schema,
            is_active=branch.is_active,
            created_at=branch.created_at
        )
        branch_responses.append(branch_response)
    return branch_responses


def branch_list(location: Point, limit, db):
    branches = find_nearest_businesses_ordered(location.y, location.x, limit, db)
    if not branches:
        return None

    branches_list = []
    for branch, distance in branches: #Create a list from return values
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
            address_text=branch.address_text,
            phone=branch.phone,
            location=location_schema,
            is_active=branch.is_active,
            created_at=branch.created_at,
            distance=distance
        )
        branches_list.append(branch_response)

    return branches_list
