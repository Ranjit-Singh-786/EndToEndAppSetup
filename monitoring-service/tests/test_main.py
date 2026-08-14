import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
import mongomock

from app.main import app
from app.database import get_db

# Setup mongomock in-memory client and db
mock_client = mongomock.MongoClient()
mock_db = mock_client.smartfarm_monitoring

def override_get_db():
    return mock_db

# Override dependency in FastAPI
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Teardown: clear collections before/after test run
    mock_db.sensor_readings.delete_many({})
    yield

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "monitoring-service"

@patch("app.routers.monitoring.verify_farm_exists")
def test_post_sensor_reading(mock_verify):
    mock_verify.return_value = True  # Mock farm validation success
    
    payload = {
        "farm_id": 1,
        "sensor_id": "SENSOR-TEST",
        "temperature": 28.5,
        "humidity": 58.0,
        "soil_moisture": 35.0,
        "rainfall": 0.0,
        "additional_data": {
            "battery": 95,
            "signal_strength": 90
        }
    }
    response = client.post("/readings", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["sensor_id"] == "SENSOR-TEST"
    assert data["farm_id"] == 1
    assert "id" in data

@patch("app.routers.monitoring.verify_farm_exists")
def test_post_sensor_reading_farm_not_found(mock_verify):
    mock_verify.return_value = False  # Mock farm validation fail
    
    payload = {
        "farm_id": 999,
        "sensor_id": "SENSOR-TEST",
        "temperature": 28.5,
        "humidity": 58.0,
        "soil_moisture": 35.0,
        "rainfall": 0.0
    }
    response = client.post("/readings", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]

@patch("app.routers.monitoring.verify_farm_exists")
def test_get_sensor_history(mock_verify):
    mock_verify.return_value = True
    
    # Seed mock db directly
    mock_db.sensor_readings.insert_many([
        {
            "farm_id": 1,
            "sensor_id": "S1",
            "timestamp": "2026-08-12T10:00:00",
            "temperature": 20.0,
            "humidity": 50.0,
            "soil_moisture": 40.0,
            "rainfall": 0.0
        },
        {
            "farm_id": 1,
            "sensor_id": "S1",
            "timestamp": "2026-08-12T10:15:00",
            "temperature": 22.0,
            "humidity": 52.0,
            "soil_moisture": 42.0,
            "rainfall": 0.5
        }
    ])
    
    response = client.get("/readings/1")
    assert response.status_code == 200
    readings = response.json()
    assert len(readings) == 2
    assert readings[0]["sensor_id"] == "S1"

@patch("app.routers.monitoring.verify_farm_exists")
def test_get_latest_reading(mock_verify):
    mock_verify.return_value = True
    
    # Seed readings with distinct timestamps
    mock_db.sensor_readings.insert_many([
        {
            "farm_id": 1,
            "sensor_id": "S-OLD",
            "timestamp": "2026-08-12T09:00:00",
            "temperature": 18.0,
            "humidity": 50.0,
            "soil_moisture": 40.0,
            "rainfall": 0.0
        },
        {
            "farm_id": 1,
            "sensor_id": "S-NEW",
            "timestamp": "2026-08-12T10:00:00",
            "temperature": 24.0,
            "humidity": 55.0,
            "soil_moisture": 42.0,
            "rainfall": 0.2
        }
    ])
    
    response = client.get("/readings/1/latest")
    assert response.status_code == 200
    latest = response.json()
    assert latest["sensor_id"] == "S-NEW"
    assert latest["temperature"] == 24.0

def test_get_latest_reading_not_found():
    response = client.get("/readings/1/latest")
    assert response.status_code == 404
    assert "No sensor readings found" in response.json()["detail"]

@patch("app.routers.monitoring.verify_farm_exists")
def test_get_summary(mock_verify):
    mock_verify.return_value = True
    
    # Seed some mock data to aggregate
    mock_db.sensor_readings.insert_many([
        {
            "farm_id": 1,
            "sensor_id": "S1",
            "temperature": 30.0,
            "humidity": 60.0,
            "soil_moisture": 40.0,
            "rainfall": 1.0
        },
        {
            "farm_id": 1,
            "sensor_id": "S2",
            "temperature": 32.0,
            "humidity": 64.0,
            "soil_moisture": 42.0,
            "rainfall": 2.0
        }
    ])
    
    response = client.get("/readings/1/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["farm_id"] == 1
    assert summary["readings_count"] == 2
    assert summary["avg_temperature"] == 31.0
    assert summary["avg_humidity"] == 62.0
    assert summary["avg_soil_moisture"] == 41.0
    assert summary["total_rainfall"] == 3.0
