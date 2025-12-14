import asyncio
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.tasks.celery_app import celery_app
from app.models import Article, ArticleStatus, Site, ImageSource
from app.models.base import async_session
from app.services import ai_processor, image_pipeline, vector_store, WordPressClient
from app.services.encryption import encryption_service
from app.utils.watermark import watermarker


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def process_article(self, article_id: str):
    """Process a single article through the AI pipeline"""
    return run_async(_process_article(article_id))


async def _process_article(article_id: str):
    """Async implementation of article processing"""
    async with async_session() as db:
        try:
            # Get article with site
            result = await db.execute(
                select(Article)
                .options(selectinload(Article.site))
                .where(Article.id == UUID(article_id))
            )
            article = result.scalar_one_or_none()
            
            if not article:
                return {"status": "error", "error": "Article not found"}
            
            if article.status not in [ArticleStatus.PENDING]:
                return {"status": "skipped", "reason": f"Article status is {article.status}"}
            
            site = article.site
            if not site:
                return {"status": "error", "error": "Site not found"}
            
            # Update status
            article.status = ArticleStatus.PROCESSING
            await db.commit()
            
            # Step 1: Detect language
            source_lang = ai_processor.detect_language(article.original_content)
            article.source_language = source_lang
            
            # Step 2: AI Rewrite and Translation
            ai_result = await ai_processor.rewrite_article(
                title=article.original_title,
                content=article.original_content,
                source_language=source_lang,
                target_language=site.target_language,
                category_map=site.category_map
            )
            
            article.processed_title = ai_result.get("title", article.original_title)
            article.processed_content = ai_result.get("content", article.original_content)
            article.meta_description = ai_result.get("meta_description", "")
            article.target_language = site.target_language
            
            # Set category
            category_id = ai_result.get("category_id")
            if category_id and site.category_map:
                article.category_id = int(category_id)
                article.category_name = site.category_map.get(str(category_id), "")
            
            # Step 3: Image Pipeline
            bing_cookie = encryption_service.decrypt(site.bing_cookie) if site.bing_cookie else None
            
            image_url, image_source = await image_pipeline.get_image(
                title=article.processed_title,
                content=article.processed_content,
                original_image_url=article.original_image_url,
                bing_cookie=bing_cookie
            )
            
            article.image_url = image_url
            article.image_source = ImageSource(image_source)
            
            # Step 4: Add to vector store
            vector_id = vector_store.add_article(
                article_id=str(article.id),
                title=article.processed_title,
                content=article.processed_content,
                metadata={"site_id": str(site.id), "source_language": source_lang}
            )
            article.vector_id = vector_id
            
            # Step 5: Publish to WordPress
            wp_client = WordPressClient(
                site_url=site.url,
                username=site.wp_username,
                app_password_encrypted=site.wp_app_password
            )
            
            # Upload image if exists
            featured_media_id = None
            if image_url and image_source != 'none':
                # Apply watermark for AI-generated images
                if image_source in ['bing', 'flux'] and site.watermark_text:
                    image_data = await watermarker.apply_watermark_from_url(
                        image_url,
                        site.watermark_text
                    )
                else:
                    image_data = await image_pipeline.download_image(image_url)
                
                if image_data:
                    filename = f"article-{article.id}.jpg"
                    media = await wp_client.upload_image(
                        image_data,
                        filename,
                        alt_text=article.processed_title[:100]
                    )
                    if media:
                        featured_media_id = media.get('id')
            
            # Create post
            author_id = int(site.default_author_id) if site.default_author_id else None
            
            post = await wp_client.create_post(
                title=article.processed_title,
                content=article.processed_content,
                category_id=article.category_id,
                featured_media_id=featured_media_id,
                meta_description=article.meta_description,
                author_id=author_id
            )
            
            if post:
                article.wp_post_id = post.get('id')
                article.wp_post_url = post.get('link')
                article.status = ArticleStatus.PUBLISHED
                article.published_at = datetime.utcnow()
            else:
                article.status = ArticleStatus.FAILED
                article.error_message = "Failed to publish to WordPress"
            
            article.processed_at = datetime.utcnow()
            await db.commit()
            
            return {
                "status": "success" if article.status == ArticleStatus.PUBLISHED else "failed",
                "article_id": str(article.id),
                "wp_post_id": article.wp_post_id
            }
            
        except Exception as e:
            await db.rollback()
            
            # Update article with error
            async with async_session() as db2:
                result = await db2.execute(
                    select(Article).where(Article.id == UUID(article_id))
                )
                article = result.scalar_one_or_none()
                if article:
                    article.status = ArticleStatus.FAILED
                    article.error_message = str(e)
                    await db2.commit()
            
            return {"status": "error", "error": str(e)}


@celery_app.task
def process_pending_articles(site_id: str = None):
    """Process all pending articles for a site"""
    return run_async(_process_pending_articles(site_id))


async def _process_pending_articles(site_id: str = None):
    """Async implementation"""
    async with async_session() as db:
        query = select(Article).where(Article.status == ArticleStatus.PENDING)
        
        if site_id:
            query = query.where(Article.site_id == UUID(site_id))
        
        query = query.order_by(Article.created_at.asc()).limit(50)
        
        result = await db.execute(query)
        articles = result.scalars().all()
        
        for article in articles:
            process_article.delay(str(article.id))
        
        return {"articles_queued": len(articles)}


@celery_app.task
def cleanup_old_articles(days: int = 30):
    """Clean up old failed/duplicate articles"""
    return run_async(_cleanup_old_articles(days))


async def _cleanup_old_articles(days: int):
    """Async implementation"""
    async with async_session() as db:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Delete old duplicates
        await db.execute(
            delete(Article).where(
                Article.status == ArticleStatus.DUPLICATE,
                Article.created_at < cutoff
            )
        )
        
        # Delete old failed articles (after 7 days)
        failed_cutoff = datetime.utcnow() - timedelta(days=7)
        await db.execute(
            delete(Article).where(
                Article.status == ArticleStatus.FAILED,
                Article.created_at < failed_cutoff,
                Article.retry_count >= 3
            )
        )
        
        await db.commit()
        
        return {"status": "cleanup completed"}
