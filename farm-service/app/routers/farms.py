import logging
from typing import List
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import FarmCreate, FarmUpdate, FarmResponse
from app import services
from app.config import settings

logger = logging.getLogger("farm-service")
router = APIRouter(prefix="/farms", tags=["Farms"])

def verify_farmer_exists(farmer_id: int):
    """Call User Service to verify if farmer exists."""
    url = f"{settings.USER_SERVICE_URL}/farmers/{farmer_id}"
    logger.info(f"Verifying farmer_id {farmer_id} via User Service: {url}")
    try:
        # Perform synchronous HTTP call to User Service
        response = httpx.get(url, timeout=3.0)
        if response.status_code == 200:
            logger.info(f"Verification successful: Farmer {farmer_id} exists")
            return True
        elif response.status_code == 404:
            logger.warning(f"Verification failed: Farmer {farmer_id} not found")
            return False
        else:
            logger.error(f"Unexpected response from User Service: status {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"User Service returned error code {response.status_code}"
            )
    except httpx.RequestError as exc:
        logger.error(f"Connection to User Service failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify farmer ID because User Service is unavailable."
        )

@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to create farm: '{farm.farm_name}' for farmer: {farm.farmer_id}")
    
    # Service-to-service communication verification
    if not verify_farmer_exists(farm.farmer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot create farm. Farmer with ID {farm.farmer_id} does not exist."
        )
        
    return services.create_farm(db=db, farm=farm)

@router.get("", response_model=List[FarmResponse])
def read_farms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Listing farms skip={skip}, limit={limit}")
    return services.get_farms(db, skip=skip, limit=limit)

@router.get("/{farm_id}", response_model=FarmResponse)
def read_farm(farm_id: int, db: Session = Depends(get_db)):
    logger.info(f"Reading farm details: ID {farm_id}")
    db_farm = services.get_farm(db, farm_id=farm_id)
    if db_farm is None:
        logger.warning(f"Farm not found: ID {farm_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found."
        )
    return db_farm

@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, farm_update: FarmUpdate, db: Session = Depends(get_db)):
    logger.info(f"Updating farm: ID {farm_id}")
    
    # If farmer_id is being updated, verify new farmer exists
    if farm_update.farmer_id is not None:
        if not verify_farmer_exists(farm_update.farmer_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cannot update farm. Farmer with ID {farm_update.farmer_id} does not exist."
            )
            
    db_farm = services.update_farm(db, farm_id=farm_id, farm_update=farm_update)
    if db_farm is None:
        logger.warning(f"Farm not found for update: ID {farm_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found."
        )
    return db_farm

@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(farm_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting farm: ID {farm_id}")
    success = services.delete_farm(db, farm_id=farm_id)
    if not success:
        logger.warning(f"Farm not found for deletion: ID {farm_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found."
        )
    return None
