from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.api.deps import get_database
from app.models import Site, Source, Article, ArticleStatus

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_database)):
    """Get dashboard statistics"""
    # Sites count
    sites_result = await db.execute(select(func.count()).select_from(Site))
    sites_count = sites_result.scalar() or 0
    
    active_sites_result = await db.execute(
        select(func.count()).select_from(Site).where(Site.is_active == True)
    )
    active_sites = active_sites_result.scalar() or 0
    
    # Sources count
    sources_result = await db.execute(select(func.count()).select_from(Source))
    sources_count = sources_result.scalar() or 0
    
    active_sources_result = await db.execute(
        select(func.count()).select_from(Source).where(Source.is_active == True)
    )
    active_sources = active_sources_result.scalar() or 0
    
    # Articles by status
    articles_stats = {}
    for status in ArticleStatus:
        result = await db.execute(
            select(func.count()).select_from(Article).where(Article.status == status)
        )
        articles_stats[status.value] = result.scalar() or 0
    
    total_articles = sum(articles_stats.values())
    
    # Today's articles
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count()).select_from(Article).where(Article.created_at >= today)
    )
    today_articles = today_result.scalar() or 0
    
    # Published today
    published_today_result = await db.execute(
        select(func.count()).select_from(Article).where(
            Article.published_at >= today,
            Article.status == ArticleStatus.PUBLISHED
        )
    )
    published_today = published_today_result.scalar() or 0
    
    return {
        "sites": {
            "total": sites_count,
            "active": active_sites
        },
        "sources": {
            "total": sources_count,
            "active": active_sources
        },
        "articles": {
            "total": total_articles,
            "by_status": articles_stats,
            "today": today_articles,
            "published_today": published_today
        }
    }


@router.get("/recent")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_database)
):
    """Get recent articles"""
    result = await db.execute(
        select(Article)
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    articles = result.scalars().all()
    
    return {
        "articles": [
            {
                "id": str(a.id),
                "title": a.processed_title or a.original_title,
                "status": a.status.value,
                "created_at": a.created_at.isoformat(),
                "image_source": a.image_source.value if a.image_source else None
            }
            for a in articles
        ]
    }


@router.get("/chart/daily")
async def get_daily_chart(
    days: int = 7,
    db: AsyncSession = Depends(get_database)
):
    """Get daily article counts for chart"""
    data = []
    
    for i in range(days - 1, -1, -1):
        day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        next_day = day + timedelta(days=1)
        
        # Articles created
        created_result = await db.execute(
            select(func.count()).select_from(Article).where(
                Article.created_at >= day,
                Article.created_at < next_day
            )
        )
        created = created_result.scalar() or 0
        
        # Articles published
        published_result = await db.execute(
            select(func.count()).select_from(Article).where(
                Article.published_at >= day,
                Article.published_at < next_day,
                Article.status == ArticleStatus.PUBLISHED
            )
        )
        published = published_result.scalar() or 0
        
        data.append({
            "date": day.strftime("%Y-%m-%d"),
            "created": created,
            "published": published
        })
    
    return {"data": data}
