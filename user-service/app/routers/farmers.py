import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import FarmerCreate, FarmerUpdate, FarmerResponse
from app import services

logger = logging.getLogger("user-service")
router = APIRouter(prefix="/farmers", tags=["Farmers"])

@router.post("", response_model=FarmerResponse, status_code=status.HTTP_201_CREATED)
def register_farmer(farmer: FarmerCreate, db: Session = Depends(get_db)):
    logger.info(f"Registering farmer: {farmer.email}")
    db_farmer = services.get_farmer_by_email(db, email=farmer.email)
    if db_farmer:
        logger.warning(f"Registration failed: Email {farmer.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farmer with this email is already registered."
        )
    return services.create_farmer(db=db, farmer=farmer)

@router.get("", response_model=List[FarmerResponse])
def read_farmers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Listing farmers skip={skip}, limit={limit}")
    return services.get_farmers(db, skip=skip, limit=limit)

@router.get("/{farmer_id}", response_model=FarmerResponse)
def read_farmer(farmer_id: int, db: Session = Depends(get_db)):
    logger.info(f"Reading farmer details for ID: {farmer_id}")
    db_farmer = services.get_farmer(db, farmer_id=farmer_id)
    if db_farmer is None:
        logger.warning(f"Farmer not found: ID {farmer_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farmer with ID {farmer_id} not found."
        )
    return db_farmer

@router.put("/{farmer_id}", response_model=FarmerResponse)
def update_farmer(farmer_id: int, farmer_update: FarmerUpdate, db: Session = Depends(get_db)):
    logger.info(f"Updating farmer details for ID: {farmer_id}")
    
    # Check if email is being updated to an existing one
    if farmer_update.email:
        existing = services.get_farmer_by_email(db, email=farmer_update.email)
        if existing and existing.id != farmer_id:
            logger.warning(f"Update failed: Email {farmer_update.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already in use by another account."
            )
            
    db_farmer = services.update_farmer(db, farmer_id=farmer_id, farmer_update=farmer_update)
    if db_farmer is None:
        logger.warning(f"Farmer not found for update: ID {farmer_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farmer with ID {farmer_id} not found."
        )
    return db_farmer

@router.delete("/{farmer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farmer(farmer_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting farmer: ID {farmer_id}")
    success = services.delete_farmer(db, farmer_id=farmer_id)
    if not success:
        logger.warning(f"Farmer not found for deletion: ID {farmer_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farmer with ID {farmer_id} not found."
        )
    return None
