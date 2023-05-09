from fastapi.testclient import TestClient
from src.api.server import app
import json

client = TestClient(app)

def test_get_fights_valid():
    response = client.get("/fights/1")
    assert response.status_code == 200

    expected_data = {
        "fight_id": 1,
        "fighter1_id": 1,
        "fighter2_id": 2,
        "method_of_vic": 7,
        "round_num": 1,
        "round_time": "2:22",
        "event_id": 2,
        "result": 2,
        "stats1_id": 1,
        "stats2_id": 2
    }
    assert response.json() == expected_data

def test_get_fights_invalid():
    response = client.get("/fights/100")
    assert response.status_code == 404

    expected_data = {
        "detail": "fight was not found"
    }
    assert response.json() == expected_data

def test_post_fight_success():
    expected_data = {
        "fight_id": 12,
        "fighter1_id": 1,
        "fighter2_id": 2,
        "method_of_vic": 1,
        "round_num": 3,
        "round_time": "3:02",
        "event_id": 8,
        "result": None,
        "stats1_id": 5,
        "stats2_id": 6
    }

    response = client.get("/fights/12")
    assert response.status_code == 200
    assert response.json() == expected_data


def test_post_fight_missing_fields():
    payload = {
        "fighter1_id": 123,
        "fighter2_id": 456,
        "round_num": 3,
        "round_time": "02:35",
        "event_id": 789,
        "result": 123,
        # Missing some fields on purpose
    }

    response = client.post("/fights", json=payload)
    assert response.status_code == 422