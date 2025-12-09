"""Crawler service using crawl4ai AsyncWebCrawler."""
import logging
import asyncio
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
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
        logger.info(
            f"CrawlerService initialized with headless={settings.browser_headless}, "
            f"verbose={settings.browser_verbose}"
        )
    
    async def crawl_url(self, url: str, timeout: Optional[int] = None) -> dict:
        """
        Crawl a URL and return markdown content.
        
        Args:
            url: The URL to crawl
            timeout: Optional timeout in seconds (defaults to settings.crawl_timeout)
            
        Returns:
            dict with 'markdown' key containing the extracted content
            
        Raises:
            asyncio.TimeoutError: If the crawl operation times out
            Exception: For other crawl failures
        """
        timeout = timeout or settings.crawl_timeout
        logger.info(f"Starting crawl for URL: {url} with timeout: {timeout}s")
        
        try:
            # Use async context manager as recommended by crawl4ai documentation
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                # Perform the crawl with timeout
                result = await asyncio.wait_for(
                    crawler.arun(url=url),
                    timeout=timeout
                )
                
                if result.success:
                    logger.info(f"Successfully crawled {url}, markdown length: {len(result.markdown)}")
                    return {
                        "markdown": result.markdown,
                        "success": True
                    }
                else:
                    error_msg = result.error_message or "Unknown error"
                    logger.error(f"Crawl failed for {url}: {error_msg}")
                    raise Exception(f"Crawl failed: {error_msg}")
                    
        except asyncio.TimeoutError:
            logger.error(f"Crawl timeout for {url} after {timeout}s")
            raise asyncio.TimeoutError(f"Crawl operation timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Crawl error for {url}: {str(e)}")
            raise


# Global crawler service instance
crawler_service = CrawlerService()
