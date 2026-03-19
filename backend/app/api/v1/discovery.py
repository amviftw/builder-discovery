import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.discovery_run import DiscoveryRun

router = APIRouter()


@router.post("/run")
async def trigger_discovery_run(body: dict, db: AsyncSession = Depends(get_db)):
    run_type = body.get("run_type", "user_search")
    strategy = body.get("strategy", "")
    parameters = body.get("parameters", {})

    run = DiscoveryRun(
        run_type=run_type,
        strategy=strategy,
        parameters=json.dumps(parameters),
        status="queued",
    )
    db.add(run)
    await db.flush()

    # Actual discovery is triggered by the service layer
    # For now, return the run ID for tracking
    return {"run_id": run.id, "status": "queued"}


@router.get("/runs")
async def list_discovery_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiscoveryRun).order_by(DiscoveryRun.started_at.desc()).limit(50))
    runs = result.scalars().all()
    return {
        "items": [
            {
                "id": r.id,
                "run_type": r.run_type,
                "strategy": r.strategy,
                "status": r.status,
                "items_found": r.items_found,
                "items_new": r.items_new,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]
    }


@router.get("/runs/{run_id}")
async def get_discovery_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiscoveryRun).where(DiscoveryRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Run not found")
    errors = []
    if run.errors:
        try:
            errors = json.loads(run.errors)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": run.id,
        "run_type": run.run_type,
        "strategy": run.strategy,
        "status": run.status,
        "items_found": run.items_found,
        "items_new": run.items_new,
        "items_updated": run.items_updated,
        "items_skipped": run.items_skipped,
        "api_calls_made": run.api_calls_made,
        "errors": errors,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
