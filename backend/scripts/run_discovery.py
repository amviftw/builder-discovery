"""
Run the full discovery pipeline: discover → enrich → score → classify.

Usage:
    python scripts/run_discovery.py discover    # Find builders via GitHub search
    python scripts/run_discovery.py enrich      # Enrich discovered profiles
    python scripts/run_discovery.py score       # Score enriched profiles
    python scripts/run_discovery.py classify    # Classify scored profiles with LLM
    python scripts/run_discovery.py full        # Run all stages
    python scripts/run_discovery.py stats       # Show pipeline stats
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("discovery")


async def main():
    from sqlalchemy import func, select
    from app.db.engine import engine, async_session
    from app.db.base import Base
    from app.models.person import Person
    import app.models  # noqa: F401

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    command = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if command == "stats":
        async with async_session() as db:
            result = await db.execute(
                select(Person.pipeline_stage, func.count()).group_by(Person.pipeline_stage)
            )
            counts = dict(result.all())
            total = sum(counts.values())
            print(f"\n{'='*50}")
            print(f" Builder Discovery Pipeline - Stats")
            print(f"{'='*50}")
            for stage in ["discovered", "enriched", "scored", "classified", "verified", "outreach", "engaged"]:
                count = counts.get(stage, 0)
                bar = "#" * min(count, 50)
                print(f"  {stage:15s} | {count:5d} {bar}")
            print(f"{'-'*50}")
            print(f"  {'Total':15s} | {total:5d}")
            print()

            # Top scored
            top = await db.execute(
                select(Person)
                .where(Person.founder_propensity_score.isnot(None))
                .order_by(Person.founder_propensity_score.desc())
                .limit(10)
            )
            top_people = top.scalars().all()
            if top_people:
                print(f" Top Scored Builders:")
                print(f"{'-'*70}")
                for p in top_people:
                    tags = ""
                    if p.builder_type:
                        tags += f"[{p.builder_type}]"
                    if p.founder_fit:
                        tags += f"[{p.founder_fit}]"
                    print(f"  {p.founder_propensity_score:.3f}  {p.display_name or 'Unknown':30s} {tags}")
                print()
        return

    from app.collectors.github.client import GitHubClient

    client = GitHubClient()

    if command in ("discover", "full"):
        logger.info("Starting discovery phase...")
        async with async_session() as db:
            from app.services.discovery_service import run_user_search_discovery, run_repo_search_discovery

            # User search
            run1 = await run_user_search_discovery(db, client, max_pages=2)
            await db.commit()
            logger.info(f"User search: found={run1.items_found}, new={run1.items_new}, skipped={run1.items_skipped}")

            # Repo-based discovery
            run2 = await run_repo_search_discovery(db, client)
            await db.commit()
            logger.info(f"Repo search: found={run2.items_found}, new={run2.items_new}, skipped={run2.items_skipped}")

    if command in ("enrich", "full"):
        logger.info("Starting enrichment phase...")
        async with async_session() as db:
            from app.services.discovery_service import batch_enrich
            enriched = await batch_enrich(db, client, limit=100)
            logger.info(f"Enriched {enriched} profiles")

    if command in ("score", "full"):
        logger.info("Starting scoring phase...")
        async with async_session() as db:
            from app.services.scoring_service import batch_score
            scored = await batch_score(db, limit=100)
            logger.info(f"Scored {scored} profiles")

    if command in ("classify", "full"):
        logger.info("Starting classification phase...")
        async with async_session() as db:
            from app.services.scoring_service import batch_classify
            classified = await batch_classify(db, limit=100)
            logger.info(f"Classified {classified} profiles")

    await client.close()

    # Show final stats
    async with async_session() as db:
        result = await db.execute(
            select(Person.pipeline_stage, func.count()).group_by(Person.pipeline_stage)
        )
        counts = dict(result.all())
        logger.info(f"Pipeline: {dict(counts)}")


if __name__ == "__main__":
    asyncio.run(main())
