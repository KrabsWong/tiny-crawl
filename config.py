"""Configuration settings for the crawl service."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Crawler settings
    crawl_timeout: int = Field(default=30, description="Timeout for crawl operations in seconds")
    browser_headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_verbose: bool = Field(default=True, description="Enable verbose browser logging")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
