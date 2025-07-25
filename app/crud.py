from datetime import datetime, timezone


from .models import *
from sqlalchemy.orm import Session

from .schemas import UserUpdate


# Kullanıcı oluştur, commit kısmı daha sonra yapılmalı
def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user

 # Kullanıcı nesnesine göre, mail ya da telefon için arama yap
def get_user_by_login(db: Session, user_data: User):
    query = db.query(User)
    if user_data.email and user_data.phone:
        return query.filter(User.email == user_data.email, User.phone == user_data.phone).first()
    elif user_data.email:
        return query.filter(User.email == user_data.email).first()
    elif user_data.phone:
        return query.filter(User.phone == user_data.phone).first()
    return None

def get_user_by_id(db: Session, userid: int) -> User | None:
    return db.query(User).filter(User.userid == userid).first()


def update_user(db: Session, user_id: int, user_update_data: UserUpdate) -> User | None:
    db_user = get_user_by_id(db, user_id)
    if db_user is None:
        return None
    
    update_data = user_update_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    return db_user

def update_user_password(db: Session, user_id: int, password: str):
    db_user = db.query(User).filter(User.userid == user_id).first()
    if db_user:
        db_user.password = password
        db.commit()
        db.refresh(db_user)
    return db_user


def save_session(db: Session, session: SessionModel) -> SessionModel:
    db.add(session)
    return session

"""
    Session getir
"""
def get_session(db: Session, session_id: str) -> SessionModel | None:
    return db.query(SessionModel).filter(SessionModel.session_id == session_id).first()

def edit_email_status(db: Session, user_id: int, status: bool):
    db.query(User).filter(User.userid == user_id).update({User.email_status: status})
    db.commit()
    return status


def get_recovery_code(db: Session, user_id: int):
    return db.query(RecoveryCode).filter(RecoveryCode.user_id == user_id).first()

def save_recovery_code(db: Session, code: RecoveryCode):
    existing = get_recovery_code(db, code.user_id)
    if existing is not None:
        db.delete(existing)
    db.add(code)
    return code

""" Checks if the Recovery Code is correct, and if it is still valid return true"""
def validate_recovery_code(db: Session, user_id: int, code: str) -> bool:
    valid_code = get_recovery_code(db, user_id)
    if valid_code is not None:
        if valid_code.valid_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            if valid_code.recovery_code == code:
                db.delete(valid_code) # Remove used entry.
                db.commit()
                return True
        else:
            db.delete(valid_code)
            return False
    return False

""" İLK KAYIT SIRASINDA EMAİL DOĞRULAMAK İÇİN"""
def get_email_verification_code(db: Session, user_id: int):
    return db.query(EmailVerificationCode).filter(EmailVerificationCode.user_id == user_id).first()

def save_email_verification_code(db: Session, code: EmailVerificationCode):
    existing = get_email_verification_code(db, code.user_id)
    if existing is not None: # remove old entries
        db.delete(existing)
    db.add(code)
    return code

""" Checks if the Verification Code is correct, and if it is still valid return true"""
def validate_email_verification_code(db: Session, user_id: int, code: str) -> bool:
    valid_code = get_email_verification_code(db, user_id)
    if valid_code is not None:
        if valid_code.valid_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            if valid_code.verification_code == code:
                db.delete(valid_code) # Remove used entry.
                db.commit()
                return True
        else:
            db.delete(valid_code)
            return False
    return False
