# Design Document: Crawl4AI Web Scraping Service

## Context
This service provides a simple HTTP API for web scraping that returns LLM-ready markdown content. The implementation must strictly follow crawl4ai's official documentation (https://github.com/unclecode/crawl4ai) to leverage its AI-optimized features including BM25 filtering, clean markdown generation, and efficient browser pooling.

### Key Constraints
- **Platform Limitation**: Vercel serverless is incompatible with crawl4ai due to Playwright/Chromium dependencies (~300MB+) and browser pooling requirements
- **Deployment Target**: Railway.app chosen for Docker support, free tier availability, and ease of deployment
- **Browser Dependencies**: Requires Chromium browser installation and proper shared memory configuration
- **Async Architecture**: Must use crawl4ai's AsyncWebCrawler as recommended in official documentation

## Goals / Non-Goals

### Goals
- Provide simple REST API for URL crawling with markdown output
- Follow crawl4ai best practices and official documentation patterns
- Deploy successfully on Railway.app with Docker
- Support concurrent requests without blocking
- Handle common error cases (invalid URLs, timeouts, unreachable hosts)

### Non-Goals
- Advanced crawl4ai features (LLM extraction, CSS selectors, deep crawling) - can be added later if needed
- Authentication/authorization - public API for now
- Rate limiting or request queuing - rely on platform limits initially
- Custom markdown formatting beyond crawl4ai defaults
- Browser screenshot or PDF generation capabilities

## Decisions

### Decision 1: FastAPI Framework
**Rationale**: FastAPI provides native async support, automatic OpenAPI documentation, and is commonly used with crawl4ai in examples.

**Alternatives Considered**:
- Flask: Lacks native async support, would require additional setup
- Django: Too heavyweight for simple API service
- Raw ASGI: More control but unnecessary complexity

### Decision 2: Railway.app for Deployment
**Rationale**: 
- Supports Docker deployments with browser dependencies
- Generous free tier for testing
- Simple deployment workflow (connect GitHub repo)
- Automatic HTTPS and domain provisioning
- Better suited than Vercel for long-running processes

**Alternatives Considered**:
- Vercel: Incompatible with Playwright/Chromium requirements
- Render.com: Viable alternative but Railway has simpler Docker deployment
- Fly.io: More complex configuration, edge deployment not needed

### Decision 3: Single AsyncWebCrawler Instance
**Rationale**: Following crawl4ai documentation pattern of using async context manager for crawler lifecycle. Browser pooling is handled internally by crawl4ai.

**Implementation**:
```python
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url=url)
```

**Alternatives Considered**:
- Global crawler instance: Risk of resource leaks, harder to manage lifecycle
- Per-request crawler: Inefficient, loses browser pooling benefits

### Decision 4: Minimal Configuration Initially
**Rationale**: Start with crawl4ai defaults (headless browser, automatic markdown extraction) and add configuration options based on actual usage patterns.

**Initial Config**:
```python
browser_config = BrowserConfig(
    headless=True,
    verbose=True
)
```

**Future Extensions** (not in initial scope):
- Custom extraction strategies (CSS/XPath selectors)
- LLM-based extraction with OpenAI/Anthropic
- Proxy configuration
- Custom user agents

## Architecture

### Component Structure
```
tiny-crawl/
├── main.py              # FastAPI application and endpoints
├── crawler.py           # AsyncWebCrawler wrapper and configuration
├── models.py            # Pydantic models for requests/responses
├── config.py            # Environment variables and settings
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container configuration
├── railway.json         # Railway deployment config (optional)
└── README.md            # Documentation
```

### API Design

**POST /crawl**
- Request: `{"url": "https://example.com"}`
- Success Response (200): 
  ```json
  {
    "success": true,
    "url": "https://example.com",
    "markdown": "# Page Title\n\nContent...",
    "timestamp": "2025-12-09T12:00:00Z"
  }
  ```
- Error Response (400/502):
  ```json
  {
    "success": false,
    "url": "https://invalid",
    "error": "Invalid URL format",
    "timestamp": "2025-12-09T12:00:00Z"
  }
  ```

**GET /health**
- Response (200): `{"status": "ok"}`

### Data Flow
1. Client sends POST request with URL to `/crawl`
2. FastAPI validates request schema
3. URL validation performed (scheme, format check)
4. AsyncWebCrawler.arun() called with timeout
5. crawl4ai performs browser automation and markdown extraction
6. Response formatted with metadata and returned
7. Error handling catches timeouts, network failures, invalid URLs

## Risks / Trade-offs

### Risk 1: Browser Memory Usage
**Description**: Chromium processes can consume significant memory, potentially exceeding Railway free tier limits (512MB).

**Mitigation**: 
- Start with headless browser (lower memory footprint)
- Monitor Railway metrics and upgrade plan if needed
- Consider implementing request queuing if memory issues arise

### Risk 2: Cold Start Performance
**Description**: First request after inactivity may be slow due to browser initialization.

**Mitigation**:
- Accept initial latency as trade-off for free hosting
- Railway keeps containers warm longer than serverless platforms
- Could add keep-alive health check pings if needed

### Risk 3: crawl4ai API Changes
**Description**: crawl4ai is actively developed; API patterns may change.

**Mitigation**:
- Pin specific crawl4ai version in requirements.txt
- Follow official documentation updates
- Test upgrades in isolated environment before production

### Risk 4: Target Website Blocking
**Description**: Some websites block automated crawling or require JavaScript rendering delays.

**Mitigation**:
- crawl4ai handles JavaScript rendering by default
- Could add configurable delays if needed
- Return error response for sites that explicitly block crawlers

## Migration Plan

### Phase 1: Initial Deployment (Current Proposal)
1. Implement basic crawl endpoint with markdown output
2. Deploy to Railway.app
3. Validate functionality with common websites

### Phase 2: Enhancements (Future)
- Add configuration options (custom strategies, timeouts)
- Implement rate limiting
- Add authentication if API becomes public-facing
- Support batch crawling of multiple URLs

### Phase 3: Production Hardening (Future)
- Set up monitoring and alerting
- Implement request queuing for high load
- Add caching layer for frequently accessed URLs
- Consider dedicated crawl4ai Docker deployment

### Rollback Strategy
- Railway supports instant rollbacks to previous deployments
- Keep Docker image versioned in registry
- Minimal data state; stateless API means safe rollbacks

## Open Questions

1. **Should we implement caching for crawled content?**
   - Decision: Defer to Phase 2, evaluate based on usage patterns
   
2. **What timeout value is appropriate?**
   - Decision: Start with 30 seconds as per spec, make configurable via environment variable

3. **Should we expose crawl4ai's advanced features (CSS selectors, LLM extraction)?**
   - Decision: Not in initial scope, add as opt-in parameters in Phase 2 if requested

4. **Do we need request authentication?**
   - Decision: No authentication initially for simplicity, add if API becomes public or has abuse issues
