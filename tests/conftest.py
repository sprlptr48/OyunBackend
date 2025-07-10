import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from app.database import Base, get_db
from app.models import User, SessionModel
from app import schemas

SQLALCHEMY_DATABASE_URL = "sqlite:///./user.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # db_session zaten yönetiliyor

    if not hasattr(app, 'dependency_overrides'):
        app.dependency_overrides = {}
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    if hasattr(app, 'dependency_overrides'):
        app.dependency_overrides.clear()
    app.dependency_overrides.clear()