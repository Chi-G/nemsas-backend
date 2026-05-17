from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import api_router
import app.models.base # Force register all models to load relationships
from app.core.config import settings
from app.core.middleware import LoggingMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from contextlib import asynccontextmanager
from app.services.notification_service import notification_service
from app.core.notifications import notification_service as fcm_notification_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await notification_service.connect_redis()
    yield
    # Shutdown
    await notification_service.disconnect_redis()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
    
    # Handle case where detail is a dict (our custom format) or a string (standard format)
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", "An error occurred")
        error = exc.detail.get("error", "Error details not provided")
    else:
        message = "An error occurred"
        error = exc.detail

    response = JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "success": False,
            "status": exc.status_code,
            "message": message,
            "error": error
        }),
    )
    # Manually add CORS headers as custom exception handlers sometimes bypass CORSMiddleware
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"ValidationError: {exc.errors()} | Body: {body.decode()}")
    response = JSONResponse(
        status_code=400,
        content={
            "success": False,
            "status": 400,
            "message": "Input validation failed",
            "error": exc.errors()
        },
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
        
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response




@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status": 500,
            "message": "An internal server error occurred",
            "error": str(exc)
        },
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
        
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response





# Add custom middleware
# app.add_middleware(LoggingMiddleware)


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import socketio
from app.core.socket_manager import sio

app.include_router(api_router, prefix=settings.API_V1_STR)

# Ensure static upload directory exists
import os
os.makedirs("static/uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, socketio_path='socket.io')
app.mount("/socket.io", socket_app)

@app.get("/")
async def root():
    return {"message": "Welcome to NEMSAS API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
