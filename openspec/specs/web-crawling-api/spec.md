# web-crawling-api Specification

## Purpose
Provides a simple HTTP API for web scraping that returns LLM-ready markdown content. Built with crawl4ai (https://github.com/unclecode/crawl4ai) for AI-optimized web crawling with browser automation, supporting async operations, concurrent requests, and deployment to Railway.app via Docker.
## Requirements
### Requirement: HTTP Endpoint for URL Crawling
The system SHALL provide an HTTP POST endpoint that accepts a URL and returns the crawled content in markdown format.

#### Scenario: Successful URL crawl
- **WHEN** a POST request is sent to `/crawl` with a valid URL in the request body
- **THEN** the system returns HTTP 200 with the page content formatted as clean markdown

#### Scenario: Invalid URL handling
- **WHEN** a POST request is sent with an invalid or malformed URL
- **THEN** the system returns HTTP 400 with an error message describing the URL validation failure

#### Scenario: Crawl failure handling
- **WHEN** the target URL is unreachable or times out
- **THEN** the system returns HTTP 502 with an error message indicating the crawl failure reason

### Requirement: AsyncWebCrawler Integration
The system SHALL use crawl4ai's AsyncWebCrawler for all web crawling operations following official documentation patterns.

#### Scenario: Async crawler initialization
- **WHEN** the service starts
- **THEN** an AsyncWebCrawler instance is initialized with proper browser configuration

#### Scenario: Markdown extraction
- **WHEN** a URL is successfully crawled
- **THEN** the result.markdown property from crawl4ai contains the LLM-ready formatted content

### Requirement: Browser Configuration
The system SHALL configure the browser with headless mode and optimized settings as recommended by crawl4ai documentation.

#### Scenario: Headless browser setup
- **WHEN** the crawler is initialized
- **THEN** BrowserConfig is set with headless=True and appropriate verbosity settings

#### Scenario: Browser resource cleanup
- **WHEN** a crawl operation completes or fails
- **THEN** browser resources are properly released using async context managers

### Requirement: Response Format
The system SHALL return crawl results in a JSON response containing the markdown content and metadata.

#### Scenario: Successful response structure
- **WHEN** a crawl succeeds
- **THEN** the response JSON contains fields: "success": true, "url": <requested_url>, "markdown": <content>, "timestamp": <iso8601_time>

#### Scenario: Error response structure
- **WHEN** a crawl fails
- **THEN** the response JSON contains fields: "success": false, "url": <requested_url>, "error": <error_message>, "timestamp": <iso8601_time>

### Requirement: Railway.app Deployment
The system SHALL be deployable to Railway.app using Docker with all necessary dependencies included.

#### Scenario: Docker container configuration
- **WHEN** the service is containerized
- **THEN** the Dockerfile includes crawl4ai installation, Playwright setup, and Chromium browser installation

#### Scenario: Railway deployment readiness
- **WHEN** deployed to Railway.app
- **THEN** the service exposes the configured port and responds to health checks

### Requirement: Health Check Endpoint
The system SHALL provide a health check endpoint for monitoring service availability.

#### Scenario: Health check success
- **WHEN** a GET request is sent to `/health`
- **THEN** the system returns HTTP 200 with status "ok"

### Requirement: Request Timeout Handling
The system SHALL implement timeouts for crawl operations to prevent indefinite hanging.

#### Scenario: Crawl timeout enforcement
- **WHEN** a crawl operation exceeds 30 seconds
- **THEN** the operation is cancelled and an error response is returned with timeout message

### Requirement: Concurrent Request Handling
The system SHALL support concurrent crawl requests using FastAPI's async capabilities.

#### Scenario: Multiple simultaneous requests
- **WHEN** multiple clients send crawl requests concurrently
- **THEN** each request is processed asynchronously without blocking others

