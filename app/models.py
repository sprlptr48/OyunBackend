from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = 'users'
    userid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=40))
    surname = Column(String(length=40))
    username = Column(String(length=40), unique=True, nullable=False)
    email = Column(String(length=40), unique=True, nullable=False)
    password = Column(String(length=60)) #bcrypt uses 60 chars
    user_status = Column(String(length=40))
    phone = Column(String(length=20), unique=True)


class SessionModel(Base):
    __tablename__ = 'session'
    session_id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.userid'))
    valid_until = Column(DateTime(timezone=True))

def schema_to_model(schema_instance, model_class):
    return model_class(**schema_instance.model_dump())
