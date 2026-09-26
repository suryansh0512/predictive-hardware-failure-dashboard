import pytest
from fastapi.testclient import TestClient
from api.app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "host_id" in data
    assert "live_mode" in data
    assert "total_records" in data
    assert "uptime_seconds" in data


def test_telemetry_latest_endpoint(client):
    response = client.get("/telemetry/latest?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "records" in data
    assert isinstance(data["records"], list)


def test_telemetry_history_endpoint(client):
    response = client.get("/telemetry/history?hours=1")
    assert response.status_code == 200
    data = response.json()
    assert "hours" in data
    assert data["hours"] == 1.0
    assert "records" in data


def test_window_latest_endpoint(client):
    response = client.get("/window/latest?entity_class=CPU&window_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["entity_class"] == "CPU"
    assert "statistical_features" in data


def test_websocket_telemetry(client):
    with client.websocket_connect("/ws/telemetry") as websocket:
        # First message sent upon connect is greeting/snapshot
        initial_msg = websocket.receive_json()
        assert initial_msg["event"] == "connected"
        assert "latest_snapshot" in initial_msg

        # Test ping/pong
        websocket.send_text("ping")
        pong_msg = websocket.receive_json()
        assert pong_msg["event"] == "pong"
