from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(Integer, nullable=False, index=True)  # No database foreign key to another service
    farm_name = Column(String(100), nullable=False)
    location = Column(String(150), nullable=False)
    area_acres = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to crops table within the same service
    crops = relationship("Crop", back_populates="farm", cascade="all, delete-orphan")

class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False, index=True)
    crop_name = Column(String(100), nullable=False)
    crop_type = Column(String(50), nullable=False)
    sowing_date = Column(Date, nullable=False)
    expected_harvest_date = Column(Date, nullable=False)
    status = Column(String(30), default="Sown")  # E.g., Sown, Growing, Harvested
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to farm table within the same service
    farm = relationship("Farm", back_populates="crops")
