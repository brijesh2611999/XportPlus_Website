from bs4 import BeautifulSoup
from typing import Dict, Any

def parse_cosco_html(html_content: str) -> Dict[str, Any]:
    """
    Parse the raw HTML returned by the COSCO Playwright scraper.
    """
    if not html_content:
        return {"error": "No HTML content provided"}
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for empty state
    texts = soup.get_text(separator=' ', strip=True)
    if "No results found" in texts or "No map result" in texts:
        return {
            "IsSuccess": False,
            "Message": "No results found (ongoing shipments or completed shipments within the last 6 months).",
            "Data": None
        }
    
    # Extract normalized data
    normalized = {}
    
    # 1. Look for transport and schedule rows (they use .ant-table-row)
    rows = soup.find_all('tr', class_='ant-table-row')
    
    from datetime import datetime
    import re
    
    for row in rows:
        cols = [col.get_text(separator=' ', strip=True) for col in row.find_all('td')]
        
        # Check if it's a transport detail row (usually has 6 cols and first is a number)
        if len(cols) == 6 and cols[0].isdigit():
            normalized['container_number'] = cols[1]
            status_text = cols[5]
            if " At " in status_text:
                parts = status_text.split(" At ")
                normalized['latest_event_activity'] = parts[0].strip()
                try:
                    normalized['latest_event_time'] = datetime.strptime(parts[1].strip(), "%Y-%m-%d %H:%M:%S")
                except:
                    pass
                    
        # Check if it's a schedule detail row (usually 6 cols, no digit first, has "Expected:" / "Actual:")
        elif len(cols) >= 5 and "Expected" in cols[3]:
            normalized['vessel_name'] = cols[0]
            normalized['voyage_number'] = cols[1]
            normalized['origin_city'] = cols[2]
            normalized['destination_city'] = cols[4]
            
            # Extract ETA from destination col (e.g. "Expected： 2026-09-02 06:00:00 Actual： Not yet arrived at port")
            eta_col = cols[5] if len(cols) > 5 else ""
            match = re.search(r'Expected[：:]\s*(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})', eta_col)
            if match:
                try:
                    normalized['eta_final_delivery'] = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                except:
                    pass

    # Find booking status (e.g. Booking Confirmed)
    status_nodes = soup.find_all(class_=lambda c: c and 'status' in c.lower())
    statuses = [n.get_text(strip=True) for n in status_nodes if "Confirmed" in n.get_text()]
    if statuses:
        normalized['status'] = statuses[0]
        
    return {
        "IsSuccess": True,
        "Message": "COSCO tracking data parsed successfully.",
        "Data": normalized
    }
