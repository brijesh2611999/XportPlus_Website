from DrissionPage import ChromiumOptions, ChromiumPage
import time
import json

def sniff_msc():
    print("Attaching to active browser...")
    co = ChromiumOptions()
    # Attach to the existing browser on port 9222
    co.set_local_port(9222)
    page = ChromiumPage(co)
    
    print(f"Connected to page: {page.title} - {page.url}")
    
    # Start listening to all network traffic
    page.listen.start('')
    print("\n" + "="*50)
    print("Listening for Network Requests...")
    print("PLEASE GO TO YOUR BROWSER AND CLICK 'SEARCH' TO FETCH RATES NOW!")
    print("="*50 + "\n")
    
    found_api = False
    start_time = time.time()
    
    # Listen for up to 60 seconds
    while time.time() - start_time < 60:
        for packet in page.listen.steps(timeout=1):
            url = packet.request.url
            method = packet.request.method
            
            if method == 'POST' and ('datadoghq' not in url.lower()) and ('applicationinsights' not in url.lower()) and ('clarity.ms' not in url.lower()):
                print(f"\n[DETECTED MSC POST REQUEST] {url}")
                print("HEADERS:")
                for k, v in packet.request.headers.items():
                    # Print authorization tokens if found
                    if k.lower() == 'authorization' or k.lower() == 'cookie' or 'token' in k.lower():
                        print(f"  {k}: {v[:100]}... (truncated)")
                
                try:
                    payload = packet.request.postData
                    print(f"PAYLOAD: {payload}")
                    found_api = True
                except Exception as e:
                    print(f"Could not parse payload: {e}")
                    
        if found_api:
            break
            
    page.listen.stop()
    if not found_api:
        print("Timed out waiting for requests. Did you click search?")

if __name__ == '__main__':
    sniff_msc()
