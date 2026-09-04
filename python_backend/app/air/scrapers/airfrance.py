from curl_cffi import requests

class AirFranceScraper:
    """
    Scraper for Air France / KLM Cargo (Prefix 057, 074)
    Note: AFKL API may sit behind Akamai. If requests block or timeout, 
    this scraper may need to be upgraded to use curl_cffi or Playwright to bypass TLS fingerprinting.
    """
    
    BASE_URL = "https://www.afklcargo.com/mycargo/api/tnt-api/shipments/{}"

    def __init__(self):
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "dnt": "1",
            "referer": "https://www.afklcargo.com/mycargo/",
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
        Fetches and parses the tracking data for an AF/KLM AWB number.
        The AWB number should ideally be 11 digits (e.g. 057-05223072).
        """
        # Clean AWB
        clean_awb = awb_number.strip()
        if len(clean_awb.replace('-', '')) == 11 and '-' not in clean_awb:
            clean_awb = f"{clean_awb[:3]}-{clean_awb[3:]}"
            
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
            
            if not data or not isinstance(data, list):
                return {"success": False, "error": "No tracking data found for this AWB."}
                
            shipment_data = data[0]
            
            # Normalize Data
            shipment_info = shipment_data.get("shipment", {})
            origin = shipment_info.get("originDestination", {}).get("departureLocation", "Unknown")
            dest = shipment_info.get("originDestination", {}).get("arrivalLocation", "Unknown")
            status = shipment_info.get("shipmentStage", {}).get("status", "Unknown")
            
            chars = shipment_data.get("shipmentCharacteristics", {})
            pcs = chars.get("totalPieceCount", 0)
            weight = chars.get("totalGrossWeight", {}).get("value", 0)
            unit = chars.get("totalGrossWeight", {}).get("unit", "KG")
            pieces_weight = f"{pcs} pcs / {weight} {unit}"
            
            # Flight details
            flight_number = "Unknown"
            flight_plan = shipment_data.get("flightPlan", {}).get("segmentDetails", [])
            for seg in flight_plan:
                if seg.get("modeCodeDescription") == "Air transport":
                    flight_number = seg.get("transportIdentifier", flight_number)
            
            # Events and Latest Time
            events = []
            latest_time = "Unknown"
            eta = "TBD"
            
            milestones = shipment_data.get("milestones", {}).get("events", [])
            for event in milestones:
                code = event.get("eventCode")
                loc = event.get("eventLocation", "")
                
                # Extract time
                dt_obj = event.get("eventActualTime", {}).get("dateTime", {})
                if dt_obj:
                    # Construct basic ISO string from their weird date format
                    date = dt_obj.get("date", {})
                    time = dt_obj.get("time", {})
                    if date and time:
                        dt = f"{date.get('year')}-{date.get('month'):02d}-{date.get('day'):02d}T{time.get('hour'):02d}:{time.get('minute'):02d}:{time.get('second'):02d}"
                        latest_time = dt
                else:
                    dt = None
                    
                desc = code
                if code == "BKG": desc = "Booked"
                elif code == "FWB": desc = "Waybill Received"
                elif code == "FOH": desc = "Freight on Hand"
                elif code == "RCS": desc = "Received from Shipper"
                elif code == "DEP": desc = "Departed"
                elif code == "ARR": desc = "Arrived"
                elif code == "RCF": desc = "Received from Flight"
                elif code == "NFD": desc = "Consignee Notified"
                elif code == "AWD": desc = "Documents Delivered"
                elif code == "DLV": desc = "Delivered"

                events.append({
                    "code": code,
                    "status": desc,
                    "date_time": dt,
                    "location": loc
                })
            
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
                "carrier": "Air France",
                "awb": clean_awb,
                "normalized": normalized,
                "raw_data": data
            }
            
        except requests.RequestsError as e:
            return {"success": False, "error": f"Failed to connect to Air France API (Check Akamai block): {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error parsing Air France response: {str(e)}"}
