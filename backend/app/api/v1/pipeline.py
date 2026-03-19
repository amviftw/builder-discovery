from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.person import Person

router = APIRouter()

STAGES = ["discovered", "enriched", "scored", "classified", "verified", "outreach", "engaged"]


@router.get("/stats")
async def pipeline_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Person.pipeline_stage, func.count())
        .where(Person.is_archived == False)  # noqa: E712
        .group_by(Person.pipeline_stage)
    )
    counts = {row[0]: row[1] for row in result.all()}
    stages = {stage: counts.get(stage, 0) for stage in STAGES}
    return {"stages": stages, "total": sum(stages.values())}


@router.post("/bulk-advance")
async def bulk_advance(body: dict, db: AsyncSession = Depends(get_db)):
    person_ids = body.get("person_ids", [])
    target_stage = body.get("target_stage", "")
    if target_stage not in STAGES:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=f"Invalid stage: {target_stage}")

    result = await db.execute(select(Person).where(Person.id.in_(person_ids)))
    people = result.scalars().all()
    for person in people:
        person.pipeline_stage = target_stage

    return {"updated": len(people)}
