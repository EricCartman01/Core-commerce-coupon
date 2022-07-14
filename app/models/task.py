from sqlalchemy import JSON, Column, DateTime, Enum, String, func

from app.db.base import Base, CreateCustomID, CustomID
from app.enums import TaskStatus

STRING_SIZE = 200
STRING_SIZE_LESS = 60


class Task(Base):
    """Model of task."""

    __tablename__ = "task"

    id = Column(
        CustomID(),
        primary_key=True,
        default=CreateCustomID(),
        server_default=CreateCustomID(),
    )
    status = Column(
        Enum(*TaskStatus.choices(), name="taskstatus"),
        nullable=False,
        default=TaskStatus.CREATED.value,
    )
    result = Column(String(length=STRING_SIZE))
    data = Column(JSON)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
