import pytest
from app.models import User, RecoveryCode, EmailVerificationCode
from datetime import datetime, timezone, timedelta

class TestDataFactory:
    @staticmethod
    def get_base_user_data():
        return {
            "name": "ali",
            "surname": "kara",
            "username": "alik16",
            "email": "testuser@example.com",
            "password": "123456",
            "phone": "+905551234567"
        }

# Fixture'lar
# Testler için gerekli olan kullanıcı ve oturum durumlarını hazırlar.

@pytest.fixture
def user_data():
    """Temel kullanıcı verisi sağlar."""
    return TestDataFactory.get_base_user_data()

@pytest.fixture
def registered_user(client, user_data, db_session):
    """Veritabanına kaydedilmiş ama e-postası doğrulanmamış bir kullanıcı oluşturur."""
    client.post("/register", json=user_data, params={"encrypted": False})
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    return user

@pytest.fixture
def verified_user(registered_user, db_session):
    """E-postası doğrulanmış bir kullanıcı oluşturur."""
    registered_user.email_status = True
    db_session.commit()
    return registered_user

@pytest.fixture
def logged_in_user(client, verified_user):
    """Giriş yapmış bir kullanıcı ve oturum bilgisini döndürür."""
    login_data = {"email": verified_user.email, "password": "123456"}
    response = client.post("/login", json=login_data)
    return {"user": verified_user, "session": response.json()["session"]}


# --- Test Grupları ---

class TestUserRegistration:
    """Kullanıcı kayıt (/register) endpoint'i ile ilgili testler."""

    def test_register_user_successfully(self, client, user_data):
        """Başarılı bir kullanıcı kaydının gerçekleştiğini doğrular."""
        response = client.post("/register", json=user_data, params={"encrypted": "false"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Email Validation Required"
        assert data["user"]["email"] == user_data["email"]

    def test_register_with_existing_email_fails(self, client, registered_user, user_data):
        """Aynı e-posta ile tekrar kayıt olunamayacağını doğrular."""
        response = client.post("/register", json=user_data, params={"encrypted": "false"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already registered" in data["message"]


    @pytest.mark.parametrize(
        "field_to_invalidate, invalid_value, expected_error_detail",
        [
            ("email", "invalid-email-format", "email"),
            ("phone", "12345", "phone number"),
            #("username", "al", "username"), kullanıcı adı kuralı yok
        ]
    )
    def test_register_with_invalid_data_fails(self, client, user_data, field_to_invalidate, invalid_value, expected_error_detail):
        """Farklı geçersiz veri formatlarıyla kaydın başarısız olacağını tek yerden test eder."""
        # Test edilecek geçersiz veriyi ayarla
        user_data[field_to_invalidate] = invalid_value

        response = client.post("/register", json=user_data, params={"encrypted": "false"})
        data = response.json()

        assert response.status_code == 200
        assert data["success"] is False
        assert expected_error_detail in data["message"]

class TestUserLogin:
    """Kullanıcı giriş (/login) endpoint'i ile ilgili testler."""

    def test_login_successfully(self, client, verified_user):
        """Doğrulanmış bir kullanıcının başarıyla giriş yapabildiğini test eder."""
        login_data = {"email": verified_user.email, "password": "123456"}
        response = client.post("/login", json=login_data)
        data = response.json()
        assert response.status_code == 200
        assert data["success"] is True
        assert "session" in data
        assert data["user"]["email"] == verified_user.email

    def test_login_with_unverified_email_fails(self, client, registered_user):
        """E-postası doğrulanmamış bir kullanıcının giriş yapamadığını test eder."""
        login_data = {"email": registered_user.email, "password": "123456"}
        response = client.post("/login", json=login_data)
        data = response.json()
        assert response.status_code == 200
        assert data["success"] is False
        assert data["message"] == "Email Validation Required"

    def test_login_with_wrong_password_fails(self, client, verified_user):
        """Yanlış şifre ile giriş yapılamadığını test eder."""
        login_data = {"email": verified_user.email, "password": "wrongpassword"}
        response = client.post("/login", json=login_data)
        data = response.json()
        assert response.status_code == 200
        assert data["success"] is False
        assert data["message"] == "Invalid credentials"
