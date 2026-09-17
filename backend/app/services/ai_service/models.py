from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base, TimestampMixin
from app.shared.enums import AiCheckStatus


class AiCheck(Base, TimestampMixin):
    __tablename__ = "ai_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[AiCheckStatus] = mapped_column(
        SAEnum(AiCheckStatus, name="ai_check_status", native_enum=False, length=20),
        nullable=False,
        default=AiCheckStatus.PENDING,
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False, default="mock")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0..100
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)