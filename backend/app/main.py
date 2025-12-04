from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_to_mongodb,close_mongo_connection
from app.routes import builds,predictions,metrics 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger=logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app:FastAPI):
    logger.info("Starting application...")
    await connect_to_mongodb()
    logger.info("Connected to MongoDB")
    yield
    logger.info("Shutting down application...")
    await close_mongo_connection()
    logger.info("MongoDB connection closed")

app=FastAPI(
    title="CI/CD AI Optimizer",
    description="AI powered pipeline optimizer for CI/CD",
    version="1.0.0",
    lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request:Request,exc:Exception):
    logger.error(f"Exception: {exc}")
    return JSONResponse(status_code=500,
    content={"details":"Internal Server Error","error":str(exc)})

@app.get("/health")
async def health_check():
     return {
        "status": "healthy",
        "service": "backend-api",
        "version": "1.0.0",
        "components": {
            "database": "connected",
            "ml_service": settings.ML_SERVICE_URL
        }
     }


@app.get('/')
async def root():
    return {"message":"Welcome to CI/CD AI Optimizer",
            "docs":"/docs",
            "health":"/health"}

app.include_router(builds.router,prefix="/api/v1/builds",tags=["builds"])
app.include_router(predictions.router,prefix="/api/v1/predictions",tags=["predictions"])
app.include_router(metrics.router,prefix="/api/v1/metrics",tags=["metrics"])

metrics_app=make_asgi_app()
app.mount("/metrics",metrics_app)

