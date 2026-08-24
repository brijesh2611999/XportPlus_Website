from datetime import datetime

def parse_one_response(real_data: dict) -> dict:
    """
    Parses the raw JSON response from the ONE Tracking API and maps it
    to the unified TrackingResponse SQL schema columns.
    """
    parsed_data = {}
    
    if not real_data.get("data") or len(real_data["data"]) == 0:
        return parsed_data

    item = real_data["data"][0]
    
    # Identifiers
    parsed_data["booking_no"] = item.get("bkgNo")
    parsed_data["bl_no"] = item.get("blNo")
    
    # Origin and Destination
    parsed_data["pol"] = item.get("por", {}).get("locationName")
    parsed_data["pod"] = item.get("pod", {}).get("locationName")
    parsed_data["carrier_line"] = "ONE"
    
    # Latest Event
    latest = item.get("latestEvent", {})
    if latest:
        parsed_data["last_event"] = latest.get("eventName")
        if latest.get("locationName"):
            parsed_data["last_event"] += f" at {latest.get('locationName')}"
            parsed_data["current_location"] = latest.get("locationName")
        if latest.get("date"):
            try:
                date_str = latest.get("date").replace("Z", "+00:00")
                parsed_data["event_date_time"] = datetime.fromisoformat(date_str).replace(tzinfo=None)
            except Exception:
                pass
    
    # Vessel Details
    vessel = item.get("vesselVoyage", {})
    parsed_data["vessel_name"] = vessel.get("vesselName")
    parsed_data["voyage_no"] = vessel.get("voyageNo")
    
    # ETA Final Delivery (Search for max ESTIMATED event)
    events = item.get("cargoEvents", [])
    eta_date = None
    for ev in events:
        if ev.get("trigger") == "ESTIMATED" and ev.get("date"):
            try:
                d_str = ev.get("date").replace("Z", "+00:00")
                d_val = datetime.fromisoformat(d_str).replace(tzinfo=None)
                if not eta_date or d_val > eta_date:
                    eta_date = d_val
            except Exception:
                pass
    
    if eta_date:
        parsed_data["eta_final_delivery"] = eta_date
        parsed_data["eta_pod"] = eta_date
    
    # Map overall status to the latest event activity
    parsed_data["status"] = parsed_data.get("last_event")
    
    return parsed_data
