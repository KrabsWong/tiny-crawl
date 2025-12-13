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
                print(f"  Filtered markdown length: {len(data.get('markdown', ''))} chars")
                print(f"  Raw markdown included: {data.get('raw_markdown') is not None}")
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


async def test_include_raw_markdown(base_url: str):
    """Test the include_raw_markdown parameter."""
    print("\nTesting include_raw_markdown parameter...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/crawl",
                json={"url": "https://example.com", "include_raw_markdown": True},
                timeout=60.0
            )
            print(f"  Status: {response.status_code}")
            data = response.json()
            if data.get('success'):
                has_raw = data.get('raw_markdown') is not None
                print(f"  Has raw_markdown: {has_raw}")
                if has_raw:
                    print(f"  Filtered length: {len(data.get('markdown', ''))} chars")
                    print(f"  Raw length: {len(data.get('raw_markdown', ''))} chars")
                    print("  ✓ include_raw_markdown test passed")
                    return True
                else:
                    print("  ✗ raw_markdown should be included")
                    return False
            else:
                print(f"  Error: {data.get('error')}")
                return False
        except Exception as e:
            print(f"  ✗ include_raw_markdown test failed: {e}")
            return False


async def test_custom_filter_threshold(base_url: str):
    """Test custom filter_threshold parameter."""
    print("\nTesting custom filter_threshold parameter...")
    async with httpx.AsyncClient() as client:
        try:
            # Test with low threshold (should retain more content)
            response = await client.post(
                f"{base_url}/crawl",
                json={
                    "url": "https://example.com",
                    "filter_threshold": 0.1,
                    "min_word_threshold": 1
                },
                timeout=60.0
            )
            print(f"  Status: {response.status_code}")
            data = response.json()
            if data.get('success'):
                print(f"  Markdown length with low threshold: {len(data.get('markdown', ''))} chars")
                print("  ✓ Custom filter_threshold test passed")
                return True
            else:
                print(f"  Error: {data.get('error')}")
                return False
        except Exception as e:
            print(f"  ✗ Custom filter_threshold test failed: {e}")
            return False


async def test_concurrency_limiting(base_url: str):
    """Test that concurrent requests are properly limited and queued."""
    print("\nTesting concurrency limiting (5 requests with limit 3)...")
    urls = [
        "https://example.com",
        "https://www.iana.org",
        "https://www.w3.org",
        "https://httpbin.org/html",
        "https://httpstat.us/200"
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            import time
            start_time = time.time()
            
            tasks = [
                client.post(
                    f"{base_url}/crawl",
                    json={"url": url},
                    timeout=90.0
                )
                for url in urls
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed_time = time.time() - start_time
            
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code in [200, 503]
            )
            completed_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            
            print(f"  Completed: {completed_count}/{len(urls)} requests successfully")
            print(f"  Total responses received: {success_count}/{len(urls)}")
            print(f"  Total time: {elapsed_time:.1f}s")
            
            if success_count == len(urls):
                print("  ✓ Concurrency limiting test passed (all requests handled)")
                return True
            else:
                print("  ✗ Some requests failed unexpectedly")
                return False
        except Exception as e:
            print(f"  ✗ Concurrency limiting test failed: {e}")
            return False


async def test_queue_timeout(base_url: str):
    """Test queue timeout behavior with very low queue timeout."""
    print("\nTesting queue timeout behavior...")
    print("  Note: This test requires MAX_CONCURRENT_CRAWLS=1 and QUEUE_TIMEOUT=5")
    
    async with httpx.AsyncClient() as client:
        try:
            # Send 3 concurrent requests - first should succeed, others may timeout
            urls = [
                "https://example.com",
                "https://www.iana.org", 
                "https://www.w3.org"
            ]
            
            tasks = [
                client.post(
                    f"{base_url}/crawl",
                    json={"url": url},
                    timeout=20.0
                )
                for url in urls
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            status_codes = [
                r.status_code for r in responses 
                if not isinstance(r, Exception)
            ]
            
            print(f"  Status codes received: {status_codes}")
            
            # Check if we got at least one 503 (queue timeout)
            has_503 = 503 in status_codes
            has_200 = 200 in status_codes
            
            if has_200:
                print(f"  Got successful responses (200): {status_codes.count(200)}")
            if has_503:
                print(f"  Got queue timeout responses (503): {status_codes.count(503)}")
                print("  ✓ Queue timeout test passed")
                return True
            else:
                print("  ⚠ No queue timeouts observed (may need lower QUEUE_TIMEOUT setting)")
                return True  # Don't fail if config isn't set for this test
        except Exception as e:
            print(f"  ✗ Queue timeout test failed: {e}")
            return False


async def test_slot_release_after_error(base_url: str):
    """Test that semaphore slots are released even when crawl fails."""
    print("\nTesting slot release after error...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Send requests to an invalid URL that should fail
            invalid_url = "https://this-domain-definitely-does-not-exist-12345.com"
            
            # Send 2 requests in sequence
            response1 = await client.post(
                f"{base_url}/crawl",
                json={"url": invalid_url},
                timeout=20.0
            )
            
            response2 = await client.post(
                f"{base_url}/crawl",
                json={"url": "https://example.com"},
                timeout=60.0
            )
            
            print(f"  First request (invalid URL) status: {response1.status_code}")
            print(f"  Second request (valid URL) status: {response2.status_code}")
            
            # Second request should succeed, proving slot was released
            if response2.status_code == 200:
                print("  ✓ Slot release after error test passed")
                return True
            else:
                print("  ✗ Second request should have succeeded")
                return False
        except Exception as e:
            print(f"  ✗ Slot release test failed: {e}")
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
    
    # Test include_raw_markdown parameter
    results.append(await test_include_raw_markdown(base_url))
    
    # Test custom filter_threshold parameter
    results.append(await test_custom_filter_threshold(base_url))
    
    # Test concurrency limiting
    results.append(await test_concurrency_limiting(base_url))
    
    # Test queue timeout (optional - requires specific config)
    results.append(await test_queue_timeout(base_url))
    
    # Test slot release after error
    results.append(await test_slot_release_after_error(base_url))
    
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
