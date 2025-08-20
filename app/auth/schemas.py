from datetime import datetime
from pydantic import ConfigDict, BaseModel


class SessionSchema(BaseModel):
    session_id: str
    user_id: int
    valid_until: datetime
    model_config = ConfigDict(from_attributes=True)


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

class UserLogoutSchema(BaseModel):
    session_id: str
    user_id: int

class ForgotPasswordSchema(BaseModel):
    email: str | None = None
    phone: str | None = None

class ResetPasswordSchema(BaseModel):
    email: str | None = None
    phone: str | None = None
    new_password: str
    recovery_code: str

class VerifyEmailSchema(BaseModel):
    email: str | None = None
    phone: str | None = None
    verification_code: str

class ReturnUser(BaseModel):
    userid: int | None = None
    name: str
    surname: str
    username: str
    email: str
    phone: str | None = None
    user_status: str
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    userid: int
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    password: str | None = None

class RegisterResponse(BaseModel):
    success: bool
    message: str | None = None
    user: ReturnUser | None = None

class LoginResponse(BaseModel):
    success: bool
    message: str | None = None
    user: ReturnUser | None = None
    session: SessionSchema | None = None

