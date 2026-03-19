from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.person import Person
from app.models.signal import Signal

router = APIRouter()


@router.get("/overview")
async def dashboard_overview(db: AsyncSession = Depends(get_db)):
    # Total people
    total = (await db.execute(select(func.count()).select_from(Person).where(Person.is_archived == False))).scalar() or 0  # noqa: E712

    # Pipeline counts
    pipeline_result = await db.execute(
        select(Person.pipeline_stage, func.count())
        .where(Person.is_archived == False)  # noqa: E712
        .group_by(Person.pipeline_stage)
    )
    pipeline_stats = {row[0]: row[1] for row in pipeline_result.all()}

    # Top scored people
    top_result = await db.execute(
        select(Person)
        .where(Person.is_archived == False, Person.founder_propensity_score.isnot(None))  # noqa: E712
        .order_by(Person.founder_propensity_score.desc())
        .limit(10)
    )
    top_people = [
        {
            "id": p.id,
            "display_name": p.display_name,
            "founder_propensity_score": p.founder_propensity_score,
            "builder_type": p.builder_type,
            "pipeline_stage": p.pipeline_stage,
            "avatar_url": p.avatar_url,
        }
        for p in top_result.scalars().all()
    ]

    # Recent signals
    recent_signals_result = await db.execute(
        select(Signal).where(Signal.is_active == True).order_by(Signal.detected_at.desc()).limit(5)  # noqa: E712
    )
    recent_signals = [
        {
            "id": s.id,
            "signal_type": s.signal_type,
            "signal_strength": s.signal_strength,
            "person_id": s.person_id,
            "detected_at": s.detected_at.isoformat() if s.detected_at else None,
        }
        for s in recent_signals_result.scalars().all()
    ]

    # New this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_this_week = (
        await db.execute(select(func.count()).select_from(Person).where(Person.created_at >= week_ago))
    ).scalar() or 0

    return {
        "total_people": total,
        "new_this_week": new_this_week,
        "pipeline_stats": pipeline_stats,
        "top_scored_people": top_people,
        "recent_signals": recent_signals,
    }
