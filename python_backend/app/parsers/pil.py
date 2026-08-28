import json
from datetime import datetime
from bs4 import BeautifulSoup

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
    
    html_str = real_data.get("data", "")
    if not html_str:
        return parsed
        
    html_str = html_str.replace('\\/', '/')
    soup = BeautifulSoup(html_str, "html.parser")

    # 1. Routing Info
    routing_rows = soup.find_all("tr", class_="resultrow")
    for row in routing_rows:
        loc_td = row.find("td", class_="location")
        if loc_td:
            text = loc_td.get_text(separator="|").strip()
            if "Load Port" in text:
                parts = text.split("|")
                if len(parts) > 1:
                    parsed["pol"] = parts[1]
            elif "Discharge Port" in text:
                parts = text.split("|")
                if len(parts) > 1:
                    parsed["pod"] = parts[1]
                
        vsl_td = row.find("td", class_="vessel-voyage")
        if vsl_td:
            text = vsl_td.get_text(separator="|").strip()
            parts = [p for p in text.split("|") if p.strip()]
            if len(parts) >= 2:
                parsed["vessel_name"] = parts[0]
                parsed["voyage_no"] = parts[1]

    # 2. Events List
    events_tbody = soup.find("tbody", id=lambda x: x and x.startswith("container_info_sub_"))
    if events_tbody:
        rows = events_tbody.find_all("tr")
        latest_event = None
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                vessel = cols[0].text.strip()
                voyage = cols[1].text.strip()
                date_str = cols[2].text.strip().replace("*", "").strip()
                event_name = cols[3].text.strip()
                event_place = cols[4].text.strip()
                
                parsed["_events_json"].append({
                    "vessel": vessel,
                    "voyage": voyage,
                    "date": date_str,
                    "event": event_name,
                    "location": event_place
                })
                
                # Keep track of latest valid date
                if date_str != "Information Not Available":
                    latest_event = {
                        "event": event_name,
                        "date": date_str,
                        "location": event_place
                    }

        if latest_event:
            parsed["status"] = latest_event["event"]
            try:
                parsed["event_date_time"] = datetime.strptime(latest_event["date"], "%d-%b-%Y %H:%M:%S")
            except Exception as e:
                pass

    return parsed
