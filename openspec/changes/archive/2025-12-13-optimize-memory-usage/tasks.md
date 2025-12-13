# Implementation Tasks: optimize-memory-usage

## Overview
This task list breaks down the memory optimization work into small, verifiable steps that deliver incremental user-visible progress. Each task includes validation criteria.

## Task Sequence

### 1. Add concurrency configuration to config.py
- [x] **What**: Add `MAX_CONCURRENT_CRAWLS` and `QUEUE_TIMEOUT` environment variables with defaults.

**Deliverable**: Configuration loaded and logged at startup.

**Validation**:
- Start service and verify log shows: "Max concurrent crawls: 3, Queue timeout: 60s"
- Set `MAX_CONCURRENT_CRAWLS=5` and verify it's respected in logs

**Dependencies**: None

---

### 2. Implement semaphore in CrawlerService
- [x] **What**: Add `asyncio.Semaphore` instance to `CrawlerService.__init__` using `MAX_CONCURRENT_CRAWLS` from config.

**Deliverable**: Semaphore created with configured limit.

**Validation**:
- Add debug log showing semaphore initialization with limit
- Verify no runtime errors on service startup

**Dependencies**: Task 1

---

### 3. Wrap crawl_url with semaphore acquisition
- [x] **What**: Modify `crawler.py::crawl_url` to acquire semaphore before creating AsyncWebCrawler, release in finally block.

**Deliverable**: Concurrent crawls are limited by semaphore.

**Validation**:
- Add logging: "Waiting for crawl slot..." and "Acquired crawl slot"
- Send 5 concurrent requests with limit=3, verify logs show queueing behavior
- Verify all requests eventually complete

**Dependencies**: Task 2

---

### 4. Add queue timeout handling
- [x] **What**: Wrap semaphore acquisition with `asyncio.wait_for(timeout=queue_timeout)` and handle `asyncio.TimeoutError` with 503 response.

**Deliverable**: Requests timeout with clear error when queue is full too long.

**Validation**:
- Set `QUEUE_TIMEOUT=5` and `MAX_CONCURRENT_CRAWLS=1`
- Send 3 concurrent requests to slow URLs (add artificial delay if needed)
- Verify 2nd/3rd requests timeout with HTTP 503 and message "Service too busy, please retry later"

**Dependencies**: Task 3

---

### 5. Update error response handling in main.py
- [x] **What**: Add handling for queue timeout errors (asyncio.TimeoutError from semaphore) to return HTTP 503 with CrawlErrorResponse.

**Deliverable**: Proper HTTP status codes and error messages for queue timeouts.

**Validation**:
- Trigger queue timeout scenario from Task 4
- Verify response JSON matches CrawlErrorResponse schema with success=false
- Verify HTTP status is 503, not 502

**Dependencies**: Task 4

---

### 6. Add queue metrics logging
- [x] **What**: Add INFO logs when request queues ("Request queued for URL: {url}"), acquires slot ("Request acquired slot after {wait_time}s"), and WARNING when timeout occurs.

**Deliverable**: Observable queue behavior through logs.

**Validation**:
- Trigger concurrent requests scenario
- Verify logs show queue events with timing information
- Verify timeout logs appear when queue timeout occurs

**Dependencies**: Task 5

---

### 7. Add minimum concurrency limit validation
- [x] **What**: In config.py, validate that `MAX_CONCURRENT_CRAWLS >= 1`, set to 1 if lower value provided.

**Deliverable**: System always has at least 1 concurrent slot to ensure progress.

**Validation**:
- Set `MAX_CONCURRENT_CRAWLS=0` and start service
- Verify log shows warning and uses limit of 1
- Verify crawl requests work normally

**Dependencies**: Task 1

---

### 8. Update .env.example with new settings
- [x] **What**: Add `MAX_CONCURRENT_CRAWLS` and `QUEUE_TIMEOUT` to `.env.example` with descriptions and default values.

**Deliverable**: Documentation for new configuration options.

**Validation**:
- Review `.env.example` file
- Verify defaults match actual code defaults
- Verify descriptions are clear

**Dependencies**: Task 1

---

### 9. Add integration tests for concurrency control
- [x] **What**: Create test cases in `test_service.py` for:
- Concurrent request limiting (5 requests, limit 3)
- Queue timeout behavior
- Slot release after success/failure

**Deliverable**: Automated tests validate concurrency behavior.

**Validation**:
- Run `python test_service.py` and verify all new tests pass
- Verify tests actually exercise concurrent code paths (use debug logs)

**Dependencies**: Tasks 1-7

---

### 10. Load test with memory monitoring
- [x] **What**: Test service under realistic high load (10+ concurrent requests to varied URLs) while monitoring memory usage.

**Deliverable**: Confirmation that memory stays under 800MB under load.

**Validation**:
- Set `MAX_CONCURRENT_CRAWLS=3`
- Send 10 concurrent crawl requests to varied URLs
- Monitor memory with `docker stats` or Railway metrics
- Verify peak memory < 800MB
- Verify no OOM crashes occur

**Dependencies**: Tasks 1-9

---

### 11. Update README.md with new configuration
- [x] **What**: Document `MAX_CONCURRENT_CRAWLS` and `QUEUE_TIMEOUT` in configuration section and troubleshooting section.

**Deliverable**: User-facing documentation updated.

**Validation**:
- Review README.md "Configuration" table includes new variables
- Verify "Troubleshooting" section mentions concurrency tuning for memory issues

**Dependencies**: Tasks 1-10

---

### 12. Update DEPLOYMENT.md with memory optimization notes
- [x] **What**: Add section on memory optimization, concurrency tuning, and queue timeout handling.

**Deliverable**: Deployment documentation reflects new capabilities.

**Validation**:
- Review DEPLOYMENT.md includes concurrency configuration guidance
- Verify troubleshooting section mentions queue timeout errors

**Dependencies**: Task 11

---

## Parallel Work Opportunities

- Tasks 8, 11, 12 (documentation) can be done in parallel after implementation tasks complete
- Task 9 (tests) can start once Tasks 1-7 are complete
- Task 10 (load test) should be last to validate entire system

## Validation Summary

After all tasks:
1. Service starts successfully with new configuration ✓
2. Concurrent requests are properly limited and queued ✓
3. Queue timeouts work correctly with 503 responses ✓
4. Memory usage stays under 800MB under high concurrent load ✓
5. Tests pass and validate concurrency behavior ✓
6. Documentation is complete and accurate ✓
