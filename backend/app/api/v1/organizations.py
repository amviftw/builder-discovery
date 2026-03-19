from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.organization import Organization

router = APIRouter()


@router.get("")
async def list_organizations(
    search: Optional[str] = None,
    company_type: Optional[str] = None,
    is_tracked: Optional[bool] = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Organization)
    if search:
        query = query.where(
            (Organization.name.ilike(f"%{search}%")) | (Organization.github_org_login.ilike(f"%{search}%"))
        )
    if company_type:
        query = query.where(Organization.company_type == company_type)
    if is_tracked is not None:
        query = query.where(Organization.is_tracked == is_tracked)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Organization.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orgs = result.scalars().all()

    return {
        "items": [
            {
                "id": o.id,
                "name": o.name,
                "github_org_login": o.github_org_login,
                "company_type": o.company_type,
                "location": o.location,
                "employee_count_est": o.employee_count_est,
                "is_tracked": o.is_tracked,
                "public_repos_count": o.public_repos_count,
            }
            for o in orgs
        ],
        "total": total,
        "page": page,
    }


@router.post("")
async def add_organization(body: dict, db: AsyncSession = Depends(get_db)):
    org = Organization(
        github_org_login=body.get("github_org_login"),
        name=body.get("name"),
        company_type=body.get("company_type"),
        location=body.get("location"),
        is_tracked=body.get("is_tracked", True),
    )
    db.add(org)
    await db.flush()
    return {"id": org.id, "status": "created"}
