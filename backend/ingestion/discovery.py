import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urlparse
import logging
from ..core.config import settings

class SourceDiscovery:
    """
    Automatic discovery of authoritative legal portals for a given country.
    """
    
    # Predefined official portals for major countries
    OFFICIAL_PORTALS = {
        "united states": [
            {"name": "GovInfo", "url": "https://www.govinfo.gov/", "type": "statutes, bills"},
            {"name": "LII Cornell", "url": "https://www.law.cornell.edu/", "type": "code, regulations"},
            {"name": "Federal Register", "url": "https://www.federalregister.gov/", "type": "regulations"}
        ],
        "germany": [
            {"name": "Gesetze im Internet", "url": "https://www.gesetze-im-internet.de/", "type": "statutes"},
            {"name": "Bundesgesetzblatt", "url": "https://www.bgbl.de/", "type": "official journal"}
        ],
        "japan": [
            {"name": "e-Gov Laws", "url": "https://elaws.e-gov.go.jp/", "type": "statutes"},
            {"name": "Supreme Court of Japan", "url": "https://www.courts.go.jp/", "type": "case law"}
        ],
        "united kingdom": [
            {"name": "Legislation.gov.uk", "url": "https://www.legislation.gov.uk/", "type": "statutes"}
        ],
        "european union": [
            {"name": "EUR-Lex", "url": "https://eur-lex.europa.eu/", "type": "eu law"}
        ],
        "nigeria": [
            {"name": "National Assembly (Acts)", "url": "https://nass.gov.ng/documents/acts", "type": "acts"},
            {"name": "Federal Ministry of Justice", "url": "https://www.justice.gov.ng/", "type": "statutes"},
            {"name": "PLAC Law Repository", "url": "https://placng.org/i/laws/", "type": "acts, bills"}
        ]
    }

    def __init__(self, country: str):
        self.country = country.lower()
        self.domains = settings.DOMAIN_RESTRICTION.split(",") if settings.DOMAIN_RESTRICTION else []
        self.discovered_sources = []

    def discover(self) -> List[Dict[str, Any]]:
        """
        Main discovery logic.
        1. Check predefined list.
        2. Perform (simulated) search if needed.
        """
        # 1. Predefined lookup
        if self.country in self.OFFICIAL_PORTALS:
            self.discovered_sources.extend(self.OFFICIAL_PORTALS[self.country])
        
        # 2. Fallback search (Simulated here; in a real scenario, this would use a search API)
        if not self.discovered_sources:
            self.discovered_sources.append({
                "name": f"{self.country.capitalize()} Official Gazette Search",
                "url": f"https://www.google.com/search?q=site:.gov.{self.country[0:2]} official+gazette+laws",
                "type": "fallback"
            })
            
        # Filter by domain restriction if provided
        if self.domains:
            self.discovered_sources = [
                s for s in self.discovered_sources 
                if any(dom in s['url'] for dom in self.domains)
            ]
            
        return self.discovered_sources

    def get_crawlable_links(self, source_url: str) -> List[str]:
        """
        Basic link extraction for crawling.
        """
        links = []
        try:
            response = requests.get(source_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract links likely to contain actual laws (e.g., pdfs or detail pages)
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(ext in href.lower() for ext in ['.pdf', '/details', '/act/', '/law/']):
                    if href.startswith('/'):
                        parsed_uri = urlparse(source_url)
                        href = f"{parsed_uri.scheme}://{parsed_uri.netloc}{href}"
                    links.append(href)
        except Exception as e:
            logging.error(f"Error fetching links from {source_url}: {e}")
        return list(set(links))
