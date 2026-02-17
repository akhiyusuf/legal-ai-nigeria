import requests
from bs4 import BeautifulSoup
import os
import sys
from urllib.parse import urljoin, urlparse

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ingestion.discovery import SourceDiscovery

def download_file(url, folder):
    local_filename = os.path.join(folder, os.path.basename(urlparse(url).path))
    if os.path.exists(local_filename):
        print(f"File {local_filename} already exists, skipping.")
        return local_filename
    
    print(f"Downloading {url}...")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def fetch_links_from_plac(url):
    """
    Specifically for PLAC's laws repository.
    """
    links = []
    try:
        response = requests.get(url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        # PLAC often lists laws in a table or list
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.pdf'):
                links.append(urljoin(url, href))
    except Exception as e:
        print(f"Error fetching from PLAC: {e}")
    return list(set(links))

def main():
    country = "nigeria"
    discovery = SourceDiscovery(country)
    sources = discovery.discover()
    
    download_folder = "data/nigeria_laws"
    os.makedirs(download_folder, exist_ok=True)
    
    all_pdf_links = []
    
    print(f"Discovering sources for {country}...")
    for source in sources:
        print(f"Found source: {source['name']} ({source['url']})")
        if "placng.org" in source['url']:
            links = fetch_links_from_plac(source['url'])
            all_pdf_links.extend(links)
        else:
            links = discovery.get_crawlable_links(source['url'])
            all_pdf_links.extend([l for l in links if l.endswith('.pdf')])
            
    print(f"Found {len(all_pdf_links)} PDF links. Starting download (Top 10 for demo purposes)...")
    
    # Downloading top 10 for now to avoid huge wait times
    for link in all_pdf_links[:10]:
        download_file(link, download_folder)

if __name__ == "__main__":
    main()
