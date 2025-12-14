from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID

from app.api.deps import get_database
from app.models import Site, Source, Article
from app.schemas import SiteCreate, SiteUpdate, SiteResponse, SiteListResponse
from app.services import encryption_service, WordPressClient

router = APIRouter()


@router.get("", response_model=SiteListResponse)
async def list_sites(db: AsyncSession = Depends(get_database)):
    """List all sites"""
    result = await db.execute(select(Site).order_by(Site.created_at.desc()))
    sites = result.scalars().all()
    
    # Get counts
    site_responses = []
    for site in sites:
        sources_result = await db.execute(
            select(func.count()).select_from(Source).where(Source.site_id == site.id)
        )
        sources_count = sources_result.scalar() or 0
        
        articles_result = await db.execute(
            select(func.count()).select_from(Article).where(Article.site_id == site.id)
        )
        articles_count = articles_result.scalar() or 0
        
        site_dict = {
            "id": site.id,
            "name": site.name,
            "url": site.url,
            "wp_username": site.wp_username,
            "target_language": site.target_language,
            "velocity_mode": site.velocity_mode,
            "category_map": site.category_map or {},
            "default_author_id": site.default_author_id,
            "watermark_text": site.watermark_text,
            "is_active": site.is_active,
            "created_at": site.created_at,
            "updated_at": site.updated_at,
            "sources_count": sources_count,
            "articles_count": articles_count
        }
        site_responses.append(SiteResponse(**site_dict))
    
    return SiteListResponse(sites=site_responses, total=len(site_responses))


@router.post("", response_model=SiteResponse)
async def create_site(site: SiteCreate, db: AsyncSession = Depends(get_database)):
    """Create a new site"""
    # Encrypt sensitive data
    encrypted_password = encryption_service.encrypt(site.wp_app_password)
    encrypted_bing = encryption_service.encrypt(site.bing_cookie) if site.bing_cookie else None
    
    new_site = Site(
        name=site.name,
        url=site.url,
        wp_username=site.wp_username,
        wp_app_password=encrypted_password,
        category_map=site.category_map,
        bing_cookie=encrypted_bing,
        velocity_mode=site.velocity_mode,
        target_language=site.target_language,
        default_author_id=site.default_author_id,
        watermark_text=site.watermark_text,
        is_active=site.is_active
    )
    
    db.add(new_site)
    await db.commit()
    await db.refresh(new_site)
    
    return SiteResponse(
        id=new_site.id,
        name=new_site.name,
        url=new_site.url,
        wp_username=new_site.wp_username,
        target_language=new_site.target_language,
        velocity_mode=new_site.velocity_mode,
        category_map=new_site.category_map or {},
        default_author_id=new_site.default_author_id,
        watermark_text=new_site.watermark_text,
        is_active=new_site.is_active,
        created_at=new_site.created_at,
        updated_at=new_site.updated_at,
        sources_count=0,
        articles_count=0
    )


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: UUID, db: AsyncSession = Depends(get_database)):
    """Get site by ID"""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    sources_result = await db.execute(
        select(func.count()).select_from(Source).where(Source.site_id == site.id)
    )
    sources_count = sources_result.scalar() or 0
    
    articles_result = await db.execute(
        select(func.count()).select_from(Article).where(Article.site_id == site.id)
    )
    articles_count = articles_result.scalar() or 0
    
    return SiteResponse(
        id=site.id,
        name=site.name,
        url=site.url,
        wp_username=site.wp_username,
        target_language=site.target_language,
        velocity_mode=site.velocity_mode,
        category_map=site.category_map or {},
        default_author_id=site.default_author_id,
        watermark_text=site.watermark_text,
        is_active=site.is_active,
        created_at=site.created_at,
        updated_at=site.updated_at,
        sources_count=sources_count,
        articles_count=articles_count
    )


@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(site_id: UUID, site_update: SiteUpdate, db: AsyncSession = Depends(get_database)):
    """Update site"""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    update_data = site_update.model_dump(exclude_unset=True)
    
    # Handle encrypted fields
    if 'wp_app_password' in update_data:
        update_data['wp_app_password'] = encryption_service.encrypt(update_data['wp_app_password'])
    if 'bing_cookie' in update_data and update_data['bing_cookie']:
        update_data['bing_cookie'] = encryption_service.encrypt(update_data['bing_cookie'])
    
    for key, value in update_data.items():
        setattr(site, key, value)
    
    await db.commit()
    await db.refresh(site)
    
    return await get_site(site_id, db)


@router.delete("/{site_id}")
async def delete_site(site_id: UUID, db: AsyncSession = Depends(get_database)):
    """Delete site"""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    await db.delete(site)
    await db.commit()
    
    return {"message": "Site deleted successfully"}


@router.post("/{site_id}/sync-categories")
async def sync_categories(site_id: UUID, db: AsyncSession = Depends(get_database)):
    """Fetch categories from WordPress and update category map"""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    wp_client = WordPressClient(
        site_url=site.url,
        username=site.wp_username,
        app_password_encrypted=site.wp_app_password
    )
    
    try:
        categories = await wp_client.get_categories()
        category_map = {str(cat['id']): cat['name'] for cat in categories}
        
        site.category_map = category_map
        await db.commit()
        
        return {"categories": category_map, "count": len(category_map)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync categories: {str(e)}")


@router.post("/{site_id}/test-connection")
async def test_connection(site_id: UUID, db: AsyncSession = Depends(get_database)):
    """Test WordPress connection"""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    wp_client = WordPressClient(
        site_url=site.url,
        username=site.wp_username,
        app_password_encrypted=site.wp_app_password
    )
    
    success, message = await wp_client.test_connection()
    
    return {"success": success, "message": message}
