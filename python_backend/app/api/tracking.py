import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
from app.scrapers.engine import scrape_sitc, scrape_cma, scrape_hmm, scrape_evergreen, scrape_pil, scrape_seaboard, scrape_anl, scrape_cnc
from app.scrapers.cosco import scrape_cosco
from app.scrapers.maersk import MaerskScraper
from app.scrapers.yangming import scrape_yangming
from app.core.models import SessionLocal, TrackingResponse
from app.parsers.one import parse_one_response
from app.parsers.zim import parse_zim_response
from app.parsers.kmtc import parse_kmtc_response
from app.parsers.msc import parse_msc_response
from app.parsers.yangming import parse_yangming_response
from app.parsers.sinokor import parse_sinokor_response
from app.parsers.maersk import parse_maersk_response
from datetime import datetime, timedelta

router = APIRouter()

class TrackingRequest(BaseModel):
    carrier: str
    tracking_number: str

# Base URLs (Note: most of these don't actually have public, unauthenticated REST APIs. 
# Many require API keys, special tokens, or graphql payloads. This is a skeleton router.)
CARRIER_URLS = {
    "Maersk": "https://api.maersk.com/track/v1/shipments", # Fictional generic endpoint for demo
    "MSC": "https://api.msc.com/tracking",
    "CMA CGM": "https://api.cma-cgm.com/tracking",
    "Hapag-Lloyd": "https://api.hapag-lloyd.com/tracking",
    "ONE": "https://api.one-line.com/tracking",
    "COSCO": "https://api.coscoshipping.com/tracking",
    "OOCL": "https://api.oocl.com/tracking",
    "Evergreen": "https://api.evergreen-line.com/tracking",
    "HMM": "https://api.hmm21.com/tracking",
    "Yang Ming": "https://api.yangming.com/tracking",
    "YANG MING": "https://api.yangming.com/tracking",
    "YANGMING": "https://api.yangming.com/tracking",
    "YML": "https://api.yangming.com/tracking",
    "ZIM": "https://api.zim.com/tracking",
    "PIL": "https://api.pilship.com/tracking",
    "Wan Hai": "https://api.wanhai.com/tracking",
    "SITC": "https://api.sitc.com/tracking",
    "KMTC": "https://api.kmtc.com/tracking",
    "SINOKOR": "https://ebiz.sinokor.co.kr/Tracking"
}

