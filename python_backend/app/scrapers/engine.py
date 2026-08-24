import requests
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions
import threading

# Lock to prevent multiple headless browsers from spinning up at the exact same time and crashing
scraper_lock = threading.Lock()

def scrape_sitc(tracking_number):
    """Scrape SITC using standard requests and BeautifulSoup (No Bot Protection)"""
    url = f"https://logistics.sitc.com/portal/track/tracks.htm?trackType=1&trackNo={tracking_number}"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    bl_block = soup.find(id='block-bl')
    vessel_block = soup.find(id='block-vessel')
    container_block = soup.find(id='block-container')
    
    def extract_text(block):
        if not block: return "No data"
        if "暂无数据" in block.text:
            return "No data found for this container."
            
        rows = block.find_all('tr')
        if not rows:
            # Clean up the text by removing excessive newlines
            import re
            return re.sub(r'\n+', '\n', block.text.strip())
        
        data = []
        for row in rows:
            cols = [col.text.strip() for col in row.find_all(['td', 'th'])]
            data.append(" | ".join(cols))
        return "\n".join(data)

    return {
        "bl_information": extract_text(bl_block),
        "vessel_information": extract_text(vessel_block),
        "container_information": extract_text(container_block),
        "note": "Scraped via BeautifulSoup"
    }


def scrape_cma(tracking_number):
    """Scrape CMA CGM using DrissionPage (Bypasses DataDome and CSRF)"""
    with scraper_lock:
        co = ChromiumOptions()
        co.headless(True)
        # Reuse user data to keep DataDome solved cookies
        co.set_user_data_path('./drission_user_data')
        co.auto_port()
        
        page = ChromiumPage(co)
        try:
            url = "https://www.cma-cgm.com/ebusiness/tracking/search"
            page.get(url)
            
            search_input = page.ele('@name=SearchViewModel.Reference', timeout=15)
            if not search_input:
                return {"error": "Failed to load CMA Tracking Page. DataDome might be blocking the headless browser."}
                
            search_input.input(tracking_number)
            
            submit_btn = page.ele('@type=submit', timeout=5)
            if submit_btn:
                submit_btn.click()
            else:
                return {"error": "Could not find submit button on CMA."}
            
            # Wait for the results to load (wait for url to change or DOM to update)
            time.sleep(3) # Give it a few seconds to process the POST request
            
            # Extract tracking results
            # The exact CSS selector might need tuning depending on CMA's actual results page DOM
            result_container = page.ele('css:.section-tracking', timeout=10) or page.ele('css:main', timeout=10)
            
            if result_container:
                # We return a preview of the text for the frontend to render
                return {
                    "raw_scraped_text": result_container.text[:1000], 
                    "note": "Scraped via DrissionPage"
                }
            else:
                return {"error": "No tracking results found in DOM after submission."}
        finally:
            page.quit()

def scrape_maersk(tracking_number):
    """Scrape Maersk using DrissionPage (Bypasses Akamai)"""
    with scraper_lock:
        co = ChromiumOptions()
        co.headless(True)
        co.set_user_data_path('./drission_user_data')
        co.auto_port()
        
        page = ChromiumPage(co)
        try:
            import time
            # Go to the main tracking page first to solve Akamai
            page.get("https://www.maersk.com/tracking/")
            time.sleep(3)
            
            # Now that Akamai cookies are set in the browser, we can directly fetch the JSON API using the browser's context!
            api_url = f"https://api.maersk.com/synergy/tracking/{tracking_number}?operator=MAEU"
            
            # Use page.get() to navigate to the JSON endpoint
            page.get(api_url)
            time.sleep(2)
            
            # Extract the JSON text from the DOM (browser renders JSON inside a <pre> tag usually)
            pre_tag = page.ele('css:pre', timeout=5)
            if pre_tag:
                import json
                try:
                    data = json.loads(pre_tag.text)
                    return data
                except:
                    return {"raw_scraped_text": pre_tag.text, "note": "Failed to parse JSON."}
            else:
                return {"error": "Failed to retrieve Maersk JSON data."}
        finally:
            page.quit()

