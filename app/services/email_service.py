import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.models.contact_request import ContactRequest
from app.models.meeting_request import MeetingRequest

logger = logging.getLogger(__name__)


class EmailService:
    """
    Unified Infrastructure Email Service.
    Handles email formatting, SMTP connection lifecycle, TLS upgrading,
    authentication, and exception logging for all application notifications.
    """

    @classmethod
    def _send_raw_email(cls, to_email: str, subject: str, body_text: str, from_name: str = None) -> bool:
        """
        Core synchronous SMTP email dispatch method.
        Designed for execution within FastAPI BackgroundTasks.
        Does not raise uncaught exceptions; logs full tracebacks and context on failure.
        """
        sender_name = from_name or settings.SMTP_FROM_NAME
        sender_email = settings.SMTP_FROM_EMAIL
        
        msg = MIMEMultipart()
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        masked_user = f"{settings.SMTP_USERNAME[:3]}***" if settings.SMTP_USERNAME else "None"

        logger.info(
            f"Dispatching email | Server: {settings.SMTP_HOST}:{settings.SMTP_PORT} | "
            f"TLS: {settings.SMTP_USE_TLS} | User: {masked_user} | To: {to_email} | Subject: '{subject}'"
        )

        try:
            # 1. Establish socket connection
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            
            # 2. Upgrade to TLS if requested
            if settings.SMTP_USE_TLS:
                server.starttls()
                
            # 3. Authenticate if credentials supplied
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp_pass = settings.SMTP_PASSWORD.replace(" ", "")
                server.login(settings.SMTP_USERNAME, smtp_pass)
                
            # 4. Transmit email message
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email successfully delivered to {to_email} (Subject: '{subject}')")
            return True

        except smtplib.SMTPAuthenticationError as exc:
            logger.error(
                f"SMTP Authentication Failed: Unable to authenticate user '{masked_user}' on {settings.SMTP_HOST}:{settings.SMTP_PORT}. "
                f"Verify SMTP_USERNAME and SMTP_PASSWORD settings."
            )
            logger.exception(exc)
        except smtplib.SMTPConnectError as exc:
            logger.error(f"SMTP Connection Failed: Unable to connect to host {settings.SMTP_HOST}:{settings.SMTP_PORT}.")
            logger.exception(exc)
        except smtplib.SMTPRecipientsRefused as exc:
            logger.error(f"SMTP Recipient Refused: Server rejected delivery to {to_email}.")
            logger.exception(exc)
        except smtplib.SMTPServerDisconnected as exc:
            logger.error(f"SMTP Server Disconnected unexpectedly during transmission to {to_email}.")
            logger.exception(exc)
        except TimeoutError as exc:
            logger.error(f"SMTP Timeout: Host {settings.SMTP_HOST}:{settings.SMTP_PORT} failed to respond within 15 seconds.")
            logger.exception(exc)
        except Exception as exc:
            logger.error(f"Unexpected error during email delivery to {to_email}: {exc}")
            logger.exception(exc)

        return False

    @classmethod
    def send_contact_notification(cls, contact: ContactRequest) -> bool:
        """Sends company notification email for a new public contact form submission."""
        subject = f"New Contact Request: {contact.name}"
        company_line = f"Company: {contact.company}\n" if contact.company else ""
        submission_time = contact.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if contact.created_at else "Just now"

        body = f"""Hello,

You have received a new contact request on PrimeConnect.

Name: {contact.name}
{company_line}Email: {contact.email}
Submission Time: {submission_time}

Message:
{contact.message}

---
PrimeConnect Automated System
"""
        return cls._send_raw_email(
            to_email=settings.CEO_EMAIL,
            subject=subject,
            body_text=body
        )

    @classmethod
    def send_admin_meeting_notification(cls, request: MeetingRequest) -> bool:
        """Sends company admin notification email for a new discovery call booking."""
        subject = f"New Discovery Call Request: {request.full_name}"
        body = f"""New Discovery Call Request

Name: {request.full_name}
Company: {request.company_name}
Email: {request.business_email}
Meeting Date: {request.meeting_date}
Created At: {request.created_at or 'Just now'}

Comment:
{request.comment or 'No comment provided.'}

---
PrimeConnect Automated System
"""
        return cls._send_raw_email(
            to_email=settings.CEO_EMAIL,
            subject=subject,
            body_text=body
        )

    @classmethod
    def send_user_meeting_confirmation(cls, request: MeetingRequest) -> bool:
        """Sends booking confirmation email to the user for a discovery call request."""
        subject = "We've Received Your Discovery Call Request"
        body = f"""Hello {request.full_name},

Thank you for contacting Prime Connect EG.

We have received your discovery call request.

Requested Date: {request.meeting_date}

Our team will review your request and contact you shortly.

Regards,
Prime Connect EG Team
"""
        return cls._send_raw_email(
            to_email=request.business_email,
            subject=subject,
            body_text=body
        )
