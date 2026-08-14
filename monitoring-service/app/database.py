import logging
from pymongo import MongoClient
from app.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)

# Global client and database instances
client = None
db = None

def init_db():
    """Initialize MongoDB connection and verify with a ping."""
    global client, db
    try:
        logger.info(f"Connecting to MongoDB: {settings.mongo_url}")
        client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
        # The ping command is cheap and checks if the server is responsive
        client.admin.command('ping')
        db = client[settings.MONGODB_DATABASE]
        logger.info("MongoDB connection established successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

def get_db():
    """Dependency to retrieve the database client. Connects dynamically if not initialized."""
    global db
    if db is None:
        local_client = MongoClient(settings.mongo_url)
        return local_client[settings.MONGODB_DATABASE]
    return db
