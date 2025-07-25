from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, service
from app.email import send_password_reset_email, send_verification_email
from app.models import User, SessionModel, schema_to_model, RecoveryCode, EmailVerificationCode
from app.schemas import UserCreate, UserLogin, SessionSchema, RegisterResponse, ReturnUser, UserUpdate, \
    ForgotPasswordSchema, ResetPasswordSchema, VerifyEmailSchema, UserLogoutSchema
from app.security import generate_session_id, hash_password, verify_password, verification_code
from app.crud import *
from app.database import get_db, Base, engine
from app.utils import validate_session, verify_email_format, verify_phone_format, normalize_phone


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"success": True, "message": "API working"}


""" Takes user info as input: name, surname, username, email, password, phone(optional)
    and uses the encrypted param to handle the password.
    returns UserInfo and Session Objects.
    UserInfo: 
"""
@app.post("/register", response_model=RegisterResponse)
def register(new_user: UserCreate, encrypted: bool, db: Session = Depends(get_db)):
    return service.register(new_user=new_user, encrypted=encrypted, db=db)


@app.post("/login", response_model=RegisterResponse, status_code=200)
async def login_endpoint(user: UserLogin, db: Session = Depends(get_db)):
    return service.login(user=user, db=db)


@app.post("/logout", response_model=RegisterResponse, status_code=200)
async def logout_endpoint(user: UserLogoutSchema, db: Session = Depends(get_db)):
    print("logged out")
    return await service.logout(user_data=user, db=db)


@app.post("/edit-user", status_code=200)
async def edit_user_endpoint(user: UserUpdate, session: SessionSchema,  db: Session = Depends(get_db)):
    return service.edit_user(user=user, session=session, db=db)


@app.get("/verify-session")
async def verify_session_endpoint(session: SessionSchema, db: Session = Depends(get_db)):
    return service.verify_session(session, db)

"""Şifremi Unuttum isteği"""
@app.post("/forgot-password", status_code=200)
async def forgot_password_endpoint(user_data: ForgotPasswordSchema, db: Session = Depends(get_db)):
    return service.forgot_password(user_data=user_data, db=db)

"""Şifre Değiştirme isteği """
@app.post("/reset-password", status_code=200)
async def reset_password_endpoint(data: ResetPasswordSchema, db: Session = Depends(get_db)):
    return service.reset_password(data=data, db=db)



@app.post("/verify-email", status_code=200)
async def verify_email_endpoint(login_data: VerifyEmailSchema, db: Session = Depends(get_db)):
    return service.verify_email(login_data, db)

