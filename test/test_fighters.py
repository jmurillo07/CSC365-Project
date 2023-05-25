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


def test_get_fighter_03():
    response = client.get("/fighters/2415")
    assert response.status_code == 200

    with open("test/fighters/2415.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_list_fighter_01():
    response = client.get("/fighters/?stance=south&height_min=0&height_max=999&"
                          + "reach_min=0&reach_max=999&wins_min=0&wins_max=9999"
                          + "&losses_min=0&losses_max=9999&draws_min=0&draws_ma"
                          + "x=9999&event=ufc&sort=height&order=ascending&limit"
                          + "=50&offset=0")
    assert response.status_code == 200

    with open("test/fighters/list_1.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_list_fighter_02():
    response = client.get("/fighters/?height_min=0&height_max=999&reach_min=0&r"
                          + "each_max=999&wins_min=0&wins_max=9999&losses_min=0"
                          + "&losses_max=9999&draws_min=0&draws_max=9999&weight"
                          + "_class=heavyweight&sort=reach&order=descending&lim"
                          + "it=102&offset=0")
    assert response.status_code == 200

    with open("test/fighters/list_2.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)

def test_add_fighter_01():
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 10,
            "reach": 74,
            "stance_id": 2
        }
    )
    assert response.status_code == 200
    fighter_id = response.json()["fighter_id"]
    get_request = "/fighters/" + str(fighter_id)
    response = client.get(get_request)
    assert response.status_code == 200

    expected_response = {
        "fighter_id": fighter_id,
        "name": "Test Delete Me",
        "height": 10,
        "reach": 74,
        "stance": "Southpaw",
        "weight": None,
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
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 0,
            "stance_id": None
        }
    )
    assert response.status_code == 200
    fighter_id = response.json()["fighter_id"]
    get_request = "/fighters/" + str(fighter_id)
    response = client.get(get_request)
    assert response.status_code == 200

    expected_response = {
        "fighter_id": fighter_id,
        "name": "Test Delete Me",
        "height": 0,
        "reach": 0,
        "stance": None,
        "weight": None,
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


def test_update_fight_01():
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 0,
            "stance_id": None
        }
    )
    assert response.status_code == 200
    fighter_id = response.json()["fighter_id"]
    get_request = "/fighters/" + str(fighter_id)
    response = client.get(get_request)
    assert response.status_code == 200

    expected_response = {
        "fighter_id": fighter_id,
        "name": "Test Delete Me",
        "height": 0,
        "reach": 0,
        "stance": None,
        "weight": None,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "recent_fights": []
    }

    assert response.json() == expected_response

    response = client.put(
        "/fighters/" + str(fighter_id),
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Testtesttest",
            "height": 50,
            "reach": 50,
            "stance_id": 3
        }
    )
    assert response.status_code == 200
    get_request = "/fighters/" + str(fighter_id)
    response = client.get(get_request)
    assert response.status_code == 200

    expected_response = {
        "fighter_id": fighter_id,
        "name": "Testtesttest Delete Me",
        "height": 50,
        "reach": 50,
        "stance": "Switch",
        "weight": None,
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


def test_list_fighter_403():
    # height_min > height_max
    response = client.get("/fighters/?stance=south&height_min=11&height_max=10&"
                          + "reach_min=0&reach_max=999&wins_min=0&wins_max=9999"
                          + "&losses_min=0&losses_max=9999&draws_min=0&draws_ma"
                          + "x=9999&event=ufc&sort=height&order=ascending&limit"
                          + "=50&offset=0")
    assert response.status_code == 403

    # reach_min > reach_max
    response = client.get("/fighters/?stance=south&height_min=0&height_max=999&"
                          + "reach_min=11&reach_max=10&wins_min=0&wins_max=9999"
                          + "&losses_min=0&losses_max=9999&draws_min=0&draws_ma"
                          + "x=9999&event=ufc&sort=height&order=ascending&limit"
                          + "=50&offset=0")
    assert response.status_code == 403

    # wins_min > wins_max
    response = client.get("/fighters/?stance=south&height_min=0&height_max=999&"
                          + "reach_min=0&reach_max=999&wins_min=100&wins_max=10"
                          + "&losses_min=0&losses_max=9999&draws_min=0&draws_ma"
                          + "x=9999&event=ufc&sort=height&order=ascending&limit"
                          + "=50&offset=0")
    assert response.status_code == 403

    # losses_min > losses_max
    response = client.get("/fighters/?stance=south&height_min=0&height_max=999&"
                          + "reach_min=0&reach_max=999&wins_min=0&wins_max=9999"
                          + "&losses_min=100&losses_max=10&draws_min=0&draws_ma"
                          + "x=9999&event=ufc&sort=height&order=ascending&limit"
                          + "=50&offset=0")
    assert response.status_code == 403

    # draws_min > draws_max
    response = client.get("/fighters/?stance=south&height_min=0&height_max=999&"
                          + "reach_min=0&reach_max=999&wins_min=0&wins_max=9999"
                          + "&losses_min=0&losses_max=9999&draws_min=100&draws_"
                          + "max=99&event=ufc&sort=height&order=ascending&limit"
                          + "=50&offset=0")
    assert response.status_code == 403


def test_add_fighter_409():
    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 0,
            "stance_id": None
        }
    )
    assert response.status_code == 200
    fighter_id = response.json()["fighter_id"]

    response = client.post(
        "/fighters/",
        headers={"Content-Type": "application/json"},
        json={
            "first_name": "Test",
            "last_name": "Delete Me",
            "height": 0,
            "reach": 0,
            "stance_id": None
        }
    )
    assert response.status_code == 409

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
            "stance_id": 1
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
            "stance_id": 1
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
            "stance_id": 1
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
            "reach": 1001231,
            "stance_id": 1
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
            "stance_id": 0
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
            "stance_id": 4
        }
    )
    assert response.status_code == 400
