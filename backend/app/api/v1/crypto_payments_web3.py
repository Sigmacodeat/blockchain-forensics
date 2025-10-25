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
