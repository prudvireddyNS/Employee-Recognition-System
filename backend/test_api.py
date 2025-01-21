from fastapi.testclient import TestClient
from .main import app
import pytest
import base64
import os
from datetime import datetime
from .database import Base, engine
from .auth import create_initial_admin
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize FastAPI cache
    FastAPICache.init(InMemoryBackend())
    
    # Create initial admin user
    create_initial_admin()
    
    yield
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

def get_test_image_base64():
    # Replace with path to a test image in your project
    image_path = "backend/tests/test_image.jpg"
    if not os.path.exists(image_path):
        raise Exception(f"Test image not found at {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_admin_login():
    response = client.post(
        "/api/v1/admin/login",
        data={
            "username": "admin",
            "password": "admin123",
            "grant_type": "password"  # Required for OAuth2 form
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]  # This is needed for other tests

# Add a new test that doesn't return anything
def test_admin_login_validation():
    response = client.post(
        "/api/v1/admin/login",
        data={
            "username": "admin",
            "password": "admin123",
            "grant_type": "password"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_register_employee():
    token = test_admin_login()
    test_image = get_test_image_base64()
    
    response = client.post(
        "/api/v1/register-employee",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "image": test_image,
            "firstName": "John",
            "lastName": "Doe",
            "department": "IT",
            "position": "Developer",
            "email": "john.doe@example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "John Doe"

def test_face_detection():
    test_image = get_test_image_base64()
    response = client.post(
        "/api/v1/detect-faces",
        json={"image": test_image}
    )
    assert response.status_code == 200
    assert "faces" in response.json()

def test_face_recognition():
    test_image = get_test_image_base64()
    response = client.post(
        "/api/v1/recognize-face",
        json={"image": test_image}
    )
    assert response.status_code == 200
    assert "success" in response.json()

def test_get_recent_activity():
    # First register an employee and mark attendance
    token = test_admin_login()
    test_image = get_test_image_base64()
    
    # Register employee
    client.post(
        "/api/v1/register-employee",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "image": test_image,
            "firstName": "Test",
            "lastName": "User",
            "department": "IT",
            "position": "Developer",
            "email": "test.user@example.com"
        }
    )
    
    # Mark attendance
    client.post(
        "/api/v1/recognize-face",
        json={"image": test_image}
    )
    
    # Get recent activity
    response = client.get("/api/v1/recent-activity")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_admin_endpoints():
    token = test_admin_login()
    headers = {"Authorization": f"Bearer {token}"}

    # Test get all employees
    response = client.get(
        "/api/v1/admin/employees",
        headers=headers
    )
    assert response.status_code == 200

    # Test daily attendance
    response = client.get(
        "/api/v1/admin/attendance/daily",
        headers=headers
    )
    assert response.status_code == 200

    # Test statistics
    response = client.get(
        "/api/v1/admin/statistics",
        headers=headers
    )
    assert response.status_code == 200

def test_export_attendance():
    token = test_admin_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    # First register an employee and mark attendance
    test_image = get_test_image_base64()
    client.post(
        "/api/v1/register-employee",
        headers=headers,
        json={
            "image": test_image,
            "firstName": "Export",
            "lastName": "Test",
            "department": "IT",
            "position": "Developer",
            "email": "export.test@example.com"
        }
    )
    
    # Mark attendance
    client.post(
        "/api/v1/recognize-face",
        json={"image": test_image}
    )
    
    # Now try to export
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(
        f"/api/v1/admin/attendance/export?start_date={today}&end_date={today}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "filename" in data
