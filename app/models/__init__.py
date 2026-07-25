# This file makes the models directory a Python package.
# Importing all models here ensures that Alembic can discover them 
# when it imports Base from this package.
from app.core.database import Base
from app.models.admin import Admin
from app.models.contact_request import ContactRequest, ContactStatus
