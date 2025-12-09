# web-crawling-api Specification Delta

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Response Format
The system SHALL return crawl results in a JSON response containing the filtered markdown content and metadata.

#### Scenario: Successful response structure
- **WHEN** a crawl succeeds
- **THEN** the response JSON contains fields: "success": true, "url": <requested_url>, "markdown": <filtered_content>, "timestamp": <iso8601_time>
- **AND** the "markdown" field contains the filtered `fit_markdown` content (not raw)

#### Scenario: Error response structure
- **WHEN** a crawl fails
- **THEN** the response JSON contains fields: "success": false, "url": <requested_url>, "error": <error_message>, "timestamp": <iso8601_time>

#### Scenario: Response with optional raw markdown
- **WHEN** a crawl succeeds with `include_raw_markdown: true`
- **THEN** the response JSON additionally contains "raw_markdown": <full_unfiltered_content>
