from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from app.business.models import Business, Branch
from app.business.schemas import BusinessCreateResponse, BusinessCreateSchema


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
    try:
        db_branch = Branch(**branch_data.model_dump())
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
