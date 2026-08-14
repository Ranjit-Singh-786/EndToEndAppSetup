import hashlib
from sqlalchemy.orm import Session
from app.models import Farmer
from app.schemas import FarmerCreate, FarmerUpdate

def hash_password(password: str) -> str:
    """Helper to hash password using SHA-256 (lightweight, zero-dependency)."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_farmer(db: Session, farmer_id: int):
    return db.query(Farmer).filter(Farmer.id == farmer_id).first()

def get_farmer_by_email(db: Session, email: str):
    return db.query(Farmer).filter(Farmer.email == email).first()

def get_farmers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Farmer).offset(skip).limit(limit).all()

def create_farmer(db: Session, farmer: FarmerCreate) -> Farmer:
    db_farmer = Farmer(
        name=farmer.name,
        email=farmer.email,
        password_hash=hash_password(farmer.password),
        phone=farmer.phone
    )
    db.add(db_farmer)
    db.commit()
    db.refresh(db_farmer)
    return db_farmer

def update_farmer(db: Session, farmer_id: int, farmer_update: FarmerUpdate) -> Farmer:
    db_farmer = get_farmer(db, farmer_id)
    if not db_farmer:
        return None
    
    update_data = farmer_update.dict(exclude_unset=True)
    if 'password' in update_data:
        update_data['password_hash'] = hash_password(update_data.pop('password'))
        
    for key, value in update_data.items():
        setattr(db_farmer, key, value)
        
    db.commit()
    db.refresh(db_farmer)
    return db_farmer

def delete_farmer(db: Session, farmer_id: int) -> bool:
    db_farmer = get_farmer(db, farmer_id)
    if not db_farmer:
        return False
    db.delete(db_farmer)
    db.commit()
    return True
