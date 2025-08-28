from typing import List, Optional

from sqlalchemy.orm import Session

from app.reviews.models import Review
from app.reviews.schemas import ReviewCreateSchema, ReviewUpdateSchema


def create_review(db: Session, review_data: ReviewCreateSchema, user_id: int) -> Review:
    """
    Creates a new review in the database.
    All reviews with a status for moderation (in dev all 'approved')
    """
    db_review = Review(
        branch_id=review_data.branch_id,
        user_id=user_id,
        rating=review_data.rating,
        comment=review_data.comment,
        is_anonymous=review_data.is_anonymous,
        status='approved'  # Default status for new reviews
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def get_reviews_by_branch_id(db: Session, branch_id: int) -> List[Review]:
    """
    Retrieves all 'approved' reviews for a specific branch, newest first.
    for public view
    """
    return (
        db.query(Review)
        .filter(Review.branch_id == branch_id, Review.status == 'approved')
        .order_by(Review.created_at.desc())
        .all()
    )


def get_reviews_by_user_id(db: Session, user_id: int) -> List[Review]:
    """
    Retrieves all reviews written by a specific user, newest first.
    """
    return (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .all()
    )

def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    """
    Retrieves a single review by its ID.
    """
    return db.query(Review).filter(Review.id == review_id).first()


def update_review(db: Session, review: Review, update_data: ReviewUpdateSchema) -> Review:
    """
    Updates a review's rating and/or comment in the database.
    The 'updated_at' timestamp will be handled automatically by the model.
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: Review) -> None:
    """
    Deletes a review from the database.
    """
    db.delete(review)
    db.commit()
    return
