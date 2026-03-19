import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.person import Person
from app.models.github_profile import GitHubProfile
from app.models.signal import Signal

router = APIRouter()


@router.get("")
async def list_people(
    search: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    builder_type: Optional[str] = None,
    founder_fit: Optional[str] = None,
    country: Optional[str] = None,
    sort_by: str = Query("score", pattern="^(score|recent|name|momentum)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Person).where(Person.is_archived == False)  # noqa: E712

    if search:
        search_filter = f"%{search}%"
        query = query.outerjoin(GitHubProfile, Person.id == GitHubProfile.person_id).where(
            (Person.display_name.ilike(search_filter))
            | (Person.bio.ilike(search_filter))
            | (GitHubProfile.login.ilike(search_filter))
        )

    if pipeline_stage:
        query = query.where(Person.pipeline_stage == pipeline_stage)
    if min_score is not None:
        query = query.where(Person.founder_propensity_score >= min_score)
    if max_score is not None:
        query = query.where(Person.founder_propensity_score <= max_score)
    if builder_type:
        query = query.where(Person.builder_type == builder_type)
    if founder_fit:
        query = query.where(Person.founder_fit == founder_fit)
    if country:
        query = query.where(Person.country == country)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    sort_col = {
        "score": Person.founder_propensity_score,
        "recent": Person.created_at,
        "name": Person.display_name,
        "momentum": Person.momentum_score,
    }[sort_by]
    if sort_dir == "desc":
        query = query.order_by(sort_col.desc().nullslast())
    else:
        query = query.order_by(sort_col.asc().nullsfirst())

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    people = result.scalars().all()

    return {
        "items": [_person_summary(p) for p in people],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get("/{person_id}")
async def get_person(person_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Person not found")

    # Eagerly load related data
    gh_result = await db.execute(select(GitHubProfile).where(GitHubProfile.person_id == person_id))
    gh = gh_result.scalar_one_or_none()

    sig_result = await db.execute(
        select(Signal).where(Signal.person_id == person_id, Signal.is_active == True).order_by(Signal.detected_at.desc())  # noqa: E712
    )
    signals = sig_result.scalars().all()

    return {
        **_person_summary(person),
        "bio": person.bio,
        "website_url": person.website_url,
        "analyst_notes": person.analyst_notes,
        "one_line_summary": person.one_line_summary,
        "github_profile": _gh_summary(gh) if gh else None,
        "signals": [_signal_summary(s) for s in signals],
    }


@router.patch("/{person_id}")
async def update_person(person_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Person not found")

    allowed = {"pipeline_stage", "tags", "analyst_notes", "is_archived"}
    for key, value in body.items():
        if key in allowed:
            if key == "tags" and isinstance(value, list):
                value = json.dumps(value)
            setattr(person, key, value)
    return {"status": "updated"}


def _person_summary(p: Person) -> dict:
    tags = []
    if p.tags:
        try:
            tags = json.loads(p.tags)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": p.id,
        "display_name": p.display_name,
        "location": p.location,
        "country": p.country,
        "avatar_url": p.avatar_url,
        "pipeline_stage": p.pipeline_stage,
        "builder_type": p.builder_type,
        "builder_experience": p.builder_experience,
        "founder_fit": p.founder_fit,
        "founder_propensity_score": p.founder_propensity_score,
        "technical_score": p.technical_score,
        "momentum_score": p.momentum_score,
        "ai_nativeness_score": p.ai_nativeness_score,
        "leadership_score": p.leadership_score,
        "departure_signal_score": p.departure_signal_score,
        "tags": tags,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _gh_summary(gh: GitHubProfile) -> dict:
    return {
        "login": gh.login,
        "followers": gh.followers,
        "following": gh.following,
        "public_repos": gh.public_repos,
        "hireable": gh.hireable,
        "company": gh.company,
        "twitter_username": gh.twitter_username,
        "total_stars_received": gh.total_stars_received,
        "profile_url": gh.profile_url,
    }


def _signal_summary(s: Signal) -> dict:
    evidence = {}
    if s.evidence:
        try:
            evidence = json.loads(s.evidence)
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": s.id,
        "signal_type": s.signal_type,
        "signal_strength": s.signal_strength,
        "description": s.description,
        "evidence": evidence,
        "detected_at": s.detected_at.isoformat() if s.detected_at else None,
        "is_active": s.is_active,
    }
