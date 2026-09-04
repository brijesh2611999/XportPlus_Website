from curl_cffi import requests

class DeltaScraper:
    """
    Scraper for Delta Cargo (Prefix 006)
    Note: Delta uses Akamai (indicated by cookies). Using curl_cffi to bypass.
    """
    
    BASE_URL = "https://www.deltacargo.com/Cargo/data/shipment/trackAwb?awbNumber={}&timeZoneOffset=-330"

    def __init__(self):
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "dnt": "1",
            "referer": "https://www.deltacargo.com/Cargo/",
            "sec-ch-ua": "\"Not=A?Brand\";v=\"99\", \"Google Chrome\";v=\"151\", \"Chromium\";v=\"151\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        }

    def scrape(self, awb_number: str) -> dict:
        """
        Fetches and parses the tracking data for a Delta AWB number.
        The AWB number should ideally be 11 digits (e.g. 00631741301).
        """
        # Clean AWB
        clean_awb = awb_number.replace('-', '').strip()
        if len(clean_awb) == 8:
            clean_awb = f"006{clean_awb}"
            
        url = self.BASE_URL.format(clean_awb)
        
        try:
            # Use curl_cffi to impersonate Chrome and bypass Akamai
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=15, 
                impersonate="chrome"
            )
            
            if response.status_code != 200:
                response.raise_for_status()
            
            data = response.json()
            
            # The actual tracking data is inside data -> trackShipment
            track_data_list = data.get("data", {}).get("trackShipment", [])
            
            if not track_data_list:
                return {"success": False, "error": "No tracking data found for this AWB."}
                
            shipment = track_data_list[0]
            
            # Normalize Data
            # Origin and dest aren't explicitly at the root level, we have to look at the first and last flights or house AWB
            # Let's try to get it from flight tracking or history
            flight_tracking = shipment.get("flightTracking", [])
            
            origin = "Unknown"
            dest = "Unknown"
            flight_number = "Unknown"
            
            if flight_tracking:
                origin = flight_tracking[0].get("source", "Unknown")
                dest = flight_tracking[-1].get("destination", "Unknown")
                flight_number = flight_tracking[0].get("flightNumber", "Unknown")
            
            # Status and ETA
            status = shipment.get("shipmentStatus", "Unknown") 
            # Status is a number in Delta (e.g., "7" = Delivered/Arrived). We'll try to map it based on latest history event instead
            
            pcs = shipment.get("pieces", 0)
            weight = shipment.get("weight", 0)
            unit = shipment.get("weightUnit", "lb")
            pieces_weight = f"{pcs} pcs / {weight} {unit}"
            
            # Events and Latest Time
            events = []
            latest_time = "Unknown"
            eta = "TBD"
            
            history = shipment.get("history", [])
            
            # Delta history is ordered newest first. Let's reverse it to chronological, or just parse as is.
            # We want chronological for our standard format.
            for event in reversed(history):
                # Date format: 07/07/2026, localTime: 0921
                d = event.get("date", "")
                t = event.get("localTime", "")
                
                dt = f"{d} {t}" if d else None
                
                # We can grab latest status from the most recent event (which is the first item in Delta's list)
                desc = event.get("activity", "").replace("<b>", "").replace("</b>", "")
                loc = event.get("origin", "")
                
                events.append({
                    "code": "EVT", # Delta doesn't use standard 3-letter codes in this payload
                    "status": desc,
                    "date_time": dt,
                    "location": loc
                })
                
            if history:
                # Top event is latest
                latest_event = history[0]
                latest_time = f"{latest_event.get('date', '')} {latest_event.get('localTime', '')}"
                status = latest_event.get("activity", "").replace("<b>", "").replace("</b>", "")
                
                if origin == "Unknown":
                    origin = history[-1].get("origin", "Unknown")
                if dest == "Unknown":
                    dest = history[0].get("origin", "Unknown") # Approximate
            
            normalized = {
                "status": status,
                "latest_event_time": latest_time,
                "origin_airport": origin,
                "destination_airport": dest,
                "flight_number": flight_number,
                "pieces_weight": pieces_weight,
                "eta": eta,
                "events": events
            }
            
            return {
                "success": True,
                "carrier": "Delta",
                "awb": f"006-{clean_awb[3:]}" if clean_awb.startswith("006") else clean_awb,
                "normalized": normalized,
                "raw_data": data
            }
            
        except requests.RequestsError as e:
            return {"success": False, "error": f"Failed to connect to Delta API (Check Akamai block): {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error parsing Delta response: {str(e)}"}
