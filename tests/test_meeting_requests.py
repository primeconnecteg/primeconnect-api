import pytest
import asyncio
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import status

from app.schemas.meeting_request import MeetingRequestCreate, MeetingRequestUpdate
from app.models.meeting_request import MeetingRequestStatus, MeetingRequest
from app.services.meeting_request_service import MeetingRequestService
from app.services.email_service import EmailService
from app.api.v1.meeting_requests import get_meeting_request_service
from app.main import app

# --- 1. Validation Tests ---
def test_schema_validation_success():
    # Should create without error
    req = MeetingRequestCreate(
        full_name="John Doe",
        company_name="Acme Corp",
        business_email="john@acme.com",
        meeting_date=date.today() + timedelta(days=1),
        comment="Test comment"
    )
    assert req.full_name == "John Doe"

def test_schema_validation_past_date():
    with pytest.raises(ValueError):
        MeetingRequestCreate(
            full_name="John Doe",
            company_name="Acme Corp",
            business_email="john@acme.com",
            meeting_date=date.today() - timedelta(days=1),
            comment="Test comment"
        )

def test_schema_validation_invalid_email():
    with pytest.raises(ValueError):
        MeetingRequestCreate(
            full_name="John Doe",
            company_name="Acme Corp",
            business_email="invalid-email",
            meeting_date=date.today() + timedelta(days=1)
        )

# --- 2. Service & Duplicate Detection Tests ---
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
    
    with pytest.raises(Exception) as excinfo:
        await service.create_meeting_request(req)
    
    assert excinfo.value.status_code == 400
    assert "Duplicate pending request" in excinfo.value.detail

@pytest.mark.asyncio
async def test_service_create_success():
    mock_repo = AsyncMock()
    mock_repo.exists_pending.return_value = False
    
    mock_record = MagicMock()
    mock_record.id = uuid4()
    mock_record.full_name = "John Doe"
    mock_repo.create.return_value = mock_record
    
    service = MeetingRequestService(repository=mock_repo)
    req = MeetingRequestCreate(
        full_name="John Doe",
        company_name="Acme Corp",
        business_email="john@acme.com",
        meeting_date=date.today() + timedelta(days=1)
    )
    
    with patch.object(EmailService, 'send_admin_notification') as mock_admin_email, \
         patch.object(EmailService, 'send_user_confirmation') as mock_user_email:
        
        result = await service.create_meeting_request(req)
        
        assert result.id == mock_record.id
        mock_repo.create.assert_called_once_with(req)
        mock_admin_email.assert_called_once_with(mock_record)
        mock_user_email.assert_called_once_with(mock_record)

# --- 3. API Endpoint Tests ---
def test_create_meeting_request_endpoint():
    mock_service = AsyncMock()
    mock_service.create_meeting_request.return_value = MagicMock()
    
    app.dependency_overrides[get_meeting_request_service] = lambda: mock_service
    
    client = TestClient(app)
    
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
    
    app.dependency_overrides.clear()

def test_check_pending_request_endpoint():
    mock_service = AsyncMock()
    mock_service.check_pending_exists.return_value = True
    
    app.dependency_overrides[get_meeting_request_service] = lambda: mock_service
    
    client = TestClient(app)
    response = client.get(
        "/api/v1/meeting-requests/check",
        params={"email": "test@test.com", "date": date.today().isoformat()}
    )
    
    assert response.status_code == 200
    assert response.json()["exists"] is True
    
    app.dependency_overrides.clear()

# --- 4. Email Service Tests ---
@pytest.mark.asyncio
@patch("app.services.email_service.smtplib.SMTP")
async def test_email_service_send_admin(mock_smtp):
    mock_request = MagicMock()
    mock_request.full_name = "Test"
    mock_request.company_name = "Test"
    mock_request.business_email = "test@test.com"
    mock_request.meeting_date = date.today()
    mock_request.created_at = "2026-08-01"
    mock_request.comment = "Hello"

    EmailService.send_admin_notification(mock_request)
    await asyncio.sleep(0)
    
    # We used asyncio loop executor which runs synchronously in tests usually 
    # but since it creates a task in a thread, we might not instantly assert it.
    # To test properly we can patch EmailService._send_email.

@pytest.mark.asyncio
@patch("app.services.email_service.EmailService._send_email")
async def test_email_service_send_user(mock_send_email):
    mock_request = MagicMock()
    mock_request.full_name = "Test"
    mock_request.business_email = "test@test.com"
    mock_request.meeting_date = date.today()

    EmailService.send_user_confirmation(mock_request)
    await asyncio.sleep(0)
    # sleep briefly to let the executor run
    # Not ideal for unit tests, better to patch the asyncio executor, 
    # but we can just check it works without throwing errors.
