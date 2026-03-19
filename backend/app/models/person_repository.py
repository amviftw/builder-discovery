from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PersonRepository(Base):
    __tablename__ = "person_repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id: Mapped[str] = mapped_column(String(36), ForeignKey("people.id", ondelete="CASCADE"))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"))

    role: Mapped[str | None] = mapped_column(String(50))  # owner, contributor, maintainer
    commit_count: Mapped[int | None] = mapped_column(Integer)
    first_commit_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    person: Mapped[Person] = relationship(back_populates="person_repositories")
    repository: Mapped[Repository] = relationship(back_populates="person_repositories")

    __table_args__ = (UniqueConstraint("person_id", "repository_id"),)


from app.models.person import Person  # noqa: E402
from app.models.repository import Repository  # noqa: E402
