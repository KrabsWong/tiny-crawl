# Design Document: Content Filtering for Core Content Extraction

## Context
The current implementation returns `result.markdown` directly from crawl4ai, which includes all page content including navigation menus, sidebars, footers, and other boilerplate elements. This creates noise for LLM consumption and requires downstream processing to extract relevant content.

crawl4ai provides built-in content filtering through:
1. **PruningContentFilter** - Scores content blocks by text density, link density, and tag importance
2. **BM25ContentFilter** - Query-based filtering using BM25 ranking algorithm
3. **excluded_tags** - Remove entire HTML elements like `<nav>`, `<header>`, `<footer>`
4. **fit_markdown** - Filtered markdown output vs raw_markdown

## Goals / Non-Goals

### Goals
- Use crawl4ai's official `PruningContentFilter` for automatic boilerplate removal
- Remove common noise elements (nav, header, footer, aside) via `excluded_tags`
- Return cleaner `fit_markdown` output by default
- Provide optional parameters for users to tune filtering behavior
- Maintain backward compatibility

### Non-Goals
- Implementing custom content extraction algorithms (use official crawl4ai features)
- BM25 query-based filtering (add later if needed)
- LLM-based extraction strategies
- Custom markdown formatting

## Decisions

### Decision 1: Use PruningContentFilter as Default Strategy
**Rationale**: PruningContentFilter is the recommended filter for general-purpose content extraction without requiring a search query. It uses text density and structural analysis to identify main content.

**Configuration**:
```python
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

prune_filter = PruningContentFilter(
    threshold=0.48,          # Default value, balanced filtering
    threshold_type="dynamic", # Adapts to page structure
    min_word_threshold=5     # Skip very short blocks
)
md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
```

### Decision 2: Pre-filter with excluded_tags
**Rationale**: Combining `excluded_tags` with content filter provides layered filtering. HTML elements are removed first, then PruningContentFilter scores remaining content.

**Tags to exclude**:
```python
excluded_tags = ['nav', 'header', 'footer', 'aside', 'form']
```

### Decision 3: Return fit_markdown by Default
**Rationale**: The `fit_markdown` output is specifically designed for LLM consumption and removes boilerplate. Users who need the full content can request `raw_markdown` explicitly.

**Access pattern**:
```python
# New behavior
markdown = result.markdown.fit_markdown

# Legacy/full content (if requested)
raw_markdown = result.markdown.raw_markdown
```

### Decision 4: Optional Request Parameters
**Rationale**: Allow users to customize filtering behavior without changing server configuration.

**New optional parameters**:
- `include_raw_markdown: bool = False` - Also return full unfiltered markdown
- `filter_threshold: float = 0.48` - PruningContentFilter threshold (lower = more content)
- `min_word_threshold: int = 5` - Minimum words per content block

## Architecture Changes

### crawler.py Changes
```python
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def crawl_url(self, url: str, timeout: Optional[int] = None, 
                    filter_threshold: float = 0.48,
                    min_word_threshold: int = 5) -> dict:
    
    prune_filter = PruningContentFilter(
        threshold=filter_threshold,
        threshold_type="dynamic",
        min_word_threshold=min_word_threshold
    )
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
    
    run_config = CrawlerRunConfig(
        excluded_tags=['nav', 'header', 'footer', 'aside', 'form'],
        markdown_generator=md_generator
    )
    
    result = await crawler.arun(url=url, config=run_config)
    
    return {
        "markdown": result.markdown.fit_markdown,
        "raw_markdown": result.markdown.raw_markdown,  # Optional
        "success": True
    }
```

### models.py Changes
```python
class CrawlRequest(BaseModel):
    url: HttpUrl
    include_raw_markdown: bool = False
    filter_threshold: float = Field(default=0.48, ge=0.0, le=1.0)
    min_word_threshold: int = Field(default=5, ge=0)
```

### Response Structure
```json
{
    "success": true,
    "url": "https://example.com",
    "markdown": "# Main Content\n\nFiltered content here...",
    "raw_markdown": "# Full Page\n\nIncludes nav, footer...",  // only if requested
    "timestamp": "2025-12-09T12:00:00Z"
}
```

## Risks / Trade-offs

### Risk 1: Over-filtering Important Content
**Description**: Aggressive filtering may remove content users want to keep.
**Mitigation**: 
- Use conservative default threshold (0.48)
- Allow threshold customization via API parameters
- Return raw_markdown as fallback option

### Risk 2: Page Structure Variations
**Description**: Some pages have unconventional structures where main content isn't in expected elements.
**Mitigation**: 
- `threshold_type="dynamic"` adapts to page structure
- Users can lower threshold to retain more content
- `excluded_tags` only removes clearly boilerplate elements

### Risk 3: Performance Impact
**Description**: Content filtering adds processing overhead.
**Mitigation**: 
- PruningContentFilter is lightweight (no LLM calls)
- Processing happens after crawl, minimal latency impact
- Most overhead is still in browser rendering

## Migration

### Backward Compatibility
- API endpoint `/crawl` remains unchanged
- Default response format stays compatible
- New parameters are optional with sensible defaults
- Users who want old behavior can set `filter_threshold=0.0` or use `raw_markdown`

### Testing Strategy
- Test with diverse page types (news articles, documentation, blogs)
- Compare markdown length before/after filtering
- Verify navigation/footer content is removed
- Ensure main content is preserved
