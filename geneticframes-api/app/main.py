"""
GeneticFrames API - Main FastAPI Application
Hybrid Stack MVP with AlphaFold Integration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from loguru import logger

from app.core.config import settings
from app.core.exceptions import SpeciesNotFoundError, NCBIConnectionError, DNAParsingError
from app.api.v1.router import api_router
from app.core.cache import cache_manager

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info(f"🚀 Starting {settings.PROJECT_NAME}")
    logger.info(f"📊 Debug mode: {settings.DEBUG}")
    logger.info(f"🧬 AlphaFold enabled: {settings.ALPHAFOLD_ENABLED}")
    logger.info(f"💾 Redis enabled: {settings.REDIS_ENABLED}")
    logger.info(f"🔬 NCBI Live Mode: {settings.NCBI_LIVE_MODE}")
    
    # Initialize cache
    if settings.REDIS_ENABLED:
        await cache_manager.connect()
        logger.info("✅ Redis cache connected")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application")
    if settings.REDIS_ENABLED:
        await cache_manager.disconnect()
        logger.info("✅ Redis cache disconnected")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Generate unique DNA art from real genetic sequences with 3D protein visualization",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Custom Exception Handlers

@app.exception_handler(SpeciesNotFoundError)
async def species_not_found_handler(request: Request, exc: SpeciesNotFoundError):
    """Handle species not found errors"""
    logger.warning(f"Species not found: {exc.species_name}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Species Not Found",
            "message": exc.message,
            "species": exc.species_name
        }
    )

@app.exception_handler(NCBIConnectionError)
async def ncbi_connection_error_handler(request: Request, exc: NCBIConnectionError):
    """Handle NCBI connection errors"""
    logger.error(f"NCBI connection error: {exc.message}")
    return JSONResponse(
        status_code=502,
        content={
            "error": "Upstream Service Error",
            "message": "Could not connect to biological database services. Please try again later.",
            "details": exc.message if settings.DEBUG else None
        }
    )

@app.exception_handler(DNAParsingError)
async def dna_parsing_error_handler(request: Request, exc: DNAParsingError):
    """Handle DNA parsing errors"""
    logger.error(f"DNA parsing error: {exc.message}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "DNA Processing Error",
            "message": "The DNA sequence could not be processed for art generation.",
            "details": exc.message if settings.DEBUG else None
        }
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "path": str(request.url)
        }
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "healthy",
        "features": {
            "dna_analysis": True,
            "alphafold": settings.ALPHAFOLD_ENABLED,
            "3d_visualization": True,
            "cache": settings.REDIS_ENABLED,
            "ncbi_live_mode": settings.NCBI_LIVE_MODE
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "operational",
            "cache": "operational" if settings.REDIS_ENABLED else "disabled",
            "alphafold": "operational" if settings.ALPHAFOLD_ENABLED else "disabled"
        }
    }
    
    # Test cache connection
    if settings.REDIS_ENABLED:
        try:
            await cache_manager.ping()
        except Exception as e:
            health_status["services"]["cache"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
