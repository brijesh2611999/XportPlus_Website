import requests

class LufthansaScraper:
    """
    Scraper for Lufthansa Cargo (Prefix 020)
    """
    
    BASE_URL = "https://api-external.lufthansa-cargo.com/stp/shipments-details/{}"

    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.lufthansa-cargo.com",
            "referer": "https://www.lufthansa-cargo.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        }

    def scrape(self, awb_number: str) -> dict:
        """
        Fetches and parses the tracking data for a Lufthansa AWB number.
        The AWB number should ideally be 11 digits (e.g. 02005985361).
        """
        # Clean AWB (remove hyphens)
        clean_awb = awb_number.replace('-', '').strip()
        
        # Ensure it has the prefix if it was omitted, or just use as is if they passed the full 11 digits
        if len(clean_awb) == 8:
            clean_awb = f"020{clean_awb}"
            
        url = self.BASE_URL.format(clean_awb)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # If not available or missing key details
            if not data.get("availabilityDetails", {}).get("isAvailable", False):
                 pass # Actually the JSON response sometimes says isAvailable: false for customs, but we still have data. Let's rely on awbDetails
            
            awb_details = data.get("awbDetails")
            if not awb_details:
                return {"success": False, "error": "No tracking data found for this AWB."}
                
            # Normalize Data
            origin = awb_details.get("originAirport", {}).get("airportCode", "Unknown")
            dest = awb_details.get("destinationAirport", {}).get("airportCode", "Unknown")
            
            # Pieces and weight
            pcs_info = awb_details.get("piecesInformation", {})
            pcs = pcs_info.get("piecesCount", 0)
            weight = pcs_info.get("piecesWeight", 0)
            pieces_weight = f"{pcs} pcs / {weight} kg"
            
            # Status and ETA
            status = awb_details.get("latestEvent", "Unknown")
            eta = awb_details.get("plannedTimeOfAvailability", "TBD")
            
            # Get latest event time from status histories
            latest_time = "Unknown"
            events = []
            histories = data.get("statusHistories", [])
            for hist in histories:
                event_code = hist.get("cargoEventType")
                actual_event = hist.get("actualCargoEvent", {})
                dt = actual_event.get("eventDateTime") if actual_event else None
                
                # Try to map status code
                desc = event_code
                if event_code == "BKD": desc = "Booked"
                elif event_code == "RCS": desc = "Received from Shipper"
                elif event_code == "DEP": desc = "Departed"
                elif event_code == "ARR": desc = "Arrived"
                elif event_code == "NFD": desc = "Consignee Notified"
                elif event_code == "DLV": desc = "Delivered"
                elif event_code == "MAN": desc = "Manifested"
                elif event_code == "RCF": desc = "Received from Flight"
                elif event_code == "FOH": desc = "Freight on Hand"
                
                loc = hist.get("stationAirport", {}).get("airportCode", "")
                
                events.append({
                    "code": event_code,
                    "status": desc,
                    "date_time": dt,
                    "location": loc
                })
                
                if dt: # Just grabbing the last valid one sequentially
                    latest_time = dt
            
            # Flight details
            flight_number = "Unknown"
            flights = data.get("flightInformation", [])
            if flights:
                flight_number = flights[-1].get("flightNumber", "Unknown")
            
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
                "carrier": "Lufthansa",
                "awb": f"020-{clean_awb[3:]}" if clean_awb.startswith("020") else clean_awb,
                "normalized": normalized,
                "raw_data": data
            }
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Failed to connect to Lufthansa API: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error parsing Lufthansa response: {str(e)}"}
