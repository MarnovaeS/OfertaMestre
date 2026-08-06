def test_register_login_and_read_current_user(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "marcelo@example.com", "full_name": "Marcelo", "password": "strong-password"},
    )

    assert register_response.status_code == 201
    assert register_response.json()["email"] == "marcelo@example.com"

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "marcelo@example.com", "password": "strong-password"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == "Marcelo"


def test_register_normalizes_email_and_rejects_duplicate(client):
    first_response = client.post(
        "/api/v1/auth/register",
        json={"email": "User@Example.com", "full_name": "User One", "password": "strong-password"},
    )
    second_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "User Two", "password": "strong-password"},
    )

    assert first_response.status_code == 201
    assert first_response.json()["email"] == "user@example.com"
    assert second_response.status_code == 409
