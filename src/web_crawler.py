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
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebCrawler:
    """Advanced web crawler for collecting company information from websites"""
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.collected_content: List[Dict] = []
        self.playwright = None
        self.browser = None
    
    async def create_session(self):
        """Create Playwright session and launch browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(headless=True)
    
    async def close_session(self):
        """Close Playwright session and browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
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
            logger.debug(f"Rejecting {url}: different domain ({parsed.netloc} vs {base_domain})")
            return False
            
        # Skip non-relevant pages
        skip_patterns = [
            r'/careers/', r'/jobs/', r'/support/', r'/help/', r'/faq/',
            r'/privacy/', r'/terms/', r'/legal/', r'/sitemap/',
            r'/search/', r'/login/', r'/register/', r'/account/',
            r'\.pdf$', r'\.doc$', r'\.jpg$', r'\.png$', r'\.gif$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logger.debug(f"Rejecting {url}: matches skip pattern {pattern}")
                return False
        
        # Accept any page on the same domain that doesn't match skip patterns
        # This allows crawling more pages while still avoiding irrelevant content
        logger.debug(f"Accepting {url}: valid company page")
        return True
    
    async def fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch and parse a single page using Playwright"""
        try:
            if not self.browser:
                await self.create_session()
            
            page = await self.browser.new_page(
                user_agent=Config.USER_AGENT,
                java_script_enabled=True
            )
            
            await page.goto(url, wait_until="domcontentloaded", timeout=Config.REQUEST_TIMEOUT * 1000)
            
            # Wait for dynamic content to load
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            links = await self.extract_links(page, url)
            text_content = self.extract_text_content(soup)
            
            result = {
                'url': url,
                'title': await page.title(),
                'content': text_content,
                'links': links,
                'meta_description': self.extract_meta_description(soup),
                'headings': self.extract_headings(soup)
            }
            
            await page.close()
            return result
            
        except Exception as e:
            logger.error(f"Error fetching {url} with Playwright: {str(e)}")
            if 'page' in locals() and not page.is_closed():
                await page.close()
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
    
    async def extract_links(self, page, base_url: str) -> List[str]:
        """Extract all links from the page using Playwright"""
        links = []
        
        # Use Playwright to get all href attributes
        hrefs = await page.eval_on_selector_all('a', 'nodes => nodes.map(n => n.href)')
        
        for href in hrefs:
            full_url = urljoin(base_url, href)
            normalized_url = self.normalize_url(full_url)
            if normalized_url and normalized_url.startswith(('http://', 'https://')):
                links.append(normalized_url)
        
        unique_links = list(set(links))  # Remove duplicates
        logger.debug(f"Extracted {len(unique_links)} unique links from {base_url}")
        return unique_links
    
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
                    logger.debug(f"Skipping already visited: {current_url}")
                    continue
                
                if not self.is_valid_company_page(current_url, base_domain):
                    logger.info(f"Skipping invalid page: {current_url}")
                    continue
                
                logger.info(f"Crawling: {current_url}")
                
                page_data = await self.fetch_page(current_url)
                if page_data:
                    self.visited_urls.add(current_url)
                    self.collected_content.append(page_data)
                    
                    # Add new links to crawl
                    new_links_added = 0
                    for link in page_data['links']:
                        if (link not in self.visited_urls and 
                            link not in urls_to_visit and
                            self.is_valid_company_page(link, base_domain)):
                            urls_to_visit.append(link)
                            new_links_added += 1
                    
                    logger.info(f"Found {len(page_data['links'])} links, added {new_links_added} new URLs to crawl queue")
                    logger.info(f"Queue size: {len(urls_to_visit)}, Visited: {len(self.visited_urls)}")
                else:
                    logger.warning(f"Failed to fetch page: {current_url}")
                
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