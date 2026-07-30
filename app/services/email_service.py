import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime

from app.core.config import settings
from app.models.meeting_request import MeetingRequest

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def _send_email(msg: EmailMessage) -> None:
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
                logger.info(f"Successfully sent email to {msg['To']}")
        except Exception as e:
            logger.error(f"Failed to send email to {msg['To']}: {e}")

    @staticmethod
    def send_admin_notification(request: MeetingRequest) -> None:
        msg = EmailMessage()
        msg["Subject"] = "New Discovery Call Request"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = settings.CEO_EMAIL
        
        body = f"""
New Discovery Call Request

Name: {request.full_name}
Company: {request.company_name}
Email: {request.business_email}
Meeting Date: {request.meeting_date}
Created At: {request.created_at}

Comment:
{request.comment or 'No comment provided.'}
"""
        msg.set_content(body)
        
        # Call it synchronously as it runs inside an async wrapper or thread if needed.
        # But to avoid blocking, we can use a small wrapper in the caller. 
        # For simplicity, we just send it. If we are in an async endpoint, 
        # it's better to run it in a threadpool executor.
        import threading
        threading.Thread(target=EmailService._send_email, args=(msg,), daemon=True).start()

    @staticmethod
    def send_user_confirmation(request: MeetingRequest) -> None:
        msg = EmailMessage()
        msg["Subject"] = "We've Received Your Discovery Call Request"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = request.business_email
        
        body = f"""
Hello {request.full_name},

Thank you for contacting Prime Connect EG.

We have received your discovery call request.

Requested Date: {request.meeting_date}

Our team will review your request and contact you shortly.

Regards,
Prime Connect EG
"""
        msg.set_content(body)
        
        import threading
        threading.Thread(target=EmailService._send_email, args=(msg,), daemon=True).start()
