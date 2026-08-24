import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import Stealth

async def scrape_cma_cgm(container_number: str) -> Optional[Dict[str, Any]]:
    """
    Scrapes the CMA CGM website for tracking information using Playwright with stealth.
    """
    async with async_playwright() as p:
        # Launch Chromium headless
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
        # Apply stealth plugin to evade DataDome
        await Stealth().apply_stealth_async(page)
        
        try:
            # Navigate to the tracking endpoint
            url = f"https://www.cma-cgm.com/ebusiness/tracking/search?Reference={container_number}&SearchBy=Container"
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # TODO: Extract specific data points based on the page structure.
            # We first need to wait for a known selector that indicates the tracking result is loaded.
            # Currently just taking a screenshot and returning raw html for debugging.
            
            # Wait for results or captcha
            await page.wait_for_timeout(5000)
            
            content = await page.content()
            title = await page.title()
            
            if "captcha" in content.lower() or "datadome" in content.lower():
                print("Hit CAPTCHA on CMA CGM.")
                return None
            
            return {
                "raw_html": content[:1000], # return preview for now
                "title": title
            }
            
        except TimeoutError:
            print("Timeout while loading CMA CGM page.")
            return None
        except Exception as e:
            print(f"Error scraping CMA CGM: {e}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(scrape_cma_cgm("CMAU4711634"))
    print("Scraping Result:", result)
