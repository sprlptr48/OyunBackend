def test_register_user_success(client):
    """
    Yeni bir kullanıcının başarıyla kaydedilmesini test eder.
    """
    test_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456"
        # phone zorunlu değilse, buraya eklemene gerek yok.
    }
    response = client.post(
        "/register",
        json=test_data,
        params={"encrypted": False}
    )
    assert response.status_code == 201

    response_data = response.json()
    assert response_data["user"]["email"] == "testuser@example.com"
    assert "password" not in response_data["user"]
    assert "session" in response_data


def test_register_existing_user_fail(client):
    """
    Mevcut bir e-posta ile kayıt olmaya çalışıldığında hata alınmasını test eder.
    """
    test_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456"
        # phone zorunlu değilse, buraya eklemene gerek yok.
    }
    # Önce kullanıcıyı oluştur
    client.post("/register", json=test_data, params={"encrypted": False})

    # Sonra aynı e-posta ile tekrar dene
    response = client.post("/register", json=test_data, params={"encrypted": False})

    print(response.json())
    assert response.status_code == 400
    assert response.json() == {"detail": "User already exists"}

def test_login_user_success(client):
    login_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456"
    }
    response = client.post(
        "/register",
        json=login_data,
        params={"encrypted": False}
    )

    register_response_data = response.json()
    assert register_response_data["user"]["email"] == "testuser@example.com"
    test_data = {
        "email": "testuser@example.com",
        "password": "123456"
    }
    response = client.post(
        "/login",
        json=test_data,
        params={"encrypted": False}
    )
    response_data = response.json()
    assert response.status_code == 200
    assert "session" in response_data
    assert "user_id" in response_data["session"]
    assert response_data["session"]["user_id"] == register_response_data["user"]["userid"]


def test_login_user_fail(client):
    login_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456"
    }
    response = client.post(
        "/register",
        json=login_data,
        params={"encrypted": False}
    )

    register_response_data = response.json()
    assert register_response_data["user"]["email"] == "testuser@example.com"
    test_data = {
        "email": "wrongmail",
        "password": "wrongpassword"
    }
    response = client.post(
        "/login",
        json=test_data,
        params={"encrypted": False}
    )
    assert response.status_code == 401
