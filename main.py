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
        "https://bleu-ims-beta.vercel.app",  # React frontend (default)
        "https://bleu-ums-zeta.vercel.app",  # OOS frontend
        "https://bleu-oos-rouge.vercel.app",  # OOS frontend alternative
        "https://bleu-oos-rouge.vercel.app",  # OOS LAN frontend
        "https://bleu-ums-zeta.vercel.app",
        "https://bleu-oos-rouge.vercel.app",
        
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
