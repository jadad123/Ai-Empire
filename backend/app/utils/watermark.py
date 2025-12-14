from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import Optional, Tuple
import httpx


class Watermarker:
    def __init__(self, font_size: int = 24, opacity: int = 128):
        self.font_size = font_size
        self.opacity = opacity  # 0-255, where 128 is semi-transparent
    
    async def apply_watermark(
        self,
        image_data: bytes,
        watermark_text: str,
        position: str = "bottom-right"
    ) -> bytes:
        """
        Apply semi-transparent text watermark to image.
        Position: 'bottom-right', 'bottom-left', 'top-right', 'top-left', 'center'
        """
        # Open image
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create transparent layer for watermark
        watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", self.font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.font_size)
            except:
                font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position
        padding = 20
        img_width, img_height = img.size
        
        positions = {
            "bottom-right": (img_width - text_width - padding, img_height - text_height - padding),
            "bottom-left": (padding, img_height - text_height - padding),
            "top-right": (img_width - text_width - padding, padding),
            "top-left": (padding, padding),
            "center": ((img_width - text_width) // 2, (img_height - text_height) // 2)
        }
        
        x, y = positions.get(position, positions["bottom-right"])
        
        # Draw shadow for better visibility
        shadow_offset = 2
        draw.text(
            (x + shadow_offset, y + shadow_offset),
            watermark_text,
            font=font,
            fill=(0, 0, 0, self.opacity // 2)
        )
        
        # Draw watermark text
        draw.text(
            (x, y),
            watermark_text,
            font=font,
            fill=(255, 255, 255, self.opacity)
        )
        
        # Composite the watermark layer onto the original image
        watermarked = Image.alpha_composite(img, watermark_layer)
        
        # Convert back to RGB for saving as JPEG
        watermarked_rgb = watermarked.convert('RGB')
        
        # Save to bytes
        output = BytesIO()
        watermarked_rgb.save(output, format='JPEG', quality=90)
        return output.getvalue()
    
    async def apply_watermark_from_url(
        self,
        image_url: str,
        watermark_text: str,
        position: str = "bottom-right"
    ) -> Optional[bytes]:
        """Download image and apply watermark"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30)
                image_data = response.content
            
            return await self.apply_watermark(image_data, watermark_text, position)
        except Exception as e:
            print(f"Watermark error: {e}")
            return None


watermarker = Watermarker()
