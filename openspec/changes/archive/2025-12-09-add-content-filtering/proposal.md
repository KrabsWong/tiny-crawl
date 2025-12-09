# Change: Add Content Filtering for Core Content Extraction

## Why
Current crawl results include excessive navigation elements, sidebars, headers, footers, and other boilerplate content that pollutes the markdown output. Users need clean, focused content suitable for LLM consumption without manually parsing out irrelevant sections.

## What Changes
- Integrate crawl4ai's built-in `PruningContentFilter` to automatically extract core page content
- Use `excluded_tags` configuration to remove common boilerplate HTML elements (nav, header, footer, aside)
- Return `fit_markdown` instead of `raw_markdown` for cleaner output
- Add optional API parameters to customize content filtering behavior
- Maintain backward compatibility by keeping full markdown available if needed

## Impact
- Affected specs: `web-crawling-api` (modified capability)
- Affected code: `crawler.py` - add content filter configuration; `models.py` - add optional request parameters; `main.py` - pass filter options
- No infrastructure changes required
- Uses official crawl4ai features: `PruningContentFilter`, `DefaultMarkdownGenerator`, `excluded_tags`

## References
- crawl4ai Fit Markdown docs: https://docs.crawl4ai.com/core/fit-markdown/
- crawl4ai Content Selection docs: https://docs.crawl4ai.com/core/content-selection/
