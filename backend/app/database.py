from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import logging
from app.config import settings

logger = logging.getLogger(__name__)

client:AsyncIOMotorClient=None
databse=None

async def connect_to_mongodb():
    global client,database

    try: 
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        database = client[settings.MONGODB_DB_NAME]
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB: {settings.MONGODB_URL}")
        await create_indexes()
    except ConnectionError as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    global client 
    if client:
        await client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    global database
    await database.builds.create_index("build_num")
    await database.builds.create_index("project_slug")
    await database.builds.create_index("created_at")
    await database.builds.create_index([('project_slug',1),('build_num',-1)])

    await database.predictions.create_index("build_num")
    await database.predictions.create_index("timestamp")

    logger.info("Indexes created successfully")

def get_database():
    return database
    
