import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    # Arrange: reset the in-memory activity database for deterministic tests
    app_module.activities.clear()
    app_module.activities.update(
        {
            "Chess Club": {
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 12,
                "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
            },
            "Programming Class": {
                "description": "Learn programming fundamentals and build software projects",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                "max_participants": 20,
                "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
            },
            "Gym Class": {
                "description": "Physical education and sports activities",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                "max_participants": 30,
                "participants": ["john@mergington.edu", "olivia@mergington.edu"],
            },
        }
    )
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_registered_activity(client):
    # Arrange
    # The fixture already seeds the activity list.

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_new_participant(client):
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post("/activities/Gym%20Class/signup?email=newstudent@mergington.edu")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == f"Signed up {email} for Gym Class"
    assert email in app_module.activities["Gym Class"]["participants"]


def test_signup_rejects_duplicate_registration(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/Chess%20Club/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Already signed up for this activity"


def test_signup_rejects_when_activity_is_full(client):
    # Arrange
    app_module.activities["Programming Class"]["participants"] = [
        f"student{i}@mergington.edu" for i in range(20)
    ]

    # Act
    response = client.post("/activities/Programming%20Class/signup?email=late@mergington.edu")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_student_from_activity(client):
    # Arrange
    email = "daniel@mergington.edu"

    # Act
    response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    # There is no such activity in the seeded dataset.

    # Act
    response = client.post("/activities/Unknown%20Club/signup?email=anyone@mergington.edu")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
