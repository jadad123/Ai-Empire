from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from app.api.deps import get_database
from app.models import Source, Article, Site
from app.schemas import SourceCreate, SourceUpdate, SourceResponse, SourceListResponse
from app.tasks.ingestion_tasks import poll_source

router = APIRouter()


@router.get("", response_model=SourceListResponse)
async def list_sources(
    site_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_database)
):
    """List all sources, optionally filtered by site"""
    query = select(Source).order_by(Source.created_at.desc())
    
    if site_id:
        query = query.where(Source.site_id == site_id)
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    source_responses = []
    for source in sources:
        articles_result = await db.execute(
            select(func.count()).select_from(Article).where(Article.source_id == source.id)
        )
        articles_count = articles_result.scalar() or 0
        
        source_responses.append(SourceResponse(
            id=source.id,
            site_id=source.site_id,
            name=source.name,
            type=source.type,
            url=source.url,
            poll_interval=source.poll_interval,
            max_articles_per_poll=source.max_articles_per_poll,
            scrape_config=source.scrape_config or {},
            is_active=source.is_active,
            last_polled_at=source.last_polled_at,
            created_at=source.created_at,
            updated_at=source.updated_at,
            articles_count=articles_count
        ))
    
    return SourceListResponse(sources=source_responses, total=len(source_responses))


@router.post("", response_model=SourceResponse)
async def create_source(source: SourceCreate, db: AsyncSession = Depends(get_database)):
    """Create a new source"""
    # Verify site exists
    site_result = await db.execute(select(Site).where(Site.id == source.site_id))
    site = site_result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    new_source = Source(
        site_id=source.site_id,
        name=source.name,
        type=source.type,
        url=source.url,
        poll_interval=source.poll_interval,
        max_articles_per_poll=source.max_articles_per_poll,
        scrape_config=source.scrape_config.model_dump() if source.scrape_config else None,
        is_active=source.is_active
    )
    
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    
    return SourceResponse(
        id=new_source.id,
        site_id=new_source.site_id,
        name=new_source.name,
        type=new_source.type,
        url=new_source.url,
        poll_interval=new_source.poll_interval,
        max_articles_per_poll=new_source.max_articles_per_poll,
        scrape_config=new_source.scrape_config or {},
        is_active=new_source.is_active,
        last_polled_at=new_source.last_polled_at,
        created_at=new_source.created_at,
        updated_at=new_source.updated_at,
        articles_count=0
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: UUID, db: AsyncSession = Depends(get_database)):
    """Get source by ID"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    articles_result = await db.execute(
        select(func.count()).select_from(Article).where(Article.source_id == source.id)
    )
    articles_count = articles_result.scalar() or 0
    
    return SourceResponse(
        id=source.id,
        site_id=source.site_id,
        name=source.name,
        type=source.type,
        url=source.url,
        poll_interval=source.poll_interval,
        max_articles_per_poll=source.max_articles_per_poll,
        scrape_config=source.scrape_config or {},
        is_active=source.is_active,
        last_polled_at=source.last_polled_at,
        created_at=source.created_at,
        updated_at=source.updated_at,
        articles_count=articles_count
    )


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: UUID, source_update: SourceUpdate, db: AsyncSession = Depends(get_database)):
    """Update source"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    update_data = source_update.model_dump(exclude_unset=True)
    
    if 'scrape_config' in update_data and update_data['scrape_config']:
        update_data['scrape_config'] = update_data['scrape_config'].model_dump()
    
    for key, value in update_data.items():
        setattr(source, key, value)
    
    await db.commit()
    await db.refresh(source)
    
    return await get_source(source_id, db)


@router.delete("/{source_id}")
async def delete_source(source_id: UUID, db: AsyncSession = Depends(get_database)):
    """Delete source"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    await db.delete(source)
    await db.commit()
    
    return {"message": "Source deleted successfully"}


@router.post("/{source_id}/poll")
async def trigger_poll(source_id: UUID, db: AsyncSession = Depends(get_database)):
    """Manually trigger source polling"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Trigger Celery task
    task = poll_source.delay(str(source_id))
    
    return {"message": "Polling started", "task_id": task.id}
