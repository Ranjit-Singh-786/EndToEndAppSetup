import pytest
from fastapi.testclient import TestClient

from app.client import ServiceError
from app.main import app


class FakeClient:
    """In-memory stand-in for the real ServiceClient so gateway routes
    can be tested without the three upstream services running."""

    def __init__(self, farmers=None, farms=None, readings=None):
        self.farmers = farmers or []
        self.farms = farms or []
        self.readings = readings or []
        self.post_calls = []

    async def get(self, service, url):
        if url.endswith("/health"):
            return {"status": "healthy", "service": service, "database": "connected"}

        if service == "user-service":
            if url.endswith("/farmers"):
                return self.farmers
            farmer_id = int(url.rsplit("/", 1)[1])
            farmer = next((f for f in self.farmers if f["id"] == farmer_id), None)
            if not farmer:
                raise ServiceError("user-service", 404, f"Farmer with ID {farmer_id} not found.")
            return farmer

        if service == "farm-service":
            if url.endswith("/farms"):
                return self.farms
            if "/crops" in url:
                farm_id = int(url.split("/farms/")[1].split("/")[0])
            else:
                farm_id = int(url.rsplit("/", 1)[1])
            farm = next((f for f in self.farms if f["id"] == farm_id), None)
            if not farm:
                raise ServiceError("farm-service", 404, f"Farm with ID {farm_id} not found.")
            return farm

        if service == "monitoring-service":
            if url.endswith("/latest"):
                if not self.readings:
                    raise ServiceError("monitoring-service", 404, "No sensor readings found.")
                return self.readings[-1]
            if url.endswith("/summary"):
                return {
                    "farm_id": 1,
                    "readings_count": len(self.readings),
                    "avg_temperature": 24.5 if self.readings else None,
                    "avg_humidity": 58.0 if self.readings else None,
                    "avg_soil_moisture": 36.5 if self.readings else None,
                    "total_rainfall": 0.0,
                }
            farm_id = int(url.rsplit("/", 1)[1])
            return [r for r in self.readings if r["farm_id"] == farm_id]

        raise AssertionError(f"Unhandled GET: {service} {url}")

    async def post(self, service, url, payload):
        self.post_calls.append((service, url, payload))
        if service == "user-service" and payload["email"] == "dup@example.com":
            raise ServiceError("user-service", 409, "A farmer with this email is already registered.")
        if service == "farm-service" and payload["farmer_id"] == 999:
            raise ServiceError("farm-service", 404, "Cannot create farm. Farmer with ID 999 does not exist.")
        return {"id": 1, **payload}


FARMER = {"id": 1, "name": "Jane Doe", "email": "jane@example.com", "phone": "+1-555-8888", "created_at": "2026-08-12T10:00:00"}
FARM = {
    "id": 1,
    "farmer_id": 1,
    "farm_name": "Sunny Acres",
    "location": "Oregon, USA",
    "area_acres": 120.0,
    "created_at": "2026-08-12T10:00:00",
    "crops": [
        {
            "id": 1,
            "farm_id": 1,
            "crop_name": "Potato",
            "crop_type": "Tuber",
            "sowing_date": "2026-08-12",
            "expected_harvest_date": "2026-12-12",
            "status": "Growing",
            "created_at": "2026-08-12T10:00:00",
        }
    ],
}
READING = {
    "id": "abc123",
    "farm_id": 1,
    "sensor_id": "SENSOR-OREGON-1",
    "timestamp": "2026-08-12T10:00:00",
    "temperature": 24.5,
    "humidity": 58.0,
    "soil_moisture": 36.5,
    "rainfall": 0.0,
    "additional_data": {"battery": 98, "signal_strength": 94},
}


@pytest.fixture(autouse=True)
def fake_backend(monkeypatch):
    fake = FakeClient(farmers=[FARMER], farms=[FARM], readings=[READING])
    monkeypatch.setattr("app.main.client", fake)
    return fake


client = TestClient(app)


def test_dashboard_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "Service health" in response.text
    assert "Registered farmers" in response.text
    assert "Managed farms" in response.text


def test_farmers_list_page():
    response = client.get("/farmers")
    assert response.status_code == 200
    assert "Farmer registry" in response.text
    assert "Jane Doe" in response.text


def test_new_farmer_form_page():
    response = client.get("/farmers/new")
    assert response.status_code == 200
    assert "Register a farmer" in response.text


def test_create_farmer_redirects(fake_backend):
    response = client.post(
        "/farmers",
        data={"name": "John Doe", "email": "john@example.com", "password": "secret123", "phone": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/farmers?")
    assert fake_backend.post_calls[0][0] == "user-service"


def test_create_farmer_duplicate_error(fake_backend):
    response = client.post(
        "/farmers",
        data={"name": "Jane Doe", "email": "dup@example.com", "password": "secret123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/farmers/new?error=")


def test_farmer_detail_page():
    response = client.get("/farmers/1")
    assert response.status_code == 200
    assert "Jane Doe" in response.text
    assert "Sunny Acres" in response.text


def test_farmer_detail_not_found():
    response = client.get("/farmers/999")
    assert response.status_code == 200
    assert "Farmer with ID 999 not found" in response.text


def test_farms_list_page():
    response = client.get("/farms")
    assert response.status_code == 200
    assert "Farm & crop registry" in response.text
    assert "Sunny Acres" in response.text
    assert "Potato" in response.text


def test_farm_detail_page():
    response = client.get("/farms/1")
    assert response.status_code == 200
    assert "Potato" in response.text


def test_crop_form_page():
    response = client.get("/farms/1/crops/new")
    assert response.status_code == 200
    assert "Add crop to Sunny Acres" in response.text


def test_create_farm_owner_missing_redirects(fake_backend):
    response = client.post(
        "/farms",
        data={"farmer_id": 999, "farm_name": "Ghost Farm", "location": "Nowhere", "area_acres": 10},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/farms/new?error=")


def test_monitoring_page_renders_latest():
    response = client.get("/monitoring?farm_id=1")
    assert response.status_code == 200
    assert "Field monitoring" in response.text
    assert "SENSOR-OREGON-1" in response.text
    assert "24.5" in response.text


def test_monitoring_ajax_endpoint():
    response = client.get("/ajax/monitoring/1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["latest"]["sensor_id"] == "SENSOR-OREGON-1"
    assert payload["summary"]["readings_count"] == 1


def test_new_reading_form_page():
    response = client.get("/monitoring/readings/new")
    assert response.status_code == 200
    assert "Record sensor reading" in response.text


def test_create_reading_redirects(fake_backend):
    response = client.post(
        "/monitoring/readings",
        data={
            "farm_id": 1,
            "sensor_id": "SENSOR-2",
            "temperature": 25.5,
            "humidity": 60.0,
            "soil_moisture": 40.0,
            "rainfall": 2.0,
            "battery": 97,
            "signal_strength": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/monitoring?farm_id=1")
    service, url, payload = fake_backend.post_calls[-1]
    assert service == "monitoring-service"
    assert payload["additional_data"] == {"battery": 97}
