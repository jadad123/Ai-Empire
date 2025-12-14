import httpx
from typing import Optional, Dict, Any, List
from base64 import b64encode
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.encryption import encryption_service


class WordPressClient:
    def __init__(self, site_url: str, username: str, app_password_encrypted: str):
        self.site_url = site_url.rstrip('/')
        self.username = username
        self.app_password = encryption_service.decrypt(app_password_encrypted)
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        
        # Basic auth header
        credentials = f"{self.username}:{self.app_password}"
        self.auth_header = b64encode(credentials.encode()).decode()
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Fetch all categories from WordPress"""
        categories = []
        page = 1
        per_page = 100
        
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{self.api_base}/categories",
                    headers=self._get_headers(),
                    params={"per_page": per_page, "page": page},
                    timeout=30
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data:
                    break
                
                categories.extend(data)
                
                # Check if more pages
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                page += 1
        
        return categories
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        alt_text: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Upload image to WordPress media library"""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Basic {self.auth_header}",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "image/jpeg"
            }
            
            response = await client.post(
                f"{self.api_base}/media",
                headers=headers,
                content=image_data,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                media = response.json()
                
                # Update alt text
                if alt_text:
                    await client.post(
                        f"{self.api_base}/media/{media['id']}",
                        headers=self._get_headers(),
                        json={"alt_text": alt_text},
                        timeout=30
                    )
                
                return media
            
            print(f"Image upload failed: {response.status_code} - {response.text}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def create_post(
        self,
        title: str,
        content: str,
        category_id: Optional[int] = None,
        featured_media_id: Optional[int] = None,
        meta_description: str = "",
        status: str = "publish",
        author_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new WordPress post"""
        
        post_data = {
            "title": title,
            "content": content,
            "status": status,
        }
        
        if category_id:
            post_data["categories"] = [category_id]
        
        if featured_media_id:
            post_data["featured_media"] = featured_media_id
        
        if author_id:
            post_data["author"] = author_id
        
        # Add meta description via Yoast/RankMath meta
        if meta_description:
            post_data["meta"] = {
                "_yoast_wpseo_metadesc": meta_description,
                "rank_math_description": meta_description
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/posts",
                headers=self._get_headers(),
                json=post_data,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            
            print(f"Post creation failed: {response.status_code} - {response.text}")
            return None
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test WordPress connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/users/me",
                    headers=self._get_headers(),
                    timeout=15
                )
                
                if response.status_code == 200:
                    user = response.json()
                    return True, f"Connected as {user.get('name', 'Unknown')}"
                else:
                    return False, f"Auth failed: {response.status_code}"
                    
        except Exception as e:
            return False, str(e)


from typing import Tuple
