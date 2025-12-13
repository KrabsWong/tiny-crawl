# Tiny Crawl - Web Scraping Service

A simple HTTP API for web crawling that returns LLM-ready markdown content, powered by [crawl4ai](https://github.com/unclecode/crawl4ai).

## Features

- 🚀 **Simple REST API** - Just POST a URL and get markdown back
- 🤖 **LLM-Ready Output** - Clean, structured markdown optimized for AI consumption
- ⚡ **Fast & Efficient** - Async architecture with browser pooling
- 🐳 **Docker Ready** - Easy deployment with Docker
- ☁️ **Railway Compatible** - Deploy to Railway.app with one click

## Quick Start

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
crawl4ai-setup
python -m playwright install chromium
```

2. **Run the service**:
```bash
python main.py
```

The service will start on `http://localhost:8000`

3. **Test the API**:
```bash
# Health check
curl http://localhost:8000/health

# Crawl a URL
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Using Docker

1. **Build the image**:
```bash
docker build -t tiny-crawl .
```

2. **Run the container**:
```bash
docker run -p 8000:8000 --shm-size=1g tiny-crawl
```

Note: `--shm-size=1g` is required for Chromium browser operations.

3. **Test the service**:
```bash
python test_service.py http://localhost:8000
```

## API Documentation

### POST /crawl

Crawl a web page and return its content as markdown.

**Request**:
```json
{
  "url": "https://example.com"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "url": "https://example.com",
  "markdown": "# Example Domain\n\nThis domain is for use in...",
  "timestamp": "2025-12-09T12:00:00Z"
}
```

**Error Response** (400/502/503):
```json
{
  "success": false,
  "url": "https://invalid-url",
  "error": "Failed to crawl URL: Connection timeout",
  "timestamp": "2025-12-09T12:00:00Z"
}
```

**Status Codes**:
- `200` - Success
- `400` - Invalid URL format
- `502` - Crawl operation failed or timed out
- `503` - Service too busy (queue timeout - retry after 60s)

### GET /health

Health check endpoint.

**Response** (200):
```json
{
  "status": "ok"
}
```

### Interactive Documentation

Once the service is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `CRAWL_TIMEOUT` | `30` | Timeout for crawl operations (seconds) |
| `BROWSER_HEADLESS` | `true` | Run browser in headless mode |
| `BROWSER_VERBOSE` | `true` | Enable verbose browser logging |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MAX_CONCURRENT_CRAWLS` | `3` | Maximum concurrent crawl operations (memory management) |
| `QUEUE_TIMEOUT` | `60` | Timeout for waiting in queue (seconds) |

## Deployment to Railway.app

### Prerequisites
- GitHub account
- Railway account (free tier available)

### Steps

1. **Push code to GitHub**:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

2. **Deploy to Railway**:
   - Go to [Railway.app](https://railway.app/)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will automatically detect the Dockerfile and deploy

3. **Configure environment** (optional):
   - Go to your project settings
   - Add environment variables if needed (defaults work fine)

4. **Get your service URL**:
   - Railway will provide a public URL
   - Test with: `curl https://your-app.railway.app/health`

### Railway Configuration

The `railway.toml` file configures:
- Docker build
- Health check endpoint at `/health`
- Automatic restarts on failure
- Port binding from Railway's `$PORT` environment variable

## Testing

Run the test suite:

```bash
# Test local instance
python test_service.py http://localhost:8000

# Test deployed instance
python test_service.py https://your-app.railway.app
```

Tests cover:
- Health endpoint
- Valid URL crawling
- Invalid URL handling
- Concurrent requests

## Example Usage

### Python

```python
import httpx
import asyncio

async def crawl_url(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/crawl",
            json={"url": url},
            timeout=60.0
        )
        return response.json()

# Usage
result = asyncio.run(crawl_url("https://example.com"))
print(result["markdown"])
```

### cURL

```bash
# Basic crawl
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com"}'

# Pretty print with jq
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com"}' | jq .
```

### JavaScript/TypeScript

```typescript
async function crawlUrl(url: string) {
  const response = await fetch('http://localhost:8000/crawl', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  return response.json();
}

// Usage
const result = await crawlUrl('https://example.com');
console.log(result.markdown);
```

## Architecture

### Components

- **main.py** - FastAPI application with endpoints
- **crawler.py** - crawl4ai AsyncWebCrawler wrapper
- **models.py** - Pydantic request/response models
- **config.py** - Environment configuration
- **Dockerfile** - Container definition
- **railway.toml** - Railway deployment config

### Technology Stack

- **Python 3.11** - Runtime
- **FastAPI** - Web framework
- **crawl4ai** - Web crawling library
- **Playwright** - Browser automation
- **Uvicorn** - ASGI server
- **Docker** - Containerization

## Troubleshooting

### Browser crashes or fails to start

Ensure sufficient shared memory:
```bash
docker run -p 8000:8000 --shm-size=1g tiny-crawl
```

### Timeout errors

Increase the timeout in `.env`:
```
CRAWL_TIMEOUT=60
```

### "Service too busy" errors (HTTP 503)

When concurrent requests exceed capacity, requests are queued. If queue wait exceeds `QUEUE_TIMEOUT`, you'll receive HTTP 503. Solutions:
- Implement exponential backoff retry in your client
- Increase `QUEUE_TIMEOUT` (default: 60s)
- Increase `MAX_CONCURRENT_CRAWLS` if you have available memory
- Space out your requests to reduce peak load

### Memory issues on Railway

Railway free tier has 512MB RAM limit. If you encounter memory issues:
- The service now includes automatic concurrency limiting (default: 3 concurrent crawls)
- Adjust `MAX_CONCURRENT_CRAWLS` environment variable to tune memory usage
  - Lower value (1-2) = less memory but slower throughput
  - Higher value (4-5) = more throughput but needs more memory
- Increase `QUEUE_TIMEOUT` if seeing "Service too busy" errors (default: 60s)
- Consider upgrading to a paid plan for more memory
- Monitor memory usage in Railway dashboard

### Playwright installation fails

Manually install with dependencies:
```bash
python -m playwright install --with-deps chromium
```

## Development

### Project Structure

```
tiny-crawl/
├── main.py              # FastAPI application
├── crawler.py           # Crawler service
├── models.py            # Data models
├── config.py            # Configuration
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── railway.toml         # Railway deployment config
├── test_service.py      # Test suite
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
├── .dockerignore        # Docker ignore rules
└── README.md            # This file
```

### Contributing

This is a minimal implementation. Future enhancements could include:
- Request rate limiting
- Authentication/API keys
- Caching layer
- Advanced crawl4ai features (CSS selectors, LLM extraction)
- Batch URL processing
- Webhook notifications

## License

This project follows crawl4ai's licensing. See [crawl4ai repository](https://github.com/unclecode/crawl4ai) for details.

## Acknowledgments

Built with [crawl4ai](https://github.com/unclecode/crawl4ai) - an amazing open-source web crawling library optimized for LLMs.
