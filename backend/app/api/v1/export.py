import csv
import io
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.person import Person
from app.models.github_profile import GitHubProfile

router = APIRouter()


@router.post("/people")
async def export_people(body: dict, db: AsyncSession = Depends(get_db)):
    query = select(Person).outerjoin(GitHubProfile, Person.id == GitHubProfile.person_id)

    min_score = body.get("min_score")
    if min_score is not None:
        query = query.where(Person.founder_propensity_score >= min_score)

    pipeline_stage = body.get("pipeline_stage")
    if pipeline_stage:
        query = query.where(Person.pipeline_stage == pipeline_stage)

    query = query.order_by(Person.founder_propensity_score.desc().nullslast())
    result = await db.execute(query)
    people = result.scalars().all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "GitHub Login", "Location", "Country", "Pipeline Stage",
        "Founder Propensity Score", "Technical Score", "Momentum Score",
        "AI Nativeness Score", "Builder Type", "Founder Fit",
        "One Line Summary", "Tags",
    ])

    for p in people:
        gh_result = await db.execute(select(GitHubProfile).where(GitHubProfile.person_id == p.id))
        gh = gh_result.scalar_one_or_none()
        tags = ""
        if p.tags:
            try:
                tags = ", ".join(json.loads(p.tags))
            except (json.JSONDecodeError, TypeError):
                pass
        writer.writerow([
            p.display_name,
            gh.login if gh else "",
            p.location,
            p.country,
            p.pipeline_stage,
            round(p.founder_propensity_score, 3) if p.founder_propensity_score else "",
            round(p.technical_score, 3) if p.technical_score else "",
            round(p.momentum_score, 3) if p.momentum_score else "",
            round(p.ai_nativeness_score, 3) if p.ai_nativeness_score else "",
            p.builder_type,
            p.founder_fit,
            p.one_line_summary,
            tags,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=builders_export.csv"},
    )
