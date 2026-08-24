import requests
from app.core.models import SessionLocal, TrackingResponse
import time
import json
from datetime import datetime

# Define dummy active tracking numbers for testing. 
# In a real environment, you'd fetch these from a Bookings/Shipments table.
ACTIVE_TRACKING_NUMBERS = [
    {"tracking_number": "MSCU1234567", "carrier": "MSC"},
    {"tracking_number": "TGSU2517987", "carrier": "Maersk"},
    {"tracking_number": "OOLU0115537", "carrier": "CMA CGM"}
]

def run_cron_job():
    print(f"Starting cron job at {datetime.now()}...")
    session = SessionLocal()
    
    for item in ACTIVE_TRACKING_NUMBERS:
        tracking_number = item["tracking_number"]
        carrier = item["carrier"]
        
        print(f"Fetching data for {carrier}: {tracking_number}")
        
        # Hit our own backend API to trigger the scraping logic
        try:
            # Assumes the FastAPI backend is running locally on port 5000/8000
            api_url = "http://localhost:5000/api/track"
            payload = {
                "tracking_number": tracking_number,
                "carrier": carrier
            }
            
            # This triggers the scraper in tracking_api.py
            response = requests.post(api_url, json=payload, timeout=60) 
            
            if response.status_code == 200:
                data = response.json()
                
                # We could add logic here to parse the `data` into standard columns 
                # (like origin_city, vessel_name, etc.) based on the carrier.
                # For now, we will store the raw JSON and basic info.
                
                # Check if it already exists in DB
                db_record = session.query(TrackingResponse).filter_by(tracking_number=tracking_number).first()
                
                if db_record:
                    db_record.raw_json = data
                    db_record.last_updated_at = datetime.utcnow()
                    db_record.status = data.get("data", {}).get("status", "Unknown")
                    print(f"  -> Updated record for {tracking_number}")
                else:
                    new_record = TrackingResponse(
                        tracking_number=tracking_number,
                        carrier=carrier,
                        raw_json=data,
                        status=data.get("data", {}).get("status", "Unknown"),
                        last_updated_at=datetime.utcnow()
                    )
                    session.add(new_record)
                    print(f"  -> Created new record for {tracking_number}")
                    
                session.commit()
            else:
                print(f"  -> API Error for {tracking_number}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  -> Request Exception for {tracking_number}: {e}")
            
        # Sleep to avoid rate limits
        print("Waiting 10 seconds before next request...")
        time.sleep(10)

    session.close()
    print("Cron job finished!")

if __name__ == "__main__":
    # Disabled by default as requested by user.
    # To run manually, execute this file.
    
    # run_cron_job()
    print("Cron job script executed. The actual run_cron_job() function is disabled by default.")
