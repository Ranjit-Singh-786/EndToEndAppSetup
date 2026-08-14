"""
MongoDB Model definitions for the Farm Monitoring Service.
Since MongoDB is schema-less, the document structure is represented
using Pydantic schemas. 

The 'sensor_readings' collection stores documents structured as follows:

{
  "_id": ObjectId("..."),
  "farm_id": 1,
  "sensor_id": "SENSOR-001",
  "timestamp": ISODate("2026-08-12T10:00:00Z"),
  "temperature": 31.5,
  "humidity": 62.0,
  "soil_moisture": 41.0,
  "rainfall": 0.0,
  "additional_data": {
    "battery": 87,
    "signal_strength": 92
  }
}
"""
