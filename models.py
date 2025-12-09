"""Pydantic models for request and response schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class CrawlRequest(BaseModel):
    """Request model for crawl endpoint."""
    url: HttpUrl = Field(..., description="URL to crawl")
    include_raw_markdown: bool = Field(
        default=False, 
        description="Include full unfiltered markdown in response"
    )
    filter_threshold: float = Field(
        default=0.48, 
        ge=0.0, 
        le=1.0, 
        description="Content filter threshold (lower = more content retained)"
    )
    min_word_threshold: int = Field(
        default=5, 
        ge=0, 
        description="Minimum words per content block"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.example.com",
                "include_raw_markdown": False,
                "filter_threshold": 0.48,
                "min_word_threshold": 5
            }
        }


class CrawlResponse(BaseModel):
    """Response model for successful crawl."""
    success: bool = Field(default=True, description="Whether the crawl was successful")
    url: str = Field(..., description="The crawled URL")
    markdown: str = Field(..., description="Filtered markdown content (core content only)")
    raw_markdown: Optional[str] = Field(
        default=None, 
        description="Full unfiltered markdown (only included if requested)"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "url": "https://www.example.com",
                "markdown": "# Example Domain\n\nThis domain is for use in illustrative examples...",
                "raw_markdown": None,
                "timestamp": "2025-12-09T12:00:00Z"
            }
        }


class CrawlErrorResponse(BaseModel):
    """Response model for failed crawl."""
    success: bool = Field(default=False, description="Whether the crawl was successful")
    url: str = Field(..., description="The requested URL")
    error: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "url": "https://invalid-url",
                "error": "Failed to crawl URL: Connection timeout",
                "timestamp": "2025-12-09T12:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(default="ok", description="Health status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok"
            }
        }
