import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.person import Person
from app.models.signal import Signal

router = APIRouter()


@router.get("")
async def list_signals(
    signal_type: Optional[str] = None,
    min_strength: Optional[float] = None,
    is_active: Optional[bool] = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Signal).join(Person, Signal.person_id == Person.id)

    if signal_type:
        query = query.where(Signal.signal_type == signal_type)
    if min_strength is not None:
        query = query.where(Signal.signal_strength >= min_strength)
    if is_active is not None:
        query = query.where(Signal.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Signal.detected_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    signals = result.scalars().all()

    items = []
    for s in signals:
        person_result = await db.execute(select(Person).where(Person.id == s.person_id))
        person = person_result.scalar_one_or_none()
        evidence = {}
        if s.evidence:
            try:
                evidence = json.loads(s.evidence)
            except (json.JSONDecodeError, TypeError):
                pass
        items.append({
            "id": s.id,
            "signal_type": s.signal_type,
            "signal_strength": s.signal_strength,
            "description": s.description,
            "evidence": evidence,
            "detected_at": s.detected_at.isoformat() if s.detected_at else None,
            "is_active": s.is_active,
            "person": {
                "id": person.id,
                "display_name": person.display_name,
                "avatar_url": person.avatar_url,
            }
            if person
            else None,
        })

    return {"items": items, "total": total, "page": page, "pages": (total + page_size - 1) // page_size if total else 0}


@router.get("/summary")
async def signal_summary(db: AsyncSession = Depends(get_db)):
    # Count by type
    type_counts = await db.execute(
        select(Signal.signal_type, func.count()).where(Signal.is_active == True).group_by(Signal.signal_type)  # noqa: E712
    )
    by_type = {row[0]: row[1] for row in type_counts.all()}

    return {"by_type": by_type}
