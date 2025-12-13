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
The system SHALL use crawl4ai's AsyncWebCrawler for all web crawling operations following official documentation patterns, with semaphore-based concurrency control.

#### Scenario: Async crawler initialization with semaphore
- **WHEN** the service starts
- **THEN** an AsyncWebCrawler instance is initialized with proper browser configuration
- **AND** a semaphore is created with limit from `MAX_CONCURRENT_CRAWLS`

#### Scenario: Semaphore-wrapped crawl execution
- **WHEN** a crawl operation is initiated
- **THEN** the system acquires a semaphore slot before creating AsyncWebCrawler
- **AND** releases the slot after crawler context manager exits

### Requirement: Browser Configuration
The system SHALL configure the browser with headless mode and optimized settings as recommended by crawl4ai documentation.

#### Scenario: Headless browser setup
- **WHEN** the crawler is initialized
- **THEN** BrowserConfig is set with headless=True and appropriate verbosity settings

#### Scenario: Browser resource cleanup
- **WHEN** a crawl operation completes or fails
- **THEN** browser resources are properly released using async context managers

### Requirement: Response Format
The system SHALL return crawl results in a JSON response containing the filtered markdown content and metadata, including queue timeout errors.

#### Scenario: Queue timeout error response structure
- **WHEN** a request exceeds the queue timeout
- **THEN** the response JSON contains fields: "success": false, "url": <requested_url>, "error": "Service too busy, please retry later", "timestamp": <iso8601_time>
- **AND** the HTTP status code is 503 Service Unavailable

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
The system SHALL implement timeouts for both queue waiting and crawl operations to prevent indefinite hanging.

#### Scenario: Crawl timeout enforcement (existing)
- **WHEN** a crawl operation exceeds 30 seconds
- **THEN** the operation is cancelled and an error response is returned with timeout message

#### Scenario: Queue timeout enforcement (new)
- **WHEN** a request waits in queue longer than `QUEUE_TIMEOUT` seconds
- **THEN** the request is rejected with HTTP 503
- **AND** the error message indicates service is too busy

#### Scenario: Total request time calculation
- **GIVEN** a request waits W seconds in queue and crawls for C seconds
- **WHEN** the request completes
- **THEN** the total request time is W + C seconds
- **AND** both timeouts are enforced independently

### Requirement: Concurrent Request Handling
The system SHALL support concurrent crawl requests using FastAPI's async capabilities.

#### Scenario: Multiple simultaneous requests
- **WHEN** multiple clients send crawl requests concurrently
- **THEN** each request is processed asynchronously without blocking others

### Requirement: Content Filtering for Core Content Extraction
The system SHALL use crawl4ai's PruningContentFilter to automatically extract core page content and filter out navigation, headers, footers, and other boilerplate elements.

#### Scenario: Default content filtering
- **WHEN** a POST request is sent to `/crawl` with a valid URL
- **THEN** the system returns filtered markdown (`fit_markdown`) with navigation, header, footer, and sidebar content removed
- **AND** the response contains the core/main content of the page

#### Scenario: Boilerplate HTML tag exclusion
- **WHEN** a page is crawled
- **THEN** HTML elements with tags `nav`, `header`, `footer`, `aside`, and `form` are excluded before content processing

#### Scenario: Raw markdown access
- **WHEN** a POST request includes `include_raw_markdown: true`
- **THEN** the response includes an additional `raw_markdown` field containing the full unfiltered page content

### Requirement: Configurable Filter Parameters
The system SHALL allow optional parameters to customize content filtering behavior.

#### Scenario: Custom filter threshold
- **WHEN** a POST request includes `filter_threshold` parameter (0.0 to 1.0)
- **THEN** the PruningContentFilter uses that threshold value (lower values retain more content)

#### Scenario: Custom word threshold
- **WHEN** a POST request includes `min_word_threshold` parameter (integer >= 0)
- **THEN** content blocks with fewer words than the threshold are excluded

#### Scenario: Default parameter values
- **WHEN** no filter parameters are provided
- **THEN** the system uses default values: `filter_threshold=0.48`, `min_word_threshold=5`

### Requirement: Concurrent Crawl Limiting
The system SHALL limit the number of simultaneously executing crawl operations to prevent memory exhaustion.

#### Scenario: Concurrency limit enforcement
- **GIVEN** the service is configured with `MAX_CONCURRENT_CRAWLS=3`
- **WHEN** 5 concurrent POST requests are sent to `/crawl` with valid URLs
- **THEN** at most 3 crawl operations execute simultaneously
- **AND** the remaining 2 requests wait for available slots

