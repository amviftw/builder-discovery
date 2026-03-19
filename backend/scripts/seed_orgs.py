"""Seed the organizations table with Indian tech companies."""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.db.engine import engine, async_session
from app.db.base import Base
from app.models.organization import Organization


async def seed():
    # Create tables
    async with engine.begin() as conn:
        import app.models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)

    seed_file = Path(__file__).parent.parent.parent / "database" / "seeds" / "indian_tech_companies.json"
    with open(seed_file) as f:
        companies = json.load(f)

    async with async_session() as session:
        added = 0
        skipped = 0
        for company in companies:
            # Check if already exists
            result = await session.execute(
                select(Organization).where(Organization.github_org_login == company["github_org_login"])
            )
            if result.scalar_one_or_none():
                skipped += 1
                continue

            org = Organization(
                github_org_login=company["github_org_login"],
                name=company["name"],
                company_type=company.get("company_type"),
                location=company.get("location"),
                is_tracked=True,
            )
            session.add(org)
            added += 1

        await session.commit()
        print(f"Seeded {added} organizations ({skipped} already existed)")


if __name__ == "__main__":
    asyncio.run(seed())
