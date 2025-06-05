import asyncio
import time
from typing import Dict, Any, Optional, List
import validators
import logging
from datetime import datetime

from web_crawler import WebCrawler
from company_extractor_agent import CompanyExtractorAgent
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PageCrawlerService:
    """Main service for crawling websites and extracting company information"""
    
    def __init__(self):
        self.crawler = WebCrawler()
        self.extractor_agent = CompanyExtractorAgent()
        self.processing_history: List[Dict] = []
    
    def validate_url(self, url: str) -> bool:
        """Validate if the provided URL is valid"""
        try:
            return validators.url(url) is True
        except Exception:
            return False
    
    async def process_company_website(
        self, 
        url: str, 
        max_pages: Optional[int] = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Main method to process a company website and extract structured information
        
        Args:
            url: The company website URL to analyze
            max_pages: Maximum number of pages to crawl (optional)
            progress_callback: Callback function for progress updates (optional)
            
        Returns:
            Dictionary containing crawling results and extracted company information
        """
        start_time = time.time()
        
        # Initialize result structure
        result = {
            'success': False,
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'processing_time': 0,
            'pages_crawled': 0,
            'company_data': None,
            'error': None,
            'crawling_summary': None
        }
        
        try:
            # Step 1: Validate URL
            if not self.validate_url(url):
                raise ValueError(f"Invalid URL provided: {url}")
            
            if progress_callback:
                progress_callback("Validating URL...", 10)
            
            logger.info(f"Starting to process company website: {url}")
            
            # Step 2: Crawl website
            if progress_callback:
                progress_callback("Crawling website pages...", 20)
            
            crawled_data = await self.crawler.crawl_website(
                start_url=url,
                max_pages=max_pages or Config.MAX_PAGES_PER_DOMAIN
            )
            
            if not crawled_data:
                raise Exception("No content was successfully crawled from the website")
            
            result['pages_crawled'] = len(crawled_data)
            result['crawling_summary'] = self._create_crawling_summary(crawled_data)
            
            if progress_callback:
                progress_callback(f"Crawled {len(crawled_data)} pages. Extracting information...", 60)
            
            # Step 3: Extract company information using Agno agent
            combined_content = self.crawler.get_combined_content()
            
            if not combined_content.strip():
                raise Exception("No text content was extracted from crawled pages")
            
            logger.info(f"Extracted {len(combined_content)} characters of content for analysis")
            
            # Use Agno agent to extract structured information
            extracted_data = self.extractor_agent.extract_company_info(combined_content)
            
            if not extracted_data:
                raise Exception("Failed to extract company information from website content")
            
            # Validate the extraction result
            if not self.extractor_agent.validate_extraction_result(extracted_data):
                logger.warning("Extraction result validation failed, but continuing with partial data")
            
            result['company_data'] = extracted_data
            result['success'] = True
            
            if progress_callback:
                progress_callback("Extraction completed successfully!", 100)
            
            logger.info(f"Successfully processed {url} - extracted information for {extracted_data.get('company_info', {}).get('name', 'Unknown Company')}")
            
        except Exception as e:
            error_msg = f"Error processing {url}: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            
            if progress_callback:
                progress_callback(f"Error: {str(e)}", 100)
        
        finally:
            # Calculate processing time
            result['processing_time'] = round(time.time() - start_time, 2)
            
            # Add to processing history
            self.processing_history.append(result)
            
            # Keep only last 100 processed items in history
            if len(self.processing_history) > 100:
                self.processing_history = self.processing_history[-100:]
        
        return result
    
    def _create_crawling_summary(self, crawled_data: List[Dict]) -> Dict[str, Any]:
        """Create a summary of the crawling process"""
        summary = {
            'total_pages': len(crawled_data),
            'pages_with_content': sum(1 for page in crawled_data if page.get('content', '').strip()),
            'total_content_length': sum(len(page.get('content', '')) for page in crawled_data),
            'pages_crawled': []
        }
        
        for page in crawled_data:
            page_info = {
                'url': page['url'],
                'title': page.get('title', '')[:100] + ('...' if len(page.get('title', '')) > 100 else ''),
                'content_length': len(page.get('content', '')),
                'headings_count': len(page.get('headings', [])),
                'links_count': len(page.get('links', []))
            }
            summary['pages_crawled'].append(page_info)
        
        return summary
    
    def get_processing_history(self) -> List[Dict]:
        """Get the history of processed websites"""
        return self.processing_history.copy()
    
    def get_latest_result(self) -> Optional[Dict]:
        """Get the most recent processing result"""
        return self.processing_history[-1] if self.processing_history else None
    
    def clear_history(self):
        """Clear the processing history"""
        self.processing_history.clear()
        logger.info("Processing history cleared")
    
    async def batch_process_websites(
        self, 
        urls: List[str], 
        max_pages_per_site: Optional[int] = None,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple websites in batch
        
        Args:
            urls: List of website URLs to process
            max_pages_per_site: Maximum pages to crawl per website
            progress_callback: Callback for progress updates
            
        Returns:
            List of processing results for each website
        """
        results = []
        total_urls = len(urls)
        
        for i, url in enumerate(urls):
            try:
                if progress_callback:
                    progress_callback(f"Processing website {i+1}/{total_urls}: {url}", 
                                    int((i / total_urls) * 90))
                
                result = await self.process_company_website(
                    url=url,
                    max_pages=max_pages_per_site
                )
                results.append(result)
                
                # Add delay between processing websites to be respectful
                if i < total_urls - 1:  # Don't delay after the last URL
                    await asyncio.sleep(2)
                    
            except Exception as e:
                error_result = {
                    'success': False,
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': 0,
                    'pages_crawled': 0,
                    'company_data': None,
                    'error': f"Batch processing error: {str(e)}",
                    'crawling_summary': None
                }
                results.append(error_result)
                logger.error(f"Error in batch processing {url}: {str(e)}")
        
        if progress_callback:
            progress_callback(f"Batch processing completed! Processed {len(results)} websites", 100)
        
        return results
    
    def export_results_to_json(self, results: List[Dict], filename: str = None) -> str:
        """
        Export processing results to JSON file
        
        Args:
            results: List of processing results to export
            filename: Optional filename, if not provided, generates timestamp-based name
            
        Returns:
            The filename of the exported file
        """
        import json
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"company_extraction_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results exported to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            raise 