#### Scenario: Semaphore-based queue management
- **GIVEN** all concurrent crawl slots are occupied
- **WHEN** a new crawl request arrives
- **THEN** the request waits to acquire a semaphore slot
- **AND** proceeds when a slot becomes available (existing crawl completes)

#### Scenario: Slot release after crawl completion
- **GIVEN** a crawl operation completes successfully
- **WHEN** the response is returned to the client
- **THEN** the semaphore slot is released
- **AND** the next queued request (if any) acquires the slot

#### Scenario: Slot release after crawl failure
- **GIVEN** a crawl operation fails with an error
- **WHEN** the error response is returned
- **THEN** the semaphore slot is released even on failure
- **AND** the next queued request proceeds

### Requirement: Configurable Concurrency Limit
The system SHALL allow configuration of the maximum concurrent crawl operations via environment variable.

#### Scenario: Default concurrency limit
- **WHEN** no `MAX_CONCURRENT_CRAWLS` environment variable is set
- **THEN** the system uses a default limit of 3 concurrent crawls

#### Scenario: Custom concurrency limit
- **GIVEN** `MAX_CONCURRENT_CRAWLS` is set to 5
- **WHEN** the service starts
- **THEN** the system allows up to 5 simultaneous crawl operations

#### Scenario: Minimum concurrency limit validation
- **GIVEN** `MAX_CONCURRENT_CRAWLS` is set to a value less than 1
- **WHEN** the service starts
- **THEN** the system uses a minimum limit of 1 to ensure forward progress

### Requirement: Queue Timeout Handling
The system SHALL timeout requests that wait too long for an available crawl slot.

#### Scenario: Queue timeout expiration
- **GIVEN** all crawl slots are occupied and `QUEUE_TIMEOUT=60` seconds
- **WHEN** a request waits in queue for more than 60 seconds
- **THEN** the system returns HTTP 503 Service Unavailable
- **AND** the error message is "Service too busy, please retry later"
- **AND** the timestamp field reflects when the timeout occurred

#### Scenario: Successful queue wait within timeout
- **GIVEN** a request is queued with `QUEUE_TIMEOUT=60` seconds
- **WHEN** a crawl slot becomes available after 10 seconds
- **THEN** the request acquires the slot and proceeds normally
- **AND** no queue timeout error occurs

#### Scenario: Configurable queue timeout
- **WHEN** `QUEUE_TIMEOUT` environment variable is set to 30
- **THEN** requests timeout after waiting 30 seconds in queue

#### Scenario: Default queue timeout
- **WHEN** no `QUEUE_TIMEOUT` environment variable is set
- **THEN** the system uses a default timeout of 60 seconds

### Requirement: Request Queue Metrics Logging
The system SHALL log queue-related events to enable monitoring and troubleshooting.

#### Scenario: Queue wait start logging
- **WHEN** a request begins waiting for an available crawl slot
- **THEN** the system logs "Request queued for URL: {url}, waiting for available slot"
- **AND** the log level is INFO

#### Scenario: Queue wait completion logging
- **WHEN** a queued request acquires a slot after waiting
- **THEN** the system logs "Request acquired slot for URL: {url} after {wait_time}s"
- **AND** the log level is INFO

#### Scenario: Queue timeout logging
- **WHEN** a request times out while waiting in queue
- **THEN** the system logs "Request timed out in queue for URL: {url} after {timeout}s"
- **AND** the log level is WARNING

### Requirement: Memory-Efficient Request Processing
The system SHALL minimize memory usage during request queuing and processing.

#### Scenario: No content pre-buffering
- **WHEN** a request is waiting in queue
- **THEN** no content fetching or buffering occurs
- **AND** only the request metadata is stored in memory

#### Scenario: Immediate slot release on error
- **GIVEN** a crawl operation encounters an error
- **WHEN** the error handling code executes
- **THEN** the semaphore slot is released immediately
- **AND** the slot is available before the error response is sent

#### Scenario: Resource cleanup on timeout
- **GIVEN** a request times out in queue
- **WHEN** the timeout exception is raised
- **THEN** no browser resources are allocated
- **AND** the response is returned without holding any crawl slots

### Requirement: Graceful Degradation Under Load
The system SHALL provide clear feedback to clients when capacity is exceeded.

#### Scenario: 503 response with retry guidance
- **WHEN** a request receives HTTP 503 due to queue timeout
- **THEN** the response includes header "Retry-After: 60"
- **AND** the error message suggests "please retry later"

#### Scenario: Concurrent request handling
- **GIVEN** the system receives 10 concurrent requests with concurrency limit 3
- **WHEN** all requests are processed
- **THEN** 3 requests process immediately
- **AND** up to 7 requests queue and eventually process (if within timeout)
- **AND** requests exceeding queue timeout receive 503 responses

