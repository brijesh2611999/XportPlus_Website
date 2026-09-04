import re
from datetime import datetime

def parse_pil_response(real_data: dict) -> dict:
    parsed = {
        "status": "In Transit",
        "event_date_time": None,
        "pol": None,
        "pod": None,
        "vessel_name": None,
        "voyage_no": None,
        "eta_final_delivery": None,
        "_events_json": []
    }
    
    text = real_data.get("raw_scraped_text", "")
    if not text:
        return parsed
        
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        if "Load Port" in line:
            if i + 1 < len(lines):
                parsed["pol"] = lines[i + 1]
        elif "Discharge Port" in line:
            if i + 1 < len(lines):
                parsed["pod"] = lines[i + 1]
                
        # Try to extract Vessel/Voyage (Usually all caps with numbers for voyage)
        if re.match(r'^[A-Z\s]+$', line) and i + 1 < len(lines) and re.match(r'^[A-Z0-9]+$', lines[i+1]):
            # Heuristic to find vessel/voyage if not already found
            if not parsed["vessel_name"] and "PORT" not in line and len(line) > 3:
                parsed["vessel_name"] = line
                parsed["voyage_no"] = lines[i+1]
                
        # Look for dates to guess the latest event
        date_match = re.search(r'(\d{2}-[A-Za-z]{3}-\d{4})', line)
        if date_match:
            try:
                parsed["event_date_time"] = datetime.strptime(date_match.group(1), "%d-%b-%Y")
                parsed["status"] = "In Transit (Tracking Active)"
            except:
                pass
                
    return {"Data": parsed}
