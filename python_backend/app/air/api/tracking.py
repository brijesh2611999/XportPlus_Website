from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.models import SessionLocal, AirTrackingResponse
from app.air.scrapers.aeromexico import AeroMexicoScraper
from app.air.scrapers.lufthansa import LufthansaScraper
from app.air.scrapers.airfrance import AirFranceScraper
from app.air.scrapers.delta import DeltaScraper

router = APIRouter()

class AirTrackingRequest(BaseModel):
    carrier: str
    awb_number: str

# Dictionary mapping airline names to their scrapers
AIRLINE_SCRAPERS = {
    "Emirates": None,
    "Qatar": None,
    "Lufthansa": LufthansaScraper(),
    "Air France": AirFranceScraper(),
    "Delta": DeltaScraper(),
    "Cathay": None,
    "FedEx": None,
    "DHL": None,
    "UPS": None,
    "Singapore": None,
    "Turkish": None,
    "KoreanAir": None,
    "AeroMexico": AeroMexicoScraper()
}

@router.post("/track")
async def track_awb(req: AirTrackingRequest):
    if req.carrier not in AIRLINE_SCRAPERS:
        raise HTTPException(status_code=400, detail=f"Unsupported Airline: {req.carrier}")
        
    scraper = AIRLINE_SCRAPERS[req.carrier]
    
    if not scraper:
        # Placeholder for airlines not yet implemented
        return {
            "success": False,
            "carrier": req.carrier,
            "awb_number": req.awb_number,
            "error": f"{req.carrier} scraper is not implemented yet."
        }
        
    print(f"Air Tracking requested for {req.carrier} - AWB {req.awb_number}")

    session = SessionLocal()
    try:
        # 1. Check DB first (Hybrid Cache)
        db_record = session.query(AirTrackingResponse).filter(
            AirTrackingResponse.awb_number == req.awb_number,
            AirTrackingResponse.carrier == req.carrier
        ).first()
        
        # If present and less than 12 hours old, return DB data
        if db_record and db_record.last_updated_at:
            if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                print(f"Returning cached {req.carrier} data for {req.awb_number}")
                return {
                    "success": True,
                    "carrier": req.carrier,
                    "awb_number": req.awb_number,
                    "data": db_record.raw_json,
                    "normalized": {
                        "status": db_record.status,
                        "latest_event_time": db_record.latest_event_time,
                        "origin_airport": db_record.origin_airport,
                        "destination_airport": db_record.destination_airport,
                        "flight_number": db_record.flight_number,
                        "pieces_weight": db_record.pieces_weight,
                        "eta": db_record.eta,
                        "events": db_record.events
                    },
                    "cached": True,
                    "last_updated": db_record.last_updated_at.isoformat()
                }

        # 2. Not in DB or too old, fetch from scraper
        print(f"Fetching live {req.carrier} data for {req.awb_number}")
        
        result = scraper.scrape(req.awb_number)
        
        if not result.get("success"):
            return {
                "success": False,
                "carrier": req.carrier,
                "awb_number": req.awb_number,
                "error": result.get("error", "Unknown error occurred.")
            }
            
        normalized_data = result["normalized"]
        raw_json_data = result.get("raw_data", {})
        
        # 3. Store/Update in DB
        if db_record:
            db_record.raw_json = raw_json_data
            db_record.last_updated_at = datetime.utcnow()
            db_record.status = normalized_data.get("status")
            db_record.latest_event_time = normalized_data.get("latest_event_time")
            db_record.origin_airport = normalized_data.get("origin_airport")
            db_record.destination_airport = normalized_data.get("destination_airport")
            db_record.flight_number = normalized_data.get("flight_number")
            db_record.pieces_weight = normalized_data.get("pieces_weight")
            db_record.eta = normalized_data.get("eta")
            db_record.events = normalized_data.get("events")
        else:
            new_record = AirTrackingResponse(
                carrier=req.carrier,
                awb_number=req.awb_number,
                status=normalized_data.get("status"),
                latest_event_time=normalized_data.get("latest_event_time"),
                origin_airport=normalized_data.get("origin_airport"),
                destination_airport=normalized_data.get("destination_airport"),
                flight_number=normalized_data.get("flight_number"),
                pieces_weight=normalized_data.get("pieces_weight"),
                eta=normalized_data.get("eta"),
                events=normalized_data.get("events"),
                raw_json=raw_json_data,
                last_updated_at=datetime.utcnow()
            )
            session.add(new_record)
        
        session.commit()
        
        return {
            "success": True,
            "carrier": req.carrier,
            "awb_number": req.awb_number,
            "data": raw_json_data,
            "normalized": normalized_data,
            "cached": False,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        session.rollback()
        return {
            "success": False,
            "carrier": req.carrier,
            "awb_number": req.awb_number,
            "error": f"Internal Error processing {req.carrier} tracking: {str(e)}"
        }
    finally:
        session.close()
