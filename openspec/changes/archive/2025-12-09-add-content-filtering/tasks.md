# Tasks: Add Content Filtering for Core Content Extraction

## Implementation Tasks

1. [x] **Update models.py with new request parameters**
   - Add optional `include_raw_markdown: bool = False`
   - Add optional `filter_threshold: float = 0.48` with validation (0.0-1.0)
   - Add optional `min_word_threshold: int = 5` with validation (>=0)
   - Update `CrawlResponse` to include optional `raw_markdown` field

2. [x] **Update crawler.py with content filtering**
   - Import `PruningContentFilter` from `crawl4ai.content_filter_strategy`
   - Import `DefaultMarkdownGenerator` from `crawl4ai.markdown_generation_strategy`
   - Create `CrawlerRunConfig` with `excluded_tags=['nav', 'header', 'footer', 'aside', 'form']`
   - Configure `PruningContentFilter` with parameters from request
   - Pass `markdown_generator` to `CrawlerRunConfig`
   - Return `result.markdown.fit_markdown` instead of `result.markdown`
   - Include `raw_markdown` in return dict for optional access

3. [x] **Update main.py to pass filter options**
   - Extract filter parameters from `CrawlRequest`
   - Pass parameters to `crawler_service.crawl_url()`
   - Conditionally include `raw_markdown` in response based on `include_raw_markdown`

4. [x] **Test content filtering locally**
   - Test with navigation-heavy pages (news sites, documentation)
   - Verify filtered output excludes nav/header/footer content
   - Compare `fit_markdown` length vs `raw_markdown` length
   - Test parameter customization (threshold adjustments)

5. [x] **Update test_service.py with new test cases**
   - Add test for default filtering behavior
   - Add test for `include_raw_markdown=True`
   - Add test for custom `filter_threshold` values
   - Add test for `min_word_threshold` parameter

## Validation Checklist

- [x] Content filtering removes navigation menus
- [x] Content filtering removes page headers/footers
- [x] Main article/content is preserved
- [x] Optional parameters work correctly
- [x] Backward compatibility maintained (existing clients work)
- [x] Error handling for invalid parameter values

## Dependencies

- No new dependencies required (uses existing crawl4ai features)
- `PruningContentFilter` available in current crawl4ai version
