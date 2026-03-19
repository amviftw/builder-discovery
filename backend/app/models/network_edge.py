from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NetworkEdge(Base):
    __tablename__ = "network_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_a_id: Mapped[str] = mapped_column(String(36), ForeignKey("people.id", ondelete="CASCADE"))
    person_b_id: Mapped[str] = mapped_column(String(36), ForeignKey("people.id", ondelete="CASCADE"))

    edge_type: Mapped[str] = mapped_column(String(100))
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    evidence: Mapped[str | None] = mapped_column(Text)  # JSON

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("person_a_id", "person_b_id", "edge_type"),
        CheckConstraint("person_a_id < person_b_id"),
    )
