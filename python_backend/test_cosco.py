import asyncio
import json
from app.scrapers.cosco import scrape_cosco

async def main():
    result = await scrape_cosco("COSU6508292580")
    if result:
        print("Success!")
        with open("cosco_test_result.html", "w", encoding="utf-8") as f:
            f.write(result["raw_html"])
    else:
        print("Failed.")

if __name__ == "__main__":
    asyncio.run(main())
