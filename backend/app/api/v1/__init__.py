from fastapi import APIRouter

from app.api.v1.people import router as people_router
from app.api.v1.signals import router as signals_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.repositories import router as repositories_router
from app.api.v1.export import router as export_router

router = APIRouter()

router.include_router(people_router, prefix="/people", tags=["people"])
router.include_router(signals_router, prefix="/signals", tags=["signals"])
router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
router.include_router(discovery_router, prefix="/discovery", tags=["discovery"])
router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
router.include_router(repositories_router, prefix="/repositories", tags=["repositories"])
router.include_router(export_router, prefix="/export", tags=["export"])
