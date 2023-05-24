from fastapi.testclient import TestClient

from src.api.server import app
from src import database as db
import sqlalchemy
import json
import pytest

client = TestClient(app)


def test_user_01():
    # Create, get name, authenticate, delete
    response = client.post(
        "/users/create",
        headers={"Content-Type": "application/json"},
        json={
            "username": "test_user",
            "password": "test_password"
        }
    )
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    response = client.get("/users/" + str(user_id))
    assert response.status_code == 200
    actual_username = response.json()["username"]
    assert actual_username == "test_user"

    response = client.post(
        "/users/create",
        headers={"Content-Type": "application/json"},
        json={
            "username": "test_user",
            "password": "test_password"
        }
    )
    assert response.status_code == 409

    response = client.post(
        "/users/login",
        headers={"Content-Type": "application/json"},
        json={
            "username": "test_user",
            "password": "test_passwordasd"
        }
    )
    assert response.status_code == 200
    actual_status = response.json()["status"]
    assert actual_status == "failed"

    response = client.post(
        "/users/login",
        headers={"Content-Type": "application/json"},
        json={
            "username": "test_user",
            "password": "test_password"
        }
    )
    assert response.status_code == 200
    actual_status = response.json()["status"]
    assert actual_status == "success"

    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.delete(
                db.users,
            )
            .where(db.users.c.user_id == user_id)
        )
    
    # Ensure the identity key is after the max id
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                """
                SELECT setval(pg_get_serial_sequence('users', 'user_id'), max(user_id))
                FROM users"""
            )
        )