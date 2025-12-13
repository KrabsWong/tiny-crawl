"""Main FastAPI application for web crawling service."""
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from config import settings
from models import CrawlRequest, CrawlResponse, CrawlErrorResponse, HealthResponse
from crawler import crawler_service

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info("Starting Crawl4AI Web Scraping Service")
    logger.info(f"Server running on {settings.host}:{settings.port}")
    logger.info(f"Crawl timeout: {settings.crawl_timeout}s")
    logger.info(f"Max concurrent crawls: {settings.max_concurrent_crawls}, Queue timeout: {settings.queue_timeout}s")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Crawl4AI Web Scraping Service")


# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="Crawl4AI Web Scraping Service",
    description="HTTP API for web crawling using crawl4ai, returning LLM-ready markdown content",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the service is running"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with status "ok"
    """
    return HealthResponse(status="ok")


@app.post(
    "/crawl",
    response_model=CrawlResponse,
    responses={
        400: {"model": CrawlErrorResponse, "description": "Invalid URL"},
        502: {"model": CrawlErrorResponse, "description": "Crawl failed"},
    },
    summary="Crawl URL",
    description="Crawl a web page and return its content as markdown"
)
async def crawl_url(request: CrawlRequest):
    """
    Crawl a URL and return filtered markdown content.
    
    Args:
        request: CrawlRequest containing the URL and optional filter parameters
        
    Returns:
        CrawlResponse with filtered markdown content
        
    Raises:
        HTTPException: For various error conditions
    """
    url = str(request.url)
    logger.info(
        f"Received crawl request for URL: {url}, "
        f"filter_threshold: {request.filter_threshold}, "
        f"min_word_threshold: {request.min_word_threshold}"
    )
    
    try:
        # Perform the crawl with filter parameters
        result = await crawler_service.crawl_url(
            url,
            filter_threshold=request.filter_threshold,
            min_word_threshold=request.min_word_threshold
        )
        
        # Return successful response
        response = CrawlResponse(
            success=True,
            url=url,
            markdown=result["markdown"],
            raw_markdown=result["raw_markdown"] if request.include_raw_markdown else None,
            timestamp=datetime.utcnow()
        )
        logger.info(f"Successfully completed crawl for {url}")
        return response
        
    except asyncio.TimeoutError as e:
        error_msg = str(e)
        
        # Distinguish between queue timeout (503) and crawl timeout (502)
        if "Service too busy" in error_msg:
            logger.warning(f"Queue timeout for {url}: {error_msg}")
            error_response = CrawlErrorResponse(
                success=False,
                url=url,
                error=error_msg,
                timestamp=datetime.utcnow()
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=error_response.model_dump(),
                headers={"Retry-After": "60"}
            )
        else:
            logger.error(f"Crawl timeout for {url}: {error_msg}")
            error_response = CrawlErrorResponse(
                success=False,
                url=url,
                error=error_msg,
                timestamp=datetime.utcnow()
            )
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content=error_response.model_dump()
            )
        
    except Exception as e:
        logger.error(f"Crawl error for {url}: {str(e)}")
        error_response = CrawlErrorResponse(
            success=False,
            url=url,
            error=f"Failed to crawl URL: {str(e)}",
            timestamp=datetime.utcnow()
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=error_response.model_dump()
        )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors."""
    logger.error(f"Validation error: {exc}")
    error_response = CrawlErrorResponse(
        success=False,
        url="",
        error=f"Invalid request: {str(exc)}",
        timestamp=datetime.utcnow()
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False
    )
