"""Crawler service using crawl4ai AsyncWebCrawler."""
import logging
import asyncio
import time
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from config import settings

logger = logging.getLogger(__name__)


class CrawlerService:
    """Service for web crawling using crawl4ai."""
    
    def __init__(self):
        """Initialize the crawler service."""
        self.browser_config = BrowserConfig(
            headless=settings.browser_headless,
            verbose=settings.browser_verbose,
        )
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_crawls)
        logger.info(
            f"CrawlerService initialized with headless={settings.browser_headless}, "
            f"verbose={settings.browser_verbose}, "
            f"max_concurrent_crawls={settings.max_concurrent_crawls}"
        )
    
    async def crawl_url(
        self, 
        url: str, 
        timeout: Optional[int] = None,
        filter_threshold: float = 0.48,
        min_word_threshold: int = 5
    ) -> dict:
        """
        Crawl a URL and return filtered markdown content.
        
        Args:
            url: The URL to crawl
            timeout: Optional timeout in seconds (defaults to settings.crawl_timeout)
            filter_threshold: PruningContentFilter threshold (0.0-1.0, lower = more content)
            min_word_threshold: Minimum words per content block
            
        Returns:
            dict with 'markdown' (filtered) and 'raw_markdown' (full) content
            
        Raises:
            asyncio.TimeoutError: If the crawl operation or queue wait times out
            Exception: For other crawl failures
        """
        timeout = timeout or settings.crawl_timeout
        queue_timeout = settings.queue_timeout
        logger.info(f"Request queued for URL: {url}, waiting for available slot")
        
        queue_start = time.time()
        
        try:
            # Wait for available slot with timeout
            await asyncio.wait_for(
                self.semaphore.acquire(),
                timeout=queue_timeout
            )
        except asyncio.TimeoutError:
            wait_time = time.time() - queue_start
            logger.warning(f"Request timed out in queue for URL: {url} after {wait_time:.1f}s")
            raise asyncio.TimeoutError(f"Service too busy, please retry later")
        
        queue_wait_time = time.time() - queue_start
        logger.info(f"Request acquired slot for URL: {url} after {queue_wait_time:.1f}s")
        
        try:
            # Configure content filter for core content extraction
            prune_filter = PruningContentFilter(
                threshold=filter_threshold,
                threshold_type="dynamic",
                min_word_threshold=min_word_threshold
            )
            md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
            
            # Configure crawl with excluded tags and markdown generator
            run_config = CrawlerRunConfig(
                excluded_tags=['nav', 'header', 'footer', 'aside', 'form'],
                markdown_generator=md_generator
            )
            
            logger.info(f"Starting crawl for URL: {url} with timeout: {timeout}s")
            
            # Use async context manager as recommended by crawl4ai documentation
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                # Perform the crawl with timeout
                result = await asyncio.wait_for(
                    crawler.arun(url=url, config=run_config),
                    timeout=timeout
                )
                
                if result.success:
                    fit_markdown = result.markdown.fit_markdown
                    raw_markdown = result.markdown.raw_markdown
                    logger.info(
                        f"Successfully crawled {url}, "
                        f"fit_markdown length: {len(fit_markdown)}, "
                        f"raw_markdown length: {len(raw_markdown)}"
                    )
                    return {
                        "markdown": fit_markdown,
                        "raw_markdown": raw_markdown,
                        "success": True
                    }
                else:
                    error_msg = result.error_message or "Unknown error"
                    logger.error(f"Crawl failed for {url}: {error_msg}")
                    raise Exception(f"Crawl failed: {error_msg}")
                    
        except asyncio.TimeoutError as e:
            # Check if it's a queue timeout or crawl timeout
            if "Service too busy" in str(e):
                raise
            logger.error(f"Crawl timeout for {url} after {timeout}s")
            raise asyncio.TimeoutError(f"Crawl operation timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Crawl error for {url}: {str(e)}")
            raise
        finally:
            # Always release the semaphore slot
            self.semaphore.release()
            logger.debug(f"Released crawl slot for URL: {url}")


# Global crawler service instance
crawler_service = CrawlerService()
