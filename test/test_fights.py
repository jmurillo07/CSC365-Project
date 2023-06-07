from fastapi.testclient import TestClient
from src.api.server import app
import json
import pytest

client = TestClient(app)

"""
TODO: New tests to correspond with the new schema (and actually huamn friendly endpoints)
"""