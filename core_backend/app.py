from connection_manager import manager
from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import logging
from room_manager import router as room_router
from login_routes import router as login_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="P2P Video Conferencing Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

@app.on_event("startup")
async def startup_event():
    await manager.connect_redis()
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    await manager.disconnect_redis()
    logger.info("Application shutdown complete")

app.include_router(room_router)
app.include_router(login_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "redis_connected": manager.redis_client is not None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)