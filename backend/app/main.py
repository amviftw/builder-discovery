from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import Base
from app.db.engine import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for SQLite, simpler than Alembic for MVP)
    async with engine.begin() as conn:
        # Import all models so they register with Base
        import app.models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Builder Discovery Pipeline",
    description="Discover high-propensity founders before they self-identify",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
from app.api.v1 import router as api_v1_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
