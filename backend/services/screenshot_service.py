import os
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
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
        Download PDF or use local path and render specific page as PNG using PyMuPDF (fitz).
        """
        filename_hash = hashlib.md5(f"{doc_url}_{page_number}".encode()).hexdigest()
        output_path = os.path.join(self.output_dir, f"{filename_hash}.png")
        
        if os.path.exists(output_path):
            return output_path
            
        temp_pdf = None
        pdf_path = None
        
        try:
            if doc_url.startswith("local://"):
                base_url = doc_url.split('#')[0]
                filename = base_url.replace("local://", "")
                pdf_path = os.path.join("data", "nigeria_laws", filename)
            else:
                temp_pdf = f"/tmp/{filename_hash}.pdf"
                pdf_path = temp_pdf
                response = requests.get(doc_url, timeout=30)
                with open(temp_pdf, 'wb') as f:
                    f.write(response.content)
            
            if not os.path.exists(pdf_path):
                print(f"PDF source not found: {pdf_path}")
                return None
                
            # PyMuPDF rendering (No Poppler needed)
            if fitz:
                doc = fitz.open(pdf_path)
                # fitz is 0-indexed, but our app is 1-indexed
                page = doc.load_page(page_number - 1)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for clarity
                pix.save(output_path)
                doc.close()
                
                if temp_pdf and os.path.exists(temp_pdf):
                    os.remove(temp_pdf)
                return output_path
            else:
                print("PyMuPDF (fitz) not installed.")
                return None
        except Exception as e:
            print(f"Screenshot Error: {e}")
            if temp_pdf and os.path.exists(temp_pdf):
                os.remove(temp_pdf)
            
        return None
