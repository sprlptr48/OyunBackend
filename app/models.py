from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = 'users'
    userid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    surname = Column(String)
    username = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    user_status = Column(String)
    phone = Column(String, unique=True)


class SessionModel(Base):
    __tablename__ = 'session'
    session_id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.userid'))
    valid_until = Column(DateTime)

def schema_to_model(schema_instance, model_class):
    return model_class(**schema_instance.model_dump())
