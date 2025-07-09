from .models import *
from sqlalchemy.orm import Session

# Kullanıcı oluştur, commit kısmı daha sonra yapılmalı
def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user

 # Kullanıcı nesnesine göre, mail ya da telefon için arama yap
def get_user_by_login(db: Session, user_data: User):
    return db.query(User).filter((User.phone == user_data.email) or (User.email == user_data.phone)).first()

def save_session(db: Session, session: SessionModel) -> SessionModel:
    db.add(session)
    return session