import asyncio
from playwright.async_api import async_playwright

async def test_cosco_direct():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("Navigating...")
            # Use query parameter
            await page.goto("https://elines.coscoshipping.com/ebusiness/cargoTracking?queryType=CONTAINER&queryValue=CBHU8846870", wait_until="load", timeout=30000)
            
            print("Waiting for results to load...")
            await page.wait_for_timeout(5000)
            
            # Try to accept cookies
            try:
                await page.get_by_role("button", name="Allow All").click(timeout=5000)
                await page.wait_for_timeout(1000)
            except Exception:
                pass
            
            inputs = await page.locator("input.ivu-input").all()
            if len(inputs) > 0:
                await inputs[0].fill("CBHU8846870")
                await inputs[0].press("Enter")
                
            await page.wait_for_timeout(10000)
            
            await page.screenshot(path="cosco_direct_test.png", full_page=True)
            content = await page.content()
            
            with open("cosco_direct_test.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("Done! Title:", await page.title())
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cosco_direct())
