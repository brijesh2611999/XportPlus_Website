import json
import re

def parse_cma_html(html_source):
    """
    Parses the CMA CGM tracking HTML source.
    Extracts the JSON payload injected into options.responseData.
    """
    # Look for the JSON payload in the script tag
    match = re.search(r"options\.responseData\s*=\s*'(\{.*?\})';", html_source, re.DOTALL)
    
    if not match:
        return {"error": "Could not find tracking data in CMA-CGM response. The session might be blocked by DataDome."}
    
    try:
        data = json.loads(match.group(1).replace("\\'", "'")) # handle any escaped quotes if present
    except Exception as e:
        return {"error": f"Failed to parse JSON data: {str(e)}"}
        
    container_no = data.get("ContainerReference", "")
    bl_no = data.get("BLNumber", "")
    booking_no = data.get("BookingNumber", "")
    
    all_moves = []
    
    # CMA organizes moves into Past, Current, and Provisional
    for key in ["PastMoves", "CurrentMoves", "ProvisionalMoves"]:
        moves = data.get(key)
        if isinstance(moves, list):
            for move in moves:
                date_str = move.get("Date", "").replace("T", " ")
                desc = move.get("StatusDescription", "")
                loc = move.get("Location", "")
                vessel = move.get("Vessel", "")
                voyage = move.get("Voyage", "")
                
                all_moves.append({
                    "date": date_str,
                    "description": desc,
                    "location": loc,
                    "vessel": vessel,
                    "voyage_no": voyage
                })
                
    normalized = {
        "container_no": container_no,
        "bl_no": bl_no,
        "booking_no": booking_no,
        "events": all_moves
    }
    
    return normalized
