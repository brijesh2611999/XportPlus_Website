from DrissionPage import ChromiumPage, ChromiumOptions

def scrape_cma_cgm_dp(container_number: str):
    co = ChromiumOptions()
    co.headless(False)
    # Basic anti-detection
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
    
    page = ChromiumPage(co)
    try:
        url = f"https://www.cma-cgm.com/ebusiness/tracking/search?Reference={container_number}&SearchBy=Container"
        page.get(url)
        page.wait(5)
        
        content = page.html
        title = page.title
        
        if "captcha" in content.lower() or "datadome" in content.lower():
            print("Hit CAPTCHA on CMA CGM with DrissionPage.")
        else:
            print("Successfully loaded CMA CGM!")
            
        print("Title:", title)
        print("Content preview:", content[:500])
    except Exception as e:
        print("Error:", e)
    finally:
        page.quit()

if __name__ == "__main__":
    scrape_cma_cgm_dp("CMAU4711634")
