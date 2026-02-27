import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict before each test."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_root_redirect():
    # Arrange: nothing special, just the client
    # Act: request root without following redirects
    resp = client.get("/", follow_redirects=False)

    # Assert: we get a redirect to the static page
    assert resp.status_code in (307, 308)
    assert resp.headers["location"].endswith("/static/index.html")


def test_get_activities():
    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # make sure one known activity exists with expected fields
    assert "Chess Club" in data
    assert "description" in data["Chess Club"]
    assert "participants" in data["Chess Club"]


def test_signup_success():
    # Arrange
    activity = "Chess Club"
    email = "new@student.com"

    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert response
    assert resp.status_code == 200
    assert f"Signed up {email} for {activity}" in resp.json()["message"]

    # Assert side effect
    resp2 = client.get("/activities")
    assert email in resp2.json()[activity]["participants"]


def test_signup_duplicate():
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"  # already in initial data

    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student already signed up"


def test_signup_nonexistent_activity():
    # Act
    resp = client.post("/activities/NoSuchActivity/signup", params={"email": "foo@bar.com"})

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_remove_signup_success():
    # Arrange
    activity = "Chess Club"
    email = "daniel@mergington.edu"

    # Act
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert response
    assert resp.status_code == 200
    assert f"Removed {email} from {activity}" in resp.json()["message"]

    # Assert side effect
    resp2 = client.get("/activities")
    assert email not in resp2.json()[activity]["participants"]


def test_remove_signup_not_signed():
    # Arrange
    activity = "Chess Club"
    email = "not@there.com"

    # Act
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Student not signed up"


def test_remove_nonexistent_activity():
    # Act
    resp = client.delete("/activities/Nope/signup", params={"email": "a@b.com"})

    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"
