import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.core.database import get_db
from app.reviews import service
from app.reviews.schemas import (
    ReviewCreateSchema,
    CustomReviewResponse,
    CustomReviewListResponse, CustomSuccessResponse, ReviewUpdateSchema
)

logger = logging.getLogger('uvicorn.error')
reviews_router = APIRouter(prefix="/reviews", tags=["Reviews"])


@reviews_router.post("/new", response_model=CustomReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review_endpoint(review_data: ReviewCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a new review for a business branch.
    - Requires authentication.
    - The new review will be 'pending' until approved.
    """
    new_review = service.create_new_review(db, review_data, current_user)
    return {
        "success": True,
        "message": "Review submitted, pending approval.",
        "review": new_review
    }


@reviews_router.get("/branch/{branch_id}", response_model=CustomReviewListResponse)
def get_reviews_for_branch_endpoint(branch_id: int, db: Session = Depends(get_db)):
    """
    Get all approved reviews for a specific branch.
    - This is a public endpoint and does not require authentication.
    """
    reviews = service.get_all_reviews_for_branch(db, branch_id)
    return {
        "success": True,
        "message": "Reviews retrieved successfully",
        "reviews": reviews
    }


@reviews_router.get("/me", response_model=CustomReviewListResponse)
def get_my_reviews_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get all reviews written by the currently logged-in user.
    Requires auth
    """
    reviews = service.get_my_reviews(db, current_user)
    return {
        "success": True,
        "message": "reviews retrieved successfully",
        "reviews": reviews
    }

@reviews_router.put("/{review_id}", response_model=CustomReviewResponse)
def update_review_endpoint(
    review_id: int,
    review_data: ReviewUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing review.
    - Requires authentication.
    - User can only update their own reviews.
    """
    updated_review = service.update_user_review(db, review_id, review_data, current_user)
    return {
        "success": True,
        "message": "Review updated successfully.",
        "review": updated_review
    }


@reviews_router.delete("/{review_id}", response_model=CustomSuccessResponse)
def delete_review_endpoint(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an existing review.
    - Requires authentication.
    - User can only delete their own reviews.
    """
    service.delete_user_review(db, review_id, current_user)
    return {
        "success": True,
        "message": "Review deleted successfully."
    }