@router.post("/track")
async def track_shipment(req: TrackingRequest):
    if req.carrier not in CARRIER_URLS:
        raise HTTPException(status_code=400, detail="Unsupported Carrier")
        
    print(f"Tracking requested for {req.carrier} - No. {req.tracking_number}")

    # KMTC API Integration (Hybrid Cache)
    if req.carrier == "KMTC":
        session = SessionLocal()
        try:
            # 1. Check DB first
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "KMTC"
            ).first()
            
            # If present and less than 12 hours old, return DB data
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached KMTC data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if getattr(db_record, c.name) and isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            # 2. Not in DB or too old, fetch from backend API
            print(f"Fetching live KMTC data for {req.tracking_number}")
            kmtc_url = "https://api.ekmtc.com/trans/trans/cargo-tracking/"
            headers = {
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "origin": "https://www.ekmtc.com",
                "referer": "https://www.ekmtc.com/",
                "service-ctrcd": "US",
                "service-lang": "ENG",
                "service-path": "#/cargo-tracking",
                "selected-profile": "{}",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
            }
            dtKnd = "BL" if len(req.tracking_number) > 11 else "CN" 
            payload1 = {
                "dtKnd": dtKnd,
                "blNo": req.tracking_number
            }
            
            # Step 1
            api1_res = requests.post(kmtc_url, json=payload1, headers=headers, timeout=45)
            api1_res.raise_for_status()
            api1_data = api1_res.json()
            
            if not api1_data or not api1_data.get("cntrList"):
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "error": "No data found from corresponding website."
                }
                
            bkgNo = api1_data["cntrList"][0].get("bkgNo")
            
            # Step 2
            api2_data = {}
            if bkgNo:
                api2_url = f"https://api.ekmtc.com/trans/trans/cargo-tracking/{bkgNo}/close-info"
                # API 2 is a GET request usually, but let's check user curl. User curl didn't specify POST/GET but had no payload. It's likely a GET.
                api2_res = requests.get(api2_url, headers=headers, timeout=45)
                if api2_res.status_code == 200:
                    api2_data = api2_res.json()
            
            real_data = {"api1": api1_data, "api2": api2_data}
            
            # 3. Parse KMTC Specific Fields
            parsed_data = parse_kmtc_response(api1_data, api2_data)
            
            # 4. Store/Update in DB
            if db_record:
                db_record.raw_json = real_data
                db_record.last_updated_at = datetime.utcnow()
                for k, v in parsed_data.items():
                    setattr(db_record, k, v)
            else:
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="KMTC",
                    raw_json=real_data,
                    last_updated_at=datetime.utcnow(),
                    **parsed_data
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data,
                "normalized": {
                    k: (v.isoformat() if isinstance(v, datetime) else v) 
                    for k, v in parsed_data.items()
                },
                "cached": False
            }
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "error": f"No data found from corresponding website. (Internal Error: {str(e)})"
            }
        finally:
            session.close()

    # ONE API Integration (Hybrid Cache)
    elif req.carrier == "ONE":
        session = SessionLocal()
        try:
            # 1. Check DB first
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "ONE"
            ).first()
            
            # If present and less than 12 hours old, return DB data
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached ONE data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            # 2. Not in DB or too old, fetch from backend API
            print(f"Fetching live ONE data for {req.tracking_number}")
            one_url = "https://ecomm.one-line.com/api/v2/edh/containers/track-and-trace/search"
            headers = {
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "origin": "https://ecomm.one-line.com",
                "referer": "https://ecomm.one-line.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
            }
            
            import re
            search_type = "CNTR_NO" if re.match(r'^[A-Z]{4}\d{7}$', req.tracking_number) else "BL_NO"
            
            payload = {
                "page": 1,
                "page_length": 10,
                "filters": {
                    "search_text": req.tracking_number,
                    "search_type": search_type
                },
                "timestamp": int(time.time() * 1000)
            }
            
            one_response = requests.post(one_url, json=payload, headers=headers, timeout=45)
            if one_response.status_code == 400:
                real_data = one_response.json()
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": real_data,
                    "error": "Invalid tracking number or not found"
                }
            one_response.raise_for_status()
            real_data = one_response.json()
            
            # 3. Parse ONE Specific Fields
            parsed_data = parse_one_response(real_data)
            
            # 4. Store/Update in DB
            if db_record:
                db_record.raw_json = real_data
                db_record.last_updated_at = datetime.utcnow()
                for k, v in parsed_data.items():
                    setattr(db_record, k, v)
            else:
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="ONE",
                    raw_json=real_data,
                    last_updated_at=datetime.utcnow(),
                    **parsed_data
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data,
                "normalized": {
                    k: (v.isoformat() if isinstance(v, datetime) else v) 
                    for k, v in parsed_data.items()
                },
                "cached": False
            }
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to fetch from ONE: {str(e)}")
        finally:
            session.close()

    # ZIM API Integration (Hybrid Cache)
    elif req.carrier == "ZIM":
        session = SessionLocal()
        try:
            # 1. Check DB first
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "ZIM"
            ).first()
            
            # If present and less than 12 hours old, return DB data
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached ZIM data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if getattr(db_record, c.name) and isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            # 2. Not in DB or too old, fetch from backend API
            print(f"Fetching live ZIM data for {req.tracking_number}")
            zim_url = f"https://apigw.zim.com/digital/TrackShipment/v2/complete-result?reference={req.tracking_number}&subscription-key=9d63cf020a4c4708a7b0ebfe39578300"
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "origin": "https://www.zim.com",
                "referer": "https://www.zim.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
            }
            
            zim_response = requests.get(zim_url, headers=headers, timeout=45)
            zim_response.raise_for_status()
            real_data = zim_response.json()
            
            # Check for error or empty result (ZIM returns empty arrays or specific error formats)
            if not real_data or "isSuccess" in real_data and not real_data["isSuccess"] or not real_data.get("unitListItem"):
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": real_data,
                    "error": "Invalid tracking number or not found"
                }
            
            # 3. Parse ZIM Specific Fields
            parsed_data = parse_zim_response(real_data)
            
            # 4. Store/Update in DB
            if db_record:
                db_record.raw_json = real_data
                db_record.last_updated_at = datetime.utcnow()
                for k, v in parsed_data.items():
                    setattr(db_record, k, v)
            else:
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="ZIM",
                    raw_json=real_data,
                    last_updated_at=datetime.utcnow(),
                    **parsed_data
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data,
                "normalized": {
                    k: (v.isoformat() if isinstance(v, datetime) else v) 
                    for k, v in parsed_data.items()
                },
                "cached": False
            }
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to fetch from ZIM: {str(e)}")
        finally:
            session.close()

    # MSC API Integration (Hybrid Cache)
    elif req.carrier == "MSC":
        session = SessionLocal()
        try:
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "MSC"
            ).first()
            
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached MSC data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if getattr(db_record, c.name) and isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            print(f"Fetching live MSC data for {req.tracking_number}")
            msc_url = "https://www.msc.com/api/feature/tools/TrackingInfo"
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "origin": "https://www.msc.com",
                "referer": "https://www.msc.com/en/track-a-shipment",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
                "x-requested-with": "XMLHttpRequest"
            }
            payload = {
                "trackingNumber": req.tracking_number,
                "trackingMode": "0"
            }
            
            msc_response = requests.post(msc_url, headers=headers, json=payload, timeout=45)
            msc_response.raise_for_status()
            real_data = msc_response.json()
            
            if not real_data or not real_data.get("IsSuccess"):
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": real_data,
                    "error": "Invalid tracking number or not found"
                }
            
            parsed_data = parse_msc_response(real_data)
            
            if db_record:
                db_record.raw_json = real_data
                db_record.last_updated_at = datetime.utcnow()
                for k, v in parsed_data.items():
                    setattr(db_record, k, v)
            else:
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="MSC",
                    raw_json=real_data,
                    last_updated_at=datetime.utcnow(),
                    **parsed_data
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data,
                "normalized": {
                    k: (v.isoformat() if isinstance(v, datetime) else v) 
                    for k, v in parsed_data.items()
                },
                "cached": False
            }
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to fetch from MSC: {str(e)}")
        finally:
            session.close()

    # NCL API Integration
    elif req.carrier == "NCL":
        ncl_url = f"https://nclweb-prod.appresso.no/_api/trackntrace?search={req.tracking_number}"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.ncl.no",
            "referer": "https://www.ncl.no/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        }
        try:
            ncl_response = requests.get(ncl_url, headers=headers, timeout=45)
            # NCL returns 404 for invalid bookings
            if ncl_response.status_code == 404:
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": None,
                    "error": "Could not find booking or container"
                }
            ncl_response.raise_for_status()
            real_data = ncl_response.json()
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch from NCL: {str(e)}")

    # SM Line API Integration
    elif req.carrier == "SM Line":
        sm_url = "https://esvc.smlines.com/smline/CUP_HOM_3301GS.do"
        # Determine search_type: 'B' for Booking/BL (if alphanumeric and not standard container), 'C' for Container
        import re
        search_type = "C" if re.match(r'^[A-Z]{4}\d{7}$', req.tracking_number) else "B"
        
        params = {
            "_search": "false",
            "nd": int(time.time() * 1000),
            "rows": "10000",
            "page": "1",
            "sidx": "",
            "sord": "asc",
            "f_cmd": "121",
            "search_type": search_type,
            "search_name": req.tracking_number,
            "cust_cd": "",
            "_": int(time.time() * 1000) + 1
        }
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://esvc.smlines.com/smline/CUP_HOM_3301.do?sessLocale=en",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        try:
            sm_response = requests.get(sm_url, params=params, headers=headers, timeout=45)
            sm_response.raise_for_status()
            real_data = sm_response.json()
            
            # SM Line returns {"TRANS_RESULT_KEY":"S","count":"0"} if not found
            if real_data.get("count") == "0":
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": real_data,
                    "error": "Could not find booking or container in SM Line"
                }
                
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch from SM Line: {str(e)}")

    # CU Lines API Integration
    elif req.carrier == "CU Lines" or req.carrier == "CULines":
        cu_url = "https://eservice.culines.com/gnoss/CUP_HOM_3301GS.do"
        import re
        search_type = "C" if re.match(r'^[A-Z]{4}\d{7}$', req.tracking_number) else "B"
        
        params = {
            "_search": "false",
            "nd": int(time.time() * 1000),
            "rows": "10000",
            "page": "1",
            "sidx": "",
            "sord": "asc",
            "f_cmd": "121",
            "search_type": search_type,
            "search_name": req.tracking_number,
            "cust_cd": "",
            "_": int(time.time() * 1000) + 1
        }
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://eservice.culines.com/gnoss/CUP_HOM_3301.do?sessLocale=en",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        try:
            cu_response = requests.get(cu_url, params=params, headers=headers, timeout=45)
            cu_response.raise_for_status()
            real_data = cu_response.json()
            
            if real_data.get("count") == "0":
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": real_data,
                    "error": "Could not find booking or container in CU Lines"
                }
                
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch from CU Lines: {str(e)}")

    # Sinokor API Integration (Hybrid Cache & 2-Step)
    elif req.carrier.upper() == "SINOKOR":
        session = SessionLocal()
        try:
            # 1. Check DB first
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "SINOKOR"
            ).first()
            
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached Sinokor data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if getattr(db_record, c.name) and isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            print(f"Fetching live Sinokor data for {req.tracking_number}")
            headers = {
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
            }
            
            bl_no = req.tracking_number
            import re
            # Check if it's a container number (4 letters + 7 digits)
            if re.match(r'^[A-Z]{4}\d{7}$', req.tracking_number):
                # We fetch the BL list first
                print(f"Fetching BL for container: {req.tracking_number}")
                bl_list_url = f"https://ebiz.sinokor.co.kr/Tracking/GetBLList?cntrno={req.tracking_number}&year={datetime.now().year}"
                bl_res = requests.get(bl_list_url, headers=headers, timeout=45)
                bl_res.raise_for_status()
                bl_data = bl_res.json()
                if not bl_data or len(bl_data) == 0:
                    return {
                        "success": False,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "error": "No data found from corresponding website."
                    }
                # Using the first B/L number as per user requirement
                bl_no = bl_data[0].get("BKNO")
                print(f"Resolved to BL: {bl_no}")

            # Fetch Full Tracking HTML
            html_url = f"https://ebiz.sinokor.co.kr/Tracking?blno={bl_no}"
            html_res = requests.get(html_url, headers=headers, timeout=45)
            html_res.raise_for_status()
            html_content = html_res.text
            
            # Sinokor returns success HTML even if not found, we check if the table exists
            if 'id="tblResult"' not in html_content:
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "error": "No data found from corresponding website."
                }
                
            # Parse HTML
            parsed_data = parse_sinokor_response(html_content)
            
            # For raw JSON, let's just store a tiny dict so we don't blow up the DB with HTML
            raw_data = {"blno": bl_no, "html_scraped": True}

            # Store in DB
            if db_record:
                db_record.raw_json = raw_data
                db_record.last_updated_at = datetime.utcnow()
                for k, v in parsed_data.items():
                    setattr(db_record, k, v)
            else:
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="SINOKOR",
                    raw_json=raw_data,
                    last_updated_at=datetime.utcnow(),
                    **parsed_data
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": raw_data,
                "normalized": {
                    k: (v.isoformat() if isinstance(v, datetime) else v) 
                    for k, v in parsed_data.items()
                },
                "cached": False
            }
        except Exception as e:
            session.rollback()
            return {
                "success": False,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "error": f"No data found from corresponding website. ({str(e)})"
            }
        finally:
            session.close()

    # Arkas Line API Integration
    elif req.carrier == "Arkas Line":
        import uuid
        arkas_url = "https://webtrackingprodnew.arkasline.com.tr/api/request/Get"
        params = {
            "controllerMethod": "webtracking/api/shipmenttracking/GetDocumentationAsync",
            "prms": f'{{"key":"{req.tracking_number}"}}'
        }
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "correlationid": str(uuid.uuid4()),
            "culture": "en-US",
            "referer": "https://webtrackingprodnew.arkasline.com.tr/shipmenttracking",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        }
        try:
            arkas_response = requests.get(arkas_url, params=params, headers=headers, timeout=45)
            arkas_response.raise_for_status()
            real_data = arkas_response.json()
            
            # Arkas returns a message when not found, with dataCount = 0
            if "dataCount" in real_data.get("data", {}) and real_data["data"]["dataCount"] == 0:
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": real_data,
                    "error": "Could not find booking or container in Arkas Line"
                }
                
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch from Arkas Line: {str(e)}")

    # Matson API Integration
    elif req.carrier == "Matson":
        import re
        matson_home = "https://www.matson.com/shipment-tracking.html"
        matson_proxy = "https://www.matson.com/wp-content/plugins/matson-plugin/Api_calls/tracking_booking_proxy.php"
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        }
        try:
            # Step 1: Hit homepage to get the CSRF token (ttr)
            session = requests.Session()
            session.headers.update(headers)
            r_home = session.get(matson_home, timeout=30)
            r_home.raise_for_status()
            
            ttr = ""
            # Look for: ttr: "898a7d2fcb"
            matches = re.findall(r'[\'"]ttr[\'"]\s*:\s*[\'"]([a-z0-9]+)[\'"]', r_home.text, re.IGNORECASE)
            if matches:
                ttr = matches[0]
            else:
                return {"success": False, "error": "Could not extract Matson CSRF token"}
                
            # Step 2: Hit the proxy API
            payload = {
                "container_trackingnumber": req.tracking_number,
                "trackingVal": "tckconta",
                "ttr": ttr
            }
            session.headers.update({
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": "https://www.matson.com",
                "referer": "https://www.matson.com/shipment-tracking.html",
                "x-requested-with": "XMLHttpRequest"
            })
            r_proxy = session.post(matson_proxy, data=payload, timeout=45)
            r_proxy.raise_for_status()
            
            # Matson returns an empty array [] if not found
            real_data = r_proxy.json()
            if not real_data:
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": real_data,
                    "error": "Could not find booking or container in Matson"
                }
                
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch from Matson: {str(e)}")

    # SITC HTML Scraper Integration
    elif req.carrier == "SITC":
        try:
            real_data = scrape_sitc(req.tracking_number)
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape SITC: {str(e)}")

    # CMA CGM Headless Scraper Integration
    elif req.carrier == "CMA CGM":
        try:
            real_data = scrape_cma(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape CMA CGM: {str(e)}")

    # ANL Headless Scraper Integration (CMA CGM subsidiary)
    elif req.carrier == "ANL":
        try:
            real_data = scrape_anl(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape ANL: {str(e)}")

    # CNC Line Headless Scraper Integration (CMA CGM subsidiary)
    elif req.carrier == "CNC Line" or req.carrier == "CNC":
        try:
            real_data = scrape_cnc(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape CNC Line: {str(e)}")

    # Maersk Subprocess Scraper Integration
    elif req.carrier == "Maersk":
        session = SessionLocal()
        try:
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "Maersk"
            ).first()
            
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached Maersk data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if getattr(db_record, c.name) and isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            print(f"Fetching live Maersk data for {req.tracking_number}")
            scraper = MaerskScraper()
            real_data = scraper.track(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
                
            parsed_data = parse_maersk_response(real_data)
            
            if db_record:
                db_record.raw_json = real_data
                db_record.last_updated_at = datetime.utcnow()
                for k, v in parsed_data.items():
                    setattr(db_record, k, v)
            else:
                valid_keys = [c.name for c in TrackingResponse.__table__.columns]
                filtered_normalized = {k: v for k, v in parsed_data.items() if k in valid_keys}
                
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="Maersk",
                    raw_json=real_data,
                    last_updated_at=datetime.utcnow(),
                    **filtered_normalized
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data,
                "normalized": {
                    k: (v.isoformat() if isinstance(v, datetime) else v) 
                    for k, v in parsed_data.items()
                },
                "cached": False
            }
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to scrape Maersk: {str(e)}")
        finally:
            session.close()

    # HMM Headless Scraper Integration
    elif req.carrier == "HMM":
        try:
            real_data = scrape_hmm(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape HMM: {str(e)}")

    # COSCO Headless Scraper Integration
    elif req.carrier == "COSCO":
        session = SessionLocal()
        try:
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "COSCO"
            ).first()
            
            # Since the user stated COSCO is called once a day, caching is perfect here
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached COSCO data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            print(f"Fetching live COSCO data for {req.tracking_number}")
            from app.scrapers.cosco import scrape_cosco_sync
            scrape_result = scrape_cosco_sync(req.tracking_number)
            if not scrape_result or "error" in scrape_result:
                error_msg = scrape_result["error"] if scrape_result else "Scraper failed"
                raise HTTPException(status_code=500, detail=error_msg)
            
            from app.parsers.cosco import parse_cosco_html
            parsed_data = parse_cosco_html(scrape_result.get("raw_html", ""))
            
            if not parsed_data.get("IsSuccess"):
                return {
                    "success": False,
                    "carrier": req.carrier,
                    "tracking_number": req.tracking_number,
                    "data": parsed_data,
                    "error": parsed_data.get("Message", "Not found")
                }

            import json
            parsed_data = json.loads(json.dumps(parsed_data, default=str))
            normalized = parsed_data.get("Data", {}) or {}
            
            if db_record:
                db_record.raw_json = parsed_data
                db_record.last_updated_at = datetime.utcnow()
                # Update with normalized data if available
                for k, v in normalized.items():
                    if hasattr(db_record, k):
                        setattr(db_record, k, v)
            else:
                valid_keys = [c.name for c in TrackingResponse.__table__.columns]
                filtered_normalized = {k: v for k, v in normalized.items() if k in valid_keys}
                
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="COSCO",
                    raw_json=parsed_data,
                    last_updated_at=datetime.utcnow(),
                    **filtered_normalized
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": parsed_data,
                "normalized": normalized,
                "cached": False
            }
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to scrape COSCO: {str(e)}")
        finally:
            session.close()

    # Yang Ming Integration
    elif req.carrier.upper() in ["YANG MING", "YANGMING", "YML"]:
        session = SessionLocal()
        try:
            db_record = session.query(TrackingResponse).filter(
                TrackingResponse.tracking_number == req.tracking_number,
                TrackingResponse.carrier == "YANG MING"
            ).first()
            
            if db_record and db_record.last_updated_at:
                if datetime.utcnow() - db_record.last_updated_at < timedelta(hours=12):
                    print(f"Returning cached YANG MING data for {req.tracking_number}")
                    return {
                        "success": True,
                        "carrier": req.carrier,
                        "tracking_number": req.tracking_number,
                        "data": db_record.raw_json,
                        "normalized": {
                            c.name: getattr(db_record, c.name).isoformat() if getattr(db_record, c.name) and isinstance(getattr(db_record, c.name), datetime) else getattr(db_record, c.name) 
                            for c in TrackingResponse.__table__.columns if c.name not in ["id", "raw_json", "last_updated_at"]
                        },
                        "cached": True,
                        "last_updated": db_record.last_updated_at.isoformat()
                    }

            print(f"Fetching live YANG MING data for {req.tracking_number}")
            scrape_result = scrape_yangming(req.tracking_number)
            if not scrape_result or "error" in scrape_result:
                error_msg = scrape_result["error"] if scrape_result else "Scraper failed"
                raise HTTPException(status_code=500, detail=error_msg)
            
            # The exact raw JSON from the website
            raw_ym_payload = scrape_result.get("raw_json", {})
            
            # Use the parser strictly to get normalized fields for the DB
            parsed_data = parse_yangming_response(raw_ym_payload)
            normalized = parsed_data.get("Data", {}) or {}

            if db_record:
                db_record.raw_json = raw_ym_payload
                db_record.last_updated_at = datetime.utcnow()
                for k, v in normalized.items():
                    if hasattr(db_record, k):
                        setattr(db_record, k, v)
            else:
                valid_keys = [c.name for c in TrackingResponse.__table__.columns]
                filtered_normalized = {k: v for k, v in normalized.items() if k in valid_keys}
                
                new_record = TrackingResponse(
                    tracking_number=req.tracking_number,
                    carrier="YANG MING",
                    raw_json=raw_ym_payload,
                    last_updated_at=datetime.utcnow(),
                    **filtered_normalized
                )
                session.add(new_record)
            
            session.commit()
            
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": raw_ym_payload,
                "normalized": {k: v for k, v in normalized.items() if k in valid_keys},
                "cached": False
            }

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to scrape YANG MING: {str(e)}")
        finally:
            session.close()

    # Evergreen HTML Scraper Integration
    elif req.carrier == "Evergreen":
        try:
            real_data = scrape_evergreen(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape Evergreen: {str(e)}")

    # PIL Headless Scraper Integration
    elif req.carrier == "PIL":
        try:
            real_data = scrape_pil(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape PIL: {str(e)}")

    # Seaboard Marine HTML Scraper Integration
    elif req.carrier == "Seaboard Marine":
        try:
            real_data = scrape_seaboard(req.tracking_number)
            if "error" in real_data:
                raise HTTPException(status_code=500, detail=real_data["error"])
            return {
                "success": True,
                "carrier": req.carrier,
                "tracking_number": req.tracking_number,
                "data": real_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape Seaboard Marine: {str(e)}")

    # For all other carriers (until you provide their APIs), we return mock data temporarily
    time.sleep(1.5)

    
    mock_data = {
        "status": "In Transit",
        "latest_event": "Departed Port of Loading",
        "location": "Singapore [SGSIN]",
        "timestamp": "2026-08-15T08:30:00Z",
        "vessel": "MSC DIANA",
        "container_number": req.tracking_number,
        "history": [
            {
                "date": "2026-08-15T08:30:00Z",
                "event": "Departed Port of Loading",
                "location": "Singapore [SGSIN]"
            }
        ],
        "note": "This is mock data. Please provide the real API for this carrier."
    }
    
    return {
        "success": True,
        "carrier": req.carrier,
        "tracking_number": req.tracking_number,
        "data": mock_data
    }
