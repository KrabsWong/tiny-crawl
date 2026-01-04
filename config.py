"""Configuration settings for the crawl service."""
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Crawler settings
    crawl_timeout: int = Field(default=60, description="Timeout for crawl operations in seconds")
    browser_headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_verbose: bool = Field(default=True, description="Enable verbose browser logging")
    max_concurrent_crawls: int = Field(default=1, description="Maximum concurrent crawl operations")
    queue_timeout: int = Field(default=60, description="Timeout for waiting in queue in seconds")
    
    # Anti-bot detection settings
    use_stealth: bool = Field(default=True, description="Enable stealth mode to bypass bot detection")
    browser_type: str = Field(default="undetected", description="Browser type: 'chromium', 'firefox', 'webkit', or 'undetected'")
    proxy_server: Optional[str] = Field(default=None, description="Proxy server URL (e.g., http://proxy.example.com:8080)")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    @field_validator('max_concurrent_crawls')
    @classmethod
    def validate_max_concurrent_crawls(cls, v: int) -> int:
        """Ensure max_concurrent_crawls is at least 1."""
        if v < 1:
            logger.warning(
                f"MAX_CONCURRENT_CRAWLS={v} is less than 1, setting to minimum of 1"
            )
            return 1
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env file


# Global settings instance
settings = Settings()
