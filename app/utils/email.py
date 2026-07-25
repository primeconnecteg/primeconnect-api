import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.models.contact_request import ContactRequest

logger = logging.getLogger(__name__)

class EmailService:
    """
    Handles all external email delivery logic.
    This class is isolated from business logic and FastAPI.
    It acts strictly as an infrastructure utility.
    """
    
    @staticmethod
    def send_contact_notification(contact: ContactRequest) -> None:
        """
        Connects to the SMTP server and sends a formatted notification email.
        
        Args:
            contact: The fully saved SQLAlchemy ContactRequest model.
        """
        subject = f"New Contact Request: {contact.name}"
        
        company_line = f"Company: {contact.company}\n" if contact.company else ""
        
        body = f"""Hello,

You have received a new contact request on PrimeConnect.

Name: {contact.name}
{company_line}Email: {contact.email}
Submission Time: {contact.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{contact.message}

---
PrimeConnect Automated System
"""
        
        msg = MIMEMultipart()
        # Format: "PrimeConnect System <no-reply@primeconnect.com>"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = settings.CEO_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        try:
            # 1. Connect
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            
            # 2. Upgrade to TLS
            if settings.SMTP_USE_TLS:
                server.starttls()
                
            # 3. Authenticate
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            # 4. Send
            server.send_message(msg)
            
            # 5. Disconnect cleanly
            server.quit()
            
            logger.info("Email successfully sent for contact request %s", contact.id)
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP authentication failure: Invalid credentials.")
            raise RuntimeError(f"SMTP Auth Error: {e}")
        except smtplib.SMTPConnectError as e:
            logger.error("SMTP connection failure: Could not connect to the server.")
            raise RuntimeError(f"SMTP Connect Error: {e}")
        except smtplib.SMTPRecipientsRefused as e:
            logger.error("SMTP failure: CEO email address was refused by the server.")
            raise RuntimeError(f"SMTP Refused Error: {e}")
        except smtplib.SMTPServerDisconnected as e:
            logger.error("SMTP failure: Server disconnected unexpectedly.")
            raise RuntimeError(f"SMTP Disconnect Error: {e}")
        except TimeoutError as e:
            logger.error("SMTP failure: Connection timed out.")
            raise RuntimeError(f"SMTP Timeout Error: {e}")
        except Exception as e:
            # Catch any other unexpected network or SSL errors
            logger.error(f"Unexpected exception during email delivery: {e}")
            raise RuntimeError(f"Unexpected SMTP Error: {e}")
