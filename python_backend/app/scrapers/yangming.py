import requests
from typing import Dict, Any, Optional

def scrape_yangming(tracking_number: str) -> Optional[Dict[str, Any]]:
    """
    Scrapes the Yang Ming tracking API.
    The API is mostly open for GET requests.
    """
    url = f"https://www.yangming.com/api/CargoTracking/GetTracking?paramTrackNo={tracking_number}&paramTrackPosition=SEARCH&paramRefNo="
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Referer": "https://www.yangming.com/en/esolution/cargo_tracking"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return {
            "raw_html": response.text,  # Not HTML, but keeping the key consistent
            "raw_json": data,
            "title": "Yang Ming Tracking"
        }
    except Exception as e:
        print(f"Failed to scrape Yang Ming: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        res = scrape_yangming(sys.argv[1])
        print(json.dumps(res, indent=2))
