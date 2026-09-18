from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import Base, TimestampMixin
from app.shared.enums import SubmissionStatus


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"
    __table_args__ = (
        # один студент = одна сдача на задание
        UniqueConstraint("task_id", "student_id", name="uq_submission_task_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus, name="submission_status", native_enum=False, length=20),
        nullable=False,
        default=SubmissionStatus.SUBMITTED,
    )
    student_comment: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ⬇️⬇️⬇️ НОВЫЕ ПОЛЯ — оценка и комментарий препода ⬇️⬇️⬇️
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teacher_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ⬆️⬆️⬆️ КОНЕЦ НОВЫХ ПОЛЕЙ ⬆️⬆️⬆️

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Comment.created_at",
    )


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)

    submission: Mapped["Submission"] = relationship(back_populates="comments")