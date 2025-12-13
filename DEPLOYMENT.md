# Deployment Guide for Railway.app

This guide walks you through deploying the Tiny Crawl service to Railway.app.

## Prerequisites

- Git repository with the code (push to GitHub/GitLab)
- Railway account (sign up at https://railway.app/)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure all files are committed:

```bash
git add .
git commit -m "Add crawl4ai web scraping service"
git push origin main
```

### 2. Create Railway Project

1. Go to https://railway.app/
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select the `tiny-crawl` repository

### 3. Railway Auto-Detection

Railway will automatically:
- Detect the `Dockerfile`
- Use the `railway.toml` configuration
- Set up the build and deployment

### 4. Environment Variables (Optional)

Railway's default environment works out of the box. To customize:

1. Go to your project in Railway dashboard
2. Click **"Variables"**
3. Add any custom settings:
   - `CRAWL_TIMEOUT=60` (if you want longer timeouts)
   - `LOG_LEVEL=DEBUG` (for more verbose logging)
   - `MAX_CONCURRENT_CRAWLS=3` (default: 3, tune for memory management)
   - `QUEUE_TIMEOUT=60` (default: 60s, time requests wait in queue)
   
**Note**: Railway automatically provides `PORT` - don't set it manually!

#### Memory Management Configuration

The service includes automatic concurrency control to prevent memory overflow:

- **`MAX_CONCURRENT_CRAWLS`** (default: 3)
  - Limits simultaneous browser instances
  - Each browser uses ~150-200MB RAM
  - For 512MB Railway free tier: keep at 2-3
  - For 8GB Hobby plan: can increase to 5-10
  
- **`QUEUE_TIMEOUT`** (default: 60s)
  - How long requests wait for available slot
  - Longer = more patient clients, higher success rate
  - Shorter = faster failure feedback, may need retry logic

### 5. Monitor Deployment

1. Click on the **"Deployments"** tab
2. Watch the build logs
3. Wait for the status to show **"Active"**

Expected build time: 5-10 minutes (due to Playwright/Chromium installation)

### 6. Get Your Service URL

1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. Railway will provide a URL like: `https://tiny-crawl-production-xxxx.up.railway.app`

### 7. Test Your Deployment

```bash
# Health check
curl https://your-app.railway.app/health

# Crawl test
curl -X POST https://your-app.railway.app/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Run full test suite
python test_service.py https://your-app.railway.app
```

## Troubleshooting

### Build Fails

**Issue**: Dockerfile build fails  
**Solution**: Check Railway build logs for specific errors. Common issues:
- Missing dependencies: Ensure Dockerfile has all system packages
- Out of memory: Railway free tier has 8GB build limit (should be sufficient)

### Service Crashes After Start

**Issue**: Container starts but crashes immediately  
**Solution**: 
1. Check Railway logs for Python errors
2. Verify Playwright installation: Look for `crawl4ai-setup` in logs
3. Ensure Chromium installed: Check for Playwright install messages

### Health Check Fails

**Issue**: Railway shows unhealthy status  
**Solution**:
1. Verify `/health` endpoint responds: Check application logs
2. Increase health check timeout in `railway.toml` if needed
3. Ensure service binds to `0.0.0.0` (already configured)

### Memory Limit Exceeded

**Issue**: Service crashes with OOM (Out of Memory)  
**Solution**:
- Railway free tier: 512MB RAM
- Service now includes automatic concurrency limiting (default: 3 concurrent crawls)
- **Tune for your tier**:
  - Free tier (512MB): Set `MAX_CONCURRENT_CRAWLS=2`
  - Hobby plan (8GB): Can use `MAX_CONCURRENT_CRAWLS=5` or higher
- Monitor memory in Railway metrics dashboard
- Check logs for "Request queued" messages indicating concurrency control is working
- If seeing "Service too busy" errors, increase `QUEUE_TIMEOUT` or space out requests

**Memory Usage Guidelines**:
- Base application: ~100-150MB
- Per browser context: ~150-200MB
- Formula: Total = Base + (MAX_CONCURRENT_CRAWLS × 200MB)
- Example: 150MB + (3 × 200MB) = ~750MB peak (fits in 1GB with headroom)

### Slow First Request

**Issue**: First crawl request takes 30+ seconds  
**Solution**: This is normal! Chromium browser initialization takes time on cold start. Subsequent requests are much faster due to browser pooling.

### HTTP 503 "Service Too Busy" Errors

**Issue**: Requests return HTTP 503 with "Service too busy, please retry later"  
**Solution**: This means the concurrency limit is reached and queue timeout exceeded.

**Client-side fixes**:
1. Implement exponential backoff retry:
   ```python
   for retry in range(3):
       response = requests.post(url, json=data)
       if response.status_code != 503:
           break
       time.sleep(2 ** retry)  # 1s, 2s, 4s
   ```
2. Space out requests (don't send all at once)
3. Check `Retry-After` header in 503 response

**Server-side tuning**:
1. Increase `QUEUE_TIMEOUT` (default: 60s) to be more patient
2. Increase `MAX_CONCURRENT_CRAWLS` if you have memory headroom
3. Monitor Railway memory metrics to ensure safe scaling

## Monitoring

### Railway Dashboard

Monitor your service:
1. **Metrics**: CPU, Memory, Network usage
2. **Logs**: Real-time application logs
3. **Deployments**: History and rollback options

### Memory Monitoring

Watch memory usage to tune concurrency settings:

1. **Railway Metrics Dashboard**:
   - Check "Memory" graph during peak load
   - Look for patterns near memory limit
   - Adjust `MAX_CONCURRENT_CRAWLS` if seeing spikes near limit

2. **Log Analysis**:
   - Search logs for "Request queued" - indicates queuing is working
   - Look for "Request acquired slot after Xs" - shows queue wait times
   - Warning logs "Request timed out in queue" - may need higher `QUEUE_TIMEOUT`

3. **Key Indicators**:
   - Memory stays under 80% of limit: Good headroom ✓
   - Frequent queue timeouts: Increase `QUEUE_TIMEOUT` or `MAX_CONCURRENT_CRAWLS`
   - Memory approaching limit: Decrease `MAX_CONCURRENT_CRAWLS` or upgrade plan

### Load Testing

Test your configuration before production:

```bash
# Run extended tests including concurrency
python test_service.py https://your-app.railway.app

# Manual concurrent load test (requires httpx)
python -c "
import asyncio
import httpx

async def load_test():
    urls = ['https://example.com'] * 10
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post('https://your-app.railway.app/crawl', 
                       json={'url': url}, timeout=90)
            for url in urls
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 200)
        print(f'Success: {success}/10')

asyncio.run(load_test())
"
```

Watch Railway memory metrics during the test to validate configuration.

### Application Logs

View logs in Railway dashboard or via CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs
```

## Scaling Considerations

### Free Tier Limits
- 512MB RAM
- $5 free credit per month
- Sleeps after inactivity (wakes on request)

### When to Upgrade
Upgrade to Hobby plan ($5/month) if you need:
- More memory (8GB)
- No sleep/always active
- Higher reliability

### Horizontal Scaling
Railway supports multiple instances:
1. Go to project settings
2. Adjust replica count
3. Railway handles load balancing automatically

## Cost Optimization

### Free Tier Strategy
- Service sleeps after inactivity (automatic)
- Wakes on first request (adds latency)
- ~500 hours free per month

### Keep-Alive (Optional)
To prevent sleeping (uses more resources):
```bash
# External service to ping every 10 minutes
# Use Uptime Robot, Cron-job.org, or similar
curl https://your-app.railway.app/health
```

## Updating Your Service

### Deploy New Changes

```bash
git add .
git commit -m "Update service"
git push origin main
```

Railway automatically deploys on push to main branch.

### Rollback

If something goes wrong:
1. Go to **"Deployments"** in Railway
2. Find a working deployment
3. Click **"Redeploy"**

## Security Notes

### Public API
By default, your API is public. To add authentication:
1. Implement API key middleware in `main.py`
2. Add environment variable for API key
3. Require `Authorization` header in requests

### Rate Limiting
Consider adding rate limiting for production:
```bash
pip install slowapi
```

See Railway documentation for rate limiting examples.

## Next Steps

Once deployed:
1. ✅ Test all endpoints
2. ✅ Monitor logs for errors
3. ✅ Set up monitoring alerts (Railway + webhooks)
4. ✅ Share your API with users
5. ✅ Consider adding authentication for production use

## Support

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- crawl4ai Issues: https://github.com/unclecode/crawl4ai/issues

Enjoy your deployed web scraping service! 🚀
