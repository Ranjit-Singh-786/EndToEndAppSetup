import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CropCreate, CropResponse
from app import services

logger = logging.getLogger("farm-service")
router = APIRouter(tags=["Crops"])

@router.post("/farms/{farm_id}/crops", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop_for_farm(farm_id: int, crop: CropCreate, db: Session = Depends(get_db)):
    logger.info(f"Adding crop '{crop.crop_name}' to farm ID {farm_id}")
    
    # Verify farm exists
    db_farm = services.get_farm(db, farm_id=farm_id)
    if db_farm is None:
        logger.warning(f"Farm not found for crop addition: ID {farm_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot add crop. Farm with ID {farm_id} does not exist."
        )
        
    return services.create_crop(db=db, farm_id=farm_id, crop=crop)

@router.get("/farms/{farm_id}/crops", response_model=List[CropResponse])
def read_crops_for_farm(farm_id: int, db: Session = Depends(get_db)):
    logger.info(f"Listing crops for farm ID {farm_id}")
    
    # Verify farm exists
    db_farm = services.get_farm(db, farm_id=farm_id)
    if db_farm is None:
        logger.warning(f"Farm not found: ID {farm_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with ID {farm_id} not found."
        )
        
    return services.get_crops_by_farm(db, farm_id=farm_id)

@router.get("/crops/{crop_id}", response_model=CropResponse)
def read_crop(crop_id: int, db: Session = Depends(get_db)):
    logger.info(f"Reading crop details: ID {crop_id}")
    db_crop = services.get_crop(db, crop_id=crop_id)
    if db_crop is None:
        logger.warning(f"Crop not found: ID {crop_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop with ID {crop_id} not found."
        )
    return db_crop
