from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    # The lesson ID is the primary key, so a lesson can be marked complete
    # only once in this database. Existing lesson routes still use this table.
    lesson_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class LearningMilestone(Base):
    __tablename__ = "learning_milestones"

    # The composite key allows a module to have one row per milestone kind.
    # Marking theory as reviewed and completing a challenge are separate events.
    module_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(24), primary_key=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    module_id: Mapped[int] = mapped_column(Integer, index=True)

    # Snapshot the questions and answer key when the quiz is issued.
    # Grading uses this snapshot so later question-bank edits do not
    # change the answers or option order for an already-issued quiz.
    questions: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Uniqueness lets the grading endpoint recognize a retry with the
    # same submission ID and prevents it from saving the attempt twice.
    submission_id: Mapped[str] = mapped_column(String(36), unique=True)
    session_id: Mapped[str] = mapped_column(String(36))
    module_id: Mapped[int] = mapped_column(Integer, index=True)
    score: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)

    # Keep the submitted choices and the grading result. The API can
    # return the original feedback for a retry and use it for revision quizzes.
    answers: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )