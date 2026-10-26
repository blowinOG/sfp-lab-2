def test_register_login_me(client, strong_password):
    r = client.post("/auth/register", json={"email": "u@example.com", "password": strong_password})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r2 = client.post("/auth/login", json={"email": "u@example.com", "password": strong_password})
    assert r2.status_code == 200

    r3 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["email"] == "u@example.com"


def test_weak_password_registration_fails(client):
    r = client.post("/auth/register", json={"email": "w@example.com", "password": "123"})
    assert r.status_code == 400


def test_login_wrong_password_returns_401(client, registered_user):
    r = client.post("/auth/login", json={"email": registered_user["email"], "password": "totally-wrong-pass-1!"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"


def test_me_without_token_returns_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401