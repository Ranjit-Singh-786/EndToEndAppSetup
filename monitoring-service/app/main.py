import logging
import time
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, get_db
from app.routers import monitoring
from app import services
from app.schemas import SensorReadingCreate, AdditionalSensorData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - %(levelname)s - [{settings.SERVICE_NAME}] - %(message)s"
)
logger = logging.getLogger(settings.SERVICE_NAME)

app = FastAPI(
    title="SmartFarm Farm Monitoring / Sensor Service",
    description="Microservice managing sensor readings and environmental metrics.",
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

# Connect to database and seed data on startup
@app.on_event("startup")
def startup_event():
    try:
        init_db()
        db = get_db()
        
        # Check if collection is empty and seed it
        readings_count = db.sensor_readings.count_documents({})
        if readings_count == 0:
            logger.info("MongoDB is empty. Seeding sample sensor readings...")
            
            # Seeding reading 1
            reading1 = SensorReadingCreate(
                farm_id=1,
                sensor_id="SENSOR-001",
                timestamp=datetime.utcnow() - timedelta(minutes=45),
                temperature=31.5,
                humidity=62.0,
                soil_moisture=41.0,
                rainfall=0.0,
                additional_data=AdditionalSensorData(battery=87, signal_strength=92)
            )
            services.create_reading(db, reading1)
            
            # Seeding reading 2 (slightly more recent, different values)
            reading2 = SensorReadingCreate(
                farm_id=1,
                sensor_id="SENSOR-001",
                timestamp=datetime.utcnow() - timedelta(minutes=15),
                temperature=30.2,
                humidity=64.0,
                soil_moisture=42.5,
                rainfall=0.5,
                additional_data=AdditionalSensorData(battery=86, signal_strength=90)
            )
            services.create_reading(db, reading2)
            
            # Seeding reading 3 (from a second sensor)
            reading3 = SensorReadingCreate(
                farm_id=1,
                sensor_id="SENSOR-002",
                timestamp=datetime.utcnow() - timedelta(minutes=5),
                temperature=29.8,
                humidity=66.2,
                soil_moisture=45.0,
                rainfall=1.2,
                additional_data=AdditionalSensorData(battery=94, signal_strength=88)
            )
            services.create_reading(db, reading3)
            
            logger.info("Sample sensor readings seeded successfully.")
    except Exception as e:
        logger.error(f"Error during MongoDB startup: {e}")

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
def health_check(db=Depends(get_db)):
    # Simple check on MongoDB connection
    mongo_status = "connected"
    try:
        db.command('ping')
    except Exception:
        mongo_status = "disconnected"
        
    return {
        "status": "healthy" if mongo_status == "connected" else "degraded",
        "service": settings.SERVICE_NAME,
        "database": mongo_status
    }

# Include routers
app.include_router(monitoring.router)
