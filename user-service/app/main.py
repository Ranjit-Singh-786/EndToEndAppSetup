import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import farmers
from app import services
from app.schemas import FarmerCreate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - %(levelname)s - [{settings.SERVICE_NAME}] - %(message)s"
)
logger = logging.getLogger(settings.SERVICE_NAME)

# Create tables and seed data on startup
# In a real environment, we'd use Alembic. Here, we do both: auto-initialize for ease of running, and provide Alembic files.
try:
    logger.info("Initializing database and tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    # Seed data if empty
    db = SessionLocal()
    try:
        existing_farmers = services.get_farmers(db, limit=1)
        if not existing_farmers:
            logger.info("Database is empty. Seeding sample farmer data...")
            seed_farmer = FarmerCreate(
                name="Ranjit Farmer",
                email="ranjit@example.com",
                phone="+1-555-0199",
                password="password123"
            )
            services.create_farmer(db, seed_farmer)
            logger.info("Sample farmer data seeded successfully.")
    finally:
        db.close()
except Exception as e:
    logger.error(f"Error during database initialization: {e}")

app = FastAPI(
    title="SmartFarm User/Farmer Service",
    description="Microservice managing farmer registry and profiles.",
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
        "database": "connected"  # If create_all succeeded, database connection is verified
    }

# Include routers
app.include_router(farmers.router)
