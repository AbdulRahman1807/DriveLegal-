"""Auth register / login / profile CRUD integration tests."""

import uuid

import pytest


@pytest.fixture
def unique_email():
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def test_auth_register_login_me_update_delete(client, unique_email):
    password = "securepass123"

    # Create
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password, "language_preference": "en"},
    )
    assert reg.status_code == 201, reg.text
    tokens = reg.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Read
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == unique_email

    # Update language
    patch = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"language_preference": "hi"},
    )
    assert patch.status_code == 200
    assert patch.json()["language_preference"] == "hi"

    # Update password
    new_password = "newsecurepass99"
    patch_pw = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"current_password": password, "new_password": new_password},
    )
    assert patch_pw.status_code == 200

    # Login with new password
    login = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": new_password},
    )
    assert login.status_code == 200
    new_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Delete (deactivate)
    delete = client.delete("/api/v1/auth/me", headers=new_headers)
    assert delete.status_code == 204

    # Deactivated user cannot log in
    login_again = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": new_password},
    )
    assert login_again.status_code == 403


def test_auth_duplicate_email(client, unique_email):
    password = "securepass123"
    payload = {"email": unique_email, "password": password}

    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
