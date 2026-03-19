from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    github_repo_id: Mapped[int] = mapped_column(Integer, unique=True)
    owner_login: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(512))

    # Metrics
    stars: Mapped[int | None] = mapped_column(Integer)
    forks: Mapped[int | None] = mapped_column(Integer)
    watchers: Mapped[int | None] = mapped_column(Integer)
    open_issues: Mapped[int | None] = mapped_column(Integer)
    size_kb: Mapped[int | None] = mapped_column(Integer)
    primary_language: Mapped[str | None] = mapped_column(String(100))
    languages: Mapped[str | None] = mapped_column(Text)  # JSON
    topics: Mapped[str | None] = mapped_column(Text)  # JSON array

    # Dates
    created_at_gh: Mapped[datetime | None] = mapped_column(DateTime)
    pushed_at_gh: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at_gh: Mapped[datetime | None] = mapped_column(DateTime)

    # Analysis
    is_fork: Mapped[bool | None] = mapped_column(Boolean)
    is_archived: Mapped[bool | None] = mapped_column(Boolean)
    contributor_count: Mapped[int | None] = mapped_column(Integer)
    has_readme: Mapped[bool | None] = mapped_column(Boolean)
    readme_length: Mapped[int | None] = mapped_column(Integer)
    has_license: Mapped[bool | None] = mapped_column(Boolean)
    has_ci: Mapped[bool | None] = mapped_column(Boolean)

    # Scoring
    quality_score: Mapped[float | None] = mapped_column(Float)
    ai_relevance_score: Mapped[float | None] = mapped_column(Float)
    is_internal_tool: Mapped[bool] = mapped_column(Boolean, default=False)
    internal_tool_confidence: Mapped[float | None] = mapped_column(Float)

    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    person_repositories: Mapped[list[PersonRepository]] = relationship(back_populates="repository")

    __table_args__ = (
        Index("idx_repos_full_name", "full_name"),
        Index("idx_repos_stars", stars.desc()),
    )


from app.models.person_repository import PersonRepository  # noqa: E402
