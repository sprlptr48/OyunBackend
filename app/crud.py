from .models import *
from sqlalchemy.orm import Session


def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    db.query(User).filter(User.email == email).first()

 # Kullanıcı nesnesine göre arama yap
def get_user_by_login(db: Session, user_data: User):
    return db.query(User).filter((User.phone == user_data.email) or (User.email == user_data.phone)).first()

def save_session(db: Session, session: SessionModel):
    db.add(session)
    db.commit()