def scrape_hmm(tracking_number):
    """Scrape HMM using DrissionPage (Bypasses Akamai and CSRF)"""
    with scraper_lock:
        co = ChromiumOptions()
        co.headless(True)
        co.set_user_data_path('./drission_user_data')
        co.auto_port()
        
        page = ChromiumPage(co)
        try:
            import time
            page.get("https://www.hmm21.com/e-service/general/trackNTrace/TrackNTrace.do")
            time.sleep(2)
            
            search_input = page.ele('@name=cntrNo', timeout=5) or page.ele('#cntrNo', timeout=5)
            if not search_input:
                return {"error": "Failed to load HMM tracking input."}
                
            search_input.input(tracking_number)
            
            submit_btn = page.ele('css:.btn_search', timeout=5) or page.ele('@type=submit', timeout=5) or page.ele('@title=Search')
            if submit_btn:
                submit_btn.click()
            else:
                # If no submit button, try running JS or pressing Enter
                page.run_js('document.forms[0].submit();')
                
            time.sleep(4)
            
            result_container = page.ele('css:.board_view', timeout=10) or page.ele('css:table', timeout=10) or page.ele('css:body')
            if result_container:
                return {"raw_scraped_text": result_container.text[:1000], "note": "Scraped via DrissionPage"}
            else:
                return {"error": "No tracking results found on HMM."}
        finally:
            page.quit()



