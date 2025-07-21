import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from app.models import User, RecoveryCode, EmailVerificationCode


def test_root_endpoint(client):
    """
    Tests the root endpoint to ensure API is working
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "API working"}


def test_register_user_success(client):
    """
    Tests successful user registration with valid data
    """
    test_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    response = client.post(
        "/register",
        json=test_data,
        params={"encrypted": False}
    )
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["success"] == True
    assert response_data["message"] == "Email Validation Required"
    assert response_data["user"]["email"] == "testuser@example.com"
    assert "password" not in response_data["user"]
    assert response_data["user"]["email_status"] == False  # Email not verified yet


def test_register_invalid_email(client):
    """
    Tests registration with invalid email format
    """
    test_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "invalid-email",
        "password": "123456",
        "phone": "+905551234567"
    }
    response = client.post("/register", json=test_data, params={"encrypted": False})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "email" in response_data["message"].lower()


def test_register_invalid_phone(client):
    """
    Tests registration with invalid phone format
    """
    test_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "invalid-phone"
    }
    response = client.post("/register", json=test_data, params={"encrypted": False})

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "phone" in response_data["message"].lower()


def test_register_existing_user_fail(client):
    """
    Tests registration failure when user already exists
    """
    test_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    # First registration
    response1 = client.post("/register", json=test_data, params={"encrypted": False})
    assert response1.status_code == 200
    assert response1.json()["success"] == True

    # Second registration with same email
    response2 = client.post("/register", json=test_data, params={"encrypted": False})
    assert response2.status_code == 200
    response_data = response2.json()
    assert response_data["success"] == False
    assert "already registered" in response_data["message"].lower()


def test_login_unverified_email(client):
    """
    Tests login attempt with unverified email
    """
    # Register user first
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Try to login without email verification
    login_data = {
        "email": "testuser@example.com",
        "password": "123456"
    }
    response = client.post("/login", json=login_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Email Validation Required" in response_data["message"]


def test_login_invalid_credentials(client):
    """
    Tests login with wrong credentials
    """
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=login_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Invalid credentials" in response_data["message"]


def test_verify_email_success(client, db_session):
    """
    Tests successful email verification
    """
    # Register user first
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Create verification code manually for testing
    verification_code = "123456"
    email_code = EmailVerificationCode(
        recovery_code=verification_code,
        user_email="testuser@example.com",
        valid_until=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db_session.add(email_code)
    db_session.commit()

    # Verify email
    verify_data = {
        "email": "testuser@example.com",
        "phone": "+905551234567",
        "recovery_code": verification_code
    }
    response = client.post("/verify-email", json=verify_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Validated Recovery Code" in response_data["message"]


def test_verify_email_invalid_code(client):
    """
    Tests email verification with invalid code
    """
    # Register user first
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Try to verify with invalid code
    verify_data = {
        "email": "testuser@example.com",
        "phone": "+905551234567",
        "recovery_code": "wrong_code"
    }
    response = client.post("/verify-email", json=verify_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Invalid credentials" in response_data["message"]


@patch('main.send_password_reset_email', new_callable=AsyncMock)
def test_forgot_password_valid_email(mock_email, client, db_session):
    """
    Tests forgot password with valid email
    """
    # Register and verify user first
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Set email as verified
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()

    # Request password reset
    forgot_data = {"email": "testuser@example.com"}
    response = client.post("/forgot-password", json=forgot_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Sent Code if the account exists" in response_data["message"]
    mock_email.assert_called_once()


def test_forgot_password_invalid_email_format(client):
    """
    Tests forgot password with invalid email format
    """
    forgot_data = {"email": "invalid-email"}
    response = client.post("/forgot-password", json=forgot_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "valid email address" in response_data["message"]


def test_forgot_password_nonexistent_user(client):
    """
    Tests forgot password with non-existent email (should still return success for security)
    """
    forgot_data = {"email": "nonexistent@example.com"}
    response = client.post("/forgot-password", json=forgot_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Sent Code if the account exists" in response_data["message"]


def test_reset_password_success(client, db_session):
    """
    Tests successful password reset
    """
    # Register and verify user
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Set email as verified
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()

    # Create recovery code manually for testing
    recovery_code = "123456"
    reset_code = RecoveryCode(
        recovery_code=recovery_code,
        user_email="testuser@example.com",
        valid_until=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db_session.add(reset_code)
    db_session.commit()

    # Reset password
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


def test_reset_password_invalid_code(client, db_session):
    """
    Tests password reset with invalid recovery code
    """
    # Register and verify user
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Set email as verified
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()

    # Try to reset with invalid code
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


def test_reset_password_nonexistent_user(client):
    """
    Tests password reset for non-existent user
    """
    reset_data = {
        "email": "nonexistent@example.com",
        "recovery_code": "123456",
        "new_password": "newpassword123"
    }
    response = client.post("/reset-password", json=reset_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Invalid email or recovery code" in response_data["message"]


def test_login_success_after_email_verification(client, db_session):
    """
    Tests successful login after email verification
    """
    # Register user
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Manually verify email
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()

    # Now login should work
    login_data = {
        "email": "testuser@example.com",
        "password": "123456"
    }
    response = client.post("/login", json=login_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "user" in response_data
    assert "session" in response_data
    assert response_data["user"]["email"] == "testuser@example.com"
    assert "password" not in response_data["user"]


def test_verify_session_success(client, db_session):
    """
    Tests successful session verification
    """
    # Register, verify, and login user to get session
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    # Manually verify email
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()

    # Login to get session
    login_response = client.post("/login", json={
        "email": "testuser@example.com",
        "password": "123456"
    })
    session_data = login_response.json()["session"]

    # Verify session
    response = client.get("/verify-session", json=session_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert "Session verified" in response_data["message"]


def test_verify_session_invalid(client):
    """
    Tests session verification with invalid session
    """
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


def test_edit_user_success(client, db_session):
    """
    Tests successful user editing with valid session
    """
    # Setup: Register, verify, login user
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    client.post("/register", json=register_data, params={"encrypted": False})

    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()

    login_response = client.post("/login", json={
        "email": "testuser@example.com",
        "password": "123456"
    })
    session_data = login_response.json()["session"]
    user_data = login_response.json()["user"]

    # Edit user
    edit_data = {
        "userid": user_data["userid"],
        "name": "Ali Updated",
        "surname": "Kara Updated"
    }

    response = client.post("/edit-user", json={
        **edit_data,
        "session": session_data
    })

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True


def test_edit_user_unauthorized(client):
    """
    Tests user editing without valid session
    """
    edit_data = {
        "userid": 1,
        "name": "Ali Updated"
    }
    invalid_session = {
        "session_id": "invalid",
        "user_id": 1,
        "valid_until": "2024-12-31T23:59:59Z"
    }

    response = client.post("/edit-user", json={
        **edit_data,
        "session": invalid_session
    })

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == False
    assert "Not Authorized" in response_data["message"]


# Integration test combining multiple flows
def test_complete_user_flow(client, db_session):
    """
    Tests the complete user flow: register -> verify email -> login -> edit user
    """
    # 1. Register
    register_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456",
        "phone": "+905551234567"
    }
    register_response = client.post("/register", json=register_data, params={"encrypted": False})
    assert register_response.json()["success"] == True

    # 2. Verify email (simulated)
    user = db_session.query(User).filter(User.email == "testuser@example.com").first()
    user.email_status = True
    db_session.commit()

    # 3. Login
    login_response = client.post("/login", json={
        "email": "testuser@example.com",
        "password": "123456"
    })
    assert login_response.json()["success"] == True
    session_data = login_response.json()["session"]
    user_data = login_response.json()["user"]

    # 4. Edit user
    edit_response = client.post("/edit-user", json={
        "userid": user_data["userid"],
        "name": "Updated Name",
        "session": session_data
    })
    assert edit_response.json()["success"] == True
