"""
Web3 Payment Endpoint
Handles direct wallet payments (MetaMask, TronLink, etc.)
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.auth.middleware import require_auth, get_current_user
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crypto-payments", tags=["crypto-payments"])


class Web3PaymentRequest(BaseModel):
    """Request for Web3 payment submission"""
    tx_hash: str
    payment_address: str
    amount: float
    currency: str
    plan: str


@router.post("/web3-payment", dependencies=[Depends(require_auth)])
async def submit_web3_payment(
    request: Web3PaymentRequest,
    current_user = Depends(get_current_user)
):
    """
    Submit a Web3 payment transaction
    
    Called after user sends transaction via MetaMask/TronLink
    Links transaction to payment and triggers verification
    
    **Flow**:
    1. User connects wallet in Chat
    2. AI creates payment with address
    3. User sends transaction via Web3
    4. Frontend calls this endpoint with TX hash
    5. Backend updates payment status
    6. WebSocket notifies about confirmation
    """
    try:
        user_id = current_user.get("id")
        
        # Find payment by address
        payment = await postgres_client.fetchrow(
            """
            SELECT * FROM crypto_payments
            WHERE pay_address = $1 
            AND user_id = $2
            AND payment_status IN ('pending', 'waiting')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            request.payment_address,
            user_id
        )
        
        if not payment:
            raise HTTPException(
                status_code=404,
                detail="No pending payment found for this address"
            )
        
        # Update payment with transaction hash
        await postgres_client.execute(
            """
            UPDATE crypto_payments
            SET 
                pay_in_hash = $1,
                payment_status = 'waiting',
                updated_at = NOW()
            WHERE payment_id = $2
            """,
            request.tx_hash,
            payment["payment_id"]
        )
        
        logger.info(f"Web3 payment submitted: TX {request.tx_hash} for payment {payment['payment_id']}")
        
        # Notify via WebSocket (if connected)
        try:
            from app.api.v1.websockets.payment import broadcast_payment_update
            await broadcast_payment_update(
                payment_id=payment["payment_id"],
                status="waiting",
                tx_hash=request.tx_hash
            )
        except Exception as ws_error:
            logger.warning(f"WebSocket broadcast failed: {ws_error}")
        
        return {
            "success": True,
            "payment_id": payment["payment_id"],
            "tx_hash": request.tx_hash,
            "status": "waiting",
            "message": "Transaction submitted! Waiting for blockchain confirmation."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting Web3 payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Web3 payment")


@router.get("/web3-verify/{tx_hash}")
async def verify_web3_transaction(tx_hash: str):
    """
    Verify a Web3 transaction on blockchain
    
    This would be called by a background worker to check
    if transaction is confirmed and amount matches
    
    **Implementation**: Basic blockchain verification for EVM chains
    - ETH/BNB/MATIC: web3.eth.get_transaction() + get_transaction_receipt()
    - TRX: Requires tronweb (future implementation)
    - Verifies: to_address, value, confirmations
    """
    try:
        # Find payment by TX hash
        payment = await postgres_client.fetchrow(
            "SELECT * FROM crypto_payments WHERE pay_in_hash = $1",
            tx_hash
        )
        
        if not payment:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Basic blockchain verification for EVM chains
        verified = False
        confirmations = 0
        message = "Transaction found in database"
        
        try:
            currency = payment.get("pay_currency", "").upper()
            if currency in ["ETH", "BNB", "MATIC"]:
                # Attempt Web3 verification (requires RPC configured)
                from web3 import Web3
                import os
                
                rpc_url = None
                if currency == "ETH":
                    rpc_url = os.getenv("ETHEREUM_RPC_URL")
                elif currency == "BNB":
                    rpc_url = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
                elif currency == "MATIC":
                    rpc_url = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
                
                if rpc_url:
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    if w3.is_connected():
                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                        if receipt:
                            confirmations = w3.eth.block_number - receipt['blockNumber']
                            verified = receipt['status'] == 1 and confirmations >= 3
                            message = f"Verified on-chain: {confirmations} confirmations"
                        else:
                            message = "Transaction pending on blockchain"
        except Exception as verify_err:
            logger.warning(f"Blockchain verification failed (fallback to DB): {verify_err}")
            message = "Using database status (RPC unavailable)"
        
        return {
            "tx_hash": tx_hash,
            "payment_id": payment["payment_id"],
            "status": payment["payment_status"],
            "verified": verified or payment["payment_status"] == "finished",
            "confirmations": confirmations,
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying transaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify transaction")


# NOTE: The endpoint to extend the client-visible payment window exists in
# app/api/v1/crypto_payments.py as /crypto-payments/extend/{payment_id}.
# To avoid duplicate route registration, we intentionally do not define it here.


# ============================================================================
# Modern Web3 Payments (MetaMask, WalletConnect)
# ============================================================================

from app.auth.dependencies import get_current_user_strict


class ModernWeb3PaymentRequest(BaseModel):
    """Request to create modern Web3 payment"""
    plan_name: str
    amount_usd: float
    currency: str = "ETH"  # ETH, USDT, USDC, etc.
    network: str = "ethereum"  # ethereum, polygon, bsc, etc.


class ModernWeb3PaymentResponse(BaseModel):
    """Modern Web3 payment response"""
    payment_id: str
    contract_address: str
    amount_wei: str
    network: str
    chain_id: int
    payment_url: Optional[str] = None


# Network configurations
NETWORK_CONFIGS = {
    "ethereum": {
        "chain_id": 1,
        "rpc_url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
        "contract_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "explorer_url": "https://etherscan.io"
    },
    "polygon": {
        "chain_id": 137,
        "rpc_url": "https://polygon-rpc.com",
        "contract_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "explorer_url": "https://polygonscan.com"
    },
    "bsc": {
        "chain_id": 56,
        "rpc_url": "https://bsc-dataseed.binance.org",
        "contract_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "explorer_url": "https://bscscan.com"
    }
}


@router.post("/web3/modern", response_model=ModernWeb3PaymentResponse)
async def create_modern_web3_payment(
    request: ModernWeb3PaymentRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """Create a modern Web3 payment request (MetaMask/WalletConnect)."""
    try:
        # Validate network
        if request.network not in NETWORK_CONFIGS:
            raise HTTPException(status_code=400, detail="Unsupported network")

        network_config = NETWORK_CONFIGS[request.network]

        # Convert USD to crypto amount (simplified conversion)
        conversion_rates = {
            "ETH": 1 / 3000,  # ~$3000/ETH
            "USDT": 1,        # 1:1 with USD
            "USDC": 1,        # 1:1 with USD
        }

        if request.currency not in conversion_rates:
            raise HTTPException(status_code=400, detail="Unsupported currency")

        crypto_amount = request.amount_usd * conversion_rates[request.currency]

        # Convert to wei/smallest unit
        if request.currency == "ETH":
            amount_wei = str(int(crypto_amount * 10**18))
        else:  # USDT/USDC have 6 decimals
            amount_wei = str(int(crypto_amount * 10**6))

        # Generate payment ID
        import uuid
        payment_id = f"web3_modern_{uuid.uuid4().hex[:16]}"

        return ModernWeb3PaymentResponse(
            payment_id=payment_id,
            contract_address=network_config["contract_address"],
            amount_wei=amount_wei,
            network=request.network,
            chain_id=network_config["chain_id"],
            payment_url=f"/web3/checkout/{payment_id}"
        )

    except Exception as e:
        logger.error(f"Modern Web3 payment creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Web3 payment")


@router.post("/web3/verify")
async def verify_modern_web3_payment(
    tx_hash: str,
    network: str = "ethereum",
    current_user: dict = Depends(get_current_user_strict)
):
    """Verify modern Web3 payment by transaction hash."""
    try:
        # This would integrate with blockchain explorers or node
        # For demo, return mock status
        import random
        statuses = ["pending", "confirmed", "failed"]

        network_config = NETWORK_CONFIGS.get(network, NETWORK_CONFIGS["ethereum"])

        return {
            "tx_hash": tx_hash,
            "network": network,
            "status": random.choice(statuses),
            "confirmations": random.randint(0, 12),
            "block_number": random.randint(18000000, 19000000),
            "explorer_url": f"{network_config['explorer_url']}/tx/{tx_hash}",
            "verified": random.choice([True, False])
        }

    except Exception as e:
        logger.error(f"Modern Web3 payment verification failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")


@router.get("/web3/networks")
async def get_supported_web3_networks():
    """Get list of supported Web3 networks and currencies."""
    return {
        "networks": [
            {
                "id": network,
                "name": network.title(),
                "chain_id": config["chain_id"],
                "explorer_url": config["explorer_url"]
            }
            for network, config in NETWORK_CONFIGS.items()
        ],
        "currencies": ["ETH", "USDT", "USDC"],
        "wallets": ["metamask", "walletconnect", "trust", "coinbase", "rainbow"]
    }
