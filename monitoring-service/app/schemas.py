from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class AdditionalSensorData(BaseModel):
    battery: Optional[int] = Field(None, ge=0, le=100, example=87)
    signal_strength: Optional[int] = Field(None, ge=0, le=100, example=92)

class SensorReadingBase(BaseModel):
    farm_id: int = Field(..., example=1)
    sensor_id: str = Field(..., min_length=2, max_length=50, example="SENSOR-001")
    timestamp: datetime = Field(default_factory=datetime.utcnow, example="2026-08-12T10:00:00")
    temperature: float = Field(..., ge=-50, le=60, example=31.5)
    humidity: float = Field(..., ge=0, le=100, example=62.0)
    soil_moisture: float = Field(..., ge=0, le=100, example=41.0)
    rainfall: float = Field(..., ge=0, example=0.0)
    additional_data: Optional[AdditionalSensorData] = None

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingResponse(SensorReadingBase):
    id: str  # MongoDB ObjectId serialized as string

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "64d6fbbf4fa61e2a0f8b4567",
                "farm_id": 1,
                "sensor_id": "SENSOR-001",
                "timestamp": "2026-08-12T10:00:00",
                "temperature": 31.5,
                "humidity": 62.0,
                "soil_moisture": 41.0,
                "rainfall": 0.0,
                "additional_data": {
                    "battery": 87,
                    "signal_strength": 92
                }
            }
        }

class MonitoringSummary(BaseModel):
    farm_id: int
    readings_count: int
    avg_temperature: Optional[float] = None
    avg_humidity: Optional[float] = None
    avg_soil_moisture: Optional[float] = None
    total_rainfall: Optional[float] = None
