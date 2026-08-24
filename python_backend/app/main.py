from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.tracking import router as tracking_router
import os

app = FastAPI(title="XPortPlus Tracking API")

# Initialize the Database tables when the app starts
@app.on_event("startup")
def on_startup():
    print("Application started.")

# Add CORS middleware to allow the frontend to access the API
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,https://xport-plus.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the tracking router
app.include_router(tracking_router, prefix="/tracking", tags=["tracking"])

@app.get("/")
def read_root():
    return {"message": "Welcome to XPortPlus Python Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
