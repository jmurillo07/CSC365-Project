from fastapi.testclient import TestClient

from src.api.server import app
from src import database as db
import sqlalchemy

import json

client = TestClient(app)


def test_get_event_01():
    response = client.get("/events/2")
    assert response.status_code == 200

    with open("test/events/2.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_get_event_02():
    response = client.get("/events/8")
    with open("test/events/8.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_get_fights_event_01():
    response = client.get("/events/?event_name=test2")
    assert response.status_code == 200

    with open("test/events/test2.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_get_fights_event_02():
    response = client.get("/events/?event_name=name")
    assert response.status_code == 200

    with open("test/events/name.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)


def test_get_event_404():
    response = client.get("/events/1131231")
    assert response.status_code == 404


def test_add_event_01():
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.select(
                sqlalchemy.func.max(db.events.c.event_id),
            )
        )
        event_id = result.first().max_1 + 1

    response = client.post(
        "/events/",
        headers={"Content-Type": "application/json"},
        json={
            "event_name": "Test",
            "event_date": "2023-05-08",
            "venue": "Test",
            "attendance": 1313,
        }
    )
    assert response.status_code == 200
    assert response.json()["event_id"] == event_id

    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.delete(
                db.events,
            )
                .where(db.events.c.event_id == event_id)
        )
        conn.commit()
        conn.close()


def test_add_event_400():
    response = client.post(
        "/events/",
        headers={"Content-Type": "application/json"},
        json={
            "event_name": "Test",
            "event_date": "test",
            "venue": "Test",
            "attendance": 1313,
        }
    )
    assert response.status_code == 400
