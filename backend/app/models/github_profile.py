from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GitHubProfile(Base):
    __tablename__ = "github_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("people.id", ondelete="CASCADE"), unique=True)

    github_id: Mapped[int] = mapped_column(Integer, unique=True)
    login: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    public_repos: Mapped[int | None] = mapped_column(Integer)
    public_gists: Mapped[int | None] = mapped_column(Integer)
    followers: Mapped[int | None] = mapped_column(Integer)
    following: Mapped[int | None] = mapped_column(Integer)
    hireable: Mapped[bool | None] = mapped_column(Boolean)
    twitter_username: Mapped[str | None] = mapped_column(String(255))
    profile_url: Mapped[str | None] = mapped_column(String(512))

    created_at_gh: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at_gh: Mapped[datetime | None] = mapped_column(DateTime)

    # Derived metrics
    total_stars_received: Mapped[int | None] = mapped_column(Integer)
    total_forks_received: Mapped[int | None] = mapped_column(Integer)
    primary_languages: Mapped[str | None] = mapped_column(Text)  # JSON array
    org_memberships: Mapped[str | None] = mapped_column(Text)  # JSON array

    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    person: Mapped[Person] = relationship(back_populates="github_profile")


from app.models.person import Person  # noqa: E402
