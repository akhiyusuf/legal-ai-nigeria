import os
import sys

# Add the project root to sys.path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.screenshot_service import ScreenshotService

def main():
    service = ScreenshotService()
    # Test with Constitution (assumes it exists in data/nigeria_laws/Constitution_1999_Amended.pdf)
    doc_url = "local://Constitution_1999_Amended.pdf#page=1"
    page_number = 1
    
    print(f"Generating screenshot for {doc_url} page {page_number}...")
    path = service.generate_screenshot(doc_url, page_number)
    
    if path and os.path.exists(path):
        print(f"Success! Screenshot saved to: {path}")
        print(f"File size: {os.path.getsize(path)} bytes")
    else:
        print("Failed to generate screenshot.")

if __name__ == "__main__":
    main()
