from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
import app.core.database as db_module
from app.core.database import Base
from app.routers import watches, search, brands, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting WatchLens API...")
    Base.metadata.create_all(bind=db_module.engine)
    os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
    logger.info("Database tables created.")
    yield
    logger.info("Shutting down WatchLens API.")


app = FastAPI(
    title="WatchLens API",
    description="Watch discovery platform — visual search & similarity engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for local image storage
if os.path.exists(settings.IMAGE_STORAGE_PATH):
    app.mount("/static/images", StaticFiles(directory=settings.IMAGE_STORAGE_PATH), name="images")

# Routers
app.include_router(watches.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(brands.router, prefix="/api/v1")
app.include_router(filters.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"service": "WatchLens API", "version": "1.0.0", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}
