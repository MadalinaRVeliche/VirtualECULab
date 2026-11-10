from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    lesson_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
