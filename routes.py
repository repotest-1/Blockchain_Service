# /backend/Blockchain_Service/routes.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from ledger_service import mint_report_to_ledger
import os
from database import get_db_connection, init_db
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI router
blockchain_router = APIRouter()

# Request model for report data
class ReportData(BaseModel):
    startDate: str
    endDate: str
    totalRevenue: float
    totalOrders: int
    avgOrderValue: float
    completionRate: float
    orders: List[Dict[str, Any]]

# Response model
class MintResponse(BaseModel):
    success: bool
    transactionHash: Optional[str] = None
    error: Optional[str] = None
    explorerUrl: Optional[str] = None

@blockchain_router.post("/mint-report", response_model=MintResponse)
async def handle_mint_report(report_data: ReportData):
    """
    Endpoint to mint a report hash onto the blockchain.
    
    Args:
        report_data: The report data to be hashed and stored on blockchain
        
    Returns:
        MintResponse with transaction hash and explorer URL
    """
    try:
        # Log the incoming request
        logger.info(f"Received mint request for report: {report_data.startDate} to {report_data.endDate}")
        
        # Convert Pydantic model to dict for processing
        data = report_data.model_dump()
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No report data provided"
            )

        # Call the core Web3 service function
        result = mint_report_to_ledger(data)
        
        # Return result to React frontend
        if result["success"]:
            # Add BuildBear explorer URL for transaction verification
            tx_hash = result["transactionHash"]

            # Ensure tx_hash has 0x prefix for explorer URL
            if not tx_hash.startswith('0x'):
                tx_hash = f"0x{tx_hash}"

            # Derive sandbox path from BB_RPC_URL env (e.g., rpc.buildbear.io/<sandbox>)
            rpc_url = os.getenv("BB_RPC_URL", "")
            sandbox = None
            try:
                if rpc_url and "rpc.buildbear.io/" in rpc_url:
                    sandbox = rpc_url.split("rpc.buildbear.io/")[1].strip("/")
            except Exception:
                sandbox = None

            # Fallback to previous sandbox if env parsing fails
            base_path = sandbox if sandbox else "selfish-gilgamesh-91962214"

            # BuildBear explorer URL format
            explorer_url = f"https://explorer.buildbear.io/{base_path}/tx/{tx_hash}"
            
            logger.info(f"Successfully minted report. TX Hash: {tx_hash}")
            
            # Persist the minted report metadata
            try:
                await init_db()
                conn = await get_db_connection()
                cursor = await conn.cursor()
                
                insert_query = """
                INSERT INTO report_blockchain 
                (startDate, endDate, totalRevenue, totalOrders, avgOrderValue, completionRate, txHash, explorerUrl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                await cursor.execute(insert_query, (
                    data.get('startDate'),
                    data.get('endDate'),
                    float(data.get('totalRevenue', 0) or 0),
                    int(data.get('totalOrders', 0) or 0),
                    float(data.get('avgOrderValue', 0) or 0),
                    float(data.get('completionRate', 0) or 0),
                    tx_hash,
                    explorer_url
                ))
                
                await cursor.close()
                await conn.close()
            except Exception as e:
                logger.error(f"Failed to store report metadata: {e}")

            return MintResponse(
                success=True,
                transactionHash=tx_hash,
                explorerUrl=explorer_url
            )
        else:
            logger.error(f"Minting failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to mint report on blockchain")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in mint endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@blockchain_router.get("/health")
async def health_check():
    """Health check endpoint for the blockchain service"""
    return {"status": "healthy", "service": "blockchain-router"}

# --- Retrieve stored hash by date range ---
class ReportQuery(BaseModel):
    startDate: str
    endDate: str


class ReportHashResponse(BaseModel):
    success: bool
    transactionHash: Optional[str] = None
    explorerUrl: Optional[str] = None


@blockchain_router.post("/report-hash", response_model=ReportHashResponse)
async def get_report_hash(query: ReportQuery):
    """Return latest stored txHash for a given date range."""
    try:
        await init_db()
        conn = await get_db_connection()
        cursor = await conn.cursor()
        
        select_query = """
        SELECT TOP 1 txHash, explorerUrl 
        FROM report_blockchain 
        WHERE startDate = ? AND endDate = ? 
        ORDER BY createdAt DESC
        """
        
        await cursor.execute(select_query, (query.startDate, query.endDate))
        row = await cursor.fetchone()
        
        await cursor.close()
        await conn.close()

        if not row:
            return {"success": False}
        
        return {
            "success": True,
            "transactionHash": row[0],
            "explorerUrl": row[1],
        }
    except Exception as e:
        logger.error(f"Failed to fetch report hash: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report hash")