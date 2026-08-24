from datetime import datetime

def parse_msc_response(real_data: dict) -> dict:
    """
    Parses the raw JSON response from the MSC Tracking API and maps it
    to the unified TrackingResponse SQL schema columns.
    """
    parsed_data = {}
    
    if not real_data or not real_data.get("IsSuccess"):
        return parsed_data
        
    data_block = real_data.get("Data", {})
    bls = data_block.get("BillOfLadings", [])
    if not bls:
        return parsed_data
        
    bl = bls[0]
    
    # Identifiers
    parsed_data["bl_no"] = bl.get("BillOfLadingNumber")
    
    # Origin and Destination
    general_info = bl.get("GeneralTrackingInfo", {})
    parsed_data["pol"] = general_info.get("ShippedFrom") or general_info.get("PortOfLoad")
    parsed_data["pod"] = general_info.get("ShippedTo") or general_info.get("PortOfDischarge")
    parsed_data["transhipment_port"] = general_info.get("Transhipment")
    parsed_data["carrier_line"] = "MSC"
    
    containers = bl.get("ContainersInfo", [])
    if containers:
        container = containers[0]
        
        parsed_data["container_no"] = container.get("ContainerNumber")
        parsed_data["container_type"] = container.get("ContainerType")
        
        # ETA
        if container.get("PodEtaDate"):
            try:
                # Format: "29/09/2026"
                date_str = container.get("PodEtaDate")
                parsed_data["eta_pod"] = datetime.strptime(date_str, "%d/%m/%Y")
                parsed_data["eta_final_delivery"] = datetime.strptime(date_str, "%d/%m/%Y")
            except Exception:
                pass
                
        # Events (usually sorted descending by Order)
        events = container.get("Events", [])
        if events:
            # We'll take the first event in the array (which seems to be the latest by Order/Date)
            latest = events[0]
            
            parsed_data["last_event"] = latest.get("Description")
            if latest.get("Location"):
                parsed_data["last_event"] += f" at {latest.get('Location')}"
                parsed_data["current_location"] = latest.get("Location")
                
            if latest.get("Date"):
                try:
                    # Format: "29/09/2026"
                    parsed_data["event_date_time"] = datetime.strptime(latest.get("Date"), "%d/%m/%Y")
                except Exception:
                    pass
                    
            vessel_info = latest.get("Vessel", {})
            parsed_data["vessel_name"] = vessel_info.get("IMO") or "Unassigned"
            
            # The Detail array usually contains Vessel Name and Voyage
            detail = latest.get("Detail", [])
            if len(detail) >= 2:
                parsed_data["vessel_name"] = detail[0]
                parsed_data["voyage_no"] = detail[1]
                
    parsed_data["status"] = parsed_data.get("last_event")
    
    return parsed_data
