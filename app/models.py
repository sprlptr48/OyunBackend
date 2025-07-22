from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = 'users'
    userid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=40))
    surname = Column(String(length=40))
    username = Column(String(length=40), unique=True, nullable=False)
    email = Column(String(length=40), unique=True, nullable=False, index=True)
    password = Column(String(length=60)) #bcrypt uses 60 chars
    phone = Column(String(length=20), unique=True)
    user_status = Column(String(length=40))
    email_status = Column(Boolean, default=False)


class SessionModel(Base):
    __tablename__ = 'session'
    session_id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.userid'), index=True)
    valid_until = Column(DateTime(timezone=True))

class RecoveryCode(Base):
    __tablename__ = 'recovery_code'
    id = Column(Integer, primary_key=True, autoincrement=True)
    recovery_code = Column(String(6), unique=True)
    user_id = Column(Integer, ForeignKey('users.userid'), nullable=False, index=True) # from user_email to user_id
    valid_until = Column(DateTime(timezone=True))

class EmailVerificationCode(Base):
    __tablename__ = 'email_verification_code'
    id = Column(Integer, primary_key=True, autoincrement=True)
    verification_code = Column(String(6), unique=True)
    user_id = Column(Integer, ForeignKey('users.userid'), nullable=False, index=True) # from user_email to user_id
    valid_until = Column(DateTime(timezone=True))

def schema_to_model(schema_instance, model_class):
    return model_class(**schema_instance.model_dump())
