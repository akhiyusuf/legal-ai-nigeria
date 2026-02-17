import os
from pdf2image import convert_from_path
from typing import Optional
from ..core.config import settings
import requests
import hashlib

class ScreenshotService:
    """
    Renders PDF pages into images for proof.
    """
    def __init__(self, output_dir: str = settings.SCREENSHOT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_screenshot(self, doc_url: str, page_number: int) -> Optional[str]:
        """
        Download PDF or use local path and render specific page as PNG.
        """
        # 1. Check if we already have it
        filename_hash = hashlib.md5(f"{doc_url}_{page_number}".encode()).hexdigest()
        output_path = os.path.join(self.output_dir, f"{filename_hash}.png")
        
        if os.path.exists(output_path):
            return output_path
            
        # 2. Get the PDF content path
        temp_pdf = None
        pdf_path = None
        
        try:
            if doc_url.startswith("local://"):
                # Source is local, get filename and map to local data directory
                # Example: local://Constitution_1999.pdf#page=10
                base_url = doc_url.split('#')[0]
                filename = base_url.replace("local://", "")
                pdf_path = os.path.join("data", "nigeria_laws", filename)
            else:
                # 2. Download temporary PDF
                temp_pdf = f"/tmp/{filename_hash}.pdf"
                pdf_path = temp_pdf
                response = requests.get(doc_url, timeout=30)
                with open(temp_pdf, 'wb') as f:
                    f.write(response.content)
            
            if not os.path.exists(pdf_path):
                print(f"PDF source not found: {pdf_path}")
                return None
                
            # 3. Convert page (pdf2image uses poppler)
            images = convert_from_path(
                pdf_path, 
                first_page=page_number, 
                last_page=page_number,
                poppler_path=settings.POPPLER_PATH if settings.POPPLER_PATH else None
            )
            
            if images:
                images[0].save(output_path, 'PNG')
                # Clean up temp if we downloaded it
                if temp_pdf and os.path.exists(temp_pdf):
                    os.remove(temp_pdf)
                return output_path
        except Exception as e:
            print(f"Screenshot Error: {e}")
            if temp_pdf and os.path.exists(temp_pdf):
                os.remove(temp_pdf)
            
        return None
