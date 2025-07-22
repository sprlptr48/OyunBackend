import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from app.models import User, RecoveryCode, EmailVerificationCode


class TestDataFactory:
    """Test verilerini merkezi olarak yönetir"""

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

    @staticmethod
    def get_login_data():
        return {
            "email": "testuser@example.com",
            "password": "123456"
        }

    @staticmethod
    def get_invalid_email_data():
        data = TestDataFactory.get_base_user_data()
        data["email"] = "invalid-email"
        return data

    @staticmethod
    def get_invalid_phone_data():
        data = TestDataFactory.get_base_user_data()
        data["phone"] = "invalid-phone"
        return data

    @staticmethod
    def get_verification_data():
        return {
            "email": "testuser@example.com",
            "phone": "+905551234567",
            "verification_code": "123456"
        }


@pytest.fixture
def user_data():
    """Her test için fresh user data döndürür"""
    return TestDataFactory.get_base_user_data()


@pytest.fixture
def registered_user(client, user_data):
    """Kayıtlı kullanıcı fixture'ı"""
    response = client.post("/register", json=user_data, params={"encrypted": False})
    return response.json()


@pytest.fixture
def verified_user(registered_user, db_session):
    """Email'i doğrulanmış kullanıcı fixture'ı"""
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()
    return user


@pytest.fixture
def logged_in_user(client, verified_user):
    """Login olmuş kullanıcı fixture'ı - session bilgisiyle birlikte"""
    login_data = TestDataFactory.get_login_data()
    response = client.post("/login", json=login_data)
    return response.json()


def test_root_endpoint(client):
    """API'nin çalıştığını test eder"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "API working"}


def test_register_user_success(client, user_data):
    """Başarılı kullanıcı kaydını test eder"""
    response = client.post("/register", json=user_data, params={"encrypted": False})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert response_data["message"] == "Email Validation Required"
    assert response_data["user"]["email"] == user_data["email"]
    assert "password" not in response_data["user"]
    assert response_data["user"]["email_status"] == False


def test_register_invalid_email(client):
    """Geçersiz email formatıyla kaydı test eder"""
    invalid_data = TestDataFactory.get_invalid_email_data()
    response = client.post("/register", json=invalid_data, params={"encrypted": False})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "email" in response_data["message"].lower()


def test_register_invalid_phone(client):
    """Geçersiz telefon formatıyla kaydı test eder"""
    invalid_data = TestDataFactory.get_invalid_phone_data()
    response = client.post("/register", json=invalid_data, params={"encrypted": False})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "phone" in response_data["message"].lower()


def test_register_existing_user_fail(client, registered_user, user_data):
    """Var olan kullanıcı kaydını test eder"""
    # İkinci kayıt denemesi
    response = client.post("/register", json=user_data, params={"encrypted": False})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "already registered" in response_data["message"].lower()


def test_login_unverified_email(client, registered_user):
    """Doğrulanmamış email ile login denemesini test eder"""
    login_data = TestDataFactory.get_login_data()
    response = client.post("/login", json=login_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Email Validation Required" in response_data["message"]


def test_login_invalid_credentials(client):
    """Yanlış kimlik bilgileriyle login denemesini test eder"""
    invalid_login = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=invalid_login)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Invalid credentials" in response_data["message"]


def test_login_success_after_email_verification(client, logged_in_user):
    """Email doğrulandıktan sonra başarılı login'i test eder"""
    assert logged_in_user["success"] == True
    assert "user" in logged_in_user
    assert "session" in logged_in_user
    assert logged_in_user["user"]["email"] == "testuser@example.com"
    assert "password" not in logged_in_user["user"]


