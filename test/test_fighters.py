from fastapi.testclient import TestClient

from src.api.server import app
from src import database as db
from .factories import FightersFactory
from .factories import FighterStatsFactory
import sqlalchemy
import json
import pytest

client = TestClient(app)


# def test_fighter_factory():
#     FightersFactory.create()


def test_get_fighter_01():
    response = client.get("/fighters/3278")
    assert response.status_code == 200

    with open("test/fighters/3278.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_get_fighter_02():
    response = client.get("/fighters/1")
    assert response.status_code == 200

    with open("test/fighters/1.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_list_fighter_01():
    response = client.get("/fighters/?stance=o&name=test&height_min=10&height"
                          + "_max=999&weight_min=100&weight_max=290&reach_min"
                          + "=20&reach_max=999&wins_min=1&wins_max=300&losses"
                          + "_min=0&losses_max=100&draws_min=1&draws_max=120&"
                          + "event=test2&sort=weight&order=descending&limit=5"
                          + "0&offset=0")
    assert response.status_code == 200

    with open("test/fighters/list_1.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_list_fighter_02():
    response = client.get("/fighters/?stance=s&name=test&height_min=0&height_m"
                          + "ax=999&weight_min=100&weight_max=9999&reach_min=2"
                          + "0&reach_max=999&wins_min=0&wins_max=20&losses_min"
                          + "=0&losses_max=20&draws_min=0&draws_max=20&sort=na"
                          + "me&order=ascending&limit=50&offset=0")
    assert response.status_code == 200

    with open("test/fighters/list_2.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)

def test_add_fighter_01():
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                """
                SELECT nextval(pg_get_serial_sequence('fighters', 'fighter_id')) as next_id
                FROM fighters
                """
            )
        )
        fighter_id = result.first().next_id

    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 10,
            "reach": 74.1,
            "stance": 2
        }
    )
    assert response.status_code == 200
    assert response.json()["fighter_id"] == fighter_id
    get_request = "/fighters/" + str(fighter_id)
    response = client.get(get_request)
    assert response.status_code == 200

    expected_response = {
        "fighter_id": fighter_id,
        "name": "Test Delete Me",
        "height": 10,
        "weight": None,
        "reach": 74.1,
        "stance": "Southpaw",
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "recent_fights": []
    }

    assert response.json() == expected_response

    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.delete(
                db.fighters,
            )
            .where(db.fighters.c.fighter_id == fighter_id)
        )
    
    # Ensure the identity key is after the max id
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                """
                SELECT setval(pg_get_serial_sequence('fighters', 'fighter_id'), max(fighter_id))
                FROM fighters"""
            )
        )


def test_add_fighter_02():
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                """
                SELECT nextval(pg_get_serial_sequence('fighters', 'fighter_id')) as next_id
                FROM fighters
                """
            )
        )
        fighter_id = result.first().next_id

    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 0,
            "stance": None
        }
    )
    assert response.status_code == 200
    assert response.json()["fighter_id"] == fighter_id
    get_request = "/fighters/" + str(fighter_id)
    response = client.get(get_request)
    assert response.status_code == 200

    expected_response = {
        "fighter_id": fighter_id,
        "name": "Test Delete Me",
        "height": 0,
        "weight": None,
        "reach": 0,
        "stance": None,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "recent_fights": []
    }

    assert response.json() == expected_response

    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.delete(
                db.fighters,
            )
            .where(db.fighters.c.fighter_id == fighter_id)
        )
    
    # Ensure the identity key is after the max id
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                """
                SELECT setval(pg_get_serial_sequence('fighters', 'fighter_id'), max(fighter_id))
                FROM fighters"""
            )
        )


def test_get_fighter_404():
    response = client.get("/fighters/9128319283")
    assert response.status_code == 404


def test_add_fighter_400():
    # Wrong height
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 1000000,
            "reach": 0,
            "stance": 1
        }
    )
    assert response.status_code == 400
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": -1,
            "reach": 0,
            "stance": 1
        }
    )
    assert response.status_code == 400

    # Wrong reach
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": -1,
            "stance": 1
        }
    )
    assert response.status_code == 400
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 100,
            "stance": 1
        }
    )
    assert response.status_code == 400

    # Wrong stance
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 0,
            "stance": 0
        }
    )
    assert response.status_code == 400
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 0,
            "stance": 4
        }
    )
    assert response.status_code == 400
