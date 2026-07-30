import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
from uuid import uuid4

from fastapi import BackgroundTasks

from app.core.config import settings
from app.models.contact_request import ContactRequest, ContactStatus
from app.models.meeting_request import MeetingRequest, MeetingRequestStatus
from app.services.email_service import EmailService


class TestEmailService(unittest.TestCase):
    """
    Test suite for the unified EmailService.
    Validates SMTP formatting, delivery dispatching, background task execution, and failure logging.
    """

    def test_smtp_configuration_loaded(self):
        """Verify SMTP configuration settings are loaded from environment/config."""
        self.assertIsNotNone(settings.SMTP_HOST)
        self.assertIsNotNone(settings.SMTP_PORT)
        self.assertIsNotNone(settings.SMTP_FROM_EMAIL)
        self.assertIsNotNone(settings.CEO_EMAIL)

    @patch("smtplib.SMTP")
    def test_send_contact_notification_success(self, mock_smtp_class):
        """Verify successful dispatch of contact form company notification."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        contact = ContactRequest(
            id=uuid4(),
            name="John Doe",
            company="Acme Corp",
            email="john@example.com",
            message="Interested in BPO services.",
            status=ContactStatus.NEW,
            created_at=datetime.utcnow()
        )

        result = EmailService.send_contact_notification(contact)
        self.assertTrue(result)
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_admin_meeting_notification_success(self, mock_smtp_class):
        """Verify successful dispatch of discovery call admin notification."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        meeting = MeetingRequest(
            id=uuid4(),
            full_name="Jane Smith",
            company_name="Tech Solutions",
            business_email="jane@techsolutions.com",
            meeting_date=date.today(),
            comment="Looking for Customer Support outsourcing.",
            status=MeetingRequestStatus.PENDING,
            created_at=datetime.utcnow()
        )

        result = EmailService.send_admin_meeting_notification(meeting)
        self.assertTrue(result)
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_user_meeting_confirmation_success(self, mock_smtp_class):
        """Verify successful dispatch of discovery call user confirmation email."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        meeting = MeetingRequest(
            id=uuid4(),
            full_name="Jane Smith",
            company_name="Tech Solutions",
            business_email="jane@techsolutions.com",
            meeting_date=date.today(),
            comment="Looking for Customer Support outsourcing.",
            status=MeetingRequestStatus.PENDING,
            created_at=datetime.utcnow()
        )

        result = EmailService.send_user_meeting_confirmation(meeting)
        self.assertTrue(result)
        mock_server.send_message.assert_called_once()
        
        # Verify recipient
        call_args = mock_server.send_message.call_args[0][0]
        self.assertEqual(call_args["To"], "jane@techsolutions.com")

    @patch("smtplib.SMTP")
    def test_background_task_execution(self, mock_smtp_class):
        """Verify that FastAPI BackgroundTasks executes email dispatch tasks properly."""
        mock_server = MagicMock()
        mock_smtp_class.return_value = mock_server

        contact = ContactRequest(
            id=uuid4(),
            name="Alice Walker",
            company="Global Logistics",
            email="alice@logistics.com",
            message="Support inquiry.",
            status=ContactStatus.NEW,
            created_at=datetime.utcnow()
        )

        tasks = BackgroundTasks()
        tasks.add_task(EmailService.send_contact_notification, contact)
        
        # Execute queued background tasks
        import asyncio
        asyncio.run(tasks())

        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_smtp_failure_handling_and_logging(self, mock_smtp_class):
        """Verify that SMTP connection or authentication failures return False and do not crash the caller."""
        import smtplib
        mock_smtp_class.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")

        contact = ContactRequest(
            id=uuid4(),
            name="Error Test",
            company="Fail Co",
            email="fail@example.com",
            message="Testing failure.",
            status=ContactStatus.NEW,
            created_at=datetime.utcnow()
        )

        result = EmailService.send_contact_notification(contact)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
