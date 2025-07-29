import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.auth.routes import app
from app.core.database import Base, get_db

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


@pytest.fixture(autouse=True)
def mock_email_sending(monkeypatch):
    """
    Tüm testler boyunca e-posta gönderimini otomatik olarak devre dışı bırakır.

    Bu fixture, 'app.email.send_email' fonksiyonunu, hiçbir şey yapmayan
    ve hiçbir değer döndürmeyen sahte bir fonksiyonla değiştirir.
    `autouse=True` sayesinde her testten önce otomatik olarak çalışır.
    """

    def fake_send_email(subject: str, recipient: str, body: str):
        print(f"--- MOCK EMAIL ---")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:50]}...")
        print(f"------------------")
        pass

    #gerçek send_email fonksiyonunu değiştir.
    monkeypatch.setattr("app.email.send_email", fake_send_email)