from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin
from geoalchemy2.shape import from_shape
from sqlalchemy import func
from sqlalchemy.orm import Session
from shapely.geometry import Point

from app.business.models import Branch
from app.business.schemas import PointSchema
import geoalchemy2

def business_near_point(point: Point, radius: int, db: Session): # business in a circle
    #search_point: Point = Point(point.longitude, point.latitude) # Convert to usable type(simplify wkb conv)
    search_point_wkb = from_shape(point, srid=4326)

    return db.query(Branch).filter(
        ST_DWithin(
            Branch.location,
            search_point_wkb,
            radius
        )
    ).all()


def find_nearest_businesses_ordered(lat: float, lon: float, limit: int, db: Session): # business list ordered by closest
    user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    # Query for the Business objects.
    # We also include the distance from the user_point in the query result.
    query = db.query(
        Branch,
        func.ST_Distance(Branch.location, user_point).label('distance')
    )
    # Order the results by the calculated distance in ascending order (closest first).
    query = query.order_by('distance')

    query = query.limit(limit)

    return query.all()

