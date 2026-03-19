import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.repository import Repository

router = APIRouter()


@router.get("")
async def list_repositories(
    search: Optional[str] = None,
    min_stars: Optional[int] = None,
    is_internal_tool: Optional[bool] = None,
    language: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Repository)
    if search:
        query = query.where(
            (Repository.full_name.ilike(f"%{search}%")) | (Repository.description.ilike(f"%{search}%"))
        )
    if min_stars is not None:
        query = query.where(Repository.stars >= min_stars)
    if is_internal_tool is not None:
        query = query.where(Repository.is_internal_tool == is_internal_tool)
    if language:
        query = query.where(Repository.primary_language == language)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Repository.stars.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    repos = result.scalars().all()

    return {
        "items": [
            {
                "id": r.id,
                "full_name": r.full_name,
                "description": r.description,
                "stars": r.stars,
                "forks": r.forks,
                "primary_language": r.primary_language,
                "topics": json.loads(r.topics) if r.topics else [],
                "quality_score": r.quality_score,
                "ai_relevance_score": r.ai_relevance_score,
                "is_internal_tool": r.is_internal_tool,
                "url": r.url,
            }
            for r in repos
        ],
        "total": total,
        "page": page,
    }
