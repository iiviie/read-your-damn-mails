import logging
import sys
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.endpoints import router as api_router
from app.models import create_tables
from app.scheduler import scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    logger.info("Initializing application...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    # Start email scheduler
    scheduler.start()
    logger.info("Email scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down application...")
    
    # Stop email scheduler
    scheduler.stop()
    logger.info("Email scheduler stopped")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 