import logging
import time
from datetime import date
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import farms, crops
from app import services
from app.schemas import FarmCreate, CropCreate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - %(levelname)s - [{settings.SERVICE_NAME}] - %(message)s"
)
logger = logging.getLogger(settings.SERVICE_NAME)

# Create tables and seed data on startup
try:
    logger.info("Initializing database and tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    # Seed data if empty
    db = SessionLocal()
    try:
        existing_farms = services.get_farms(db, limit=1)
        if not existing_farms:
            logger.info("Database is empty. Seeding sample farm and crop data...")
            seed_farm = FarmCreate(
                farmer_id=1,  # Corresponds to seed farmer Ranjit
                farm_name="Green Valley Farm",
                location="California, USA",
                area_acres=50.0
            )
            created_farm = services.create_farm(db, seed_farm)
            logger.info(f"Sample farm seeded with ID {created_farm.id}")
            
            seed_crop = CropCreate(
                crop_name="Wheat",
                crop_type="Cereal",
                sowing_date=date(2026, 8, 12),
                expected_harvest_date=date(2026, 12, 12),
                status="Growing"
            )
            created_crop = services.create_crop(db, created_farm.id, seed_crop)
            logger.info(f"Sample crop '{created_crop.crop_name}' seeded for farm ID {created_farm.id}")
    finally:
        db.close()
except Exception as e:
    logger.error(f"Error during database initialization: {e}")

app = FastAPI(
    title="SmartFarm Farm/Crop Service",
    description="Microservice managing farms and crop analytics.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Enable CORS for the frontend application
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    logger.info(f"Incoming Request: {method} {path}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Completed Request: {method} {path} - "
            f"Status: {response.status_code} - "
            f"Latency: {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"Failed Request: {method} {path} - "
            f"Error: {str(e)} - "
            f"Latency: {process_time:.2f}ms"
        )
        raise e

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "database": "connected"
    }

# Include routers
app.include_router(farms.router)
app.include_router(crops.router)
