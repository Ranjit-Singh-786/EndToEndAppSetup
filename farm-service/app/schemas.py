from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List

# ==============================================================================
# Crop Schemas
# ==============================================================================

class CropBase(BaseModel):
    crop_name: str = Field(..., min_length=2, max_length=100, example="Wheat")
    crop_type: str = Field(..., min_length=2, max_length=50, example="Cereal")
    sowing_date: date = Field(..., example="2026-08-12")
    expected_harvest_date: date = Field(..., example="2026-12-12")
    status: str = Field("Sown", max_length=30, example="Sown")

class CropCreate(CropBase):
    pass

class CropResponse(CropBase):
    id: int
    farm_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# Farm Schemas
# ==============================================================================

class FarmBase(BaseModel):
    farmer_id: int = Field(..., example=1)
    farm_name: str = Field(..., min_length=2, max_length=100, example="Green Valley Farm")
    location: str = Field(..., min_length=2, max_length=150, example="California, USA")
    area_acres: float = Field(..., gt=0.0, example=50.5)

class FarmCreate(FarmBase):
    pass

class FarmUpdate(BaseModel):
    farmer_id: Optional[int] = None
    farm_name: Optional[str] = Field(None, min_length=2, max_length=100)
    location: Optional[str] = Field(None, min_length=2, max_length=150)
    area_acres: Optional[float] = Field(None, gt=0.0)

class FarmResponse(FarmBase):
    id: int
    created_at: datetime
    crops: List[CropResponse] = []

    class Config:
        from_attributes = True
