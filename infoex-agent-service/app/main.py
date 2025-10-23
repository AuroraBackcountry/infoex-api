"""Main FastAPI application for InfoEx Claude Agent Service"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with helpful response"""
    logger.warning("validation_error",
                  path=request.url.path,
                  errors=exc.errors())
    
    # Build helpful error response based on the endpoint
    if request.url.path == "/api/process-report":
        example_body = {
            "session_id": "your-unique-session-id",
            "message": "Your observation or report text here",
            "request_values": {
                "operation_id": "your-operation-uuid (from InfoEx)",
                "location_uuids": ["location-uuid-1", "location-uuid-2"],
                "zone_name": "Your zone name (e.g., 'North Bowl')",
                "date": "MM/DD/YYYY (e.g., '10/23/2025')"
            },
            "auto_submit": True  # Optional, defaults to true
        }
        
        field_descriptions = {
            "session_id": "A unique identifier for this conversation session",
            "message": "The observation text from your guide (e.g., 'Size 2 avalanche observed')",
            "request_values": "Required context for the submission",
            "request_values.operation_id": "Your Aurora Backcountry operation UUID from InfoEx",
            "request_values.location_uuids": "Array of location UUIDs where observation occurred",
            "request_values.zone_name": "The zone/area name for context",
            "request_values.date": "Today's date in MM/DD/YYYY format",
            "auto_submit": "If true, automatically submits to InfoEx when ready (default: true)"
        }
    elif request.url.path == "/api/submit-to-infoex":
        example_body = {
            "session_id": "your-session-id",
            "submission_types": ["avalanche_observation", "field_summary"]
        }
        
        field_descriptions = {
            "session_id": "The session ID containing payloads ready for submission",
            "submission_types": "Optional array of observation types to submit (submits all ready payloads if omitted)"
        }
    else:
        example_body = None
        field_descriptions = None
    
    # Extract the specific missing/invalid fields
    missing_fields = []
    invalid_fields = []
    for error in exc.errors():
        if error["type"] == "missing":
            missing_fields.append(".".join(str(loc) for loc in error["loc"]))
        else:
            invalid_fields.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "issue": error["msg"],
                "type": error["type"]
            })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request format",
            "agent_message": "I need help fixing the request format. Please update your HTTP Request node.",
            "missing_fields": missing_fields,
            "invalid_fields": invalid_fields,
            "validation_errors": exc.errors(),
            "correct_format": example_body,
            "field_descriptions": field_descriptions,
            "instructions_for_n8n_agent": (
                "Please update the HTTP Request body to match the 'correct_format' structure. "
                "The most common issue is using 'fixed_values' instead of 'request_values'. "
                "Make sure all fields in 'missing_fields' are included."
            )
        }
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
