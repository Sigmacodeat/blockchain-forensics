"""Smart Contract Deep Analysis API Endpoints"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel, Field

from app.contracts.service import contracts_service
from app.contracts.function_signature_matcher import function_signature_matcher
from app.contracts.event_signature_matcher import event_signature_matcher
from app.contracts.history_tracker import history_tracker
from app.contracts.report_generator import report_generator
from app.contracts.webhook_manager import webhook_manager, WebhookConfig
from app.auth.dependencies import require_plan
from app.analytics.smart_contract_analyzer import smart_contract_analyzer
from fastapi.responses import Response

router = APIRouter(tags=["Contracts"]) 


class ContractAnalysisRequest(BaseModel):
    """Request model for contract analysis"""
    address: str = Field(..., description="Contract address to analyze")
    chain: str = Field(default="ethereum", description="Blockchain network")
    include_bytecode: bool = Field(default=False, description="Include full bytecode in response")
    resolve_proxy: bool = Field(default=True, description="Resolve and analyze proxy implementation (EIP-1967/EIP-1167)")


class FunctionLookupRequest(BaseModel):
    """Request for function signature lookup"""
    selector: str = Field(..., description="4-byte function selector (0x12345678)")


class BytecodeAnalysisRequest(BaseModel):
    """Request model for direct bytecode analysis"""
    address: str = Field(..., description="Contract address (for reporting)")
    chain: str = Field(default="ethereum", description="Blockchain network")
    bytecode: str = Field(..., description="Contract bytecode (0x prefixed hex)")


class EventLookupRequest(BaseModel):
    """Request for event signature lookup"""
    topic0: str = Field(..., description="32-byte event signature hash (0x...)")


class EventBatchLookupRequest(BaseModel):
    """Request for batch event lookup"""
    topics: List[str] = Field(..., description="List of event topic0 hashes")


class BatchAnalysisRequest(BaseModel):
    """Request for batch contract analysis"""
    contracts: List[ContractAnalysisRequest] = Field(..., description="List of contracts to analyze")
    resolve_proxy: bool = Field(default=True, description="Resolve proxies for all contracts")


class ContractComparisonRequest(BaseModel):
    """Request for contract comparison"""
    address1: str = Field(..., description="First contract address")
    address2: str = Field(..., description="Second contract address")
    chain: str = Field(default="ethereum", description="Blockchain network")
    resolve_proxy: bool = Field(default=True, description="Resolve proxies before comparison")


@router.post("/analyze", dependencies=[Depends(require_plan("pro"))])
async def analyze_contract(
    request: ContractAnalysisRequest,
):
    """
    Deep Contract Analysis
    
    Performs comprehensive analysis including:
    - Bytecode pattern analysis
    - Vulnerability detection
    - Exploit pattern recognition
    - Function signature matching
    - Interface detection (ERC20, ERC721, etc.)
    
    **Requires:** Pro plan or higher
    """
    try:
        result = await contracts_service.analyze_async(
            address=request.address,
            chain=request.chain,
            resolve_proxy=request.resolve_proxy,
        )
        
        if "error" in result and not result.get("findings"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analyze/{chain}/{address}", dependencies=[Depends(require_plan("pro"))])
async def analyze_contract_get(
    address: str,
    chain: str = "ethereum",
    include_bytecode: bool = Query(default=False),
    resolve_proxy: bool = Query(default=True),
):
    """
    Deep Contract Analysis (GET version)
    
    Same as POST /analyze but via GET for easy browser access
    """
    request = ContractAnalysisRequest(
        address=address,
        chain=chain,
        include_bytecode=include_bytecode,
        resolve_proxy=resolve_proxy,
    )
    return await analyze_contract(request)


@router.post("/analyze/bytecode", dependencies=[Depends(require_plan("pro"))])
async def analyze_contract_bytecode(request: BytecodeAnalysisRequest):
    """
    Deep Contract Analysis (direct bytecode)

    Nutzt den internen SmartContractAnalyzer zur Analyse ohne RPC/Fetched-Bytecode.

    Liefert u.a.:
    - Vulnerabilities (Heuristiken)
    - Function Selectors (PUSH4)
    - Similarity Key
    - Proxy/Honeypot-Heuristiken

    **Requires:** Pro plan or higher
    """
    try:
        analysis = await smart_contract_analyzer.analyze_contract(request.address, request.bytecode)
        return analysis.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bytecode analysis failed: {str(e)}")


@router.post("/function/lookup", dependencies=[Depends(require_plan("community"))])
async def lookup_function_signature(request: FunctionLookupRequest):
    """
    Resolve function selector to signature
    
    Uses 4byte.directory + local database to identify function signatures
    
    **Example:**
    ```
    POST /api/v1/contracts/function/lookup
    {"selector": "0xa9059cbb"}
    
    Response:
    {
      "selector": "0xa9059cbb",
      "signature": "transfer(address,uint256)",
      "name": "transfer",
      "params": ["address", "uint256"],
      "source": "local",
      "confidence": 0.95
    }
    ```
    
    **Requires:** Community plan or higher
    """
    try:
        result = await function_signature_matcher.resolve_selector_async(request.selector)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No signature found for selector {request.selector}"
            )
        
        return {
            "selector": result.selector,
            "signature": result.signature,
            "name": result.name,
            "params": result.params,
            "source": result.source,
            "confidence": result.confidence,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/function/{selector}", dependencies=[Depends(require_plan("community"))])
async def lookup_function_signature_get(selector: str):
    """
    Resolve function selector to signature (GET version)
    
    **Example:** GET /api/v1/contracts/function/0xa9059cbb
    """
    request = FunctionLookupRequest(selector=selector)
    return await lookup_function_signature(request)


@router.post("/event/lookup", dependencies=[Depends(require_plan("community"))])
async def lookup_event(request: EventLookupRequest):
    """
    Event Signature Lookup
    
    Resolves event topic0 hash to signature.
    Uses 4byte.directory events API + local database.
    
    **Requires:** Community plan or higher
    """
    try:
        event = event_signature_matcher.resolve_event(request.topic0)
        
        if not event:
            raise HTTPException(
                status_code=404,
                detail=f"Event signature not found for topic0: {request.topic0}"
            )
        
        return {
            "topic0": event.topic0,
            "signature": event.signature,
            "name": event.name,
            "params": event.params,
            "source": event.source,
            "confidence": event.confidence,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{topic0}", dependencies=[Depends(require_plan("community"))])
async def lookup_event_get(topic0: str):
    """
    Event Signature Lookup (GET version)
    
    Same as POST /event/lookup but via GET for easy browser access.
    """
    request = EventLookupRequest(topic0=topic0)
    return await lookup_event(request)


@router.post("/events/batch", dependencies=[Depends(require_plan("pro"))])
async def lookup_events_batch(request: EventBatchLookupRequest):
    """
    Batch Event Lookup
    
    Resolve multiple event signatures at once.
    
    **Requires:** Pro plan or higher
    """
    try:
        results = []
        for topic0 in request.topics:
            event = event_signature_matcher.resolve_event(topic0)
            if event:
                results.append({
                    "topic0": event.topic0,
                    "signature": event.signature,
                    "name": event.name,
                    "params": event.params,
                    "source": event.source,
                    "confidence": event.confidence,
                })
            else:
                results.append({
                    "topic0": topic0,
                    "error": "Not found"
                })
        
        return {
            "total": len(request.topics),
            "found": sum(1 for r in results if "error" not in r),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/standards/{chain}/{address}", dependencies=[Depends(require_plan("pro"))])
async def detect_contract_standards(address: str, chain: str = "ethereum"):
    """
    Detect ERC Standards
    
    Identifies which ERC standards (ERC20, ERC721, ERC1155, etc.) a contract implements
    
    **Requires:** Pro plan or higher
    """
    try:
        # Quick analysis focused on interface detection
        result = await contracts_service.analyze_async(address, chain)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "address": address,
            "chain": chain,
            "standards": result["interface"]["standards"],
            "is_proxy": result["interface"]["is_proxy"],
            "functions_count": result["interface"]["functions_count"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/batch", dependencies=[Depends(require_plan("pro"))])
async def analyze_contracts_batch(request: BatchAnalysisRequest):
    """
    Batch Contract Analysis
    
    Analyze multiple contracts in parallel.
    Significantly faster than sequential requests.
    
    **Requires:** Pro plan or higher
    """
    import asyncio
    
    try:
        # Analyze all contracts in parallel
        tasks = [
            contracts_service.analyze_async(
                address=contract.address,
                chain=contract.chain,
                resolve_proxy=request.resolve_proxy
            )
            for contract in request.contracts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        analyzed = []
        errors = []
        
        for i, result in enumerate(results):
            contract = request.contracts[i]
            if isinstance(result, Exception):
                errors.append({
                    "address": contract.address,
                    "chain": contract.chain,
                    "error": str(result)
                })
            else:
                analyzed.append(result)
        
        return {
            "total": len(request.contracts),
            "analyzed": len(analyzed),
            "errors": len(errors),
            "results": analyzed,
            "failed": errors if errors else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", dependencies=[Depends(require_plan("pro"))])
async def compare_contracts(request: ContractComparisonRequest):
    """
    Contract Comparison
    
    Compare two contracts side-by-side:
    - Bytecode similarity
    - Diff of functions/events
    - Risk score comparison
    - Vulnerability differences
    
    **Requires:** Pro plan or higher
    """
    import asyncio
    
    try:
        # Analyze both contracts in parallel
        result1, result2 = await asyncio.gather(
            contracts_service.analyze_async(
                address=request.address1,
                chain=request.chain,
                resolve_proxy=request.resolve_proxy
            ),
            contracts_service.analyze_async(
                address=request.address2,
                chain=request.chain,
                resolve_proxy=request.resolve_proxy
            )
        )
        
        # Calculate bytecode similarity
        
        bytecode1 = result1.get("statistics", {}).get("bytecode_hash", "")
        bytecode2 = result2.get("statistics", {}).get("bytecode_hash", "")
        
        # Simple similarity: exact match or different
        exact_match = bytecode1 == bytecode2 if bytecode1 and bytecode2 else False
        
        # Function differences
        funcs1 = set(result1.get("interface", {}).get("top_functions", []))
        funcs2 = set(result2.get("interface", {}).get("top_functions", []))
        
        common_functions = funcs1 & funcs2
        only_in_1 = funcs1 - funcs2
        only_in_2 = funcs2 - funcs1
        
        # Event differences
        events1 = set(result1.get("interface", {}).get("events", []))
        events2 = set(result2.get("interface", {}).get("events", []))
        
        common_events = events1 & events2
        only_in_1_events = events1 - events2
        only_in_2_events = events2 - events1
        
        # Risk comparison
        risk1 = result1.get("score", 0.0)
        risk2 = result2.get("score", 0.0)
        risk_delta = abs(risk1 - risk2)
        
        # Vulnerability comparison
        vulns1 = result1.get("vulnerabilities", {}).get("total", 0)
        vulns2 = result2.get("vulnerabilities", {}).get("total", 0)
        
        return {
            "contract1": {
                "address": request.address1,
                "analysis": result1
            },
            "contract2": {
                "address": request.address2,
                "analysis": result2
            },
            "comparison": {
                "bytecode": {
                    "exact_match": exact_match,
                    "hash1": bytecode1,
                    "hash2": bytecode2,
                },
                "functions": {
                    "common": list(common_functions),
                    "only_in_contract1": list(only_in_1),
                    "only_in_contract2": list(only_in_2),
                    "similarity_ratio": len(common_functions) / max(len(funcs1), len(funcs2), 1),
                },
                "events": {
                    "common": list(common_events),
                    "only_in_contract1": list(only_in_1_events),
                    "only_in_contract2": list(only_in_2_events),
                },
                "risk": {
                    "contract1_score": risk1,
                    "contract2_score": risk2,
                    "delta": risk_delta,
                    "higher_risk": request.address1 if risk1 > risk2 else request.address2,
                },
                "vulnerabilities": {
                    "contract1_total": vulns1,
                    "contract2_total": vulns2,
                    "delta": abs(vulns1 - vulns2),
                },
            },
            "summary": _generate_comparison_summary(
                exact_match, 
                len(common_functions), 
                len(funcs1), 
                len(funcs2),
                risk_delta,
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_comparison_summary(
    exact_match: bool,
    common_funcs: int,
    funcs1: int,
    funcs2: int,
    risk_delta: float
) -> str:
    """Generate human-readable comparison summary"""
    lines = []
    
    if exact_match:
        lines.append("✅ Identical bytecode - likely same contract or exact clone")
    else:
        similarity = common_funcs / max(funcs1, funcs2, 1)
        if similarity > 0.9:
            lines.append("⚠️ Very similar contracts (>90% function overlap)")
        elif similarity > 0.7:
            lines.append("⚠️ Similar contracts (>70% function overlap)")
        elif similarity > 0.5:
            lines.append("ℹ️ Moderately similar contracts")
        else:
            lines.append("ℹ️ Different contracts with some overlap")
    
    if risk_delta > 0.3:
        lines.append(f"⚠️ Significant risk difference ({risk_delta:.2f})")
    elif risk_delta > 0.1:
        lines.append(f"ℹ️ Moderate risk difference ({risk_delta:.2f})")
    else:
        lines.append("✅ Similar risk profile")
    
    return "\n".join(lines)


@router.get("/history/{chain}/{address}", dependencies=[Depends(require_plan("pro"))])
async def get_contract_history(address: str, chain: str, days: int = Query(default=30, ge=1, le=365)):
    """
    Contract History & Timeline
    
    Get historical analysis data including:
    - Proxy upgrades
    - Risk score trends
    - Significant events
    
    **Requires:** Pro plan or higher
    """
    try:
        timeline = history_tracker.get_timeline_summary(address, chain, days)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{chain}/{address}/risk-trend", dependencies=[Depends(require_plan("pro"))])
async def get_risk_trend(address: str, chain: str, days: int = Query(default=30, ge=1, le=365)):
    """
    Risk Score Trend Analysis
    
    Analyze how risk score has evolved over time.
    
    **Requires:** Pro plan or higher
    """
    try:
        trend = history_tracker.get_risk_trend(address, chain, days)
        return trend
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{chain}/{address}/json", dependencies=[Depends(require_plan("pro"))])
async def export_json_report(address: str, chain: str):
    """
    Export Analysis as JSON
    
    Download complete analysis report in JSON format.
    
    **Requires:** Pro plan or higher
    """
    try:
        # Get latest analysis
        analysis = await contracts_service.analyze_async(address, chain)
        
        # Generate JSON report
        json_report = report_generator.generate_json_report(analysis)
        
        return Response(
            content=json_report,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=contract-analysis-{address[:10]}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{chain}/{address}/markdown", dependencies=[Depends(require_plan("pro"))])
async def export_markdown_report(address: str, chain: str):
    """
    Export Analysis as Markdown
    
    Download analysis report in Markdown format.
    
    **Requires:** Pro plan or higher
    """
    try:
        analysis = await contracts_service.analyze_async(address, chain)
        md_report = report_generator.generate_markdown_report(analysis)
        
        return Response(
            content=md_report,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=contract-analysis-{address[:10]}.md"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{chain}/{address}/pdf", dependencies=[Depends(require_plan("business"))])
async def export_pdf_report(address: str, chain: str):
    """
    Export Analysis as PDF
    
    Download professional audit report in PDF format.
    
    **Requires:** Business plan or higher
    """
    try:
        analysis = await contracts_service.analyze_async(address, chain)
        pdf_report = report_generator.generate_pdf_report(analysis)
        
        return Response(
            content=pdf_report,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=contract-audit-{address[:10]}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class WebhookRegistrationRequest(BaseModel):
    """Request to register webhook"""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Optional webhook secret")


@router.post("/webhooks/{chain}/{address}/register", dependencies=[Depends(require_plan("business"))])
async def register_webhook(address: str, chain: str, request: WebhookRegistrationRequest):
    """
    Register Webhook
    
    Subscribe to contract events:
    - critical_finding
    - high_risk
    - proxy_upgrade
    - risk_spike
    
    **Requires:** Business plan or higher
    """
    try:
        config = WebhookConfig(
            url=request.url,
            events=request.events,
            secret=request.secret,
            enabled=True
        )
        
        webhook_manager.register_webhook(address, chain, config)
        
        return {
            "status": "registered",
            "address": address,
            "chain": chain,
            "webhook_url": request.url,
            "events": request.events,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/webhooks/{chain}/{address}/unregister", dependencies=[Depends(require_plan("business"))])
async def unregister_webhook(address: str, chain: str, url: str = Query(..., description="Webhook URL to remove")):
    """
    Unregister Webhook
    
    Remove webhook subscription.
    
    **Requires:** Business plan or higher
    """
    try:
        webhook_manager.unregister_webhook(address, chain, url)
        return {"status": "unregistered", "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    **Public** - No authentication required
    """
    return {
        "status": "healthy",
        "service": "contract_analysis",
        "version": "1.0.0",
        "features": [
            "deep_analysis",
            "vulnerability_detection",
            "proxy_resolution",
            "batch_analysis",
            "contract_comparison",
            "historical_analysis",
            "pdf_export",
            "webhooks",
        ]
    }
