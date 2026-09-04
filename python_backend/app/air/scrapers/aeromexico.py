import requests
from app.air.parsers.fsu_parser import FSUParser

class AeroMexicoScraper:
    """
    Scraper for AeroMexico Cargo (Prefix 139)
    """
    
    BASE_URL = "https://serv-amcargo.amsrvc.com/back-office/api/track/v3/139/{}"

    def __init__(self):
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://amcargo.aeromexico.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        }

    def scrape(self, awb_number: str) -> dict:
        """
        Fetches and parses the tracking data for an AWB number.
        The AWB number should ideally be 8 digits (excluding the 139 prefix).
        """
        # Clean AWB (remove hyphens, prefix if accidentally included)
        clean_awb = awb_number.replace('-', '').strip()
        if clean_awb.startswith('139'):
            clean_awb = clean_awb[3:]
            
        url = self.BASE_URL.format(clean_awb)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            raw_fsu_string = data.get("data", "")
            
            if not raw_fsu_string:
                return {"success": False, "error": "No tracking data found for this AWB."}
                
            # Parse FSU
            normalized = FSUParser.parse(raw_fsu_string)
            
            return {
                "success": True,
                "carrier": "AeroMexico",
                "awb": f"139-{clean_awb}",
                "normalized": normalized,
                "raw_data": data
            }
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Failed to connect to AeroMexico API: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error parsing AeroMexico response: {str(e)}"}

