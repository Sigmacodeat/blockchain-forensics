"""
Smart Money Tracking API
========================

REST API für Smart Money Tracking (Nansen-Style Features)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from app.services.smart_money_tracker import smart_money_tracker
from app.services.multi_chain import multi_chain_engine
from app.api.deps import get_current_user, require_plan
from pydantic import BaseModel

router = APIRouter(prefix="/smart-money", tags=["smart_money"])
logger = logging.getLogger(__name__)


# =========================================================================
# REQUEST/RESPONSE MODELS
# =========================================================================

class ClassifyRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    min_transactions: int = 50


class SmartMoneyResponse(BaseModel):
    address: str
    chain: str
    classification: str
    confidence: float
    metrics: dict
    labels: List[str]
    total_value_usd: float
    win_rate: float
    timestamp: str


class TradingSignalResponse(BaseModel):
    signal_type: str
    trader_address: str
    trader_reputation: float
    token_symbol: str
    amount_usd: float
    confidence: float
    reasoning: List[str]
    timestamp: str


# =========================================================================
# ENDPOINTS
# =========================================================================

@router.post("/classify", response_model=SmartMoneyResponse)
async def classify_smart_money(
    request: ClassifyRequest,
    current_user = Depends(get_current_user),
    _plan_check = Depends(require_plan('pro'))
) -> SmartMoneyResponse:
    """
    Klassifiziere Wallet als Smart Money
    
    **Required Plan:** Pro+
    
    Identifiziert:
    - Top Traders (High Win Rate)
    - Whales (Large Holdings)
    - MEV Bots (Frontrunning)
    - Early Adopters
    - Crypto Funds
    """
    try:
        # Initialize chain
        await multi_chain_engine.initialize_chains([request.chain])
        
        # Fetch transactions
        transactions = await multi_chain_engine.get_address_transactions_paged(
            request.chain,
            request.address,
            limit=500
        )
        
        if len(transactions) < request.min_transactions:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient transaction history ({len(transactions)} < {request.min_transactions})"
            )
        
        # Try all classifiers
        profile = None
        
        # 1. Top Trader
        profile = await smart_money_tracker.classify_top_trader(request.address, transactions)
        
        # 2. Whale (würde balance fetchen)
        if not profile:
            balance_usd = 0  # Would fetch from chain
            profile = await smart_money_tracker.classify_whale(request.address, balance_usd, transactions)
        
        # 3. MEV Bot
        if not profile:
            profile = await smart_money_tracker.classify_mev_bot(request.address, transactions)
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="No smart money classification found for this address"
            )
        
        return SmartMoneyResponse(
            address=profile.address,
            chain=request.chain,
            classification=profile.classification,
            confidence=profile.confidence,
            metrics=profile.metrics,
            labels=profile.labels,
            total_value_usd=profile.total_value_usd,
            win_rate=profile.win_rate,
            timestamp=profile.timestamp.isoformat()
        )
    
    except Exception as e:
        logger.error(f"Smart money classification error for {request.address}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.get("/signals", response_model=List[TradingSignalResponse])
async def get_trading_signals(
    chain: str = Query("ethereum", description="Blockchain"),
    min_confidence: float = Query(0.7, description="Min confidence (0-1)"),
    limit: int = Query(20, description="Max signals"),
    current_user = Depends(get_current_user),
    _plan_check = Depends(require_plan('plus'))
) -> List[TradingSignalResponse]:
    """
    Get Copy-Trading Signals from Smart Money
    
    **Required Plan:** Plus+
    
    Returns recent moves from Top Traders with high confidence.
    """
    # Would query database for recent signals
    return []


@router.get("/leaderboard", response_model=List[dict])
async def get_leaderboard(
    classification: Optional[str] = Query(None, description="Filter by type"),
    chain: Optional[str] = Query(None, description="Filter by chain"),
    limit: int = Query(50, description="Top N"),
    current_user = Depends(get_current_user),
    _plan_check = Depends(require_plan('pro'))
):
    """
    Get Smart Money Leaderboard
    
    **Required Plan:** Pro+
    
    Returns ranked list of:
    - Top Traders by Win Rate
    - Whales by Holdings
    - Most Profitable MEV Bots
    """
    # Would query database for leaderboard
    return []


@router.get("/portfolio/{address}", response_model=dict)
async def get_portfolio(
    address: str,
    chain: str = Query("ethereum", description="Blockchain"),
    current_user = Depends(get_current_user),
    _plan_check = Depends(require_plan('pro'))
):
    """
    Get Smart Money Portfolio Analysis
    
    **Required Plan:** Pro+
    
    Shows:
    - Token holdings
    - Recent trades
    - PnL history
    - Position sizes
    """
    # Would fetch portfolio data
    return {
        "address": address,
        "chain": chain,
        "tokens": [],
        "total_value_usd": 0,
        "pnl_30d": 0
    }
