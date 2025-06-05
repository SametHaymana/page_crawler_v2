import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from typing import List, Dict, Set, Optional
import time
import re
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebCrawler:
    """Advanced web crawler for collecting company information from websites"""
    
    def __init__(self):
        self.session = None
        self.visited_urls: Set[str] = set()
        self.collected_content: List[Dict] = []
        
    async def create_session(self):
        """Create aiohttp session with proper headers"""
        headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            headers=headers, 
            connector=connector, 
            timeout=timeout
        )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and query parameters"""
        parsed = urlparse(url)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            '',  # Remove query
            ''   # Remove fragment
        ))
        return normalized.rstrip('/')
    
    def is_valid_company_page(self, url: str, base_domain: str) -> bool:
        """Check if URL is likely to contain company information"""
        parsed = urlparse(url)
        
        # Must be same domain
        if parsed.netloc.lower() != base_domain.lower():
            return False
            
        # Skip non-relevant pages
        skip_patterns = [
            r'/blog/', r'/news/', r'/press/', r'/careers/', 
            r'/jobs/', r'/support/', r'/help/', r'/faq/',
            r'/privacy/', r'/terms/', r'/legal/', r'/sitemap/',
            r'/search/', r'/login/', r'/register/', r'/account/',
            r'\.pdf$', r'\.doc$', r'\.jpg$', r'\.png$', r'\.gif$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # Prioritize company-relevant pages
        priority_patterns = [
            r'/about', r'/company', r'/team', r'/contact',
            r'/products', r'/services', r'/solutions',
            r'/customers', r'/case-studies', r'/portfolio'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in priority_patterns) or parsed.path in ['/', '']
    
    async def fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch and parse a single page"""
        try:
            if not self.session:
                await self.create_session()
                
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract text content
                    text_content = self.extract_text_content(soup)
                    
                    # Extract links for further crawling
                    links = self.extract_links(soup, url)
                    
                    return {
                        'url': url,
                        'title': soup.title.string if soup.title else '',
                        'content': text_content,
                        'links': links,
                        'meta_description': self.extract_meta_description(soup),
                        'headings': self.extract_headings(soup)
                    }
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit content length
        if len(text) > Config.MAX_CONTENT_LENGTH:
            text = text[:Config.MAX_CONTENT_LENGTH] + "..."
        
        return text
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            normalized_url = self.normalize_url(full_url)
            if normalized_url and normalized_url.startswith(('http://', 'https://')):
                links.append(normalized_url)
        return list(set(links))  # Remove duplicates
    
    def extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        return ''
    
    def extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract all headings from the page"""
        headings = []
        for i in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{i}'):
                if heading.get_text(strip=True):
                    headings.append(heading.get_text(strip=True))
        return headings
    
    async def crawl_website(self, start_url: str, max_pages: int = None) -> List[Dict]:
        """Crawl website starting from given URL"""
        if max_pages is None:
            max_pages = Config.MAX_PAGES_PER_DOMAIN
        
        self.visited_urls.clear()
        self.collected_content.clear()
        
        try:
            await self.create_session()
            
            # Parse base domain
            base_domain = urlparse(start_url).netloc
            
            # Initialize with start URL
            urls_to_visit = [self.normalize_url(start_url)]
            
            while urls_to_visit and len(self.visited_urls) < max_pages:
                current_url = urls_to_visit.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                
                if not self.is_valid_company_page(current_url, base_domain):
                    continue
                
                logger.info(f"Crawling: {current_url}")
                
                page_data = await self.fetch_page(current_url)
                if page_data:
                    self.visited_urls.add(current_url)
                    self.collected_content.append(page_data)
                    
                    # Add new links to crawl
                    for link in page_data['links']:
                        if (link not in self.visited_urls and 
                            link not in urls_to_visit and
                            self.is_valid_company_page(link, base_domain)):
                            urls_to_visit.append(link)
                
                # Add delay between requests
                await asyncio.sleep(Config.CRAWLER_DELAY)
            
            logger.info(f"Crawling completed. Visited {len(self.visited_urls)} pages")
            return self.collected_content
            
        finally:
            await self.close_session()
    
    def get_combined_content(self) -> str:
        """Combine all collected content into a single text"""
        combined_text = ""
        for page in self.collected_content:
            combined_text += f"\n\n=== PAGE: {page['url']} ===\n"
            combined_text += f"TITLE: {page['title']}\n"
            if page['meta_description']:
                combined_text += f"DESCRIPTION: {page['meta_description']}\n"
            if page['headings']:
                combined_text += f"HEADINGS: {' | '.join(page['headings'])}\n"
            combined_text += f"CONTENT: {page['content']}\n"
        
        return combined_text 