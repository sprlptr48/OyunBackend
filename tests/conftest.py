import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from app.database import Base, get_db
from app import models, schemas

SQLALCHEMY_DATABASE_URL = 'sqlite:///:memory:'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session(): #SQLite bağlantısını oluştur.
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client(db_session): # MySQL yerine SQLite bağlantısı sağlayacak bir override
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
