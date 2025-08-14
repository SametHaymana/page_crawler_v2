import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
import validators
import logging
from datetime import datetime
import concurrent.futures
from functools import partial

from web_crawler import WebCrawler
from company_extractor_agent import CompanyExtractorAgent
from database import CrawlerDatabase
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PageCrawlerService:
    """Main service for crawling websites and extracting company information"""
    
    def __init__(self):
        self.crawler = WebCrawler()
        self.extractor_agent = CompanyExtractorAgent()
        self.database = CrawlerDatabase()
        self.processing_history: List[Dict] = []
        self._agent_pool = None
    
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
        progress_callback=None,
        extractor_agent: Optional[CompanyExtractorAgent] = None
    ) -> Dict[str, Any]:
        """
        Main method to process a company website and extract structured information
        
        Args:
            url: The company website URL to analyze
            max_pages: Maximum number of pages to crawl (optional)
            progress_callback: Callback function for progress updates (optional)
            extractor_agent: Optional specific extractor agent to use (for parallel processing)
            
        Returns:
            Dictionary containing crawling results and extracted company information
        """
        start_time = time.time()
        
        # Use provided agent or default instance
        agent = extractor_agent or self.extractor_agent
        
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
            
            # Create a new crawler instance for each URL to avoid conflicts
            crawler = WebCrawler()
            
            crawled_data = await crawler.crawl_website(
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
            combined_content = crawler.get_combined_content()
            
            if not combined_content.strip():
                raise Exception("No text content was extracted from crawled pages")
            
            logger.info(f"Extracted {len(combined_content)} characters of content for analysis")
            
            # Use Agno agent to extract structured information
            extracted_data = agent.extract_company_info(combined_content)
            
            if not extracted_data:
                raise Exception("Failed to extract company information from website content")
            
            # Validate the extraction result
            if not agent.validate_extraction_result(extracted_data):
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
            
            # Save to database
            try:
                self.database.save_processing_result(result)
                logger.info(f"Saved processing result to database for {url}")
            except Exception as db_error:
                logger.error(f"Failed to save to database: {str(db_error)}")
            
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
    
    def _initialize_agent_pool(self, pool_size: int = None) -> List[CompanyExtractorAgent]:
        """Initialize or get the agent pool"""
        if self._agent_pool is None:
            pool_size = pool_size or Config.MAX_PARALLEL_PROCESSES
            self._agent_pool = CompanyExtractorAgent.create_agent_pool(pool_size)
            logger.info(f"Initialized agent pool with {len(self._agent_pool)} agents")
        return self._agent_pool
    
    def _process_website_sync(self, url: str, max_pages: int, agent: CompanyExtractorAgent) -> Dict[str, Any]:
        """
        Process a website synchronously (for use in thread pool)
        
        Args:
            url: Website URL to process
            max_pages: Maximum pages to crawl
            agent: CompanyExtractorAgent instance to use
            
        Returns:
            Processing result dictionary
        """
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Process the website
            result = loop.run_until_complete(
                self.process_company_website(
                    url=url,
                    max_pages=max_pages,
                    extractor_agent=agent
                )
            )
            
            # Clean up
            loop.close()
            
            return result
        except Exception as e:
            logger.error(f"Error in _process_website_sync for {url}: {str(e)}")
            return {
                'success': False,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'processing_time': 0,
                'pages_crawled': 0,
                'company_data': None,
                'error': f"Thread processing error: {str(e)}",
                'crawling_summary': None
            }
    
    def _process_batch_parallel(self, urls: List[str], max_pages: int) -> List[Dict[str, Any]]:
        """
        Process a batch of websites in parallel using thread pool
        
        Args:
            urls: List of website URLs to process
            max_pages: Maximum pages to crawl per website
            
        Returns:
            List of processing results
        """
        # Initialize agent pool if needed
        agents = self._initialize_agent_pool()
        
        # Create a thread pool
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
            # Submit tasks
            future_to_url = {}
            for i, url in enumerate(urls):
                # Use modulo to cycle through available agents
                agent = agents[i % len(agents)]
                future = executor.submit(
                    self._process_website_sync,
                    url=url,
                    max_pages=max_pages,
                    agent=agent
                )
                future_to_url[future] = url
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed processing {url} in parallel mode")
                except Exception as e:
                    logger.error(f"Exception processing {url} in parallel mode: {str(e)}")
                    results.append({
                        'success': False,
                        'url': url,
                        'timestamp': datetime.now().isoformat(),
                        'processing_time': 0,
                        'pages_crawled': 0,
                        'company_data': None,
                        'error': f"Parallel processing error: {str(e)}",
                        'crawling_summary': None
                    })
        
        return results
    
    async def batch_process_websites(
        self, 
        urls: List[str], 
        max_pages_per_site: Optional[int] = None,
        progress_callback=None,
        parallel: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple websites in batch
        
        Args:
            urls: List of website URLs to process
            max_pages_per_site: Maximum pages to crawl per website
            progress_callback: Callback for progress updates
            parallel: Override config setting for parallel processing
            
        Returns:
            List of processing results for each website
        """
        results = []
        total_urls = len(urls)
        max_pages = max_pages_per_site or Config.MAX_PAGES_PER_DOMAIN
        
        # Determine if we should use parallel processing
        use_parallel = parallel if parallel is not None else Config.PARALLEL_PROCESSING_ENABLED
        
        if progress_callback:
            progress_callback(f"Starting batch processing of {total_urls} websites...", 5)
        
        if use_parallel and total_urls > 1:
            logger.info(f"Using parallel processing for {total_urls} websites")
            if progress_callback:
                progress_callback(f"Using parallel processing with {Config.MAX_PARALLEL_PROCESSES} agents", 10)
            
            # Process in batches to avoid overwhelming the system
            batch_size = min(Config.BATCH_SIZE, total_urls)
            total_batches = (total_urls + batch_size - 1) // batch_size  # Ceiling division
            
            processed_count = 0
            for batch_index in range(total_batches):
                start_idx = batch_index * batch_size
                end_idx = min(start_idx + batch_size, total_urls)
                batch_urls = urls[start_idx:end_idx]
                
                if progress_callback:
                    batch_progress = int(20 + (70 * batch_index / total_batches))
                    progress_callback(f"Processing batch {batch_index+1}/{total_batches} ({len(batch_urls)} websites)", batch_progress)
                
                # Process this batch in parallel
                batch_results = self._process_batch_parallel(batch_urls, max_pages)
                results.extend(batch_results)
                
                processed_count += len(batch_urls)
                if progress_callback:
                    batch_complete_progress = int(20 + (70 * processed_count / total_urls))
                    progress_callback(f"Completed {processed_count}/{total_urls} websites", batch_complete_progress)
        else:
            # Sequential processing
            logger.info(f"Using sequential processing for {total_urls} websites")
            
            for i, url in enumerate(urls):
                try:
                    if progress_callback:
                        progress_callback(f"Processing website {i+1}/{total_urls}: {url}", 
                                        int(20 + (70 * i / total_urls)))
                    
                    result = await self.process_company_website(
                        url=url,
                        max_pages=max_pages
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
    
    # Database access methods
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies from database"""
        return self.database.get_all_companies()
    
    def get_company_details(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed company information from database"""
        return self.database.get_company_details(company_id)
    
    def search_companies(self, query: str) -> List[Dict[str, Any]]:
        """Search companies in database"""
        return self.database.search_companies(query)
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.database.get_statistics()
    
    def get_database_processing_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get processing results from database"""
        return self.database.get_processing_results(limit)
    
    def delete_company(self, company_id: str) -> bool:
        """Delete a company from database"""
        return self.database.delete_company(company_id)
    
    def export_database_data(self) -> Dict[str, Any]:
        """Export all database data"""
        return self.database.export_data() 