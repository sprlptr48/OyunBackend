from sqlalchemy.orm import Session

from app.business.schemas import PointSchema
import geoalchemy2

def business_near_point(point: PointSchema, db: Session):
    db.query(point).filter_by()