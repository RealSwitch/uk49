# Star49s.com Scraper - Playwright Implementation

## Overview

The star49s.com website uses Next.js with client-side rendering (JavaScript). The previous static HTML parser couldn't extract draw data because the content is loaded dynamically via AJAX.

**Solution**: Updated scraper to use Playwright (headless browser automation) to:
1. Load the page in a headless Chromium browser
2. Wait for JavaScript rendering to complete
3. Extract visible draw data from the rendered DOM
4. Parse dates and winning numbers

## Setup

### 1. Update Docker Image

The API service now uses a custom Dockerfile with Playwright system dependencies:

```bash
# Rebuild the API service with Playwright support
docker-compose up --build -d api
```

This will:
- Install system libraries required for Playwright/Chromium
- Install Python dependencies (including playwright==1.40.0)
- Download and install Chromium browser

### 2. Test the Scraper

```bash
# Test the scraper directly
docker-compose exec api python airflow/scripts/scraper_star49s.py

# Or trigger via API
curl -X POST http://localhost:8000/admin/scrape

# Check results
docker-compose exec api python scripts/test_db.py
```

## Features

✅ **Dual Draw Support**: Fetches both lunchtime and teatime draws
✅ **JavaScript Rendering**: Uses Playwright for dynamic content
✅ **Error Handling**: Graceful fallback if Playwright isn't available
✅ **Logging**: Detailed logging for debugging
✅ **CSV Export**: Timestamps and draw data saved for analysis

## Scraper Logic

The scraper performs these steps for each draw type (lunchtime/teatime):

1. **Launch Chromium browser** in headless mode
2. **Navigate to history page** and wait for network idle
3. **Wait for result elements** to load (10 second timeout)
4. **Extract text content** from all result rows
5. **Parse dates and numbers** using regex patterns
6. **Validate results**: Must be 6 unique numbers 1-49
7. **Combine & return** lunchtime + teatime draws

## Extract selectors tried

The scraper tries multiple selectors to find result rows:
- `[data-testid="result"]` - Test ID attribute
- `.result` - CSS class
- `tr[data-result]` - Table row with data attribute
- `[class*="result"]` - Any element with "result" in class
- `div[class*="DrawRow"]` - Draw row components
- `article` - Fallback semantic HTML

## Handling Issues

### No results extracted?

1. **Check browser rendering time**: Page may need more time
   - Increase timeout in scraper: Change `timeout=10000` to `timeout=20000`

2. **Verify page structure changed**: Star49s.com may have updated their UI
   - Run diagnostic: `docker-compose exec api python scripts/inspect_star49s.py`
   - Extract selector info: `docker-compose exec api python scripts/extract_script.py`

3. **Playwright not installed properly**:
   ```bash
   docker-compose exec api python -m playwright install chromium
   docker-compose exec api python -m playwright install-deps chromium
   ```

### Slow performance?

Playwright can be slower than static parsing. Options:
1. Use headless mode (already set) - fastest option
2. Reduce timeout if pages load quickly
3. Cache results to avoid repeated scrapes

## Database

After scraping, draws are stored with:
- `draw_date`: Date string (DD/MM or DD/MM/YYYY)
- `draw_type`: 'lunchtime' or 'teatime'
- `numbers`: Comma-separated winning numbers (1-49)

## Files Modified

- `airflow/scripts/scraper_star49s.py` - Updated to use Playwright
- `requirements.txt` - Added playwright==1.40.0
- `Dockerfile.api` - New Docker image with Playwright dependencies
- `docker-compose.yml` - Updated to use custom Dockerfile

## Next Steps

If scraping still fails, consider:
1. Checking if star49s.com has **API documentation** (contact site owner)
2. Using a **different draw source** with static HTML/JSON API
3. Implementing **cloud-based scraping** (Apify, Bright Data, etc.)
