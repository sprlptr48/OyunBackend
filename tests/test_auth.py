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
    if response.status_code != 201:
        print("HATA DETAYI:", response.json())
    assert response.status_code == 201

    response_data = response.json()
    assert response_data["user"]["email"] == "testuser@example.com"
    assert "password" not in response_data["user"]
    assert "session" in response_data


def test_register_existing_user_fail(client):
    """
    Mevcut bir e-posta ile kayıt olmaya çalışıldığında hata alınmasını test eder.
    """
    # Her test temiz bir veritabanı ile başladığı için, aynı veriyi kullanabiliriz.
    test_data = {
        "name": "ali",
        "surname": "kara",
        "username": "alik16",
        "email": "testuser@example.com",
        "password": "123456"
        # phone zorunlu değilse, buraya eklemene gerek yok.
    }
    # Önce kullanıcıyı oluştur
    client.post("/register", json=test_data)

    # Sonra aynı e-posta ile tekrar dene
    response = client.post("/register", json=test_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "User already exists"}
