from datetime import datetime
import re

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
def get_user_by_id(db: Session, userid: int):
    return db.query(User).filter(User.userid == userid).first()

def edit_user(db: Session, user_id: int, user_update_data: UserUpdate):
    """
    Updates a user in the database with the provided data.
    """
    db_user = get_user_by_id(db, user_id)
    if db_user is None:
        return None
    update_data = user_update_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
""" Check if email is in correct form: example@domain.com """
def verify_email(email: str):
    regex = r'^[\w\-\.]+@([\w-]+\.)+[\w-]{2,}$'

    matches = re.findall(regex, email, re.MULTILINE)
    if len(matches) != 1:
        return False
    else:
        return True
""" Check if phone number is in correct form:  """
def verify_phone(phone: str):
    regex = r'^(?:\+?\d{1,4})?0?\d{10}$'
    return re.fullmatch(regex, phone, re.MULTILINE)
""" Telefon numarasındaki boşlukları ve gereksiz işaretleri siler. """
def normalize_phone(phone: str) -> str:
    # Remove spaces, dashes, underscores, parentheses, asterisks, etc.
    phone = phone.strip()

    # Preserve leading '+' if present, remove all non-digit characters
    if phone.startswith('+'):
        phone = '+' + re.sub(r'\D', '', phone[1:])
    else:
        phone = re.sub(r'\D', '', phone)
    return phone


def save_session(db: Session, session: SessionModel) -> SessionModel:
    db.add(session)
    return session

"""
    Session hala geçerliyse döndür, değilse None döndür
"""
def get_session(db: Session, session_id: str):
    return db.query(SessionModel).filter(SessionModel.session_id == session_id).first()