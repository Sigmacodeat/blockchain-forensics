"""
Privacy Demixing API Endpoints
==============================

**Endpoints:**
- POST /api/v1/demixing/tornado-cash - 1-Click Tornado Cash Demixing
- POST /api/v1/demixing/detect-mixer - Detect Mixer Usage
- GET /api/v1/demixing/supported-mixers - List Supported Mixers
- POST /api/v1/demixing/privacy-coin - Privacy Coin Tracing (limited)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.auth.dependencies import require_plan
from app.db.neo4j_client import get_neo4j
from app.db.postgres import get_postgres
from app.tracing.privacy_demixing import PrivacyDemixer, PrivacyCoinTracer
from app.services.case_service import log_case_action

import logging

router = APIRouter(prefix="/demixing", tags=["Privacy Demixing"])
logger = logging.getLogger(__name__)


# ===== Request Models =====

class TornadoCashDemixRequest(BaseModel):
    """Request for Tornado Cash demixing"""
    address: str = Field(..., description="Wallet address to demix")
    chain: str = Field("ethereum", description="Blockchain (ethereum/bsc/polygon)")
    max_hops: int = Field(3, ge=1, le=10, description="Max hops after withdrawal")
    time_window_hours: int = Field(168, ge=1, le=720, description="Time window in hours (default: 1 week)")
    case_id: Optional[str] = Field(None, description="Link to existing case")


class MixerDetectionRequest(BaseModel):
    """Request for mixer usage detection"""
    address: str = Field(..., description="Wallet address to check")
    chain: str = Field("ethereum", description="Blockchain")
    case_id: Optional[str] = None


class PrivacyCoinTraceRequest(BaseModel):
    """Request for privacy coin tracing"""
    address: str = Field(..., description="Address/TX to trace")
    coin: str = Field(..., description="Privacy coin (zcash/monero)")
    transaction_type: Optional[str] = Field("transparent", description="Zcash: transparent/shielded/mixed")


class CoinJoinDemixRequest(BaseModel):
    """Request für CoinJoin-Demixing (Bitcoin)"""
    address: str = Field(..., description="Bitcoin-Adresse")
    mixer_type: str = Field("auto", description="'auto', 'wasabi', 'samourai', 'joinmarket'")
    case_id: Optional[str] = Field(None, description="Optional: Case-ID für Logging")


# ===== Response Models =====

class TornadoCashDemixResponse(BaseModel):
    """Response from Tornado Cash demixing"""
    deposits: List[Dict[str, Any]]
    likely_withdrawals: List[Dict[str, Any]]
    probability_scores: Dict[str, float]
    demixing_path: List[Dict[str, Any]]
    confidence: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MixerDetectionResponse(BaseModel):
    """Response from mixer detection"""
    has_mixer_activity: bool
    mixers_used: List[str]
    total_deposits: int
    total_withdrawals: int
    risk_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== Endpoints =====

@router.post("/tornado-cash", response_model=TornadoCashDemixResponse)
async def demix_tornado_cash(
    request: TornadoCashDemixRequest,
    current_user: dict = Depends(require_plan("pro")),  # Pro+ Feature
    neo4j=Depends(get_neo4j),
    postgres=Depends(get_postgres)
):
    """
    **1-Click Tornado Cash Demixing**
    
    Findet wahrscheinliche Withdrawal-Adressen für Tornado Cash Deposits.
    
    **Algorithmus:**
    1. Findet alle Deposits von der Adresse
    2. Korreliert mit Withdrawals über Time-Window
    3. Berechnet Wahrscheinlichkeits-Scores
    4. Traced Post-Mixer-Pfade
    
    **Requires:** Pro Plan oder höher
    
    **Use Case:** 
    - Geldwäsche-Investigations
    - Ransomware-Tracing
    - Sanktions-Compliance
    """
    try:
        logger.info(f"Tornado Cash demixing for {request.address} by {current_user.get('email')}")
        
        # Initialize demixer
        demixer = PrivacyDemixer(neo4j_client=neo4j, postgres_client=postgres)
        
        # Run demixing
        result = await demixer.demix_tornado_cash(
            address=request.address,
            chain=request.chain,
            max_hops=request.max_hops,
            time_window_hours=request.time_window_hours
        )
        
        # Log to case if provided
        if request.case_id:
            await log_case_action(
                case_id=request.case_id,
                action="tornado_demixing",
                data={
                    "address": request.address,
                    "chain": request.chain,
                    "deposits_found": len(result['deposits']),
                    "withdrawals_found": len(result['likely_withdrawals']),
                    "confidence": result['confidence']
                },
                user_id=current_user.get("id")
            )
        
        return TornadoCashDemixResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in Tornado Cash demixing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coinjoin")
async def demix_coinjoin(
    request: CoinJoinDemixRequest,
    current_user: dict = Depends(require_plan("pro")),  # Pro+ Feature
    neo4j=Depends(get_neo4j),
):
    """
    CoinJoin-Demixing (Bitcoin) basierend auf Equal-Output-Heuristik und Denomination-Hints.

    - mixer_type: 'auto' | 'wasabi' | 'samourai' | 'joinmarket'
    - nutzt Neo4j UTXO-Graph wenn verfügbar
    """
    try:
        demixer = PrivacyDemixer(neo4j_client=neo4j)
        result = await demixer.demix_coinjoin(
            address=request.address,
            mixer_type=request.mixer_type
        )

        # Optional: Case-Logging
        if request.case_id:
            try:
                await log_case_action(
                    case_id=request.case_id,
                    action="coinjoin_demixing",
                    data={
                        "address": request.address,
                        "coinjoin_count": result.get("coinjoin_count", 0),
                        "confidence": result.get("confidence", 0.0),
                        "mixer_type": request.mixer_type,
                    },
                    user_id=current_user.get("id")
                )
            except Exception:
                pass

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in CoinJoin demixing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-mixer", response_model=MixerDetectionResponse)
async def detect_mixer_usage(
    request: MixerDetectionRequest,
    current_user: dict = Depends(require_plan("community")),  # Community+ Feature
    neo4j=Depends(get_neo4j),
    postgres=Depends(get_postgres)
):
    """
    **Detect Mixer Usage**
    
    Prüft, ob eine Adresse Mixer verwendet hat (Tornado Cash, Cyclone, etc.).
    
    **Returns:**
    - Liste der verwendeten Mixer
    - Anzahl Deposits/Withdrawals
    - Risk Score basierend auf Mixer-Aktivität
    
    **Requires:** Community Plan oder höher
    """
    try:
        logger.info(f"Mixer detection for {request.address} by {current_user.get('email')}")
        
        demixer = PrivacyDemixer(neo4j_client=neo4j, postgres_client=postgres)
        
        result = await demixer.detect_mixer_usage(
            address=request.address,
            chain=request.chain
        )
        
        # Log to case
        if request.case_id:
            await log_case_action(
                case_id=request.case_id,
                action="mixer_detection",
                data={
                    "address": request.address,
                    "has_mixer_activity": result['has_mixer_activity'],
                    "mixers_used": result['mixers_used'],
                    "risk_score": result['risk_score']
                },
                user_id=current_user.get("id")
            )
        
        return MixerDetectionResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in mixer detection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-mixers")
async def get_supported_mixers(
    current_user: dict = Depends(require_plan("community"))
):
    """
    **List Supported Mixers**
    
    Gibt Liste aller unterstützten Mixer zurück.
    
    **Categories:**
    - ZK Mixers (Tornado Cash, Cyclone, Railgun)
    - CoinJoin (Wasabi, Samourai)
    - Centralized (ChipMixer, Blender.io)
    """
    mixers = {
        "zk_mixers": [
            {
                "name": "Tornado Cash",
                "chains": ["ethereum", "bsc", "polygon"],
                "status": "sanctioned",
                "demixing_support": "full",
                "features": ["1-click-demixing", "time-window-analysis", "graph-matching"]
            },
            {
                "name": "Cyclone Protocol",
                "chains": ["ethereum", "bsc"],
                "status": "active",
                "demixing_support": "full",
                "features": ["1-click-demixing", "cross-chain-tracking"]
            },
            {
                "name": "Railgun",
                "chains": ["ethereum"],
                "status": "active",
                "demixing_support": "partial",
                "features": ["relayer-detection", "shielded-analysis"]
            }
        ],
        "coinjoin": [
            {
                "name": "Wasabi Wallet",
                "chains": ["bitcoin"],
                "status": "active",
                "demixing_support": "planned",
                "features": ["equal-output-detection", "change-tracking"]
            },
            {
                "name": "Samourai Wallet",
                "chains": ["bitcoin"],
                "status": "active",
                "demixing_support": "planned",
                "features": ["whirlpool-analysis", "utxo-clustering"]
            }
        ],
        "centralized": [
            {
                "name": "ChipMixer",
                "chains": ["bitcoin"],
                "status": "shutdown",
                "demixing_support": "partial",
                "features": ["chip-reassembly", "peeling-detection"]
            },
            {
                "name": "Blender.io",
                "chains": ["bitcoin"],
                "status": "shutdown",
                "demixing_support": "partial",
                "features": ["centralized-correlation"]
            }
        ],
        "privacy_coins": [
            {
                "name": "Zcash",
                "type": "privacy_coin",
                "status": "active",
                "tracing_support": "limited",
                "notes": "Only transparent transactions traceable"
            },
            {
                "name": "Monero",
                "type": "privacy_coin",
                "status": "active",
                "tracing_support": "minimal",
                "notes": "Ring signatures make tracing extremely difficult"
            }
        ]
    }
    
    return {
        "mixers": mixers,
        "total_supported": sum(len(v) for v in mixers.values()),
        "message": "Privacy demixing capabilities - best-in-class"
    }


@router.post("/privacy-coin")
async def trace_privacy_coin(
    request: PrivacyCoinTraceRequest,
    current_user: dict = Depends(require_plan("pro"))  # Pro+ Feature
):
    """
    **Privacy Coin Tracing (Limited)**
    
    Versucht Privacy Coins zu tracen (Zcash, Monero).
    
    **WICHTIG:**
    - Zcash: Nur transparent transactions tracebar
    - Monero: Extrem limitiert (nur Metadata)
    
    **Realistic Expectations:**
    Privacy Coins erfüllen ihren Zweck - vollständiges Tracing ist unmöglich.
    Nur exchange correlations und metadata analysis möglich.
    """
    try:
        logger.info(f"Privacy coin tracing for {request.coin} by {current_user.get('email')}")
        
        tracer = PrivacyCoinTracer()
        
        if request.coin.lower() == "zcash":
            result = await tracer.trace_zcash(
                address=request.address,
                transaction_type=request.transaction_type
            )
        elif request.coin.lower() == "monero":
            result = await tracer.trace_monero(address=request.address)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported privacy coin: {request.coin}"
            )
        
        return {
            "result": result,
            "disclaimer": "Privacy coin tracing is inherently limited due to strong cryptographic privacy",
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in privacy coin tracing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_demixing_stats(
    current_user: dict = Depends(require_plan("pro")),
    postgres=Depends(get_postgres)
):
    """
    **Demixing Statistics**
    
    Statistiken über durchgeführte Demixing-Operationen.
    
    **Metrics:**
    - Total demixing operations
    - Success rate
    - Average confidence scores
    - Most used mixers
    """
    try:
        # Query actual stats from database
        from app.db.postgres import postgres_client
        
        # Get demixing operation counts
        stats_query = """
            SELECT 
                COUNT(*) as total,
                AVG(CASE WHEN confidence > 0.5 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(confidence) as avg_confidence
            FROM trace_results
            WHERE mixer_detected = true
        """
        
        stats = await postgres_client.fetchrow(stats_query) if postgres_client else None
        
        # Get most used mixers (from labels or traces)
        mixer_query = """
            SELECT mixer_type, COUNT(*) as count
            FROM trace_results
            WHERE mixer_type IS NOT NULL
            GROUP BY mixer_type
            ORDER BY count DESC
            LIMIT 5
        """
        mixers_raw = await postgres_client.fetch(mixer_query) if postgres_client else []
        
        most_used_mixers = [
            {"mixer": row["mixer_type"], "count": row["count"]} 
            for row in mixers_raw
        ] if mixers_raw else []
        
        return {
            "total_operations": int(stats["total"]) if stats and stats["total"] else 0,
            "success_rate": float(stats["success_rate"]) if stats and stats["success_rate"] else 0.0,
            "avg_confidence": float(stats["avg_confidence"]) if stats and stats["avg_confidence"] else 0.0,
            "most_used_mixers": most_used_mixers,
            "message": "Live statistics from database"
        }
    except Exception as e:
        logger.warning(f"Stats query failed, returning defaults: {e}")
        return {
            "total_operations": 0,
            "success_rate": 0.0,
            "avg_confidence": 0.0,
            "most_used_mixers": [],
            "message": "Statistics unavailable (database query failed)"
        }
