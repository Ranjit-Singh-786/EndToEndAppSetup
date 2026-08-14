import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite database with StaticPool to persist schemas across session connections
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "farm-service"

@patch("app.routers.farms.verify_farmer_exists")
def test_create_farm(mock_verify):
    mock_verify.return_value = True  # Mock farmer verification success
    
    payload = {
        "farmer_id": 1,
        "farm_name": "Test Farm",
        "location": "Test Region",
        "area_acres": 12.5
    }
    response = client.post("/farms", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["farm_name"] == "Test Farm"
    assert data["farmer_id"] == 1
    assert "id" in data

@patch("app.routers.farms.verify_farmer_exists")
def test_create_farm_farmer_not_found(mock_verify):
    mock_verify.return_value = False  # Mock farmer verification failure
    
    payload = {
        "farmer_id": 999,
        "farm_name": "Test Farm",
        "location": "Test Region",
        "area_acres": 12.5
    }
    response = client.post("/farms", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]

@patch("app.routers.farms.verify_farmer_exists")
def test_add_crop(mock_verify):
    mock_verify.return_value = True
    
    # 1. Create farm first
    farm_payload = {
        "farmer_id": 1,
        "farm_name": "My Farm",
        "location": "Midwest",
        "area_acres": 250.0
    }
    farm_res = client.post("/farms", json=farm_payload).json()
    farm_id = farm_res["id"]
    
    # 2. Add crop
    crop_payload = {
        "crop_name": "Corn",
        "crop_type": "Grain",
        "sowing_date": "2026-05-01",
        "expected_harvest_date": "2026-09-01",
        "status": "Sown"
    }
    response = client.post(f"/farms/{farm_id}/crops", json=crop_payload)
    assert response.status_code == 201
    
    crop_data = response.json()
    assert crop_data["crop_name"] == "Corn"
    assert crop_data["farm_id"] == farm_id
    assert "id" in crop_data

def test_add_crop_to_nonexistent_farm_fails():
    crop_payload = {
        "crop_name": "Corn",
        "crop_type": "Grain",
        "sowing_date": "2026-05-01",
        "expected_harvest_date": "2026-09-01"
    }
    response = client.post("/farms/999/crops", json=crop_payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]

@patch("app.routers.farms.verify_farmer_exists")
def test_get_crops_for_farm(mock_verify):
    mock_verify.return_value = True
    
    farm_res = client.post("/farms", json={
        "farmer_id": 1,
        "farm_name": "Crop Farm",
        "location": "North",
        "area_acres": 5.0
    }).json()
    farm_id = farm_res["id"]
    
    client.post(f"/farms/{farm_id}/crops", json={
        "crop_name": "Potato",
        "crop_type": "Tuber",
        "sowing_date": "2026-04-10",
        "expected_harvest_date": "2026-08-10"
    })
    
    response = client.get(f"/farms/{farm_id}/crops")
    assert response.status_code == 200
    crops = response.json()
    assert len(crops) == 1
    assert crops[0]["crop_name"] == "Potato"
