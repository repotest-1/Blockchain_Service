from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routers
from routes import blockchain_router
from database import init_db

app = FastAPI(title="Blockchain Service")

# Include the blockchain router
app.include_router(blockchain_router, prefix='/blockchain', tags=['blockchain'])

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend (default)
        "http://localhost:4002",  # OOS frontend
        "http://localhost:5000",  # OOS frontend alternative
        "http://192.168.100.14:5000",  # OOS LAN frontend
        "http://127.0.0.1:4002",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:7000",  # Ordering service
        "http://localhost:7000",
        "http://127.0.0.1:7001",  # Delivery service
        "http://localhost:7001",
        "http://127.0.0.1:7002",  # Notification service
        "http://localhost:7002",
        "http://127.0.0.1:7003",  # Concerns service
        "http://localhost:7003",
        "http://127.0.0.1:7004",  # Track Order service
        "http://localhost:7004",
        "http://127.0.0.1:7005",  # Payment service
        "http://localhost:7005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Blockchain Service is running", "service": "blockchain"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "blockchain"}

# Run the app (only used when running as a script directly)
if __name__ == "__main__":
    import asyncio
    # Ensure DB schema exists before starting
    asyncio.run(init_db())
    uvicorn.run("main:app", port=7006, host="127.0.0.1", reload=True)
