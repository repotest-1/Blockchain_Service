# Blockchain Service for Report Generation

## Overview
This service provides blockchain integration for securing and verifying admin reports using BuildBear testnet and smart contracts. Reports are hashed and minted to the blockchain to create immutable, verifiable records.

## Architecture

### Backend Components
- **main.py**: FastAPI application server
- **routes.py**: API endpoints for blockchain operations
- **ledger_service.py**: Web3 integration and blockchain interaction
- **contract_abi.json**: Smart contract ABI definition
- **.env**: Configuration (RPC URL, contract address, private key)

### Frontend Integration
- **report.js**: Admin report generation and blockchain integration UI

## Features

✅ **Hash Generation**: Creates cryptographic hash per report export  
✅ **Blockchain Minting**: Stores report hash on BuildBear blockchain  
✅ **Transaction Verification**: Provides transaction hash and explorer link  
✅ **Modal UI**: Clean interface for hash display and verification  
✅ **Copy to Clipboard**: Easy hash copying functionality  
✅ **BuildBear Explorer**: Direct link to verify transaction on blockchain  

## Configuration

### Environment Variables (.env)
```env
BB_RPC_URL="https://rpc.buildbear.io/selfish-gilgamesh-91962214"
CONTRACT_ADDRESS="0x96a3D22e16a6C94e25421DB22795267D72c75A9A"
ADMIN_PRIVATE_KEY="0x20730dd2f23ceca3ad6d0c5cf20752024ac43af4ad3695e9e1425552908a0939"
```

## API Endpoints

### POST /blockchain/mint-report
Mints a report to the blockchain.

**Request Body:**
```json
{
  "startDate": "2024-01-01",
  "endDate": "2024-01-31",
  "totalRevenue": 450000,
  "totalOrders": 1100,
  "avgOrderValue": 400,
  "completionRate": 92,
  "orders": [...]
}
```

**Response:**
```json
{
  "success": true,
  "transactionHash": "0x1234...abcd",
  "explorerUrl": "https://explorer.buildbear.io/selfish-gilgamesh-91962214/tx/0x1234...abcd"
}
```

### GET /health
Health check endpoint.

## Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- BuildBear account and testnet setup

### Backend Setup
```bash
cd backend/Blockchain_Service
pip install -r requirements.txt
python main.py
```

The service will start on `http://127.0.0.1:7006`

### Frontend Setup
The frontend automatically connects to the blockchain service at `http://127.0.0.1:7006`

## Usage

1. **Generate Report**: In admin dashboard, set date range and click "Generate Report"
2. **Review Data**: Modal shows report summary with metrics
3. **Secure on Blockchain**: Click "Secure & Mint Report" button
4. **Wait for Mining**: Transaction is sent and confirmed on blockchain (~3-5 seconds)
5. **Verify**: Transaction hash displayed with link to BuildBear Explorer
6. **Copy Hash**: Click clipboard icon to copy transaction hash
7. **Export**: Download CSV or PDF with blockchain verification included

## Smart Contract

The service interacts with a Solidity smart contract deployed on BuildBear:

```solidity
function recordReport(string memory _reportData) public returns (uint256)
```

This function:
- Takes report data as JSON string
- Generates keccak256 hash
- Stores hash with unique ID
- Emits `ReportMinted` event
- Returns report ID

## Security Features

- **Immutable Records**: Once minted, report data cannot be altered
- **Cryptographic Proof**: Keccak256 hashing ensures data integrity
- **Timestamp**: Blockchain timestamp proves when report was created
- **Verifiable**: Anyone can verify report hash on blockchain explorer

## Task Integration

Added to `.vscode/tasks.json`:
```json
{
  "label": "Start Blockchain Service",
  "type": "shell",
  "command": "cd backend/Blockchain_Service; python main.py"
}
```

Included in "Start All Services" task for easy startup.

## Troubleshooting

### Web3 Connection Issues
- Verify BB_RPC_URL in .env file
- Check BuildBear testnet status
- Ensure network connectivity

### Transaction Failures
- Check admin account has sufficient test ETH
- Verify contract address is correct
- Increase gas limits if needed

### CORS Errors
- Ensure frontend URL is in CORS allowed origins
- Check browser console for specific errors

## Development Notes

- Service runs on port **7006**
- Uses Web3.py version 7.6.0
- Compatible with BuildBear testnet (Chain ID: 31337)
- Supports EIP-1559 transactions (maxFeePerGas, maxPriorityFeePerGas)

## Future Enhancements

- [ ] Add report retrieval by hash
- [ ] Implement batch report minting
- [ ] Support multiple blockchain networks
- [ ] Add transaction history viewing
- [ ] Integrate IPFS for full report storage
- [ ] Add signature verification for admins

## License
Part of OOS-2 project

## Contact
For issues or questions, please contact the development team.
