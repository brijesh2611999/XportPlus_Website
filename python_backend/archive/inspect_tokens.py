import os
import time
from dotenv import load_dotenv
from DrissionPage import ChromiumPage, ChromiumOptions

load_dotenv()

def inspect_tokens():
    print("Starting DrissionPage CMA-CGM Scraper for inspection...")
    co = ChromiumOptions()
    co.headless(False) 
    co.set_user_data_path('./drission_user_data')
    page = ChromiumPage(co)
    
    login_trigger_url = "https://www.cma-cgm.com/ebusiness/pricing/instant-Quoting"
    page.get(login_trigger_url)
    
    print("Waiting 10 seconds for page to load completely...")
    time.sleep(10)
    
    print("Dumping cookies...")
    cookies = page.cookies()
    for cookie in cookies:
        print(f"Cookie {cookie.get('name')}: {str(cookie.get('value'))[:30]}...")
            
    print("Dumping LocalStorage...")
    local_storage = page.run_js('return window.localStorage;')
    for k, v in local_storage.items():
        print(f"LS {k}: {str(v)[:50]}")
        
    print("Dumping SessionStorage...")
    session_storage = page.run_js('return window.sessionStorage;')
    for k, v in session_storage.items():
        print(f"SS {k}: {str(v)[:50]}")
        
    print("Dumping window variables...")
    csrf = page.run_js('return window.csrfToken || window.__CSRF_TOKEN__ || document.querySelector(\'meta[name="csrf-token"]\')?.content;')
    print(f"Window CSRF: {csrf}")
    
    page.quit()

if __name__ == "__main__":
    inspect_tokens()
