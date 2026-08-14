from sqlalchemy.orm import Session
from app.models import Farm, Crop
from app.schemas import FarmCreate, FarmUpdate, CropCreate

# ==============================================================================
# Farm CRUD
# ==============================================================================

def get_farm(db: Session, farm_id: int):
    return db.query(Farm).filter(Farm.id == farm_id).first()

def get_farms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Farm).offset(skip).limit(limit).all()

def create_farm(db: Session, farm: FarmCreate) -> Farm:
    db_farm = Farm(
        farmer_id=farm.farmer_id,
        farm_name=farm.farm_name,
        location=farm.location,
        area_acres=farm.area_acres
    )
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm

def update_farm(db: Session, farm_id: int, farm_update: FarmUpdate) -> Farm:
    db_farm = get_farm(db, farm_id)
    if not db_farm:
        return None
    
    update_data = farm_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_farm, key, value)
        
    db.commit()
    db.refresh(db_farm)
    return db_farm

def delete_farm(db: Session, farm_id: int) -> bool:
    db_farm = get_farm(db, farm_id)
    if not db_farm:
        return False
    db.delete(db_farm)
    db.commit()
    return True

# ==============================================================================
# Crop CRUD
# ==============================================================================

def get_crop(db: Session, crop_id: int):
    return db.query(Crop).filter(Crop.id == crop_id).first()

def get_crops_by_farm(db: Session, farm_id: int):
    return db.query(Crop).filter(Crop.farm_id == farm_id).all()

def create_crop(db: Session, farm_id: int, crop: CropCreate) -> Crop:
    db_crop = Crop(
        farm_id=farm_id,
        crop_name=crop.crop_name,
        crop_type=crop.crop_type,
        sowing_date=crop.sowing_date,
        expected_harvest_date=crop.expected_harvest_date,
        status=crop.status
    )
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    return db_crop
