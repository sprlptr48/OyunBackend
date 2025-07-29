from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.email import send_password_reset_email, send_verification_email
from app.auth.schemas import UserCreate, UserLogin, SessionSchema, ReturnUser, ForgotPasswordSchema, ResetPasswordSchema, VerifyEmailSchema, UserLogoutSchema
from app.auth.security import generate_session_id, hash_password, verify_password, verification_code
from app.auth.crud import *
from app.auth.utils import validate_session, verify_email_format, verify_phone_format, normalize_phone


def register(new_user: UserCreate, encrypted: bool, db: Session):
    if not verify_email_format(new_user.email):
        return {"success": False, "message": "Please enter a correct email"}
    new_user.phone = normalize_phone(new_user.phone)
    if not verify_phone_format(new_user.phone):
        return {"success": False, "message": "Please enter a valid phone number"}
    if not encrypted:
        new_user.password = hash_password(new_user.password)
    user: User = User(**(new_user.model_dump()), user_status="open") # Gelen UserCreate schema User Model yapılır
    try:
        created_user = create_user(db, user)
        db.flush()
        db.commit()
        db.refresh(created_user)
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
        code = EmailVerificationCode(user_id=created_user.userid, verification_code=email_code,
                                     valid_until=datetime.now(timezone.utc) + timedelta(hours=1))
        save_email_verification_code(db, code)
        send_verification_email(user.email, email_code)
        db.commit()
        db.refresh(code)
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(501, "Error when creating user")

    returnUser = ReturnUser.model_validate(created_user) # Convert to return value, which removes password
    return {"success": True, "message": "Email Validation Required", "user": returnUser}#, "session": saved_session}

def login(user: UserLogin, db: Session):
    userModel = schema_to_model(user, User)
    foundUser = get_user_by_login(db, userModel)
    if foundUser is None:  # Kullanıcı yok
        return {"success": False, "message": "Invalid credentials"}
    if not verify_password(user.password, foundUser.password):  # Şifre yanlış
        return {"success": False, "message": "Invalid credentials"}
    elif not foundUser.email_status:  # Henüz Email Doğrulanmadıysa
        return {"success": False, "message": "Email Validation Required"}
    #    elif not foundUser.forgot_password:
    #        return {"success": False, "message": "Password reset required"}

    session_id = generate_session_id()
    try:
        session = SessionSchema(session_id=session_id,
                             user_id=foundUser.userid, valid_until=datetime.now(timezone.utc) + timedelta(days=1))
        sessionModel = schema_to_model(session, SessionModel)
        save_session(db, sessionModel)
        db.commit()
        db.refresh(sessionModel)  # Refresh to get the new session info
    except SQLAlchemyError as e:
        db.rollback()
        print(f"SQL Error: {e}")
        return {"success": False, "message": "Internal Server Error"}
    returnUser = ReturnUser.model_validate(foundUser)  # Convert to return value, which removes password
    return {"success": True, "user": returnUser, "session": session}

def edit_user(user: UserUpdate, session: SessionSchema,  db: Session):
    db_session = get_session(db, session.session_id)
    if db_session is None: # session yoksa
        return {"success": False, "message": "Not Authorized"}
    elif db_session.user_id != user.userid: # session, düzenlemeyi yapandan başkasına aitse
        return {"success": False, "message": "Not Authorized"}
    elif not validate_session(session):
        return {"success": False, "message": "Not Authorized"}
    if user.password:
        user.password = hash_password(user.password)
    edited = update_user(db, user.userid, user)
    if edited is None: return {"success": False, "message": "Server Error"}
    db.commit()
    edited_return = ReturnUser.model_validate(edited)
    return {"success": True, "user": edited_return}

def verify_session(session: SessionSchema, db: Session):
    db_session = get_session(db, session.session_id)
    if db_session is None:
        return {"success": False, "message": "Session not found"}
    if not validate_session(session):
        return {"success": False, "message": "Session expired"}
    if db_session.user_id != session.user_id:
        return {"success": False, "message": "Session not found"}
    return {"success": True, "message": "Session verified"}

def forgot_password(user_data: ForgotPasswordSchema, db: Session):
    if not verify_email_format(user_data.email):
        return {"success": False, "message": "Please enter a valid email address"}
    blank_user = User(email=user_data.email)
    blank_user = get_user_by_login(db, blank_user)
    if blank_user is None: return {"success": True, "message": "Sent Code if the account exists"}
    code = verification_code()
    valid_until = datetime.now(timezone.utc) + timedelta(minutes=5)
    saved_code = RecoveryCode(recovery_code=code, user_id=blank_user.userid, valid_until=valid_until)
    saved_code = save_recovery_code(db, saved_code)
    db.commit()
    send_password_reset_email(blank_user.email, code)

    return {"success": True, "message": "Sent Code if the account exists"}

def reset_password(data: ResetPasswordSchema, db: Session):
    blank_user = User(email=data.email)
    blank_user = get_user_by_login(db, blank_user) #DB'den kullanıcı verisini getir.
    if blank_user is None: return {"success": False, "message": "Invalid email or recovery code."}
    if blank_user.email != data.email: return {"success": False, "message": "Invalid email or recovery code."}
    hashed_password = hash_password(data.new_password)
    blank_user.password = hashed_password
    if not validate_recovery_code(db, blank_user.userid, data.recovery_code):
        return {"success": False, "message": "Invalid email or recovery code."}

    edited = update_user_password(db, blank_user.userid, blank_user.password)
    if edited is None: return {"success": False, "message": "Invalid email or recovery code."}
    return {"success": True, "message": "Password Reset Successfully."}

def verify_email(login_data: VerifyEmailSchema, db: Session):
    new_user = User(email=login_data.email, phone=login_data.phone)
    new_user = get_user_by_login(db, new_user)
    if new_user is None: return {"success": False, "message": "Invalid credentials"}
    validation_result = validate_email_verification_code(db, new_user.userid, login_data.verification_code)
    if not validation_result:
        return {"success": False, "message": "Invalid credentials"}
    edit_email_status(db, new_user.userid, True)
    return {"success": True, "message": "Validated Verification Code", "code": login_data.verification_code}

async def logout(user_data: UserLogoutSchema, db: Session):
    db_session = get_session(db, user_data.session_id)
    if db_session is None or db_session.user_id != user_data.user_id:
        return {"success": False, "message": "Session does not exist"}
    try:
        db.delete(db_session)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        return {"success": False, "message": "Internal Server Error"}
    return {"success": True, "message": "Successfully logged out"}
