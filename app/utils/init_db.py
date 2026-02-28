import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize MongoDB database collections and indexes"""
    load_dotenv()
    
    # Get MongoDB connection details from environment variables
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    db_name = os.getenv('DB_NAME', 'instructai')
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        logger.info(f"Connecting to MongoDB: {db_name}")

        # Create indexes for 'courses' collection
        # MongoDB creates collections automatically on first insert, 
        # but we can pre-define indexes for performance
        db.courses.create_index([("title", ASCENDING)])
        db.courses.create_index([("createdAt", ASCENDING)])
        logger.info("Successfully created/verified indexes for 'courses' collection")

        # In the new simplified workflow, weekly topics are stored 
        # within the course document's 'weeklyTopics' array.
        # If we ever need to query by week across courses:
        db.courses.create_index([("weeklyTopics.week", ASCENDING)])
        
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    init_db()
