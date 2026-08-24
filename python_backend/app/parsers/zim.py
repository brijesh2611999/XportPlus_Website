from datetime import datetime

def parse_zim_response(real_data: dict) -> dict:
    """
    Parses the raw JSON response from the ZIM Tracking API and maps it
    to the unified TrackingResponse SQL schema columns.
    """
    parsed_data = {}
    
    unit_list = real_data.get("unitListItem", [])
    if not unit_list:
        return parsed_data
        
    item = unit_list[0]
    
    # Identifiers
    prefix = item.get("unitPrefix", "")
    no = item.get("unitNo", "")
    if prefix or no:
        parsed_data["container_no"] = f"{prefix}{no}"    
    # ETA
    final_eta = item.get("finalEta", {})
    if final_eta.get("etaDelDate") or final_eta.get("etaPodDate"):
        try:
            date_str = final_eta.get("etaDelDate") or final_eta.get("etaPodDate")
            parsed_data["eta_final_delivery"] = datetime.fromisoformat(date_str).replace(tzinfo=None)
        except Exception:
            pass
            
    # Activities
    activities = item.get("unitActivities", {}).get("unitActivitiesItem", [])
    if activities:
        latest = activities[-1]
        
        parsed_data["last_event"] = latest.get("activityDesc")
        if latest.get("placeFromDesc"):
            parsed_data["last_event"] += f" at {latest.get('placeFromDesc')}"
            parsed_data["current_location"] = latest.get("placeFromDesc")
            
        if latest.get("activityDateTz"):
            try:
                date_str = latest.get("activityDateTz")
                parsed_data["event_date_time"] = datetime.fromisoformat(date_str).replace(tzinfo=None)
            except Exception:
                pass
                
        parsed_data["vessel_name"] = latest.get("vesselName")
        parsed_data["voyage_no"] = latest.get("voyage")
        
    # Routing (Origin and Destination)
    routing = item.get("vpBrl", {}).get("vpBrl", [])
    if routing:
        first_leg = routing[0]
        last_leg = routing[-1]
        parsed_data["pol"] = first_leg.get("portNameFrom") or first_leg.get("depotNameFrom")
        parsed_data["pod"] = last_leg.get("portNameTo") or last_leg.get("depotNameTo")
        
    parsed_data["status"] = parsed_data.get("last_event")
    parsed_data["carrier_line"] = "ZIM"
    
    return parsed_data
