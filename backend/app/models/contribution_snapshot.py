from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ContributionSnapshot(Base):
    __tablename__ = "contribution_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("people.id", ondelete="CASCADE"))

    week_start: Mapped[date] = mapped_column(Date)
    total_contributions: Mapped[int | None] = mapped_column(Integer)
    commits: Mapped[int | None] = mapped_column(Integer)
    pull_requests_opened: Mapped[int | None] = mapped_column(Integer)
    pull_requests_merged: Mapped[int | None] = mapped_column(Integer)
    issues_opened: Mapped[int | None] = mapped_column(Integer)
    code_reviews: Mapped[int | None] = mapped_column(Integer)
    repos_contributed_to: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(50), default="github_graphql")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    person: Mapped[Person] = relationship(back_populates="contribution_snapshots")

    __table_args__ = (
        UniqueConstraint("person_id", "week_start"),
        Index("idx_contrib_person_week", "person_id", week_start.desc()),
    )


from app.models.person import Person  # noqa: E402
