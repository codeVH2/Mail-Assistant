from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base

class EmailClassification(Base):
    __tablename__ = "email_classifications"

    __table_args__ = (
        UniqueConstraint("message_id", "provider", "model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(index=True)
    category: Mapped[str]
    score: Mapped[float]
    provider: Mapped[str]
    model: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
