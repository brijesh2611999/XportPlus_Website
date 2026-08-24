import requests
import json
import time
import os
from DrissionPage import ChromiumOptions, ChromiumPage
from db_manager import get_db_connection

def update_msc_tokens_in_db(access_token):
    import json
    token_payload = json.dumps({"MSC_ACCESS_TOKEN": access_token})
    
    upsert_query = """
        INSERT INTO site_tokens (site_name, token_data, last_updated)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (site_name)
        DO UPDATE SET token_data = EXCLUDED.token_data, last_updated = CURRENT_TIMESTAMP;
    """
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(upsert_query, ('MSC', token_payload))
    conn.commit()
    cursor.close()
    conn.close()

def get_msc_token_from_db():
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT token_data FROM site_tokens WHERE site_name = 'MSC';")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        token_data = row[0]
        if isinstance(token_data, str):
            token_data = json.loads(token_data)
        return token_data.get('MSC_ACCESS_TOKEN')
    return None

def fetch_msc_tokens_background():
    """
    Uses DrissionPage in headless mode to navigate to MSC, login, and capture the bearer token.
    """
    print("Starting MSC token capture in background...")
    co = ChromiumOptions()
    
    is_headless = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
    co.headless(is_headless)
    
    co.set_user_data_path('./msc_drission_user_data')
    co.auto_port()
    
    # Prevent timeouts on slower systems
    co.set_timeouts(base=20, page_load=30)
    
    page = ChromiumPage(co)
    
    try:
        # Start directly at the myMSC portal where the login form is embedded
        print("Navigating to myMSC Login Portal...")
        page.get("https://www.mymsc.com/myMSC/")
        
        # Click cookie banner if it exists ("Accept All" button shown in screenshot)
        cookie_btn = page.ele('text:Accept All', timeout=5) or page.ele('@id=onetrust-accept-btn-handler')
        if cookie_btn:
            print("Accepting cookies...")
            cookie_btn.click()
            time.sleep(1)
            
        print("Looking for MSC email field...")
        email_field = page.ele('@name=signInName', timeout=10) or page.ele('#signInName') or page.ele('@type=email') or page.ele('@name=logonIdentifier')
        if email_field:
            print("Entering email...")
            email_field.input('alejandro.delcarpio@primeteam.com.mx')
            
            # The Next button shown in the screenshot
            next_btn = page.ele('@id=next') or page.ele('text:Next') or page.ele('text:Sign in') or page.ele('@type=submit')
            if next_btn:
                print("Clicking Next...")
                next_btn.click()
                time.sleep(3)
                
            print("Looking for password field...")
            pass_field = page.ele('@name=password', timeout=10) or page.ele('#password') or page.ele('@type=password')
            if pass_field:
                print("Entering password...")
                pass_field.input('Adc19770123$')
                
                # The final submit button after password
                submit_btn = page.ele('@id=next') or page.ele('text:Sign in') or page.ele('text:Next') or page.ele('@type=submit') or page.ele('@id=continue')
                if submit_btn:
                    print("Submitting login...")
                    # Listen to ALL requests to ensure we don't miss the token
                    page.listen.start()
                    submit_btn.click()
                    
                    # Wait for Microsoft B2C login redirects to finish (this can take up to 25 seconds on slow networks)
                    print("Waiting for Microsoft B2C redirects to finish...")
                    time.sleep(25)
                    
                    # Force a navigation to the quote dashboard to guarantee an API call is made with the Bearer token
                    print("Navigating to Quotes page to trigger API call...")
                    page.get("https://www.mymsc.com/myMSC/Quotes/Request")
                    
                    # Wait for the API call that has the Bearer token
                    found_token = None
                    print("Listening for MSC Bearer token...")
                    for packet in page.listen.steps(timeout=30):
                        req_headers = packet.request.headers
                        auth_header = req_headers.get('Authorization') or req_headers.get('authorization')
                        if auth_header and 'Bearer' in auth_header:
                            found_token = auth_header.split('Bearer ')[1]
                            break
                    
                    if found_token:
                        print("Successfully intercepted MSC token!")
                        update_msc_tokens_in_db(found_token)
                    else:
                        print("Failed to intercept MSC token. Check if login was successful.")
        else:
            print("Could not find the MSC login fields. Are we on the right page?")
            
    except Exception as e:
        print(f"Error capturing MSC tokens: {e}")
    finally:
        page.quit()

