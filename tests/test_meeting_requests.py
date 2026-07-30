import pytest
import asyncio
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import status, HTTPException

from app.schemas.meeting_request import MeetingRequestCreate
from app.services.meeting_request_service import MeetingRequestService
from app.services.email_service import EmailService
from app.api.v1.meeting_requests import get_meeting_request_service
from app.main import app

client = TestClient(app)

# --- 1. Validation Tests ---
def test_schema_validation_success():
    req = MeetingRequestCreate(
        full_name="John Doe",
        company_name="Acme Corp",
        business_email="john@acme.com",
        meeting_date=date.today() + timedelta(days=1),
        comment="Test comment"
    )
    assert req.full_name == "John Doe"
    assert req.company_name == "Acme Corp"
    assert req.business_email == "john@acme.com"

def test_schema_validation_past_date():
    with pytest.raises(ValueError) as excinfo:
        MeetingRequestCreate(
            full_name="John Doe",
            company_name="Acme Corp",
            business_email="john@acme.com",
            meeting_date=date.today() - timedelta(days=5),
            comment="Test comment"
        )
    assert "in the past" in str(excinfo.value)

def test_schema_validation_invalid_email():
    with pytest.raises(ValueError) as excinfo:
        MeetingRequestCreate(
            full_name="John Doe",
            company_name="Acme Corp",
            business_email="invalid-email",
            meeting_date=date.today() + timedelta(days=1)
        )
    assert "valid business email" in str(excinfo.value)

# --- 2. Duplicate Detection Tests ---
@pytest.mark.asyncio
async def test_service_create_duplicate():
    mock_repo = AsyncMock()
    mock_repo.exists_pending.return_value = True
    
    service = MeetingRequestService(repository=mock_repo)
    req = MeetingRequestCreate(
        full_name="John Doe",
        company_name="Acme Corp",
        business_email="john@acme.com",
        meeting_date=date.today() + timedelta(days=1)
    )
    
    with pytest.raises(HTTPException) as excinfo:
        await service.create_meeting_request(req)
    
    assert excinfo.value.status_code == 409
    assert "A pending discovery call request already exists" in excinfo.value.detail

# --- 3. Database Failure Tests ---
@pytest.mark.asyncio
async def test_service_database_failure():
    mock_repo = AsyncMock()
    mock_repo.exists_pending.return_value = False
    mock_repo.create.side_effect = Exception("Database connection error")
    
    service = MeetingRequestService(repository=mock_repo)
    req = MeetingRequestCreate(
        full_name="John Doe",
        company_name="Acme Corp",
        business_email="john@acme.com",
        meeting_date=date.today() + timedelta(days=1)
    )
    
    with pytest.raises(HTTPException) as excinfo:
        await service.create_meeting_request(req)
    
    assert excinfo.value.status_code == 500
    assert "Database insertion failed" in excinfo.value.detail

# --- 4. API Endpoint Integration Tests ---
def test_create_meeting_request_endpoint_success():
    mock_service = AsyncMock()
    mock_record = MagicMock()
    mock_record.id = uuid4()
    mock_record.status = "Pending"
    mock_service.create_meeting_request.return_value = mock_record
    
    app.dependency_overrides[get_meeting_request_service] = lambda: mock_service
    
    response = client.post(
        "/api/v1/meeting-requests",
        json={
            "full_name": "Test User",
            "company_name": "Test Company",
            "business_email": "test@test.com",
            "meeting_date": (date.today() + timedelta(days=2)).isoformat(),
            "comment": "Test"
        }
    )
    
    assert response.status_code == 201
    assert response.json()["message"] == "Discovery call request submitted successfully."
    assert "id" in response.json()
    
    app.dependency_overrides.clear()

def test_create_meeting_request_endpoint_invalid_email():
    response = client.post(
        "/api/v1/meeting-requests",
        json={
            "full_name": "Test User",
            "company_name": "Test Company",
            "business_email": "invalidemail",
            "meeting_date": (date.today() + timedelta(days=2)).isoformat()
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "validation_error"
    assert "valid business email" in data["message"]

def test_create_meeting_request_endpoint_missing_fields():
    response = client.post(
        "/api/v1/meeting-requests",
        json={
            "business_email": "test@test.com"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "validation_error"

# --- 5. Email Service Failure Handling ---
@patch("smtplib.SMTP")
def test_email_service_failure_handling(mock_smtp):
    import smtplib
    mock_smtp.side_effect = smtplib.SMTPConnectError(421, "Connection refused")
    
    mock_request = MagicMock()
    mock_request.full_name = "Test"
    mock_request.company_name = "Test"
    mock_request.business_email = "test@test.com"
    mock_request.meeting_date = date.today()
    mock_request.created_at = None
    mock_request.comment = "Hello"

    result = EmailService.send_admin_meeting_notification(mock_request)
    assert result is False
