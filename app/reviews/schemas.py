from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    rating: int = Field(..., gt=0, lt=6, description="Rating from 1 to 5")
    comment: Optional[str] = None
    is_anonymous: bool = False

class ReviewCreateSchema(ReviewBase):
    """
    Schema used when a user creates a new review.
    """
    branch_id: int


class ReviewResponseSchema(ReviewBase):
    id: int
    user_id: int
    branch_id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomReviewResponse(BaseModel):
    success: bool
    message: str
    review: Optional[ReviewResponseSchema] = None


class CustomReviewListResponse(BaseModel):
    success: bool
    message: str
    reviews: List[ReviewResponseSchema] = []

class ReviewUpdateSchema(BaseModel):
    """
    Schema for updating an existing review. All fields are optional.
    """
    rating: Optional[int] = Field(None, gt=0, lt=6, description="New rating from 1 to 5")
    comment: Optional[str] = None


class CustomSuccessResponse(BaseModel):
    """
    A generic success response for operations that don't return data.
    """
    success: bool
    message: str