def fetch_msc_quotes(origin, destination, equipment, commodity="FAK"):
    """
    Uses python requests with the DB token to fetch MSC rates.
    """
    token = get_msc_token_from_db()
    if not token:
        return {"success": False, "error": "MSC Token not found. Scraper may still be initializing."}
        
    print(f"Fetching MSC rates for {origin} -> {destination} using Live Requests API!")
    
    url = 'https://services.mymsc.com/quote/graphql'
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'mymsc-user-email': 'alejandro.delcarpio@primeteam.com.mx',
        'origin': 'https://www.mymsc.com',
        'referer': 'https://www.mymsc.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'
    }
    
    # We are temporarily hardcoding the Shanghai -> Barcelona IDs until UNLOCODE lookup is implemented
    # Shanghai = 7759, Barcelona = 8834
    
    payload = {
        "query": "\n    query InstantQuoteSearchV5($input: RateCardSearchCriteriaInput!) {\n  searchRateCardsV5(request: $input) {\n    shippingWindowBasedGroups {\n      rateCards {\n        myMscId\n        sizeType\n        total\n        subTotal\n        currency\n        scheduleInformation {\n          oceanTransitDays\n          departureDate\n          arrivalDate\n          serviceName\n        }\n      }\n    }\n    vesselBasedGroups {\n      rateCards {\n        myMscId\n        sizeType\n        total\n        subTotal\n        currency\n        scheduleInformation {\n          oceanTransitDays\n          departureDate\n          arrivalDate\n          serviceName\n        }\n      }\n    }\n  }\n}\n    ",
        "variables": {
            "input": {
                "originId": 7759,
                "isOriginAPort": True,
                "destinationId": 8834,
                "isDestinationAPort": True,
                "originTransportationMode": "",
                "destinationTransportationMode": "",
                "originZipcode": "",
                "destinationZipcode": "",
                "equipmentFilter": [
                    {
                        "equipmentType": "20DV" if "20" in equipment else "40HC",
                        "weightValue": 18000
                    }
                ],
                "weightUnit": "Kgs",
                "commodityGroupCode": "",
                "temperature": None,
                "temperatureUnit": None,
                "cargoValue": None,
                "cargoDestinationCountryId": 230,
                "cargoOriginCountryId": 195,
                "commodityGroupDescription": ""
            }
        },
        "operationName": "InstantQuoteSearchV5"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 401:
            return {"success": False, "error": "MSC Token expired or invalid (401). Background scraper needs to refresh."}
            
        response.raise_for_status()
        res_json = response.json()
        
        # Parse GraphQL response
        data = res_json.get('data', {}).get('searchRateCardsV5', {})
        if not data:
            return {"success": False, "error": "Invalid GraphQL response format from MSC"}
            
        groups = data.get('shippingWindowBasedGroups', []) + data.get('vesselBasedGroups', [])
        
        formatted_quotes = []
        for group in groups:
            rate_cards = group.get('rateCards', [])
            for rc in rate_cards:
                sched = rc.get('scheduleInformation', {})
                formatted_quotes.append({
                    "scheduleId": rc.get('myMscId', 'MSC-UNKNOWN'),
                    "departureDate": sched.get('departureDate', ''),
                    "arrivalDate": sched.get('arrivalDate', ''),
                    "transitTime": sched.get('oceanTransitDays', 0),
                    "vesselName": sched.get('serviceName', 'MSC Vessel'),
                    "equipmentName": rc.get('sizeType', ''),
                    "co2": 0,
                    "prices": [
                        {
                            "equipmentType": rc.get('sizeType', ''),
                            "oceanFreight": rc.get('subTotal', 0),
                            "totalCharge": rc.get('total', 0),
                            "currency": rc.get('currency', 'USD')
                        }
                    ]
                })
                
        return {
            "success": True,
            "data": formatted_quotes
        }
    except Exception as e:
        print(f"MSC API Error: {e}")
        return {"success": False, "error": str(e)}
