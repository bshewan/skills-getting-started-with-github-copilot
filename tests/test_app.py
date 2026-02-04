import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    snapshot = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(snapshot)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"].endswith("/static/index.html")


def test_get_activities_returns_data():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant():
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response.status_code == 200
    assert email in activities[activity]["participants"]


def test_signup_rejects_duplicate_participant():
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_delete_participant_removes_participant():
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    response = client.delete(f"/activities/{activity}/participant", params={"email": email})
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]


def test_delete_participant_not_found():
    activity = "Chess Club"
    email = "missing@mergington.edu"

    response = client.delete(f"/activities/{activity}/participant", params={"email": email})
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"


def test_delete_activity_not_found():
    response = client.delete("/activities/Unknown%20Club/participant", params={"email": "test@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
