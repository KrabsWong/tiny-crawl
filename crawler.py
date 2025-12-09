"""Crawler service using crawl4ai AsyncWebCrawler."""
import logging
import asyncio
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
        logger.info(
            f"CrawlerService initialized with headless={settings.browser_headless}, "
            f"verbose={settings.browser_verbose}"
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
            asyncio.TimeoutError: If the crawl operation times out
            Exception: For other crawl failures
        """
        timeout = timeout or settings.crawl_timeout
        logger.info(f"Starting crawl for URL: {url} with timeout: {timeout}s")
        
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
        
        try:
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
                    
        except asyncio.TimeoutError:
            logger.error(f"Crawl timeout for {url} after {timeout}s")
            raise asyncio.TimeoutError(f"Crawl operation timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Crawl error for {url}: {str(e)}")
            raise


# Global crawler service instance
crawler_service = CrawlerService()
