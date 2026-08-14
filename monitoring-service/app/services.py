from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo import MongoClient
from app.schemas import SensorReadingCreate, MonitoringSummary

def create_reading(db, reading: SensorReadingCreate) -> Dict[str, Any]:
    """Insert a new sensor reading document into MongoDB."""
    reading_dict = reading.dict()
    # MongoDB stores nested objects nicely
    if reading_dict.get('additional_data'):
        reading_dict['additional_data'] = reading.additional_data.dict()
        
    result = db.sensor_readings.insert_one(reading_dict)
    reading_dict["id"] = str(result.inserted_id)
    return reading_dict

def get_readings_by_farm(db, farm_id: int) -> List[Dict[str, Any]]:
    """Retrieve all readings for a given farm, sorted newest first."""
    cursor = db.sensor_readings.find({"farm_id": farm_id}).sort("timestamp", -1)
    readings = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        readings.append(doc)
    return readings

def get_latest_reading(db, farm_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve the single latest reading for a farm."""
    doc = db.sensor_readings.find_one(
        {"farm_id": farm_id}, 
        sort=[("timestamp", -1)]
    )
    if doc:
        doc["id"] = str(doc["_id"])
        return doc
    return None

def get_farm_summary(db, farm_id: int) -> Dict[str, Any]:
    """Calculate average conditions and total rainfall using MongoDB Aggregation Pipeline."""
    pipeline = [
        {"$match": {"farm_id": farm_id}},
        {
            "$group": {
                "_id": "$farm_id",
                "readings_count": {"$sum": 1},
                "avg_temperature": {"$avg": "$temperature"},
                "avg_humidity": {"$avg": "$humidity"},
                "avg_soil_moisture": {"$avg": "$soil_moisture"},
                "total_rainfall": {"$sum": "$rainfall"}
            }
        }
    ]
    
    result = list(db.sensor_readings.aggregate(pipeline))
    
    if result:
        summary = result[0]
        return {
            "farm_id": farm_id,
            "readings_count": summary["readings_count"],
            "avg_temperature": round(summary["avg_temperature"], 2) if summary["avg_temperature"] is not None else 0.0,
            "avg_humidity": round(summary["avg_humidity"], 2) if summary["avg_humidity"] is not None else 0.0,
            "avg_soil_moisture": round(summary["avg_soil_moisture"], 2) if summary["avg_soil_moisture"] is not None else 0.0,
            "total_rainfall": round(summary["total_rainfall"], 2) if summary["total_rainfall"] is not None else 0.0
        }
        
    return {
        "farm_id": farm_id,
        "readings_count": 0,
        "avg_temperature": 0.0,
        "avg_humidity": 0.0,
        "avg_soil_moisture": 0.0,
        "total_rainfall": 0.0
    }
