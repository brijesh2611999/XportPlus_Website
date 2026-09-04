from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
import datetime
import os
from dotenv import load_dotenv

# Load environment variables (from ../xportplus_backend/.env or locally)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'xportplus_backend', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class TrackingResponse(Base):
    __tablename__ = "tracking_responses"

    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(String, index=True, nullable=False)
    
    # 1. SHIPMENT IDENTIFIERS
    tracking_number = Column(String, index=True, nullable=False)  # Often same as container_no or bl_no depending on search
    container_no = Column(String, index=True, nullable=True)
    bl_no = Column(String, index=True, nullable=True)
    booking_no = Column(String, index=True, nullable=True)
    seal_no = Column(String, nullable=True)

    # 2. ROUTING
    vessel_name = Column(String, nullable=True)
    voyage_no = Column(String, nullable=True)
    carrier_line = Column(String, nullable=True)
    service_type = Column(String, nullable=True)
    pol = Column(String, nullable=True)
    pod = Column(String, nullable=True)
    final_destination = Column(String, nullable=True)
    transhipment_port = Column(String, nullable=True)

    # 3. DATES
    etd_pol = Column(DateTime, nullable=True)
    atd_pol = Column(DateTime, nullable=True)
    eta_transhipment = Column(DateTime, nullable=True)
    eta_pod = Column(DateTime, nullable=True)
    ata_pod = Column(DateTime, nullable=True)
    eta_final_delivery = Column(DateTime, nullable=True)

    # 4. CONTAINER DETAILS
    container_size = Column(String, nullable=True)
    container_type = Column(String, nullable=True)
    gross_weight = Column(String, nullable=True)
    cargo_description = Column(String, nullable=True)
    package_count = Column(String, nullable=True)

    # 5. CURRENT STATUS
    current_location = Column(String, nullable=True)
    last_event = Column(String, nullable=True)
    event_date_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    milestone = Column(String, nullable=True)

    # 6. CUSTOMS & DOCUMENTS
    customs_status = Column(String, nullable=True)
    boe_no_date = Column(String, nullable=True)
    do_status = Column(String, nullable=True)
    detention_free_days = Column(String, nullable=True)
    demurrage_free_days = Column(String, nullable=True)

    # RAW DATA
    raw_json = Column(JSONB, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class AirTrackingResponse(Base):
    __tablename__ = "air_tracking_responses"

    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(String, index=True, nullable=False)
    awb_number = Column(String, index=True, nullable=False)
    
    # Air specific fields
    status = Column(String, nullable=True)
    latest_event_time = Column(String, nullable=True) # Stored as string or parsed to DateTime
    origin_airport = Column(String, nullable=True)
    destination_airport = Column(String, nullable=True)
    flight_number = Column(String, nullable=True)
    pieces_weight = Column(String, nullable=True)
    eta = Column(String, nullable=True)
    events = Column(JSONB, nullable=True) # Normalized events list

    # RAW DATA
    raw_json = Column(JSONB, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class SiteToken(Base):
    __tablename__ = "site_tokens"

    site_name = Column(String(50), primary_key=True, index=True)
    token_data = Column(JSONB, nullable=False)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, server_default=os.environ.get("CURRENT_TIMESTAMP", "CURRENT_TIMESTAMP"))

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing Database Schema...")
    init_db()
    print("Database tables created successfully!")
