import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import Stealth
import json

async def scrape_cosco(container_number: str) -> Optional[Dict[str, Any]]:
    """
    Scrapes the COSCO website for tracking information using Playwright with stealth.
    COSCO encrypts their payload, so we use Playwright to load the page and intercept the decrypted responses,
    or we can let the page render and extract the DOM text.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ])
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        captured_data = None
        
        # We can intercept the network responses. COSCO might decrypt it via JS, so we'll look for XHR/fetch requests.
        # However, the decryption happens in JS, so the raw XHR response is still encrypted.
        try:
            # COSCO Tracking URL (Requires checking their exact query format, usually they use a POST to an API
            # but they also have a direct tracking page). 
            # We will use their main tracking page and fill the input.
            # We'll use a robust retry loop to handle flakiness
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    import re
                    tracking_type = "CONTAINER" if re.match(r'^[A-Z]{4}\d{7}$', container_number) else "BOOKING"
                    
                    # COSCO Tracking actually loads an iframe for the results
                    url = f"https://elines.coscoshipping.com/scct/public/ct/base?lang=en&trackingType={tracking_type}&number={container_number}"
                    await page.goto(url, wait_until="load", timeout=45000)
                    
                    # Wait for results to load inside the iframe page
                    # The results usually have a class like .ivu-table or some tracking blocks
                    await page.wait_for_timeout(10000)
                    
                    content = await page.content()
                    title = await page.title()
                    
                    # If we got here without exception, break the retry loop
                    return {
                        "raw_html": content,
                        "title": title
                    }
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        import traceback
                        traceback.print_exc()
                        return None
                    await page.wait_for_timeout(5000)
        finally:
            await browser.close()

def scrape_cosco_sync(container_number: str) -> Optional[Dict[str, Any]]:
    """
    Runs the playwright scraper in an isolated subprocess to prevent asyncio loop conflicts with FastAPI.
    """
    import subprocess
    import os
    import json
    
    script_path = os.path.abspath(__file__)
    try:
        output = subprocess.check_output(
            ["python", script_path, container_number],
            stderr=subprocess.PIPE,
            timeout=60,
            text=True
        )
        # Parse the JSON printed to stdout
        return json.loads(output.strip())
    except subprocess.TimeoutExpired:
        return {"error": "Scraper timeout"}
    except subprocess.CalledProcessError as e:
        return {"error": f"Scraper process failed: {e.stderr}"}
    except Exception as e:
        return {"error": f"Scraper execution error: {str(e)}"}

if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        container_number = sys.argv[1]
        result = asyncio.run(scrape_cosco(container_number))
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "No container number provided"}))
