import asyncio
import httpx
import random
from typing import Optional, Tuple
from PIL import Image
from io import BytesIO
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.ai_processor import ai_processor


class ImagePipeline:
    """
    Image Waterfall Pipeline using OpenRouter for Flux generation:
    1. Source Image (if clean)
    2. Stock APIs (Pexels/Unsplash)
    3. Flux via OpenRouter
    """
    
    def __init__(self):
        self.pexels_key = settings.pexels_api_key
        self.unsplash_key = settings.unsplash_access_key
        self.openrouter_key = settings.openrouter_api_key
    
    async def get_image(
        self,
        title: str,
        content: str,
        original_image_url: Optional[str] = None,
        bing_cookie: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Execute image waterfall pipeline.
        Returns (image_url, source) where source is 'original', 'stock', or 'flux'
        """
        
        # Step 1: Try original image
        if original_image_url:
            analysis = await ai_processor.analyze_image(original_image_url)
            if analysis.get('clean', False):
                return original_image_url, 'original'
        
        # Generate search query from content
        search_query = await self._generate_search_query(title)
        
        # Step 2: Try stock photos
        stock_url = await self._search_stock_photos(search_query)
        if stock_url:
            return stock_url, 'stock'
        
        # Step 3: Generate with Flux via OpenRouter
        flux_url = await self._generate_flux_image(search_query)
        if flux_url:
            return flux_url, 'flux'
        
        return None, 'none'
    
    async def _generate_search_query(self, title: str) -> str:
        """Generate a search-friendly query from article title"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were'}
        words = title.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return ' '.join(keywords[:5])
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def _search_stock_photos(self, query: str) -> Optional[str]:
        """Search Pexels and Unsplash for stock photos"""
        
        # Try Pexels first
        if self.pexels_key:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.pexels.com/v1/search",
                        headers={"Authorization": self.pexels_key},
                        params={"query": query, "per_page": 5, "orientation": "landscape"},
                        timeout=15
                    )
                    data = response.json()
                    if data.get('photos'):
                        photo = random.choice(data['photos'])
                        return photo['src']['large']
            except Exception as e:
                print(f"Pexels error: {e}")
        
        # Try Unsplash
        if self.unsplash_key:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.unsplash.com/search/photos",
                        headers={"Authorization": f"Client-ID {self.unsplash_key}"},
                        params={"query": query, "per_page": 5, "orientation": "landscape"},
                        timeout=15
                    )
                    data = response.json()
                    if data.get('results'):
                        photo = random.choice(data['results'])
                        return photo['urls']['regular']
            except Exception as e:
                print(f"Unsplash error: {e}")
        
        return None
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def _generate_flux_image(self, prompt: str) -> Optional[str]:
        """Generate image using Flux via OpenRouter"""
        if not self.openrouter_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://empire.local",
                        "X-Title": "AI Content Empire"
                    },
                    json={
                        "model": "black-forest-labs/flux-schnell",
                        "prompt": f"Professional photograph, high quality, {prompt}",
                        "n": 1,
                        "size": "1024x576"
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data") and len(data["data"]) > 0:
                        return data["data"][0].get("url")
                else:
                    print(f"Flux generation error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Flux image generation error: {e}")
        
        return None
    
    async def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                return response.content
        except:
            return None


image_pipeline = ImagePipeline()
