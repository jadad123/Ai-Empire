import asyncio
import random
import feedparser
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import re

from app.config import settings


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 2560, "height": 1440},
]


@dataclass
class ScrapedArticle:
    url: str
    title: str
    content: str
    image_url: Optional[str] = None
    published_date: Optional[str] = None


class ContentIngestor:
    def __init__(self):
        self.browser = None
        self.context = None
    
    async def _init_browser(self):
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
    
    async def _get_context(self, anti_ban_config: dict = None):
        await self._init_browser()
        
        config = anti_ban_config or {}
        user_agent = random.choice(USER_AGENTS) if config.get('rotate_user_agent', True) else USER_AGENTS[0]
        viewport = random.choice(VIEWPORTS)
        
        context = await self.browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        return context
    
    # RSS Feed Parsing
    async def parse_rss(self, feed_url: str, max_items: int = 10) -> List[ScrapedArticle]:
        """Parse RSS feed and return articles"""
        articles = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(feed_url, timeout=30)
                feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:max_items]:
                # Extract content
                content = ""
                if hasattr(entry, 'content'):
                    content = entry.content[0].value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                elif hasattr(entry, 'description'):
                    content = entry.description
                
                # Clean HTML
                soup = BeautifulSoup(content, 'lxml')
                clean_content = soup.get_text(separator='\n', strip=True)
                
                # Extract image
                image_url = None
                if hasattr(entry, 'media_content'):
                    image_url = entry.media_content[0].get('url')
                elif hasattr(entry, 'media_thumbnail'):
                    image_url = entry.media_thumbnail[0].get('url')
                else:
                    # Try to find image in content
                    img_tag = soup.find('img')
                    if img_tag:
                        image_url = img_tag.get('src')
                
                articles.append(ScrapedArticle(
                    url=entry.get('link', ''),
                    title=entry.get('title', 'Untitled'),
                    content=clean_content,
                    image_url=image_url,
                    published_date=entry.get('published', None)
                ))
            
        except Exception as e:
            print(f"RSS parsing error: {e}")
        
        return articles
    
    # Direct URL Scraping with Playwright
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def scrape_url(
        self, 
        url: str, 
        scrape_config: dict = None
    ) -> Optional[ScrapedArticle]:
        """Scrape article from URL using Playwright with stealth"""
        config = scrape_config or {}
        anti_ban = config.get('anti_ban', {})
        
        context = await self._get_context(anti_ban)
        page = await context.new_page()
        
        try:
            # Apply stealth
            await stealth_async(page)
            
            # Random delay
            if anti_ban.get('random_delay', True):
                await asyncio.sleep(random.uniform(1, 3))
            
            # Navigate
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for dynamic content
            
            # Extract title
            title_selector = config.get('title_selector', 'h1')
            title_element = await page.query_selector(title_selector)
            title = await title_element.inner_text() if title_element else "Untitled"
            
            # Extract content
            content_selector = config.get('content_selector', 'article')
            content_element = await page.query_selector(content_selector)
            
            if content_element:
                content_html = await content_element.inner_html()
                soup = BeautifulSoup(content_html, 'lxml')
                
                # Remove unwanted elements
                for element in soup.find_all(['script', 'style', 'nav', 'footer', 'aside', 'iframe']):
                    element.decompose()
                
                content = soup.get_text(separator='\n', strip=True)
            else:
                content = ""
            
            # Extract image
            image_url = None
            image_selector = config.get('image_selector', 'article img')
            image_element = await page.query_selector(image_selector)
            if image_element:
                image_url = await image_element.get_attribute('src')
            
            return ScrapedArticle(
                url=url,
                title=title.strip(),
                content=content,
                image_url=image_url
            )
            
        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            
            # Try ScraperAPI fallback
            if anti_ban.get('use_scraperapi') and settings.scraperapi_key:
                return await self._scrape_with_scraperapi(url, config)
            
            return None
        
        finally:
            await page.close()
            await context.close()
    
    async def _scrape_with_scraperapi(self, url: str, config: dict) -> Optional[ScrapedArticle]:
        """Fallback scraping using ScraperAPI"""
        try:
            api_url = f"http://api.scraperapi.com?api_key={settings.scraperapi_key}&url={url}&render=true"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, timeout=60)
                html = response.text
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract title
            title_element = soup.select_one(config.get('title_selector', 'h1'))
            title = title_element.get_text(strip=True) if title_element else "Untitled"
            
            # Extract content
            content_element = soup.select_one(config.get('content_selector', 'article'))
            if content_element:
                for element in content_element.find_all(['script', 'style', 'nav', 'footer']):
                    element.decompose()
                content = content_element.get_text(separator='\n', strip=True)
            else:
                content = ""
            
            # Extract image
            image_url = None
            image_element = soup.select_one(config.get('image_selector', 'article img'))
            if image_element:
                image_url = image_element.get('src')
            
            return ScrapedArticle(
                url=url,
                title=title,
                content=content,
                image_url=image_url
            )
            
        except Exception as e:
            print(f"ScraperAPI error: {e}")
            return None
    
    async def scrape_links_from_page(self, root_url: str, link_selector: str = "a") -> List[str]:
        """Extract article links from a root page"""
        context = await self._get_context()
        page = await context.new_page()
        links = []
        
        try:
            await stealth_async(page)
            await page.goto(root_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)
            
            elements = await page.query_selector_all(link_selector)
            
            for element in elements:
                href = await element.get_attribute('href')
                if href and not href.startswith('#'):
                    # Make absolute URL
                    if href.startswith('/'):
                        from urllib.parse import urljoin
                        href = urljoin(root_url, href)
                    links.append(href)
            
        except Exception as e:
            print(f"Link extraction error: {e}")
        
        finally:
            await page.close()
            await context.close()
        
        return list(set(links))  # Remove duplicates
    
    async def close(self):
        if self.browser:
            await self.browser.close()


content_ingestor = ContentIngestor()
