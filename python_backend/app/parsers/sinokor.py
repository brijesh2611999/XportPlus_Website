from bs4 import BeautifulSoup
from datetime import datetime

def parse_sinokor_response(html_content: str) -> dict:
    """
    Parses the full HTML payload from Sinokor.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    parsed = {
        "status": "In Transit",
        "event_date_time": None,
        "pol": None,
        "pod": None,
        "vessel_name": None,
        "voyage_no": None,
        "eta_final_delivery": None
    }
    
    # 1. Parse Routing details from Schedule Info list items (.form-both .liLeft)
    li_lefts = soup.find_all('div', class_='liLeft')
    if li_lefts:
        # Get first leg for origin
        first_leg = li_lefts[0]
        vsl_elem = first_leg.find('a', href=lambda h: h and 'viewVslInfo' in h)
        if vsl_elem:
            vsl_text = vsl_elem.text.strip()
            # e.g. MUMBAI BRIDGE / 2604E
            if " / " in vsl_text:
                parsed["vessel_name"] = vsl_text.split(" / ")[0]
                parsed["voyage_no"] = vsl_text.split(" / ")[1]
        
        col8s = first_leg.find_all('div', class_='col-sm-6')
        if len(col8s) >= 1:
            pol_b = col8s[0].find('b')
            if pol_b:
                parsed["pol"] = pol_b.text.strip()
                
        # Get last leg for destination
        last_leg = li_lefts[-1]
        col8s_last = last_leg.find_all('div', class_='col-sm-6')
        if len(col8s_last) >= 2:
            pod_b = col8s_last[1].find('b')
            if pod_b:
                parsed["pod"] = pod_b.text.strip()
    
    # 2. Parse Events Table
    table = soup.find('table', {'id': 'tblResult'})
    if table and table.find('tbody'):
        rows = table.find('tbody').find_all('tr')
        if rows:
            latest_row = None
            for row in reversed(rows):
                cols = row.find_all('td')
                if len(cols) >= 4:
                    latest_row = row
                    break
            
            if latest_row:
                cols = latest_row.find_all('td')
                parsed["status"] = cols[0].text.strip()
                date_time_str = cols[3].text.strip()
                # Format: 2026-08-24 MON 15:00
                if date_time_str and date_time_str != "-":
                    try:
                        # Extract YYYY-MM-DD HH:MM
                        parts = date_time_str.split(" ")
                        if len(parts) >= 3:
                            clean_dt = f"{parts[0]} {parts[2]}"
                            parsed["event_date_time"] = datetime.strptime(clean_dt, "%Y-%m-%d %H:%M")
                    except Exception:
                        pass
                        
            # Try to find final ETA from Arrival events
            for row in reversed(rows):
                cols = row.find_all('td')
                if len(cols) >= 4:
                    evt = cols[0].text.strip().lower()
                    if "arrival" in evt and "(t/s)" not in evt:
                        dt_str = cols[3].text.strip()
                        if dt_str and dt_str != "-":
                            try:
                                parts = dt_str.split(" ")
                                if len(parts) >= 3:
                                    clean_dt = f"{parts[0]} {parts[2]}"
                                    parsed["eta_final_delivery"] = datetime.strptime(clean_dt, "%Y-%m-%d %H:%M")
                            except Exception:
                                pass
                        break

    return parsed
