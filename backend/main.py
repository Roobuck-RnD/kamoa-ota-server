"""
FastAPI application entry point with all routes.
"""
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.responses import FileResponse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import API routers
from backend.api.devices import router as devices_router
from backend.api.config import router as config_router
from backend.api.firmware import router as firmware_router
from backend.api.ota import router as ota_router

# Import MQTT client
from backend.mqtt_client import mqtt_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown handlers."""
    # Startup: Connect to MQTT broker
    print("Starting OTA Server...")
    mqtt_client.connect()
    yield
    # Shutdown: Disconnect from MQTT broker
    print("Shutting down OTA Server...")
    mqtt_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title="IoT OTA Update Server",
    description="Over-The-Air update management system for IoT devices",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(devices_router)
app.include_router(config_router)
app.include_router(firmware_router)
app.include_router(ota_router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.is_connected()
    }


# Serve firmware files statically
firmware_dir = Path(__file__).parent / "firmware"
firmware_dir.mkdir(exist_ok=True)
app.mount("/firmware", StaticFiles(directory=str(firmware_dir)), name="firmware")

# Serve frontend static files
# In Docker: /app/frontend, Local: ../frontend from backend/
frontend_dir = Path(__file__).parent.parent / "frontend"
if not frontend_dir.exists():
    # Fallback for different deployment scenarios
    frontend_dir = Path("/app/frontend")

app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")


@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html."""
    return FileResponse(frontend_dir / "index.html")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str, request: Request):
    """Serve SPA routes - fallback to index.html for any non-API path."""
    # Don't interfere with API routes or firmware
    if full_path.startswith("api/") or full_path.startswith("firmware/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(frontend_dir / "index.html")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
