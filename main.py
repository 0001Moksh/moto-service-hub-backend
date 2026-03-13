from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import check_database_connection
from app.routers import customer, vehicle, admin, owner, mechanic
from app.routers import booking_v2 as booking  # Use scalable booking router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Moto Service Hub - Backend API",
    description="Complete motorcycle service booking and management system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:8000",
    "http://127.0.0.1:8000"
],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Change in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# ==================== Health Check ====================

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint"""
    db_status = await check_database_connection()
    
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "database": db_status
    }


# ==================== Root ====================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/health"
    }


# ==================== Include Routers ====================

app.include_router(customer.router)
app.include_router(vehicle.router)
app.include_router(admin.router)
app.include_router(owner.router)
app.include_router(mechanic.router)
app.include_router(booking.router)


# ==================== Exception Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }
    )


# ==================== Startup & Shutdown ====================

# ==================== Startup & Shutdown ====================

async def startup_event():
    """Run on app startup"""
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.APP_NAME} API Starting...")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info("=" * 50)
    
    # Check database connection
    db_status = await check_database_connection()
    if db_status["status"] == "connected":
        logger.info("✅ Database connected")
    else:
        logger.error(f"❌ Database connection failed: {db_status['message']}")


async def shutdown_event():
    """Run on app shutdown"""
    logger.info("=" * 50)
    logger.info("🛑 Application shutting down...")
    logger.info("=" * 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
