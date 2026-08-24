import json
from bs4 import BeautifulSoup

def test_parse():
    with open("cosco_test_result.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    
    data = {}
    
    # Extract Booking/BL No
    title = soup.find('div', class_=lambda c: c and 'title' in c)
    if title:
        data['Title'] = title.get_text(strip=True)
        
    # Find all ant-table-row (transport details and schedules)
    rows = soup.find_all('tr', class_='ant-table-row')
    transport_details = []
    for row in rows:
        cols = [col.get_text(separator=' ', strip=True) for col in row.find_all('td')]
        transport_details.append(cols)
        
    data['TableRows'] = transport_details
    
    # Extract Latest Status
    status_nodes = soup.find_all(class_=lambda c: c and 'status' in c.lower())
    data['Statuses'] = [n.get_text(separator=' ', strip=True) for n in status_nodes]
    
    # Extract anything that looks like a port or location
    locations = soup.find_all(class_=lambda c: c and ('location' in c.lower() or 'port' in c.lower()))
    data['Locations'] = [l.get_text(separator=' ', strip=True) for l in locations]
    
    with open("cosco_parsed.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    test_parse()
