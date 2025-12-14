from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.api.routes import sites, sources, articles, dashboard
from app.models.base import engine, Base
# Import all models so they register with Base.metadata
from app.models import Site, Source, Article

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    logger.info("Starting up - creating database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title="Global AI Content Empire",
    description="Centralized automation platform for managing niche websites",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow all origins if ALLOWED_ORIGINS contains *
origins_str = settings.allowed_origins
if "*" in origins_str:
    origins = ["*"]
else:
    origins = [o.strip() for o in origins_str.split(",") if o.strip()]

logger.info(f"Configuring CORS with origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(sites.router, prefix="/api/sites", tags=["Sites"])
app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])


@app.get("/")
async def root():
    return {"message": "Global AI Content Empire API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
