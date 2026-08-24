from typing import Dict, Any
from datetime import datetime

def parse_yangming_response(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses the Yang Ming JSON response into the normalized format.
    """
    if not json_data or json_data.get("successCnt") == 0:
        return {
            "IsSuccess": False,
            "Message": "No tracking results found for Yang Ming.",
            "Data": None
        }
        
    # Data can be in blList, containerList, or bookingList
    bl_list = json_data.get("blList", [])
    container_list = json_data.get("containerList", [])
    booking_list = json_data.get("bookingList", [])
    
    # We will pick the first available item to extract basic info
    item = None
    if bl_list:
        item = bl_list[0]
    elif container_list:
        item = container_list[0]
    elif booking_list:
        item = booking_list[0]
        
    if not item:
        return {
            "IsSuccess": False,
            "Message": "No tracking results found for Yang Ming.",
            "Data": None
        }
        
    basic_info = item.get("basicInfo", {})
    routing_info = item.get("routingInfo", {})
    schedules = routing_info.get("routingSchedule", [])
    containers = item.get("containerInfo", []) or item.get("dcsaContainerInfo", [])
    
    normalized = {}
    
    # 1. SHIPMENT IDENTIFIERS
    normalized["bl_no"] = item.get("returnTrackNo", "") if item.get("trackTypeCode") == "BLNO" else ""
    normalized["booking_no"] = item.get("bkgRef", "")
    
    # 2. ROUTING
    normalized["vessel_name"] = basic_info.get("vesselName", "")
    normalized["voyage_no"] = basic_info.get("voyageCode", "")
    normalized["carrier_line"] = "Yang Ming"
    normalized["pol"] = basic_info.get("loading", "")
    normalized["pod"] = basic_info.get("discharge", "")
    normalized["final_destination"] = basic_info.get("delivery", "")
    
    # 4. CONTAINER DETAILS
    # Only picking the first container's details if searched by BL
    if containers and isinstance(containers, list):
        c = containers[0]
        normalized["container_no"] = c.get("cntrNo", "")
        normalized["container_size"] = c.get("cntrSize", "")
        normalized["container_type"] = c.get("cntrType", "")
        normalized["seal_no"] = c.get("sealNo", "")
        
    normalized["gross_weight"] = f"{basic_info.get('grossWgt', '')} {basic_info.get('grossWgtUnit', '')}".strip()
    normalized["package_count"] = f"{basic_info.get('numPkg', '')} {basic_info.get('pkgType', '')}".strip()
    
    # Extract latest status from containerInfo or routingSchedule
    latest_activity = ""
    latest_time = None
    
    if containers and isinstance(containers, list):
        # Pick the first container's last event
        c = containers[0]
        latest_activity = c.get("lastEvent", "")
        time_str = c.get("moveDate", "")
        if time_str:
            try:
                latest_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
            except:
                pass
                
    if not latest_activity and schedules:
        # Fallback to the last routing schedule event
        last_route = schedules[-1]
        latest_activity = f"Reached {last_route.get('placeName', '')}"
        time_str = last_route.get("dateTime", "")
        if time_str:
            try:
                latest_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
            except:
                pass

    normalized["last_event"] = latest_activity
    normalized["event_date_time"] = latest_time
    normalized["status"] = latest_activity if latest_activity else "Unknown"
    
    # Extract ETA / DATES
    if schedules:
        for s in schedules:
            qlfr = s.get("picQlfr", "")
            time_str = s.get("dateTime", "")
            if time_str:
                try:
                    dt = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
                    if qlfr == "LOADING":
                        normalized["atd_pol"] = dt
                        normalized["etd_pol"] = dt
                    elif qlfr == "DISCHARGE":
                        normalized["ata_pod"] = dt
                        normalized["eta_pod"] = dt
                    elif qlfr == "DESTINATION":
                        normalized["eta_final_delivery"] = dt
                except:
                    pass

    return {
        "IsSuccess": True,
        "Message": "Yang Ming tracking data parsed successfully.",
        "Data": normalized
    }
