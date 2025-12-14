from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from app.api.deps import get_database
from app.models import Article, ArticleStatus
from app.schemas import ArticleResponse, ArticleDetailResponse, ArticleListResponse
from app.tasks.processing_tasks import process_article

router = APIRouter()


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    site_id: Optional[UUID] = None,
    source_id: Optional[UUID] = None,
    status: Optional[ArticleStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database)
):
    """List articles with filters"""
    query = select(Article).order_by(Article.created_at.desc())
    count_query = select(func.count()).select_from(Article)
    
    if site_id:
        query = query.where(Article.site_id == site_id)
        count_query = count_query.where(Article.site_id == site_id)
    
    if source_id:
        query = query.where(Article.source_id == source_id)
        count_query = count_query.where(Article.source_id == source_id)
    
    if status:
        query = query.where(Article.status == status)
        count_query = count_query.where(Article.status == status)
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    article_responses = [
        ArticleResponse(
            id=a.id,
            source_id=a.source_id,
            site_id=a.site_id,
            original_url=a.original_url,
            original_title=a.original_title,
            processed_title=a.processed_title,
            source_language=a.source_language,
            target_language=a.target_language,
            category_name=a.category_name,
            image_url=a.image_url,
            image_source=a.image_source,
            wp_post_id=a.wp_post_id,
            wp_post_url=a.wp_post_url,
            status=a.status,
            error_message=a.error_message,
            created_at=a.created_at,
            published_at=a.published_at
        )
        for a in articles
    ]
    
    return ArticleListResponse(
        articles=article_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article(article_id: UUID, db: AsyncSession = Depends(get_database)):
    """Get article details"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleDetailResponse(
        id=article.id,
        source_id=article.source_id,
        site_id=article.site_id,
        original_url=article.original_url,
        original_title=article.original_title,
        original_content=article.original_content,
        processed_title=article.processed_title,
        processed_content=article.processed_content,
        meta_description=article.meta_description,
        source_language=article.source_language,
        target_language=article.target_language,
        category_name=article.category_name,
        vector_id=article.vector_id,
        similarity_score=article.similarity_score,
        image_url=article.image_url,
        image_source=article.image_source,
        wp_post_id=article.wp_post_id,
        wp_post_url=article.wp_post_url,
        status=article.status,
        error_message=article.error_message,
        retry_count=article.retry_count,
        created_at=article.created_at,
        processed_at=article.processed_at,
        published_at=article.published_at
    )


@router.post("/{article_id}/retry")
async def retry_article(article_id: UUID, db: AsyncSession = Depends(get_database)):
    """Retry failed article"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article.status not in [ArticleStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Article is not in failed state")
    
    # Reset status and trigger processing
    article.status = ArticleStatus.PENDING
    article.error_message = None
    article.retry_count += 1
    await db.commit()
    
    # Trigger processing task
    task = process_article.delay(str(article_id))
    
    return {"message": "Retry started", "task_id": task.id}


@router.delete("/{article_id}")
async def delete_article(article_id: UUID, db: AsyncSession = Depends(get_database)):
    """Delete article"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    await db.delete(article)
    await db.commit()
    
    return {"message": "Article deleted successfully"}


@router.get("/stats/summary")
async def get_article_stats(
    site_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_database)
):
    """Get article statistics"""
    base_query = select(func.count()).select_from(Article)
    
    if site_id:
        base_query = base_query.where(Article.site_id == site_id)
    
    # Get counts by status
    stats = {}
    for status in ArticleStatus:
        result = await db.execute(base_query.where(Article.status == status))
        stats[status.value] = result.scalar() or 0
    
    total_result = await db.execute(base_query)
    stats['total'] = total_result.scalar() or 0
    
    return stats
