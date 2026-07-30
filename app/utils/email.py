"""
Legacy email module alias.
All email logic has been consolidated into app.services.email_service.EmailService.
"""
from app.services.email_service import EmailService

__all__ = ["EmailService"]
