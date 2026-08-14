import logging
from typing import List
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.database import get_db
from app.schemas import SensorReadingCreate, SensorReadingResponse, MonitoringSummary
from app import services
from app.config import settings

logger = logging.getLogger("monitoring-service")
router = APIRouter(tags=["Monitoring & Sensor Readings"])

def verify_farm_exists(farm_id: int) -> bool:
    """Call Farm Service to verify if farm exists."""
    url = f"{settings.FARM_SERVICE_URL}/farms/{farm_id}"
    logger.info(f"Verifying farm_id {farm_id} via Farm Service: {url}")
    try:
        response = httpx.get(url, timeout=3.0)
        if response.status_code == 200:
            logger.info(f"Verification successful: Farm {farm_id} exists")
            return True
        elif response.status_code == 404:
            logger.warning(f"Verification failed: Farm {farm_id} not found")
            return False
        else:
            logger.error(f"Unexpected response from Farm Service: status {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Farm Service returned error code {response.status_code}"
            )
    except httpx.RequestError as exc:
        logger.error(f"Connection to Farm Service failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify farm ID because Farm Service is unavailable."
        )

@router.post("/readings", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
def post_sensor_reading(reading: SensorReadingCreate, db: Database = Depends(get_db)):
    logger.info(f"Received sensor reading for farm {reading.farm_id} (Sensor: {reading.sensor_id})")
    
    # Service-to-service validation
    if not verify_farm_exists(reading.farm_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot add reading. Farm with ID {reading.farm_id} does not exist."
        )
        
    return services.create_reading(db=db, reading=reading)

@router.get("/readings/{farm_id}", response_model=List[SensorReadingResponse])
def read_farm_sensor_history(farm_id: int, db: Database = Depends(get_db)):
    logger.info(f"Fetching sensor history for farm ID {farm_id}")
    return services.get_readings_by_farm(db=db, farm_id=farm_id)

@router.get("/readings/{farm_id}/latest", response_model=SensorReadingResponse)
def read_farm_latest_conditions(farm_id: int, db: Database = Depends(get_db)):
    logger.info(f"Fetching latest conditions for farm ID {farm_id}")
    doc = services.get_latest_reading(db=db, farm_id=farm_id)
    if doc is None:
        logger.warning(f"No sensor readings found for farm ID {farm_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sensor readings found for farm with ID {farm_id}."
        )
    return doc

@router.get("/readings/{farm_id}/summary", response_model=MonitoringSummary)
def read_farm_summary_metrics(farm_id: int, db: Database = Depends(get_db)):
    logger.info(f"Computing monitoring summary metrics for farm ID {farm_id}")
    return services.get_farm_summary(db=db, farm_id=farm_id)
