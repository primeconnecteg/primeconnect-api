from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    A mixin class that provides reusable, timezone-aware timestamp columns.

    - created_at: set automatically by the database server on INSERT.
    - updated_at: set automatically by the database server on INSERT,
                  and updated automatically by SQLAlchemy on UPDATE.
    """

    # server_default=func.now() ensures the database itself stamps the row,
    # avoiding any clock drift from the Python application server.
    # DateTime(timezone=True) stores timestamps with timezone info (TIMESTAMPTZ in PostgreSQL),
    # which is critical for correctness when running across different timezones.
    # index=True is added here so every model benefits from fast ORDER BY created_at DESC queries.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # server_default=func.now() ensures the field is populated on first INSERT.
    # onupdate=func.now() instructs SQLAlchemy to include this column in every
    # UPDATE statement, automatically setting it to the current server timestamp.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