def test_verify_email_success(client, registered_user, db_session):
    """Başarılı email doğrulamasını test eder"""
    # Doğrulama kodu oluştur
    verification_code = "123456"
    email_code = EmailVerificationCode(
        user_id=1,  # Assuming first user gets ID 1
        verification_code=verification_code,
        valid_until=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db_session.add(email_code)
    db_session.commit()

    verify_data = TestDataFactory.get_verification_data()
    response = client.post("/verify-email", json=verify_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Validated Verification Code" in response_data["message"]


def test_verify_email_invalid_code(client, registered_user):
    """Geçersiz doğrulama koduyla email doğrulamasını test eder"""
    verify_data = TestDataFactory.get_verification_data()
    verify_data["verification_code"] = "wrong_code"

    response = client.post("/verify-email", json=verify_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Invalid credentials" in response_data["message"]


@patch('main.send_password_reset_email', new_callable=AsyncMock)
def test_forgot_password_valid_email(mock_email, client, verified_user):
    """Geçerli email ile şifre sıfırlama talebini test eder"""
    forgot_data = {"email": "testuser@example.com"}
    response = client.post("/forgot-password", json=forgot_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Sent Code if the account exists" in response_data["message"]
    mock_email.assert_called_once()


def test_forgot_password_invalid_email_format(client):
    """Geçersiz email formatıyla şifre sıfırlama talebini test eder"""
    forgot_data = {"email": "invalid-email"}
    response = client.post("/forgot-password", json=forgot_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "valid email address" in response_data["message"]


def test_reset_password_success(client, verified_user, db_session):
    """Başarılı şifre sıfırlamayı test eder"""
    # Recovery kodu oluştur
    recovery_code = "123456"
    reset_code = RecoveryCode(
        recovery_code=recovery_code,
        user_id=verified_user.userid,
        valid_until=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db_session.add(reset_code)
    db_session.commit()

    reset_data = {
        "email": "testuser@example.com",
        "recovery_code": recovery_code,
        "new_password": "newpassword123"
    }
    response = client.post("/reset-password", json=reset_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Password Reset Successfully" in response_data["message"]


def test_reset_password_invalid_code(client, verified_user):
    """Geçersiz recovery code ile şifre sıfırlamayı test eder"""
    reset_data = {
        "email": "testuser@example.com",
        "recovery_code": "wrong_code",
        "new_password": "newpassword123"
    }
    response = client.post("/reset-password", json=reset_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Invalid email or recovery code" in response_data["message"]


def test_verify_session_success(client, logged_in_user):
    """Başarılı session doğrulamasını test eder"""
    session_data = logged_in_user["session"]
    response = client.get("/verify-session", json=session_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Session verified" in response_data["message"]


def test_verify_session_invalid(client):
    """Geçersiz session doğrulamasını test eder"""
    invalid_session = {
        "session_id": "invalid_session_id",
        "user_id": 999,
        "valid_until": "2024-12-31T23:59:59Z"
    }
    response = client.get("/verify-session", json=invalid_session)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Session not found" in response_data["message"]


def test_edit_user_success(client, logged_in_user, user_data):
    """Başarılı kullanıcı düzenlemesini test eder"""
    session_data = logged_in_user["session"]
    user_data = logged_in_user["user"]

    edit_data = {
        "userid": user_data["userid"],
        "name": "Ali Updated",
        "surname": "Kara Updated"
    }

    response = client.post("/edit-user", json={**edit_data, "session": session_data})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True


def test_edit_user_unauthorized(client):
    """Yetkisiz kullanıcı düzenlemesini test eder"""
    edit_data = {"userid": 1, "name": "Ali Updated"}
    invalid_session = {
        "session_id": "invalid",
        "user_id": 1,
        "valid_until": "2024-12-31T23:59:59Z"
    }

    response = client.post("/edit-user", json={**edit_data, "session": invalid_session})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Not Authorized" in response_data["message"]


def test_complete_user_flow(client, db_session):
    """Tüm kullanıcı akışını test eder: kayıt -> doğrulama -> login -> düzenleme"""
    # 1. Kayıt
    user_data = TestDataFactory.get_base_user_data()
    register_response = client.post("/register", json=user_data, params={"encrypted": False})
    assert register_response.json()["success"] == True

    # 2. Email doğrulama (simulated)
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    user.email_status = True
    db_session.commit()

    # 3. Login
    login_data = TestDataFactory.get_login_data()
    login_response = client.post("/login", json=login_data)
    assert login_response.json()["success"] == True

    session_data = login_response.json()["session"]
    user_response_data = login_response.json()["user"]

    # 4. Kullanıcı düzenleme
    edit_response = client.post("/edit-user", json={
        "userid": user_response_data["userid"],
        "name": "Updated Name",
        "session": session_data
    })
    assert edit_response.json()["success"] == True