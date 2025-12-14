import httpx
from langdetect import detect
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import re

from app.config import settings


class AIProcessor:
    """
    AI Processor using OpenRouter API for all LLM operations.
    Supports Gemini Flash (primary) and Llama 3 (fallback) via OpenRouter.
    """
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.primary_model = "google/gemini-flash-1.5"
        self.fallback_model = "meta-llama/llama-3.1-70b-instruct"
    
    def detect_language(self, text: str) -> str:
        """Detect source language"""
        try:
            return detect(text)
        except:
            return "en"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_openrouter(self, prompt: str, model: str = None) -> str:
        """Call OpenRouter API"""
        if not self.api_key:
            raise Exception("OpenRouter API key not configured")
        
        model = model or self.primary_model
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://empire.local",
                    "X-Title": "AI Content Empire"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4000
                },
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter error: {response.status_code} - {response.text}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with fallback (Gemini -> Llama)"""
        try:
            return await self._call_openrouter(prompt, self.primary_model)
        except Exception as e:
            print(f"Primary model failed: {e}, falling back to Llama")
            return await self._call_openrouter(prompt, self.fallback_model)
    
    async def rewrite_article(
        self,
        title: str,
        content: str,
        source_language: str,
        target_language: str,
        category_map: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Rewrite and translate article using the quality-first strategy:
        1. If source != target: Rewrite in source language first
        2. Then translate to target language
        """
        
        # Build category selection prompt
        category_prompt = ""
        if category_map:
            categories_list = ", ".join([f"{k}: {v}" for k, v in category_map.items()])
            category_prompt = f"""
Select the most appropriate category for this article from the following list.
Available Categories (ID: Name): {categories_list}
Return ONLY the category ID number."""
        
        # Step 1: Rewrite in source language (if different languages)
        if source_language != target_language:
            rewrite_prompt = f"""You are an expert journalist. Rewrite this article in {source_language}.
Improve the structure, clarity, and flow while preserving all facts and key information.
Remove any promotional content or bias. Make it professional and engaging.

Original Title: {title}

Original Content:
{content}

Respond with JSON:
{{
    "rewritten_title": "improved title in {source_language}",
    "rewritten_content": "improved content in {source_language}"
}}"""
            
            try:
                rewrite_response = await self._call_llm(rewrite_prompt)
                rewrite_data = self._parse_json(rewrite_response)
                title = rewrite_data.get('rewritten_title', title)
                content = rewrite_data.get('rewritten_content', content)
            except Exception as e:
                print(f"Rewrite step failed: {e}")
        
        # Step 2: Translate and finalize
        final_prompt = f"""You are an expert content writer and translator.
{"Translate this article to " + target_language + " and " if source_language != target_language else ""}Rewrite this article to be SEO-optimized, engaging, and professional.

Source Language: {source_language}
Target Language: {target_language}

Title: {title}

Content:
{content}

{category_prompt}

Respond with JSON only:
{{
    "title": "SEO-optimized title in {target_language}",
    "content": "Full rewritten article in {target_language}, properly formatted with paragraphs",
    "meta_description": "Compelling meta description under 160 characters in {target_language}",
    "category_id": "{list(category_map.keys())[0] if category_map else 'null'}"
}}"""
        
        response = await self._call_llm(final_prompt)
        result = self._parse_json(response)
        
        return {
            "title": result.get("title", title),
            "content": result.get("content", content),
            "meta_description": result.get("meta_description", ""),
            "category_id": result.get("category_id"),
            "source_language": source_language,
            "target_language": target_language
        }
    
    async def generate_image_prompt(self, title: str, content: str) -> str:
        """Generate an image prompt from article content"""
        prompt = f"""Based on this article, create a short, descriptive image prompt for AI image generation.
The prompt should describe a photorealistic scene that represents the article's main topic.
Keep it under 100 words, focus on visual elements.

Title: {title}
Content excerpt: {content[:500]}

Respond with just the image prompt, no JSON or extra text."""
        
        return await self._call_llm(prompt)
    
    async def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """Analyze image using Vision model to check for watermarks/text"""
        try:
            # Use Gemini Flash for vision (supports images)
            prompt = f"""Analyze the image at this URL and determine if it's suitable for use as a featured image.
Image URL: {image_url}

Check for:
1. Visible watermarks
2. Text overlays
3. Logos
4. Low quality or artifacts

Respond with JSON:
{{
    "clean": true/false,
    "has_watermark": true/false,
    "has_text": true/false,
    "has_logo": true/false,
    "quality": "high/medium/low",
    "reason": "explanation"
}}"""
            
            response = await self._call_openrouter(prompt, "google/gemini-flash-1.5")
            return self._parse_json(response)
            
        except Exception as e:
            return {"clean": False, "reason": str(e)}
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response"""
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try cleaning common issues
        cleaned = text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        try:
            return json.loads(cleaned.strip())
        except:
            return {}


ai_processor = AIProcessor()
