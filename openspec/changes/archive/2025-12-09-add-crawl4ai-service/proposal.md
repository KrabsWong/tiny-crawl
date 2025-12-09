# Change: Add Crawl4AI Web Scraping Service

## Why
Users need a simple HTTP API to crawl web pages and receive clean, LLM-ready markdown content. This service leverages crawl4ai's AI-optimized features for efficient web scraping without managing complex browser automation infrastructure.

## What Changes
- Add new Python-based HTTP service using crawl4ai library (strictly following https://github.com/unclecode/crawl4ai guidelines)
- Provide RESTful API endpoint accepting URL parameters and returning markdown-formatted content
- Configure Docker-based deployment for Railway.app platform (crawl4ai requires Playwright/Chromium, not compatible with Vercel serverless)
- Implement async crawler with browser pooling for optimal performance
- Support crawl4ai's core features: clean markdown output, BM25 filtering, and error handling

## Impact
- Affected specs: `web-crawling-api` (new capability)
- Affected code: New Python service implementation (new codebase)
- Infrastructure: Railway.app deployment with Docker configuration
- Dependencies: crawl4ai, FastAPI, Playwright, Chromium browser
