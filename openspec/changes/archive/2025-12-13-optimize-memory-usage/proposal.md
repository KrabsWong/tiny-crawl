# Proposal: optimize-memory-usage

## Problem Statement

The service encounters frequent memory overflow (OOM) issues under high concurrent load, especially when crawling slow-loading pages. With a 1GB memory limit, the current architecture creates unbounded concurrent crawl operations, each spawning browser contexts and buffering large content in memory. This leads to memory exhaustion and service crashes.

## Current Behavior

- Each crawl request creates a new AsyncWebCrawler instance within an async context manager
- No limits on concurrent crawl operations - all requests execute simultaneously
- Full markdown content (both `fit_markdown` and `raw_markdown`) is buffered in memory
- No mechanism to shed load or queue requests during high traffic
- Browser contexts are created per-request without reuse optimization

## Proposed Solution

Implement a multi-layered memory optimization strategy:

1. **Concurrency Control**: Add semaphore-based limits to restrict simultaneous crawl operations
2. **Request Queue Management**: Implement request queuing with configurable queue size and timeout
3. **Streaming Response**: Support streaming large markdown content to avoid full buffering
4. **Browser Pool Management**: Reuse browser contexts more efficiently with lifecycle management
5. **Memory Monitoring**: Add memory usage metrics and automatic backpressure

## Success Criteria

- Service remains stable under high concurrent load (>10 simultaneous requests)
- Memory usage stays under 800MB peak (80% of 1GB limit, leaving headroom)
- Requests are queued when capacity is reached instead of failing
- Slow page crawls don't block other requests
- Response times remain acceptable (<5s for typical pages) when not queued

## User Impact

- **Positive**: Dramatically improved stability under load, no more OOM crashes
- **Positive**: Graceful degradation with queuing instead of hard failures
- **Neutral**: Some requests may be queued during peak load (transparent to user)
- **Positive**: Better resource utilization and predictable performance

## Out of Scope

- Distributed crawling across multiple instances
- Advanced caching mechanisms for repeated URLs
- Content compression or external storage
- Dynamic scaling based on load

## Dependencies

None - this is a self-contained optimization to the existing `web-crawling-api` capability.

## Related Changes

None - first change focused on memory optimization.
