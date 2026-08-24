import os
import time
from dotenv import load_dotenv
from DrissionPage import ChromiumPage, ChromiumOptions
from db_manager import save_cma_tokens

load_dotenv()

import threading

# Global lock to prevent multiple scrapers from running simultaneously
scraper_lock = threading.Lock()

def scrape_cma_tokens():
    with scraper_lock:
        print("Starting DrissionPage CMA-CGM Scraper...")
    
    email = os.getenv("CMA_EMAIL")
    password = os.getenv("CMA_PASSWORD")
    
    if not email or not password:
        print("CMA_EMAIL or CMA_PASSWORD not found in .env!")
        return

    # Initialize DrissionPage with options to evade detection
    co = ChromiumOptions()
    
    # We will run headless if SCRAPER_HEADLESS is true, otherwise visible
    is_headless = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
    co.headless(is_headless) 

    
    # Store session data so we only have to clear DataDome once!
    co.set_user_data_path('./drission_user_data')
    co.auto_port()
    
    page = ChromiumPage(co)
    
    # Start listening to all network traffic to rip the tokens
    page.listen.start('cma-cgm.com')

    # Go to the quoting page directly
    start_url = "https://www.cma-cgm.com/ebusiness/pricing/instant-Quoting"
    print(f"Navigating to {start_url} ...")
    page.get(start_url)
    
    print("Waiting for page load or DataDome slider...")
    time.sleep(5)
    
    # If we are not automatically redirected to the login page, we might need to click the login button
    if 'auth.cma-cgm.com' not in page.url:
        print("Not on PingIdentity yet. Attempting to trigger login automatically...")
        try:
            # Look for a sign-in button or link
            login_btn = page.ele('@text():Sign In', timeout=2) or page.ele('@text():Log In', timeout=2) or page.ele('css:a.login', timeout=2)
            if login_btn:
                print("Clicking Sign In button...")
                login_btn.click()
                time.sleep(5)
            else:
                # Alternatively, forcefully navigate to the login route if we know it
                print("No Sign In button found. Attempting forceful redirect to Dashboard to trigger auth...")
                page.get("https://www.cma-cgm.com/ebusiness/dashboard")
                time.sleep(5)
        except Exception as e:
            print(f"Error triggering login: {e}")
            
    if 'auth.cma-cgm.com' in page.url:
        print("Found PingIdentity Login page!")
        
        # Wait for the username field to be fully loaded in the DOM
        try:
            print("Waiting for login form to render...")
            
            # Using DrissionPage attribute matching syntax (@attribute=value)
            username_field = page.ele('@name=pf.username', timeout=15) or page.ele('@type=email') or page.ele('@type=text')
            password_field = page.ele('@name=pf.pass') or page.ele('@type=password')
            submit_btn = page.ele('@type=submit') or page.ele('css:button[type="submit"]') or page.ele('css:.button')

            username_field.input(email)
            password_field.input(password)
            submit_btn.click()
            print("Injected credentials and clicked submit...")
            
            # Wait for login to complete and redirect back to CMA-CGM
            print("Waiting for login to complete...")
            page.wait.url_change('auth.cma-cgm.com', timeout=15)
        except Exception as e:
            print(f"Failed to inject credentials: {e}")
            
    # Now that we are authenticated, go to the quoting page
    quoting_url = "https://www.cma-cgm.com/ebusiness/pricing/instant-Quoting"
    print(f"Navigating to {quoting_url} to capture SpotOn tokens...")
    page.get(quoting_url)
            
    # We will trigger a native Fetch request from the page context. 
    # Because it is triggered from the authenticated page context, the browser 
    # will automatically attach the correct Cookies and the React/Angular app 
    # or the browser will attach the CSRF token if it's configured to do so.
    # Actually, a better way is to just click the "Search" button programmatically, 
    # but we can also just fetch the config endpoint which usually contains it.
    
    print("Waiting for SPA to initialize...")
    time.sleep(10)
    
    print("Triggering background API request to capture tokens...")
    # This forces the browser to make a request to the spoton API, which will include the CSRF token!
    page.run_js('''
        fetch('/apigw/commercial/spoton/bff/v1/getbestoffer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({})
        }).catch(e => console.log(e));
    ''')
    
    found = False
    for packet in page.listen.steps(timeout=30):
        headers = packet.request.headers
        
        # Make header extraction case-insensitive
        cookie_string = next((v for k, v in headers.items() if k.lower() == 'cookie'), '')
        csrf_token = next((v for k, v in headers.items() if k.lower() == 'x-csrf-token'), '')
        
        if cookie_string and csrf_token:
            print("Successfully intercepted CMA-CGM Tokens!")
            save_cma_tokens(cookie_string, csrf_token)
            found = True
            break
            
    if not found:
        print("Still couldn't intercept CSRF naturally. Attempting to extract from DOM/Cookies...")
        # Fallback: Sometimes CSRF is stored in a cookie named XSRF-TOKEN
        all_cookies = page.cookies()
        xsrf_cookie = next((c.get('value') for c in all_cookies if c.get('name') == 'XSRF-TOKEN'), None)
        cookie_str = "; ".join([f"{c.get('name')}={c.get('value')}" for c in all_cookies])
        
        if xsrf_cookie:
            print("Successfully extracted CSRF from cookies!")
            save_cma_tokens(cookie_str, xsrf_cookie)
            found = True

    print("Closing browser in 5 seconds...")
    time.sleep(5)
    page.quit()

if __name__ == "__main__":
    scrape_cma_tokens()
