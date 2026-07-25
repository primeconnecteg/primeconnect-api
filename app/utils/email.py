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
                
            # 3. Authenticate (strip spaces from App Password if any)
            smtp_pass = settings.SMTP_PASSWORD.replace(" ", "")
            server.login(settings.SMTP_USERNAME, smtp_pass)
            
            # 4. Send
            server.send_message(msg)
            
            # 5. Disconnect cleanly
            server.quit()
            
            logger.info("Email successfully sent for contact request %s", contact.id)
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failure: Invalid credentials.")
        except smtplib.SMTPConnectError:
            logger.error("SMTP connection failure: Could not connect to the server.")
        except smtplib.SMTPRecipientsRefused:
            logger.error("SMTP failure: CEO email address was refused by the server.")
        except smtplib.SMTPServerDisconnected:
            logger.error("SMTP failure: Server disconnected unexpectedly.")
        except TimeoutError:
            logger.error("SMTP failure: Connection timed out.")
        except Exception as e:
            # Catch any other unexpected network or SSL errors
            logger.error(f"Unexpected exception during email delivery: {e}")
