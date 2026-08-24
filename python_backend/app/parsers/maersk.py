from datetime import datetime

def parse_maersk_response(raw_data: dict) -> dict:
    """
    Parses the raw Maersk JSON response into normalized fields for the database.
    """
    normalized = {}
    
    if not isinstance(raw_data, dict):
        return normalized
        
    try:
        # Extract origin and destination
        normalized["pol"] = raw_data.get("origin", {}).get("city", "")
        normalized["pod"] = raw_data.get("destination", {}).get("city", "")
            
        containers = raw_data.get("containers", [])
        if containers and isinstance(containers, list):
            container = containers[0]
            
            # Shipment identifiers
            normalized["container_no"] = container.get("container_num", "")
            
            # Container details
            normalized["container_size"] = container.get("container_size", "")
            normalized["container_type"] = container.get("container_type", "")
            
            # Status
            normalized["status"] = container.get("status", "")
            
            # ETA Final Delivery
            eta_str = container.get("eta_final_delivery")
            if eta_str:
                try:
                    normalized["eta_final_delivery"] = datetime.strptime(eta_str.split(".")[0].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass
            
            # Find latest event by iterating through locations and events
            latest_time = None
            latest_activity = ""
            vessel = ""
            voyage = ""
            current_location = ""
            
            locations = container.get("locations", [])
            for loc in locations:
                events = loc.get("events", [])
                for event in events:
                    event_time_str = event.get("event_time")
                    if event_time_str:
                        try:
                            # Format is usually 2026-07-30T04:46:00.000
                            dt = datetime.strptime(event_time_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                            if not latest_time or dt > latest_time:
                                latest_time = dt
                                latest_activity = event.get("activity", "")
                                current_location = loc.get("city", "")
                                
                                # Vessel info is usually attached to LOAD/DISCHARGE events
                                if event.get("vessel_name"):
                                    vessel = event.get("vessel_name")
                                if event.get("voyage_num"):
                                    voyage = event.get("voyage_num")
                        except Exception:
                            continue
                            
            if latest_time:
                normalized["event_date_time"] = latest_time
            if latest_activity:
                normalized["last_event"] = latest_activity
            if current_location:
                normalized["current_location"] = current_location
            if vessel:
                normalized["vessel_name"] = vessel
            if voyage:
                normalized["voyage_no"] = voyage
                
            normalized["carrier_line"] = "Maersk"
                
    except Exception as e:
        print(f"Error parsing Maersk data for DB: {e}")
        
    return normalized
