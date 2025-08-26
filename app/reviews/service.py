from typing import List
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.auth.models import User
from app.reviews import crud
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreateSchema

logger = logging.getLogger('uvicorn.error')


def create_new_review(db: Session, review_data: ReviewCreateSchema, current_user: User) -> Review:
    """
    Business logic for creating a new review.
    """
    try:
        # Here you could add more logic in the future, like checking if the
        # user has visited the branch before allowing a review.
        review = crud.create_review(db, review_data, current_user.userid)
        return review
    except Exception as e:
        logger.error(f"Error creating review: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the review."
        )


def get_all_reviews_for_branch(db: Session, branch_id: int) -> List[Review]:
    """
    Business logic for fetching reviews for a specific branch.
    """
    try:
        return crud.get_reviews_by_branch_id(db, branch_id)
    except Exception as e:
        logger.error(f"Error fetching reviews for branch {branch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching reviews."
        )


def get_my_reviews(db: Session, current_user: User) -> List[Review]:
    """
    Business logic for fetching all reviews written by the current user.
    """
    try:
        return crud.get_reviews_by_user_id(db, current_user.userid)
    except Exception as e:
        logger.error(f"Error fetching reviews for user {current_user.userid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching your reviews."
        )
