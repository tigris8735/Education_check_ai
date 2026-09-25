from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import Base, TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Оставлено для обратной совместимости; у мульти-групповых заданий = None
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # 0 = без ограничений

    groups: Mapped[list["TaskGroupAssignment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )


class TaskGroupAssignment(Base):
    """Many-to-many связь задания и групп."""
    __tablename__ = "task_groups"
    __table_args__ = (
        UniqueConstraint("task_id", "group_id", name="uq_task_group"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )

    task: Mapped["Task"] = relationship(back_populates="groups")