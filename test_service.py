"""Test script for the crawl service."""
import asyncio
import httpx
import sys


async def test_health_endpoint(base_url: str):
    """Test the health endpoint."""
    print("Testing /health endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/health", timeout=10.0)
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            print("  ✓ Health check passed")
            return True
        except Exception as e:
            print(f"  ✗ Health check failed: {e}")
            return False


async def test_crawl_endpoint(base_url: str, url: str):
    """Test the crawl endpoint with a specific URL."""
    print(f"\nTesting /crawl endpoint with URL: {url}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/crawl",
                json={"url": url},
                timeout=60.0
            )
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Success: {data.get('success')}")
            print(f"  URL: {data.get('url')}")
            if data.get('success'):
                markdown_preview = data.get('markdown', '')[:200]
                print(f"  Markdown preview: {markdown_preview}...")
                print(f"  Markdown length: {len(data.get('markdown', ''))} chars")
                print("  ✓ Crawl test passed")
                return True
            else:
                print(f"  Error: {data.get('error')}")
                print("  ✗ Crawl returned error")
                return False
        except Exception as e:
            print(f"  ✗ Crawl test failed: {e}")
            return False


async def test_invalid_url(base_url: str):
    """Test the crawl endpoint with an invalid URL."""
    print("\nTesting /crawl endpoint with invalid URL...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/crawl",
                json={"url": "not-a-valid-url"},
                timeout=10.0
            )
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Success: {data.get('success')}")
            if response.status_code == 400 or response.status_code == 422:
                print("  ✓ Invalid URL properly rejected")
                return True
            else:
                print("  ✗ Invalid URL should return 400 or 422")
                return False
        except Exception as e:
            print(f"  ✗ Invalid URL test failed: {e}")
            return False


async def test_concurrent_requests(base_url: str):
    """Test concurrent crawl requests."""
    print("\nTesting concurrent requests...")
    urls = [
        "https://example.com",
        "https://www.iana.org",
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            tasks = [
                client.post(
                    f"{base_url}/crawl",
                    json={"url": url},
                    timeout=60.0
                )
                for url in urls
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            print(f"  Completed: {success_count}/{len(urls)} requests")
            if success_count == len(urls):
                print("  ✓ Concurrent requests test passed")
                return True
            else:
                print("  ✗ Some concurrent requests failed")
                return False
        except Exception as e:
            print(f"  ✗ Concurrent requests test failed: {e}")
            return False


async def run_tests(base_url: str = "http://localhost:8000"):
    """Run all tests."""
    print(f"Starting tests against {base_url}\n")
    print("=" * 60)
    
    results = []
    
    # Test health endpoint
    results.append(await test_health_endpoint(base_url))
    
    # Test crawl with valid URL
    results.append(await test_crawl_endpoint(base_url, "https://example.com"))
    
    # Test crawl with another URL
    results.append(await test_crawl_endpoint(base_url, "https://www.iana.org"))
    
    # Test invalid URL
    results.append(await test_invalid_url(base_url))
    
    # Test concurrent requests
    results.append(await test_concurrent_requests(base_url))
    
    print("\n" + "=" * 60)
    print(f"\nTest Summary: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    exit_code = asyncio.run(run_tests(base_url))
    sys.exit(exit_code)
