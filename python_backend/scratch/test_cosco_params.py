import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled', '--no-sandbox'])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        # Try different tracking types
        print("Testing trackingType=BILL")
        url = "https://elines.coscoshipping.com/scct/public/ct/base?lang=en&trackingType=BILL&number=COSU6508292580"
        await page.goto(url, wait_until="load", timeout=30000)
        await page.wait_for_timeout(10000)
        await page.screenshot(path="cosco_bill_test.png", full_page=True)
        
        print("Testing trackingType=BOOKING")
        url = "https://elines.coscoshipping.com/scct/public/ct/base?lang=en&trackingType=BOOKING&number=COSU6508292580"
        await page.goto(url, wait_until="load", timeout=30000)
        await page.wait_for_timeout(10000)
        await page.screenshot(path="cosco_booking_test.png", full_page=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
