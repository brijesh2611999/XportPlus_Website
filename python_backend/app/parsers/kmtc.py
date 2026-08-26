from datetime import datetime

def parse_kmtc_response(api1_data, api2_data):
    """
    Parses KMTC response combining two API payloads:
    1. Cargo Tracking base (cntrList)
    2. Close Info (routing and dates)
    """
    parsed = {}
    
    # 1. Base Container Info
    if api1_data and "cntrList" in api1_data and len(api1_data["cntrList"]) > 0:
        cntr = api1_data["cntrList"][0]
        parsed["container_no"] = cntr.get("cntrNo")
    
    # 2. Detailed Routing (Close Info)
    if api2_data:
        parsed["booking_no"] = api2_data.get("bkgNo")
        parsed["vessel_name"] = api2_data.get("vslNm")
        parsed["voyage_no"] = api2_data.get("voyNo")
        
        # Ports
        parsed["pol"] = api2_data.get("polPortEnm")
        parsed["pod"] = api2_data.get("podPortEnm")
        parsed["final_destination"] = api2_data.get("dlyPlcEnm")
        
        # Cargo Details
        parsed["gross_weight"] = api2_data.get("grsWt")
        parsed["cargo_description"] = api2_data.get("cmdtDsc")
        
        # Parse Dates (Format: "202609110700" -> YYYYMMDDHHMM)
        etd_raw = api2_data.get("etd")
        if etd_raw and len(etd_raw) >= 12:
            try:
                parsed["etd_pol"] = datetime.strptime(etd_raw[:12], "%Y%m%d%H%M")
            except ValueError:
                pass
                
        eta_raw = api2_data.get("eta")
        if eta_raw and len(eta_raw) >= 12:
            try:
                parsed["eta_pod"] = datetime.strptime(eta_raw[:12], "%Y%m%d%H%M")
                parsed["eta_final_delivery"] = parsed["eta_pod"]
            except ValueError:
                pass
                
        # Status
        status_code = api2_data.get("bkgStsCd")
        if status_code == "01":
            parsed["status"] = "BOOKING CONFIRMED"
        elif api2_data.get("vslClosed") == "Y":
            parsed["status"] = "DEPARTED"
        else:
            parsed["status"] = "IN TRANSIT"

    # Clean up empty values
    return {k: v for k, v in parsed.items() if v}
