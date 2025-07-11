from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.models import User, SessionModel, schema_to_model
from app.schemas import UserCreate, UserLogin, SessionSchema, RegisterResponse, ReturnUser, UserUpdate, ForgotPassword
from app.security import generate_session_id, hash_password, verify_password, forgot_password_code
from app.crud import create_user, save_session, get_user_by_login, get_session, edit_user
from app.database import get_db, Base, engine
from app.utils import validate_session, verify_email, verify_phone, normalize_phone


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
async def register(new_user: UserCreate, encrypted: bool, db: Session = Depends(get_db)):
    email_success = verify_email(new_user.email)
    if email_success is False:
        return {"success": False, "message": "Please enter a correct email"}
    phone_success = verify_phone(new_user.phone)
    if phone_success is False:
        new_phone = normalize_phone(new_user.phone)
        phone_success = verify_phone(new_phone)
        if phone_success is False:
            return {"success": False, "message": "Please enter a valid phone number"}
    if not encrypted:
        new_user.password = hash_password(new_user.password)

    user: User = User(**(new_user.model_dump()), user_status="open") # Gelen UserCreate schema User Model yapılır
    session_id = generate_session_id()
    session = SessionSchema(session_id=session_id,
                            user_id=-1, valid_until=datetime.now(timezone.utc) + timedelta(days=1))
    sessionModel = schema_to_model(session, SessionModel)  # Convert to model for DB operations

    try:
        created_user = create_user(db, user)
        db.flush()
        sessionModel.user_id = created_user.userid
        saved_session = save_session(db, sessionModel)
        db.commit()
        db.refresh(created_user)
        db.refresh(saved_session)
    except IntegrityError as e:
        print(e)
        db.rollback()
        # get the original DB error from mysql
        error_info = str(e.orig).lower()
        if 'email' in error_info:
            return {"success": False, "message": "Email already registered"}
        elif 'username' in error_info:
            return {"success": False, "message": "Username already registered"}
        elif 'phone' in error_info:
            return {"success": False, "message": "Phone number already registered"}
        return {"success": False, "message": "User already exists"}
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(501, "Error when creating user")
    returnUser = ReturnUser.model_validate(created_user) # Convert to return value, which removes password
    return {"success": True, "user": returnUser, "session": saved_session}


@app.post("/login", response_model=RegisterResponse, status_code=200)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    userModel = schema_to_model(user, User)
    foundUser = get_user_by_login(db, userModel)
    if foundUser is None: # Kullanıcı yok
        return {"success": False, "message": "Invalid credentials"}
    if not verify_password(user.password, foundUser.password): # Şifre yanlış
        return {"success": False, "message": "Invalid credentials"}

    session_id = generate_session_id()
    session = SessionSchema(session_id=session_id,
                            user_id=foundUser.userid, valid_until=datetime.now(timezone.utc) + timedelta(days=1))
    sessionModel = schema_to_model(session, SessionModel)
    save_session(db, sessionModel)
    db.commit()
    db.refresh(foundUser)
    db.refresh(sessionModel)
    returnUser = ReturnUser.model_validate(foundUser) # Convert to return value, which removes password
    return {"success": True, "user": returnUser, "session": session}

""" Gelen kullanıcı verisine göre düzenleme yapar.
    userid ve password bulunmalıdır.
"""
@app.post("/edit-user", status_code=200)
def edit_user_endpoint(user: UserUpdate, session: SessionSchema,  db: Session = Depends(get_db)):
    db_session = get_session(db, session.session_id)
    if db_session is None: # session yoksa
        return {"success": False, "message": "Not Authorized"}
    elif db_session.user_id != user.userid: # session, düzenlemeyi yapandan başkasına aitse
        return {"success": False, "message": "Not Authorized"}
    elif validate_session(session):
        return {"success": False, "message": "Not Authorized"}
    user.password = hash_password(user.password)
    edited = edit_user(db, user.userid, user)
    if edited is None: return {"success": False, "message": "Invalid credentials"}
    return {"success": True}


@app.get("/verify-session")
def verify_session_endpoint(session: SessionSchema, db: Session = Depends(get_db)):
    db_session = get_session(db, session.session_id)
   # print("DB valid_until:", db_session.valid_until)
    #print("Now:", datetime.now(timezone.utc))
    #print("TZ info:", db_session.valid_until.tzinfo)
    print(db_session.user_id)
    print(session)
    if db_session is None:
        return {"success": False, "message": "Session not found"}
    session_new = SessionSchema.model_validate(db_session)
    if not validate_session(session_new):
        return {"success": False, "message": "Session expired"}
    if db_session.user_id != session.user_id:
        return {"success": False, "message": "Session not found"}
    return {"success": True, "message": "Session verified"}

@app.post("/forgot-password", status_code=200)
def forgot_password(user_data: ForgotPassword, db: Session = Depends(get_db)):
    blank_user = User(email=user_data.email, phone=user_data.phone)
    blank_user = get_user_by_login(db, blank_user)
    if blank_user is None: return {"success": False, "message": "Invalid credentials"}
    code = forgot_password_code()
    return {"code": code}
