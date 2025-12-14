import asyncio
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.tasks.celery_app import celery_app
from app.models import Source, Site, Article, ArticleStatus, SourceType, VelocityMode
from app.models.base import async_session
from app.services import content_ingestor, vector_store


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def poll_source(self, source_id: str):
    """Poll a single source for new articles"""
    return run_async(_poll_source(source_id))


async def _poll_source(source_id: str):
    """Async implementation of source polling"""
    async with async_session() as db:
        try:
            # Get source with site
            result = await db.execute(
                select(Source)
                .options(selectinload(Source.site))
                .where(Source.id == UUID(source_id))
            )
            source = result.scalar_one_or_none()
            
            if not source or not source.is_active:
                return {"status": "skipped", "reason": "Source inactive or not found"}
            
            site = source.site
            if not site or not site.is_active:
                return {"status": "skipped", "reason": "Site inactive"}
            
            articles_created = 0
            articles_skipped = 0
            
            # Fetch articles based on source type
            if source.type == SourceType.RSS:
                scraped_articles = await content_ingestor.parse_rss(
                    source.url,
                    max_items=source.max_articles_per_poll
                )
            else:
                # URL scraping - get links first then scrape each
                links = await content_ingestor.scrape_links_from_page(
                    source.url,
                    source.scrape_config.get('link_selector', 'a')
                )
                
                scraped_articles = []
                for link in links[:source.max_articles_per_poll]:
                    article = await content_ingestor.scrape_url(
                        link,
                        source.scrape_config
                    )
                    if article:
                        scraped_articles.append(article)
            
            # Process each scraped article
            for scraped in scraped_articles:
                # Check if URL already exists
                existing = await db.execute(
                    select(Article).where(Article.original_url == scraped.url)
                )
                if existing.scalar_one_or_none():
                    articles_skipped += 1
                    continue
                
                # Check semantic duplicate
                is_duplicate, existing_id, similarity = vector_store.check_duplicate(
                    scraped.title,
                    scraped.content
                )
                
                if is_duplicate:
                    # Create article record as duplicate
                    article = Article(
                        source_id=source.id,
                        site_id=site.id,
                        original_url=scraped.url,
                        original_title=scraped.title,
                        original_content=scraped.content,
                        original_image_url=scraped.image_url,
                        target_language=site.target_language,
                        status=ArticleStatus.DUPLICATE,
                        similarity_score=str(round(similarity, 3)) if similarity else None
                    )
                    db.add(article)
                    articles_skipped += 1
                    continue
                
                # Create new article
                article = Article(
                    source_id=source.id,
                    site_id=site.id,
                    original_url=scraped.url,
                    original_title=scraped.title,
                    original_content=scraped.content,
                    original_image_url=scraped.image_url,
                    target_language=site.target_language,
                    status=ArticleStatus.PENDING
                )
                db.add(article)
                articles_created += 1
            
            # Update last polled
            source.last_polled_at = datetime.utcnow()
            await db.commit()
            
            # Trigger processing for new articles
            from app.tasks.processing_tasks import process_pending_articles
            if articles_created > 0:
                process_pending_articles.delay(str(site.id))
            
            return {
                "status": "success",
                "source": source.name,
                "created": articles_created,
                "skipped": articles_skipped
            }
            
        except Exception as e:
            await db.rollback()
            return {"status": "error", "error": str(e)}


@celery_app.task
def poll_all_sources(velocity_mode: str = "news"):
    """Poll all sources matching velocity mode"""
    return run_async(_poll_all_sources(velocity_mode))


async def _poll_all_sources(velocity_mode: str):
    """Async implementation"""
    async with async_session() as db:
        mode = VelocityMode.NEWS if velocity_mode == "news" else VelocityMode.EVERGREEN
        
        result = await db.execute(
            select(Source)
            .join(Site)
            .where(
                Source.is_active == True,
                Site.is_active == True,
                Site.velocity_mode == mode
            )
        )
        sources = result.scalars().all()
        
        # Trigger polling for each source
        for source in sources:
            poll_source.delay(str(source.id))
        
        return {"sources_queued": len(sources)}
