from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TwitterProfile(Base):
    __tablename__ = "twitter_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("people.id", ondelete="CASCADE"), unique=True)

    twitter_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    handle: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    followers_count: Mapped[int | None] = mapped_column(Integer)
    following_count: Mapped[int | None] = mapped_column(Integer)
    tweet_count: Mapped[int | None] = mapped_column(Integer)
    verified: Mapped[bool | None] = mapped_column(Boolean)
    linked_via: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[float | None] = mapped_column(Float)

    # Sentiment (future)
    avg_sentiment_score: Mapped[float | None] = mapped_column(Float)
    founder_intent_score: Mapped[float | None] = mapped_column(Float)
    post_frequency_7d: Mapped[float | None] = mapped_column(Float)
    post_frequency_30d: Mapped[float | None] = mapped_column(Float)

    fetched_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    person: Mapped[Person] = relationship(back_populates="twitter_profile")


from app.models.person import Person  # noqa: E402
