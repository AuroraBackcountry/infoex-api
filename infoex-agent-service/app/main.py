"""Main FastAPI application for InfoEx Claude Agent Service"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import logging
import sys
import os
from typing import Dict, Any

from app.config import settings
from app.api.routes import router
from app.services.session import session_manager
from app import __version__

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Set up standard logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, settings.log_level.upper()),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("starting_infoex_agent_service",
               version=__version__,
               environment=settings.infoex_environment)
    
    # Connect to Redis
    try:
        await session_manager.connect()
        logger.info("redis_connection_established")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        raise
    
    # Log configuration
    logger.info("service_configuration",
               infoex_env=settings.infoex_environment,
               redis_host=settings.redis_host,
               session_ttl=settings.session_ttl_seconds,
               max_conversation=settings.max_conversation_length)
    
    yield
    
    # Shutdown
    logger.info("shutting_down_infoex_agent_service")
    await session_manager.disconnect()
    logger.info("service_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title="InfoEx Claude Agent Service",
    description="Intelligent middleware for InfoEx API submissions using Claude",
    version=__version__,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error("unhandled_exception",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.log_level == "DEBUG" else "An unexpected error occurred",
            "code": "INTERNAL_ERROR"
        }
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses"""
    import time
    
    # Skip health check logging to reduce noise
    if request.url.path == "/health":
        return await call_next(request)
    
    start_time = time.time()
    
    # Log request
    logger.info("request_received",
               method=request.method,
               path=request.url.path,
               client=request.client.host if request.client else None)
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info("request_completed",
               method=request.method,
               path=request.url.path,
               status_code=response.status_code,
               duration_seconds=round(duration, 3))
    
    return response


# Include routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "InfoEx Claude Agent",
        "version": __version__,
        "status": "running",
        "environment": settings.infoex_environment,
        "endpoints": {
            "process_report": "/api/process-report",
            "submit": "/api/submit-to-infoex",
            "session_status": "/api/session/{session_id}/status",
            "clear_session": "/api/session/{session_id}/clear",
            "health": "/health",
            "locations": "/api/locations",
            "docs": "/docs"
        }
    }


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "detail": f"Path {request.url.path} not found",
            "code": "NOT_FOUND"
        }
    )


# Rate limit handler (if implementing rate limiting)
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    """Handle rate limit errors"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please try again later.",
            "code": "RATE_LIMIT_EXCEEDED"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Use PORT from environment if available (for Render)
    port = int(os.environ.get("PORT", settings.service_port))
    
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=port,
        reload=settings.log_level == "DEBUG",
        log_level=settings.log_level.lower()
    )
