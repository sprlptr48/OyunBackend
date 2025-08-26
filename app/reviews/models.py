from datetime import datetime, timezone

from sqlalchemy import (Column, ForeignKey, Integer, String, DateTime,
                        Boolean, Text, SmallInteger)
from sqlalchemy.orm import relationship, backref

from app.core.database import Base


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey('branch.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.userid', ondelete='CASCADE'), nullable=False, index=True)

    rating = Column(SmallInteger, nullable=False, index=True)
    comment = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    # Status for moderation: 'pending', 'approved', 'rejected'
    status = Column(String(15), default='pending', nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # Relationships
    # The user who wrote the review. A backref creates the 'reviews' collection on the User model.
    user = relationship("User", backref=backref("reviews", cascade="all, delete-orphan"))

    # The branch that was reviewed. A backref creates the 'reviews' collection on the Branch model.
    branch = relationship("Branch", backref=backref("reviews", cascade="all, delete-orphan"))

    # The one-to-one response from the business.
    response = relationship(
        "ReviewResponse",
        back_populates="review",
        uselist=False,  # This enforces a one-to-one relationship
        cascade="all, delete-orphan"
    )


class ReviewResponse(Base):
    __tablename__ = 'review_responses'

    id = Column(Integer, primary_key=True, index=True)
    # The review this is a response to. 'unique=True' enforces the one-to-one relationship at the database level.
    review_id = Column(Integer, ForeignKey('reviews.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    # The business staff member (from users table) who wrote the response.
    user_id = Column(Integer, ForeignKey('users.userid'), nullable=False, index=True)
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # Relationships
    # The review this response is for.
    review = relationship("Review", back_populates="response")
    # The user (staff) who wrote the response.
    user = relationship("User", backref="review_responses")