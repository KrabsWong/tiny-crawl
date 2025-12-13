# Design: Memory Optimization for High-Concurrency Crawling

## Overview

This design addresses memory overflow issues under high concurrent load by implementing multiple complementary strategies: concurrency limiting, request queuing, and efficient resource management. The solution must work within a 1GB memory constraint while maintaining reasonable response times.

## Context

The current implementation creates a new AsyncWebCrawler instance for each request using an async context manager. While this ensures proper resource cleanup, it doesn't prevent unbounded concurrency. When multiple slow-loading pages are crawled simultaneously, memory usage multiplies (browser contexts + large content buffering), leading to OOM crashes.

## Key Constraints

- **Memory Limit**: 1GB total memory (aim for <800MB peak usage)
- **Deployment**: Railway.app with Docker, single instance
- **Existing API**: Must maintain backward compatibility with `/crawl` endpoint
- **Response Time**: Should remain <5s for typical pages when not queued

## Architecture Decisions

### Decision 1: Semaphore-Based Concurrency Control

**Choice**: Use `asyncio.Semaphore` to limit concurrent crawl operations

**Rationale**: 
- Semaphores provide simple, efficient concurrency control in async code
- Automatically handles request queuing without manual queue implementation
- Integrates cleanly with existing async/await patterns
- Low overhead compared to process pools or worker queues

**Alternatives Considered**:
- Thread/process pool executors - adds complexity, not needed for I/O bound tasks
- External queue system (Redis, RabbitMQ) - overkill for single-instance deployment
- Rate limiting only - doesn't prevent memory spikes from slow concurrent requests

### Decision 2: Configurable Concurrency Limit

**Choice**: Set default max concurrent crawls to 3, make it configurable via environment variable

**Rationale**:
- Chromium browser contexts consume ~150-200MB each under load
- 3 concurrent crawls = ~600MB + ~200MB overhead + application memory ≈ 800MB peak
- Provides balance between throughput and safety margin
- Can be tuned based on actual workload characteristics

**Configuration**:
```
MAX_CONCURRENT_CRAWLS=3  # Default
QUEUE_TIMEOUT=60         # Seconds to wait for available slot
```

### Decision 3: Request Timeout and Queue Timeout

**Choice**: Separate timeouts for queue waiting and crawl execution

**Rationale**:
- Queue timeout (60s default) - prevents requests from waiting indefinitely
- Crawl timeout (30s existing) - prevents individual crawls from hanging
- Total request time = queue_wait + crawl_time, bounded and predictable

**Error Responses**:
- HTTP 503 when queue timeout exceeded: "Service too busy, please retry later"
- HTTP 502 when crawl timeout exceeded: "Crawl operation timed out"

### Decision 4: In-Memory Queuing

**Choice**: Use semaphore's built-in waiting mechanism, not a separate queue

**Rationale**:
- `asyncio.Semaphore.acquire()` with timeout naturally queues requests
- No need for explicit queue data structure (Redis, asyncio.Queue)
- Simpler implementation with fewer failure modes
- Sufficient for single-instance deployment

**Trade-offs**:
- No visibility into queue position (acceptable for this use case)
- No queue metrics/monitoring (can add later if needed)
- Not distributed (fine for Railway single-instance deployment)

### Decision 5: Global Crawler Pool with Semaphore

**Choice**: Keep existing per-request crawler pattern, add semaphore wrapper

**Rationale**:
- Minimal code changes to existing `crawler.py`
- AsyncWebCrawler already uses async context manager for cleanup
- Semaphore wraps the entire crawl operation (acquire before creating crawler)
- Leverages crawl4ai's internal browser pooling

**Implementation Pattern**:
```python
async with self.semaphore:  # Wait for available slot
    async with AsyncWebCrawler(config=self.browser_config) as crawler:
        result = await asyncio.wait_for(crawler.arun(url=url, config=run_config), timeout=timeout)
```

### Decision 6: Memory Monitoring (Optional Enhancement)

**Choice**: Add basic memory logging, defer advanced monitoring

**Rationale**:
- Use `psutil` to log memory usage at service startup and in error conditions
- Helps diagnose issues and validate optimization effectiveness
- Full monitoring dashboard (Prometheus, Grafana) is out of scope
- Can add detailed metrics later based on operational needs

## Component Changes

### config.py
- Add `MAX_CONCURRENT_CRAWLS` (default: 3)
- Add `QUEUE_TIMEOUT` (default: 60 seconds)

### crawler.py
- Add `asyncio.Semaphore` instance in `CrawlerService.__init__`
- Wrap `crawl_url` body with semaphore acquire
- Add queue timeout handling with clear error message

### main.py
- Update error handling for new 503 "Service too busy" response
- Add queue timeout to `CrawlErrorResponse` scenarios

### models.py
- No changes required - existing error response format supports new error messages

## Edge Cases

### Case 1: All Slots Occupied, Queue Builds Up
- Requests wait up to `QUEUE_TIMEOUT` seconds
- After timeout, return HTTP 503 with "Service too busy" message
- Client should implement exponential backoff retry

### Case 2: Slow Crawl Blocks Slot
- Individual crawl timeout (30s) still enforced
- Frees semaphore slot when timeout triggers
- Other requests can proceed

### Case 3: Browser Crash During Crawl
- AsyncWebCrawler context manager ensures cleanup
- Semaphore released via `finally` block in wrapper
- Slot becomes available for next request

### Case 4: Service Restart Under Load
- All pending requests fail (connection reset)
- Semaphore state is lost (not persistent)
- Clients retry, new requests queued properly

## Testing Strategy

### Unit Tests
- Semaphore acquisition/release logic
- Timeout handling (both queue and crawl)
- Error message format for 503 responses

### Integration Tests
- Concurrent requests (5+ simultaneous) with concurrency limit 3
- Verify some requests wait, all eventually succeed
- Memory usage monitoring during test

### Load Tests
- Simulate 10 concurrent requests to slow-loading pages
- Verify memory stays under 800MB
- Measure queue wait times and success rate

## Risks and Mitigations

### Risk 1: Concurrency Limit Too Low
**Description**: Setting limit too low reduces throughput unnecessarily.

**Mitigation**: 
- Start with conservative default (3)
- Make configurable via environment variable
- Monitor queue wait times to tune

### Risk 2: Queue Timeout Too Short
**Description**: Clients experience false "service busy" errors.

**Mitigation**:
- Set generous default (60s)
- Document recommended client retry strategy
- Return clear error message for exponential backoff

### Risk 3: Memory Leak in Browser Contexts
**Description**: Browser contexts not properly cleaned up, memory creeps up.

**Mitigation**:
- AsyncWebCrawler context manager handles cleanup
- Add memory logging to detect leaks early
- Consider periodic browser pool restart (future enhancement)

## Future Enhancements

- **Adaptive Concurrency**: Dynamically adjust limit based on memory pressure
- **Priority Queue**: Premium users get faster queue progression
- **Distributed Queue**: Redis-backed queue for multi-instance scaling
- **Content Streaming**: Stream large markdown instead of buffering
- **Browser Pool Lifecycle**: Periodic browser restarts to prevent memory leaks
