from sqlalchemy.orm import Session, joinedload
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_SetSRID, ST_MakePoint
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from .models import Branch, Business  # Assuming models are in the same directory/module


def business_near_point(point: Point, radius: int, db: Session):
    """
    Finds active branches within a given radius of a point.
    Optimized to pre-load business data to avoid N+1 queries.
    """
    search_point_wkb = from_shape(point, srid=4326)

    query = db.query(Branch).options(
        # --- OPTIMIZATION ---
        # Eagerly loads the related Business object in the same query.
        # This prevents a separate DB call for each branch to get its name.
        joinedload(Branch.business)
    ).filter(
        # --- FILTER ---
        # Ensures only active and available branches are returned.
        Branch.is_active == True,

        # Geospatial filter to find branches within the specified radius.
        ST_DWithin(
            Branch.location,
            search_point_wkb,
            radius
        )
    )

    return query.all()


def find_nearest_businesses_ordered(lat: float, lon: float, limit: int, db: Session):
    """
    Finds a limited number of the nearest active branches to a point,
    ordered by distance. Optimized to pre-load business data.
    """
    user_point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

    query = db.query(
        Branch,
        ST_Distance(Branch.location, user_point).label('distance')
    ).options(
        joinedload(Branch.business)
    ).filter(
        Branch.is_active == True # Only open branches
    ).order_by(
        'distance'  # Order by the calculated distance, closest first
    ).limit(
        limit
    )

    return query.all()

def get_branch_with_details_by_id(db: Session, branch_id: int):
    """
    Verilen ID'ye sahip aktif bir şubeyi, bağlı olduğu aktif işletme
    bilgileriyle birlikte getirir.
    """
    return db.query(Branch).options(
        joinedload(Branch.business)
    ).filter(
        Branch.id == branch_id,
        Branch.is_active == True,
        Branch.business.has(Business.is_active == True)
    ).first()
