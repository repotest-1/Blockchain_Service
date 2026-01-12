# /backend/Blockchain_Service/ledger_service.py

import json
import os
from pathlib import Path
from web3 import Web3
from web3.exceptions import TransactionNotFound, BadFunctionCallOutput
import logging

# Assuming you use python-dotenv to load environment variables
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION LOADING ---
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY")
RPC_URL = os.getenv("BB_RPC_URL")

# Validate environment variables
if not all([CONTRACT_ADDRESS, ADMIN_PRIVATE_KEY, RPC_URL]):
    raise Exception("ERROR: Missing required environment variables. Check .env file.")

# Load ABI
try:
    # Get the directory where this script is located
    current_dir = Path(__file__).parent
    abi_path = current_dir / 'contract_abi.json'
    
    with open(abi_path, 'r') as f:
        CONTRACT_ABI = json.load(f)
    logger.info(f"Successfully loaded contract ABI from {abi_path}")
except FileNotFoundError:
    raise Exception(f"ERROR: contract_abi.json not found at {abi_path}. Check file path.")
except json.JSONDecodeError as e:
    raise Exception(f"ERROR: Invalid JSON in contract_abi.json: {e}")


# --- WEB3 SETUP ---
try:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    # Check connection status
    if not w3.is_connected():
        raise Exception(f"ERROR: Cannot connect to BuildBear RPC at {RPC_URL}. Check URL/Network status.")
    
    logger.info(f"Successfully connected to BuildBear RPC: {RPC_URL}")
    logger.info(f"Chain ID: {w3.eth.chain_id}")
    
    # Account Setup
    ADMIN_ACCOUNT = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
    logger.info(f"Admin account address: {ADMIN_ACCOUNT.address}")
    
    # Create contract instance
    ReportLedger = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)
    logger.info(f"Contract instance created at address: {CONTRACT_ADDRESS}")
    
except Exception as e:
    raise Exception(f"ERROR: Failed to set up Web3 components. Details: {e}")


def mint_report_to_ledger(report_data_json):
    """
    Takes the report data (JSON), stringifies it, and mints the hash onto the BuildBear ledger.
    
    Args:
        report_data_json (dict): The data received from the OOS frontend (report.js).
        
    Returns:
        dict: Contains success status and transactionHash or error message.
    """
    
    # 1. Prepare Data String (MUST BE DETERMINISTIC for correct hashing in SC)
    # The Smart Contract calls keccak256(abi.encodePacked(_reportData)).
    # We must ensure the Python string matches the Solidity input structure.
    # The easiest way is deterministic JSON serialization.
    try:
        # Use sort_keys=True to ensure the JSON key order is always the same.
        report_data_string = json.dumps(report_data_json, sort_keys=True, separators=(',', ':'))
        logger.info(f"Prepared report data string (first 200 chars): {report_data_string[:200]}...")
    except Exception as e:
        logger.error(f"Failed to serialize report data: {e}")
        return {"success": False, "error": f"Failed to serialize report data: {e}"}

    # 2. Build, Sign, and Send Transaction
    try:
        # Get current gas price and nonce
        nonce = w3.eth.get_transaction_count(ADMIN_ACCOUNT.address)
        logger.info(f"Current nonce for admin account: {nonce}")
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        logger.info(f"Current gas price: {w3.from_wei(gas_price, 'gwei')} gwei")
        
        # Estimate gas based on actual payload
        estimated_gas = ReportLedger.functions.recordReport(
            report_data_string
        ).estimate_gas({
            'from': ADMIN_ACCOUNT.address
        })
        
        logger.info(f"Estimated gas: {estimated_gas}")
        
        # Build the function call payload
        tx_build = ReportLedger.functions.recordReport(report_data_string).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': ADMIN_ACCOUNT.address,
            'nonce': nonce,
            'gas': estimated_gas + 50_000,  # safety buffer
            'maxFeePerGas': w3.to_wei('50', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2', 'gwei')
        })
        
        logger.info("Transaction built successfully, signing...")
        
        # Sign the transaction using the Admin's private key
        signed_tx = w3.eth.account.sign_transaction(tx_build, private_key=ADMIN_PRIVATE_KEY)
        
        logger.info("Transaction signed, sending to network...")
        
        # Send the transaction to the BuildBear network
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Transaction sent! Hash: {tx_hash.hex()}")
        logger.info("Waiting for transaction receipt...")
        
        # Wait for the transaction to be mined/confirmed (timeout 120 seconds)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # Check if transaction was successful
        if tx_receipt['status'] == 1:
            logger.info(f"Transaction successful! Block number: {tx_receipt['blockNumber']}")
            logger.info(f"Gas used: {tx_receipt['gasUsed']}")
            
            # Get the actual transaction hash with 0x prefix
            actual_tx_hash = tx_receipt['transactionHash'].hex() if hasattr(tx_receipt['transactionHash'], 'hex') else tx_receipt['transactionHash']
            logger.info(f"Returning transaction hash: {actual_tx_hash}")
            
            # Success! Return the transaction hash in hexadecimal format
            return {
                "success": True,
                "transactionHash": actual_tx_hash,
                "blockNumber": tx_receipt['blockNumber'],
                "gasUsed": tx_receipt['gasUsed']
            }
        else:
            logger.error("Transaction failed with status 0")
            return {
                "success": False,
                "error": "Transaction failed during execution"
            }

    except BadFunctionCallOutput as e:
        logger.error(f"Smart Contract function call failed: {e}")
        return {
            "success": False,
            "error": "Smart Contract function call failed. Check gas limit or contract logic."
        }
    except ValueError as e:
        logger.error(f"Value error during transaction: {e}")
        return {
            "success": False,
            "error": f"Transaction value error: {str(e)}"
        }
    except TimeoutError as e:
        logger.error(f"Transaction timeout: {e}")
        return {
            "success": False,
            "error": "Transaction timed out waiting for confirmation"
        }
    except Exception as e:
        logger.error(f"Unexpected error during minting: {e.__class__.__name__}: {e}")
        return {
            "success": False,
            "error": f"Web3 error during minting: {e.__class__.__name__} - {str(e)}"
        }


def get_report_hash(report_id):
    """
    Retrieves the stored hash for a given report ID from the blockchain.
    
    Args:
        report_id (int): The ID of the report
        
    Returns:
        dict: Contains success status and hash or error message
    """
    try:
        report_hash = ReportLedger.functions.getReportHash(report_id).call()
        return {
            "success": True,
            "hash": report_hash.hex()
        }
    except Exception as e:
        logger.error(f"Error retrieving report hash: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve report hash: {str(e)}"
        }