def scrape_evergreen(tracking_number):
    """Scrape Evergreen (ShipmentLink) using standard requests and BeautifulSoup (No Bot Protection)"""
    url = "https://ct.shipmentlink.com/servlet/TDB1_CargoTracking.do"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://ct.shipmentlink.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
    }
    
    # We will try BL, CNTR, and BKNO to be safe since we don't know what the user inputted
    # We will just default to BL if it's alphanumeric, or try CNTR if it looks like one.
    tracking_type = "CNTR" if len(tracking_number) == 11 and tracking_number[:4].isalpha() else "BL"
    
    # Form data from the user's curl
    raw_payload = f"BL={tracking_number if tracking_type == 'BL' else ''}&CNTR={tracking_number if tracking_type == 'CNTR' else ''}&bkno={tracking_number if tracking_type == 'BKNO' else ''}&TYPE={tracking_type}&NO=&NO=&NO=&NO=&NO=&SEL=s_{tracking_type.lower()}&NO={tracking_number}"
    
    response = requests.post(url, data=raw_payload, headers=headers, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Just extract all tables for now
    tables = soup.find_all('table')
    if not tables:
        # Check if there is an error message
        error_msg = soup.find(class_='errormsg') or soup.find('font', color='red')
        if error_msg:
            return {"error": error_msg.text.strip()}
        import re
        return {"raw_scraped_text": re.sub(r'\n+', '\n', soup.text.strip()[:1000]), "note": "No tables found on Evergreen"}
        
    data = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = [col.text.strip() for col in row.find_all(['td', 'th']) if col.text.strip()]
            if cols:
                data.append(" | ".join(cols))
                
    return {
        "raw_scraped_text": "\n".join(data[:50]),  # Limit to avoid massive payloads
        "note": "Scraped via BeautifulSoup"
    }

def scrape_pil(tracking_number):
    """Scrape PIL using DrissionPage (Bypasses WAF and dynamic tokens)"""
    with scraper_lock:
        co = ChromiumOptions()
        co.headless(True)
        co.set_user_data_path('./drission_user_data')
        co.auto_port()
        
        page = ChromiumPage(co)
        try:
            import time
            page.get("https://www.pilship.com/digital-solutions/?tab=customer&id=track-trace")
            time.sleep(4)
            
            # Find input
            search_input = page.ele('@name=refNo', timeout=5) or page.ele('css:input[placeholder*="Container"]', timeout=5) or page.ele('@type=text', timeout=5)
            if not search_input:
                return {"error": "Failed to load PIL tracking input."}
                
            search_input.input(tracking_number)
            
            # Click search
            submit_btn = page.ele('css:.btn-search', timeout=5) or page.ele('@type=submit', timeout=5) or page.ele('@type=button', timeout=5) or page.ele('css:button', timeout=5)
            if submit_btn:
                submit_btn.click()
            else:
                return {"error": "Could not find submit button on PIL."}
                
            time.sleep(5)
            
            # Extract tracking results
            result_container = page.ele('css:.track-result', timeout=10) or page.ele('css:table', timeout=10) or page.ele('css:.row', timeout=10) or page.ele('css:body')
            
            if result_container:
                text = result_container.text
                if "August" in text and "Today" in text:
                    # Filter out datepicker junk if we accidentally grabbed the whole body
                    lines = [line for line in text.split('\n') if not ('Su' in line and 'Mo' in line and 'Tu' in line) and not line.isdigit()]
                    text = '\n'.join(lines[:50]) # limit
                return {"raw_scraped_text": text[:1000], "note": "Scraped via DrissionPage"}
            else:
                return {"error": "No tracking results found on PIL."}
        finally:
            page.quit()

def scrape_seaboard(tracking_number):
    """Scrape Seaboard Marine HTML using BeautifulSoup"""
    import requests
    from bs4 import BeautifulSoup
    url = f"https://www.seaboardmarine.com/tracking-results/?eq_number={tracking_number}&vin_number="
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if "No records found" in response.text or "not found" in response.text.lower():
            return {"error": "Container not found in Seaboard Marine"}
            
        # Extract tables
        tables = soup.find_all('table')
        if not tables:
            import re
            return {"raw_scraped_text": re.sub(r'\n+', '\n', soup.text.strip()[:1000]), "note": "No tables found on Seaboard Marine"}
            
        data = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = [col.text.strip() for col in row.find_all(['td', 'th']) if col.text.strip()]
                if cols:
                    data.append(" | ".join(cols))
                    
        return {
            "raw_scraped_text": "\n".join(data[:50]),
            "note": "Scraped via BeautifulSoup"
        }
    except Exception as e:
        return {"error": str(e)}

def scrape_anl(tracking_number):
    """Scrape ANL (CMA CGM subsidiary) using DrissionPage (Bypasses DataDome and CSRF)"""
    with scraper_lock:
        co = ChromiumOptions()
        co.headless(True)
        # Reuse user data to keep DataDome solved cookies
        co.set_user_data_path('./drission_user_data')
        co.auto_port()
        
        page = ChromiumPage(co)
        try:
            import time
            url = "https://www.anl.com.au/ebusiness/tracking/search"
            page.get(url)
            
            search_input = page.ele('@name=SearchViewModel.Reference', timeout=15)
            if not search_input:
                return {"error": "Failed to load ANL Tracking Page. DataDome might be blocking the headless browser."}
                
            search_input.input(tracking_number)
            
            submit_btn = page.ele('@type=submit', timeout=5)
            if submit_btn:
                submit_btn.click()
            else:
                return {"error": "Could not find submit button on ANL."}
            
            time.sleep(3) 
            
            result_container = page.ele('css:.section-tracking', timeout=10) or page.ele('css:main', timeout=10)
            
            if result_container:
                return {
                    "raw_scraped_text": result_container.text[:1000], 
                    "note": "Scraped via DrissionPage"
                }
            else:
                return {"error": "No tracking results found in DOM after submission."}
        finally:
            page.quit()

def scrape_cnc(tracking_number):
    """Scrape CNC Line (CMA CGM subsidiary) using DrissionPage (Bypasses DataDome and CSRF)"""
    with scraper_lock:
        co = ChromiumOptions()
        co.headless(True)
        co.set_user_data_path('./drission_user_data')
        co.auto_port()
        
        page = ChromiumPage(co)
        try:
            import time
            url = "https://www.cnc-line.com/ebusiness/tracking/search"
            page.get(url)
            
            search_input = page.ele('@name=SearchViewModel.Reference', timeout=15)
            if not search_input:
                return {"error": "Failed to load CNC Tracking Page. DataDome might be blocking the headless browser."}
                
            search_input.input(tracking_number)
            
            submit_btn = page.ele('@type=submit', timeout=5)
            if submit_btn:
                submit_btn.click()
            else:
                return {"error": "Could not find submit button on CNC."}
            
            time.sleep(3) 
            
            result_container = page.ele('css:.section-tracking', timeout=10) or page.ele('css:main', timeout=10)
            
            if result_container:
                return {
                    "raw_scraped_text": result_container.text[:1000], 
                    "note": "Scraped via DrissionPage"
                }
            else:
                return {"error": "No tracking results found in DOM after submission."}
        finally:
            page.quit()
