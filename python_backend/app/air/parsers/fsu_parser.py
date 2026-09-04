import re
from datetime import datetime

class FSUParser:
    """
    Parser for Cargo-IMP FSU/FSA standard messages.
    Many airlines expose their tracking data in this format.
    """
    
    STATUS_CODES = {
        'BKD': 'Booked',
        'FOH': 'Freight on Hand',
        'RCS': 'Received from Shipper',
        'MAN': 'Manifested',
        'DEP': 'Departed',
        'ARR': 'Arrived',
        'AWR': 'Documents delivered to consignee/agent',
        'RCF': 'Received from Flight',
        'NFD': 'Consignee Notified',
        'AWD': 'Documents Delivered',
        'DLV': 'Delivered',
        'TFD': 'Transferred to another carrier',
        'DIS': 'Discrepancy'
    }

    @staticmethod
    def parse(data_string: str) -> dict:
        """
        Parses the raw FSU string and returns a normalized dictionary.
        """
        lines = data_string.strip().split('\r\n')
        events = []
        
        # We will try to extract origin and destination from the first line usually
        origin = None
        destination = None
        pieces_weight = None
        
        for line in lines:
            # e.g., 139-38411004AMSMEX/T15K5025.00
            if 'K' in line and not '/' in line[:5]:
                # Attempt to extract routing from header lines
                match = re.search(r'([A-Z]{3})([A-Z]{3})/T(\d+)K([\d\.]+)', line)
                if match:
                    origin = match.group(1)
                    destination = match.group(2)
                    pieces = match.group(3)
                    weight = match.group(4)
                    pieces_weight = f"{pieces} pcs / {weight} kg"
                continue

            parts = line.split('/')
            if not parts: 
                continue
                
            code = parts[0]
            if code in FSUParser.STATUS_CODES:
                event = {
                    "code": code,
                    "status": FSUParser.STATUS_CODES[code],
                    "raw": line
                }
                
                # Extract details based on standard FSU structure
                if code in ['BKD', 'MAN', 'DEP', 'ARR', 'AWR', 'RCF']:
                    if len(parts) > 1: event["flight"] = parts[1]
                    if len(parts) > 2: event["date"] = parts[2]
                    if len(parts) > 3: event["route"] = parts[3]
                elif code in ['FOH', 'RCS', 'NFD', 'AWD', 'DLV']:
                    if len(parts) > 1: event["date_time"] = parts[1]
                    if len(parts) > 2: event["location"] = parts[2]
                    
                events.append(event)
                
        # Determine the latest event
        latest_event = events[-1] if events else None
        
        # Build normalized output
        normalized = {
            "status": latest_event['status'] if latest_event else "Unknown",
            "latest_event_time": latest_event.get('date_time', latest_event.get('date', 'Unknown')) if latest_event else "Unknown",
            "origin_airport": origin or "Unknown",
            "destination_airport": destination or "Unknown",
            "flight_number": latest_event.get('flight', 'Unknown') if latest_event else "Unknown",
            "pieces_weight": pieces_weight or "Unknown",
            "eta": "TBD", # ETA is harder to parse from raw FSU without flight schedules
            "events": events
        }
        
        return normalized
