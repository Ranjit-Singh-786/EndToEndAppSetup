import pytest
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

# Dependency override
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
    # Setup: Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown: Drop tables
    Base.metadata.drop_all(bind=engine)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "user-service"

def test_create_farmer():
    # Create farmer
    payload = {
        "name": "Jane Farmer",
        "email": "jane@example.com",
        "password": "securepassword",
        "phone": "+1-555-9876"
    }
    response = client.post("/farmers", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "Jane Farmer"
    assert data["email"] == "jane@example.com"
    assert data["phone"] == "+1-555-9876"
    assert "id" in data
    assert "password" not in data  # Ensure password is not exposed

def test_create_duplicate_farmer_fails():
    payload = {
        "name": "Jane Farmer",
        "email": "jane@example.com",
        "password": "securepassword",
        "phone": "+1-555-9876"
    }
    # First creation
    response = client.post("/farmers", json=payload)
    assert response.status_code == 201
    
    # Second creation with duplicate email
    response2 = client.post("/farmers", json=payload)
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"]

def test_get_farmer():
    # Create a farmer
    payload = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "mypassword"
    }
    create_res = client.post("/farmers", json=payload).json()
    farmer_id = create_res["id"]
    
    # Retrieve farmer
    response = client.get(f"/farmers/{farmer_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"
    assert response.json()["email"] == "john@example.com"

def test_get_nonexistent_farmer_fails():
    response = client.get("/farmers/999")
    assert response.status_code == 404

def test_list_farmers():
    # Create two farmers
    client.post("/farmers", json={"name": "Farmer A", "email": "a@example.com", "password": "password"})
    client.post("/farmers", json={"name": "Farmer B", "email": "b@example.com", "password": "password"})
    
    response = client.get("/farmers")
    assert response.status_code == 200
    farmers_list = response.json()
    assert len(farmers_list) >= 2
    
def test_update_farmer():
    payload = {
        "name": "Farmer Original",
        "email": "orig@example.com",
        "password": "password"
    }
    create_res = client.post("/farmers", json=payload).json()
    farmer_id = create_res["id"]
    
    # Update phone and name
    update_payload = {
        "name": "Farmer Updated",
        "phone": "+99-999-999"
    }
    response = client.put(f"/farmers/{farmer_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Farmer Updated"
    assert response.json()["phone"] == "+99-999-999"
    assert response.json()["email"] == "orig@example.com"

def test_delete_farmer():
    payload = {
        "name": "To Delete",
        "email": "del@example.com",
        "password": "password"
    }
    create_res = client.post("/farmers", json=payload).json()
    farmer_id = create_res["id"]
    
    # Delete
    response = client.delete(f"/farmers/{farmer_id}")
    assert response.status_code == 204
    
    # Verify not found
    get_res = client.get(f"/farmers/{farmer_id}")
    assert get_res.status_code == 404
