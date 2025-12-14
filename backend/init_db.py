import asyncio
import logging
from app.models.base import engine, Base
from app.models import Site, Source, Article

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_models():
    logger.info("Connecting to database...")
    try:
        async with engine.begin() as conn:
            logger.info("Dropping all tables (if exist) to ensure clean state...")
            # Uncomment the next line if you want to force a full reset
            # await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
        logger.info(" Tables created successfully!")
    except Exception as e:
        logger.error(f" Error creating tables: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_models())
