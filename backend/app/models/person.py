from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Person(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Identity
    display_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    website_url: Mapped[str | None] = mapped_column(String(512))

    # Classification
    builder_experience: Mapped[str | None] = mapped_column(String(50))
    builder_type: Mapped[str | None] = mapped_column(String(50))
    founder_fit: Mapped[str | None] = mapped_column(String(50))

    # Pipeline
    pipeline_stage: Mapped[str] = mapped_column(String(50), default="discovered")

    # Composite scores (denormalized)
    founder_propensity_score: Mapped[float | None] = mapped_column(Float)
    technical_score: Mapped[float | None] = mapped_column(Float)
    momentum_score: Mapped[float | None] = mapped_column(Float)
    ai_nativeness_score: Mapped[float | None] = mapped_column(Float)
    leadership_score: Mapped[float | None] = mapped_column(Float)
    departure_signal_score: Mapped[float | None] = mapped_column(Float)

    # Metadata
    tags: Mapped[str | None] = mapped_column(Text)  # JSON array as text
    analyst_notes: Mapped[str | None] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    one_line_summary: Mapped[str | None] = mapped_column(Text)

    last_enriched_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_scored_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    github_profile: Mapped[GitHubProfile | None] = relationship(back_populates="person", uselist=False)
    twitter_profile: Mapped[TwitterProfile | None] = relationship(back_populates="person", uselist=False)
    signals: Mapped[list[Signal]] = relationship(back_populates="person")
    notes: Mapped[list[Note]] = relationship(back_populates="person")
    contribution_snapshots: Mapped[list[ContributionSnapshot]] = relationship(back_populates="person")
    person_repositories: Mapped[list[PersonRepository]] = relationship(back_populates="person")

    __table_args__ = (
        Index("idx_people_pipeline_stage", "pipeline_stage"),
        Index("idx_people_propensity_score", founder_propensity_score.desc()),
        Index("idx_people_country", "country"),
    )


# Resolve forward refs
from app.models.github_profile import GitHubProfile  # noqa: E402
from app.models.twitter_profile import TwitterProfile  # noqa: E402
from app.models.signal import Signal  # noqa: E402
from app.models.note import Note  # noqa: E402
from app.models.contribution_snapshot import ContributionSnapshot  # noqa: E402
from app.models.person_repository import PersonRepository  # noqa: E402
