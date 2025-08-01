import logging

from fastapi import FastAPI, Depends, APIRouter
from starlette.requests import Request

from app.auth import service
from app.auth.schemas import UserCreate, UserLogin, SessionSchema, RegisterResponse, ForgotPasswordSchema, ResetPasswordSchema, VerifyEmailSchema, UserLogoutSchema
from app.auth.crud import *
from app.core.database import get_db, Base, engine
from app.core.limiter import limiter


logger = logging.getLogger('uvicorn.error')
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.get("/")
async def root():
    return {"success": True, "message": "AUTH API Working"}


""" Takes user info as input: name, surname, username, email, password, phone(optional)
    and uses the encrypted param to handle the password.
    returns UserInfo and Session Objects.
    UserInfo: 
"""
@auth_router.post("/register", response_model=RegisterResponse)
def register(new_user: UserCreate, encrypted: bool, db: Session = Depends(get_db)):

    result = service.register(new_user=new_user, encrypted=encrypted, db=db)
    logger.info(result)
    return result


@auth_router.post("/login", response_model=RegisterResponse, status_code=200)
async def login_endpoint(user: UserLogin, db: Session = Depends(get_db)):
    return service.login(user=user, db=db)


@auth_router.post("/logout", response_model=RegisterResponse, status_code=200)
async def logout_endpoint(user: UserLogoutSchema, db: Session = Depends(get_db)):
    print("logged out")
    return await service.logout(user_data=user, db=db)


@auth_router.post("/edit-user", status_code=200)
async def edit_user_endpoint(user: UserUpdate, session: SessionSchema,  db: Session = Depends(get_db)):
    return service.edit_user(user=user, session=session, db=db)


@auth_router.get("/verify-session")
async def verify_session_endpoint(session: SessionSchema, db: Session = Depends(get_db)):
    return service.verify_session(session, db)

"""Şifremi Unuttum isteği"""
@auth_router.post("/forgot-password", status_code=200)
async def forgot_password_endpoint(user_data: ForgotPasswordSchema, db: Session = Depends(get_db)):
    return service.forgot_password(user_data=user_data, db=db)

"""Şifre Değiştirme isteği """
@auth_router.post("/reset-password", status_code=200)
async def reset_password_endpoint(data: ResetPasswordSchema, db: Session = Depends(get_db)):
    return service.reset_password(data=data, db=db)


@auth_router.post("/verify-email", status_code=200)
@limiter.limit("15/15 minutes")
async def verify_email_endpoint(request: Request, login_data: VerifyEmailSchema, db: Session = Depends(get_db)):
    return service.verify_email(login_data, db)

