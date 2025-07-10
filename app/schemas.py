from datetime import datetime
from pydantic import BaseModel

from app.models import SessionModel


class SessionSchema(BaseModel):
    session_id: str
    user_id: int
    valid_until: datetime
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str

class UserCreate(BaseModel):
    name: str
    surname: str
    username: str
    email: str
    password: str
    phone: str | None = None

class UserLogin(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str

class ForgotPassword(BaseModel):
    email: str | None = None
    phone: str | None = None


class ReturnUser(BaseModel):
    userid: int | None = None
    name: str
    surname: str
    username: str
    email: str
    phone: str | None = None
    user_status: str
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    userid: int
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    password: str | None = None

class RegisterResponse(BaseModel):
    user: ReturnUser
    session: SessionSchema
