import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

def parse_evergreen_response(real_data: dict) -> dict:
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
    
    html_str = real_data.get("raw_html", "")
    if not html_str:
        return parsed
        
    soup = BeautifulSoup(html_str, "html.parser")
    
    # 1. Extract ETA
    # Example: Estimated Date of Arrival : <br/>SEP-06-2026
    eta_td = soup.find(lambda tag: tag.name == "td" and "Estimated Date of Arrival" in tag.text)
    if eta_td:
        text = eta_td.get_text(" ", strip=True)
        m = re.search(r'Arrival\s*:\s*([A-Za-z]{3}-\d{2}-\d{4})', text)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%b-%d-%Y")
                parsed["eta_final_delivery"] = dt.isoformat()
            except:
                pass
                
    # 2. Extract Vessel/Voyage
    # Vessel Voyage on B/L -> EVER EXCEL 194E
    vsl_th = soup.find(lambda tag: tag.name == "th" and "Vessel Voyage on B/L" in tag.text)
    if vsl_th:
        vsl_td = vsl_th.find_next_sibling("td")
        if vsl_td:
            text = vsl_td.get_text(" ", strip=True)
            # Remove chinese chars
            text = re.sub(r'\(.*?\)', '', text).strip()
            parts = text.rsplit(' ', 1)
            if len(parts) == 2:
                parsed["vessel_name"] = parts[0]
                parsed["voyage_no"] = parts[1]

    # 3. Events
    tables = soup.find_all("table", class_="ec-table")
    for table in tables:
        if "Container(s) information" in table.text or "Container No." in table.text:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 6:
                    texts = [c.get_text(" ", strip=True) for c in cols]
                    if len(texts[0]) >= 10:  # Container No looks like EGSU3255911
                        # Container No | Size/Type | Date | Container Moves | Location | Vessel Voyage
                        date_str = texts[2]
                        activity = texts[3]
                        location = texts[4]
                        vsl = texts[5] if len(texts) > 5 else ""
                        
                        dt = None
                        if date_str:
                            try:
                                dt = datetime.strptime(date_str, "%b-%d-%Y").isoformat()
                            except:
                                dt = date_str
                                
                        parsed["_events_json"].append({
                            "description": activity,
                            "location": location,
                            "date": dt,
                            "vessel": vsl
                        })
                        
    return parsed
