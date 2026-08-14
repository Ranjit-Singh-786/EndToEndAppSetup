from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class FarmerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Ranjit Farmer")
    email: EmailStr = Field(..., example="ranjit@example.com")
    phone: Optional[str] = Field(None, example="+1-123-456-7890")

class FarmerCreate(FarmerBase):
    password: str = Field(..., min_length=6, example="secret123")

class FarmerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)

class FarmerResponse(FarmerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Ranjit Farmer",
                "email": "ranjit@example.com",
                "phone": "+1-123-456-7890",
                "created_at": "2026-08-12T10:00:00"
            }
        }
