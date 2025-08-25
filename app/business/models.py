from datetime import datetime, timezone
from typing import List

from geoalchemy2 import Geography
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import backref, relationship, Mapped

from app.core.database import Base

class Business(Base):
    __tablename__ = 'business'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.userid'))
    name = Column(String(length=50))
    description = Column(String(length=255))
    #business_type_id = Column(Integer, ForeignKey('business_types.id'))
    is_active = Column(Boolean, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    branches: Mapped[List["Branch"]] = relationship(back_populates="business") #doesn't exist normally, just a type hint.


class Branch(Base):
    __tablename__ = 'branch'
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('business.id', ondelete='CASCADE'), index=True)
    address_text = Column(String(length=255))
    phone = Column(String(length=16))
    location = Column(Geography(geometry_type='POINT', srid=4326, spatial_index=True), index=True)
    is_active = Column(Boolean, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    business: Mapped["Business"] = relationship(back_populates="branches")

class BusinessStaff(Base):
    __tablename__ = 'business_staff'
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('business.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('users.userid', ondelete='CASCADE'))
    role = Column(String(length=15))
    parent = relationship('User', backref=backref('BusinessStaff', passive_deletes=True))


