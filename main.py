from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.email import send_password_reset_email, send_verification_email
from app.models import User, SessionModel, schema_to_model, RecoveryCode, EmailVerificationCode
from app.schemas import UserCreate, UserLogin, SessionSchema, RegisterResponse, ReturnUser, UserUpdate, \
    ForgotPasswordSchema, ResetPasswordSchema, VerifyEmailSchema
from app.security import generate_session_id, hash_password, verify_password, verification_code
from app.crud import create_user, save_session, get_user_by_login, get_session, edit_user, save_recovery_code, \
    update_user_password, validate_recovery_code, validate_email_verification_code, edit_email_status, \
    save_email_verification_code
from app.database import get_db, Base, engine
from app.utils import validate_session, verify_email_format, verify_phone_format, normalize_phone


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    Base.metadata.drop_all(bind=engine)
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
    email_success = verify_email_format(new_user.email)
    if email_success is False:
        return {"success": False, "message": "Please enter a correct email"}
    phone_success = verify_phone_format(new_user.phone)
    if phone_success is False:
        new_phone = normalize_phone(new_user.phone)
        phone_success = verify_phone_format(new_phone)
        if phone_success is False:
            return {"success": False, "message": "Please enter a valid phone number"}
    if not encrypted:
        new_user.password = hash_password(new_user.password)

    user: User = User(**(new_user.model_dump()), user_status="open") # Gelen UserCreate schema User Model yapılır
    #session_id = generate_session_id()
    #session = SessionSchema(session_id=session_id,
    #                        user_id=-1, valid_until=datetime.now(timezone.utc) + timedelta(days=1))
    #sessionModel = schema_to_model(session, SessionModel)  # Convert to model for DB operations

    try:
        created_user = create_user(db, user)
        db.flush()
        #sessionModel.user_id = created_user.userid
        #saved_session = save_session(db, sessionModel)
        db.commit()
        db.refresh(created_user)
        #db.refresh(saved_session)
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
    # Email Doğrulama kodu oluştur ve kaydet
    try:
        email_code = verification_code()
        code = EmailVerificationCode(user_email=user.email, verification_code=email_code,
                                     valid_until=datetime.now(timezone.utc) + timedelta(hours=1))
        save_email_verification_code(db, code)
        await send_verification_email(user.email, email_code)
        db.commit()
        db.refresh(code)
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(501, "Error when creating user")

    returnUser = ReturnUser.model_validate(created_user) # Convert to return value, which removes password
    return {"success": True, "message": "Email Validation Required", "user": returnUser}#, "session": saved_session}


@app.post("/login", response_model=RegisterResponse, status_code=200)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    userModel = schema_to_model(user, User)
    foundUser = get_user_by_login(db, userModel)
    if foundUser is None: # Kullanıcı yok
        return {"success": False, "message": "Invalid credentials"}
    if not verify_password(user.password, foundUser.password): # Şifre yanlış
        return {"success": False, "message": "Invalid credentials"}
    elif not foundUser.email_status: # Henüz Email Doğrulanmadıysa
        return {"success": False, "message": "Email Validation Required"}
#    elif not foundUser.forgot_password:
#        return {"success": False, "message": "Password reset required"}


    session_id = generate_session_id()
    session = SessionSchema(session_id=session_id,
                            user_id=foundUser.userid, valid_until=datetime.now(timezone.utc) + timedelta(days=1))
    sessionModel = schema_to_model(session, SessionModel)
    save_session(db, sessionModel)
    db.commit()
    db.refresh(foundUser) # Refresh to get the id from the user
    returnUser = ReturnUser.model_validate(foundUser) # Convert to return value, which removes password
    return {"success": True, "user": returnUser, "session": session}

""" Gelen kullanıcı verisine göre düzenleme yapar.
    userid ve password bulunmalıdır.
"""
@app.post("/edit-user", status_code=200)
async def edit_user_endpoint(user: UserUpdate, session: SessionSchema,  db: Session = Depends(get_db)):
    db_session = get_session(db, session.session_id)
    if db_session is None: # session yoksa
        return {"success": False, "message": "Not Authorized"}
    elif db_session.user_id != user.userid: # session, düzenlemeyi yapandan başkasına aitse
        return {"success": False, "message": "Not Authorized"}
    elif not validate_session(session):
        return {"success": False, "message": "Not Authorized"}
    if user.password:
        user.password = hash_password(user.password)
    edited = edit_user(db, user.userid, user)
    db.commit()
    if edited is None: return {"success": False, "message": "Invalid credentials"}
    return {"success": True}


@app.get("/verify-session")
async def verify_session_endpoint(session: SessionSchema, db: Session = Depends(get_db)):
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

"""Şifremi Unuttum isteği"""
@app.post("/forgot-password", status_code=200)
async def forgot_password(user_data: ForgotPasswordSchema, db: Session = Depends(get_db)):
    if not verify_email_format(user_data.email):
        return {"success": False, "message": "Please enter a valid email address"}
    blank_user = User(email=user_data.email)
    blank_user = get_user_by_login(db, blank_user)
    if blank_user is None: return {"success": True, "message": "Sent Code if the account exists"}
    code = verification_code()
    valid_until = datetime.now(timezone.utc) + timedelta(minutes=5)
    saved_code = RecoveryCode(recovery_code=code, user_email=user_data.email, valid_until=valid_until)
    saved_code = save_recovery_code(db, saved_code)
    db.commit()
    await send_password_reset_email(blank_user.email, code)

    return {"success": True, "message": "Sent Code if the account exists", code: saved_code}
"""Şifre Değiştirme isteği """
@app.post("/reset-password", status_code=200)
async def reset_password_endpoint(data: ResetPasswordSchema, db: Session = Depends(get_db)):
    blank_user = User(email=data.email)
    blank_user = get_user_by_login(db, blank_user)
    if blank_user is None: return {"success": False, "message": "Invalid email or recovery code."}
    if blank_user.email != data.email: return {"success": False, "message": "Invalid email or recovery code."}
    hashed_password = hash_password(data.new_password)
    blank_user.password = hashed_password
    if not validate_recovery_code(db, data.email, data.recovery_code):
        return {"success": False, "message": "Invalid email or recovery code."}

    edited = update_user_password(db, blank_user.userid, blank_user)
    if edited is None: return {"success": False, "message": "Invalid email or recovery code."}
    return {"success": True, "message": "Password Reset Successfully."}



@app.post("/verify-email", status_code=200)
async def verify_email_endpoint(login_data: VerifyEmailSchema, db: Session = Depends(get_db)):
    new_user = User(email=login_data.email, phone=login_data.phone)
    new_user = get_user_by_login(db, new_user)
    if new_user is None: return {"success": False, "message": "Invalid credentials"}
    validation_result = validate_email_verification_code(db, new_user.email, login_data.recovery_code)
    if not validation_result:
        return {"success": False, "message": "Invalid credentials"}
    edit_email_status(db, new_user.email, True)
    return {"success": True, "message": "Validated Recovery Code", "code": login_data.recovery_code}

