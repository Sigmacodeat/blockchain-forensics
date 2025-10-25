"""Smart Contract Deep Analysis Service"""

from typing import Dict, List, Optional
import httpx
import asyncio
import os
from app.contracts.bytecode_analyzer import bytecode_analyzer, BytecodeAnalysis
from app.contracts.vulnerability_detector import vulnerability_detector, VulnerabilityReport
from app.contracts.exploit_detector import exploit_detector, ExploitDetection
from app.contracts.function_signature_matcher import function_signature_matcher, ContractInterface
from app.contracts.event_signature_matcher import event_signature_matcher
from app.contracts.models import ContractAnalysis, ContractRiskIssue
import logging

logger = logging.getLogger(__name__)


class ContractsService:
    """
    Smart Contract Deep Analysis Service
    Orchestriert alle Analyse-Komponenten:
    - Bytecode Analysis (ML-based)
    - Vulnerability Detection
    - Exploit Pattern Recognition
    - Function Signature Matching
    """
    
    def __init__(self):
        self.bytecode_analyzer = bytecode_analyzer
        self.vulnerability_detector = vulnerability_detector
        self.exploit_detector = exploit_detector
        self.function_matcher = function_signature_matcher
        self.event_matcher = event_signature_matcher
        
        # RPC endpoints for fetching bytecode
        self.rpc_endpoints = {
            "ethereum": "https://eth.llamarpc.com",
            "polygon": "https://polygon.llamarpc.com",
            "bsc": "https://bsc.llamarpc.com",
            "arbitrum": "https://arbitrum.llamarpc.com",
            "optimism": "https://optimism.llamarpc.com",
            "base": "https://base.llamarpc.com",
        }
        # Simple in-memory bytecode cache
        self._bytecode_cache: Dict[str, str] = {}
        self.etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
    
    async def analyze_async(self, address: str, chain: str = "ethereum", *, resolve_proxy: bool = True) -> Dict:
        """
        Async version für bessere Performance
        """
        try:
            # 1. Fetch bytecode from chain
            bytecode = await self._fetch_bytecode_async(address, chain)
            if not bytecode or bytecode == "0x":
                return {
                    "address": address,
                    "chain": chain,
                    "error": "No bytecode found - not a contract or contract destroyed",
                    "score": 0.0,
                    "findings": [],
                }
            # 1b. Proxy-Resolution (mehrstufig bis Tiefe 3)
            impl_addr: Optional[str] = None
            is_proxy = False
            proxy_type: Optional[str] = None
            proxy_source: Optional[str] = None
            bytecode_to_analyze = bytecode
            implementation_hint: Optional[str] = None
            proxy_chain: List[str] = []

            if resolve_proxy:
                impl_addr, proxy_type, proxy_source, proxy_chain = await self._resolve_proxy_chain(address, chain, bytecode)
                if impl_addr:
                    try:
                        impl_code = await self._fetch_bytecode_async(impl_addr, chain)
                        if impl_code and impl_code != "0x":
                            is_proxy = True
                            bytecode_to_analyze = impl_code
                            implementation_hint = impl_addr
                    except Exception:
                        pass

            # 2. Run all analyses (ggf. mit Implementation-Bytecode)
            result = await self._run_full_analysis_async(
                address,
                chain,
                bytecode_to_analyze,
                is_proxy=is_proxy,
                implementation_hint=implementation_hint,
                proxy_type=proxy_type,
                proxy_source=proxy_source,
            )

            # 3. Optional: ABI-Fetch (Etherscan) – nur Ethereum und wenn Key gesetzt
            try:
                if self.etherscan_api_key and chain.lower() == "ethereum":
                    abi, verified = await self._fetch_etherscan_abi(implementation_hint or address)
                    if abi:
                        result.setdefault("metadata", {})["abi_verified"] = verified
                        if verified:
                            # ABI ist groß – nur Kennzeichen + Funktionsanzahl speichern
                            result["metadata"]["abi_functions_count"] = sum(1 for e in abi if e.get("type") == "function")
                        else:
                            result["metadata"]["abi_present"] = True
            except Exception:
                pass

            # 4. Proxy-Chain ins Ergebnis aufnehmen
            if proxy_chain:
                result.setdefault("proxy", {})["chain"] = proxy_chain
            return result
            
        except Exception as e:
            logger.error(f"Contract analysis failed for {address}: {e}")
            return {
                "address": address,
                "chain": chain,
                "error": str(e),
                "score": 0.0,
                "findings": [],
            }
    
    def analyze(self, address: str, chain: str = "ethereum") -> Dict:
        """
        Synchronous wrapper für API compatibility
        """
        try:
            # Use asyncio.run for sync context
            return asyncio.run(self.analyze_async(address, chain))
        except Exception as e:
            logger.error(f"Contract analysis failed: {e}")
            return {
                "address": address,
                "chain": chain,
                "error": str(e),
                "score": 0.0,
                "findings": [],
            }
    
    async def _fetch_bytecode_async(self, address: str, chain: str) -> str:
        """Fetches contract bytecode from RPC (mit Retries & Backoff)"""
        rpc_url = self.rpc_endpoints.get(chain.lower())
        if not rpc_url:
            raise ValueError(f"Unsupported chain: {chain}")

        cache_key = f"{chain.lower()}:{address.lower()}"
        if cache_key in self._bytecode_cache:
            return self._bytecode_cache[cache_key]

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [address, "latest"],
            "id": 1,
        }

        data = await self._rpc_post(rpc_url, payload, retries=3, timeout=10.0)
        if "result" in data:
            code = data["result"]
            self._bytecode_cache[cache_key] = code
            return code
        raise Exception(f"RPC error: {data.get('error', 'Unknown error')}")

    async def _get_storage_at_async(self, address: str, slot: str, chain: str) -> str:
        """eth_getStorageAt helper (hex string)"""
        rpc_url = self.rpc_endpoints.get(chain.lower())
        if not rpc_url:
            raise ValueError(f"Unsupported chain: {chain}")

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getStorageAt",
            "params": [address, slot, "latest"],
            "id": 1,
        }
        data = await self._rpc_post(rpc_url, payload, retries=3, timeout=10.0)
        return data.get("result", "0x")

    async def _resolve_eip1967_implementation(self, address: str, chain: str) -> Optional[str]:
        """
        Versucht die Implementation-Adresse gemäß EIP-1967 zu ermitteln.
        Slot: keccak256("eip1967.proxy.implementation") - 1
        = 0x360894A13BA1A3210667C828492DB98DCA3E2076CC3735A920A3CA505D382BBC
        """
        try:
            slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
            raw = await self._get_storage_at_async(address, slot, chain)
            if not raw or raw == "0x" or len(raw) < 66:
                return None
            # Letzte 20 Bytes als Adresse extrahieren
            impl_hex = "0x" + raw[-40:]
            if impl_hex.lower() == "0x0000000000000000000000000000000000000000":
                return None
            return impl_hex
        except Exception:
            return None

    async def _resolve_proxy_chain(self, address: str, chain: str, bytecode: str, *, max_depth: int = 3) -> (Optional[str], Optional[str], Optional[str], List[str]):
        """Versucht, eine Proxy-Kette aufzudecken (bis max_depth). Gibt finale Implementation + Kette zurück."""
        seen: set[str] = set()
        current_addr = address
        current_code = bytecode
        chain_addrs: List[str] = []
        proxy_type: Optional[str] = None
        proxy_source: Optional[str] = None
        impl_addr: Optional[str] = None

        for _ in range(max_depth):
            if current_addr.lower() in seen:
                break
            seen.add(current_addr.lower())

            # EIP-1967 zuerst (verlässlich)
            impl = await self._resolve_eip1967_implementation(current_addr, chain)
            if not impl:
                # EIP-1167 aus Bytecode ableiten
                impl = self._resolve_eip1167_implementation_from_bytecode(current_code)
                if impl:
                    proxy_type = "eip-1167"
                    proxy_source = "bytecode"
            else:
                proxy_type = "eip-1967"
                proxy_source = "storage"

            if not impl:
                break
            chain_addrs.append(impl)
            impl_addr = impl
            # Lade Code für nächste Runde
            try:
                current_code = await self._fetch_bytecode_async(impl, chain)
                current_addr = impl
            except Exception:
                break

        return impl_addr, proxy_type, proxy_source, chain_addrs

    async def _fetch_etherscan_abi(self, address: str) -> (Optional[List[Dict]], bool):
        """Lädt ABI von Etherscan, wenn API-Key vorhanden. Gibt (abi, verified) zurück."""
        if not self.etherscan_api_key:
            return None, False
        url = "https://api.etherscan.io/api"
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
            "apikey": self.etherscan_api_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10.0)
            data = resp.json()
            if data.get("status") == "1" and data.get("result"):
                import json as _json
                try:
                    abi = _json.loads(data["result"])  # list
                    return abi, True
                except Exception:
                    return None, False
        return None, False

    def _resolve_eip1167_implementation_from_bytecode(self, bytecode: str) -> Optional[str]:
        """
        Ermittelt Implementation aus EIP-1167 Minimal Proxy Bytecode.
        Standardpattern enthält PUSH20 (0x73) gefolgt von 20 Byte Adresse.
        """
        try:
            code = bytecode.lower().replace("0x", "")
            # Suche nach '73' (PUSH20) und extrahiere nächste 20 Bytes
            idx = code.find("73")
            while idx != -1 and idx + 42 <= len(code):
                # Stellen sicher, dass dies wirklich das Minimal-Proxy-Motiv ist: häufig beginnt mit 363d3d373d3d3d363d73
                start_motif = code[max(0, idx-22):idx+2]
                if "363d3d373d3d3d363d73" in start_motif or code.startswith("363d3d373d3d3d363d73", max(0, idx-20)):
                    addr_hex = code[idx+2:idx+42]
                    if len(addr_hex) == 40 and all(c in "0123456789abcdef" for c in addr_hex):
                        if addr_hex != "0"*40:
                            return "0x" + addr_hex
                # Falls weitere Vorkommen
                idx = code.find("73", idx+2)
        except Exception:
            return None
        return None

    async def _rpc_post(self, rpc_url: str, payload: Dict, retries: int = 3, timeout: float = 10.0) -> Dict:
        """HTTP JSON-RPC POST mit Retries und Exponential Backoff"""
        backoff = 0.5
        last_err: Optional[Exception] = None
        async with httpx.AsyncClient() as client:
            for attempt in range(retries):
                try:
                    resp = await client.post(rpc_url, json=payload, timeout=timeout)
                    resp.raise_for_status()
                    data = resp.json()
                    # JSON-RPC Fehler?
                    if data.get("error"):
                        last_err = Exception(str(data["error"]))
                        raise last_err
                    return data
                except Exception as e:
                    last_err = e
                    if attempt < retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    break
        # Wenn alle Versuche scheitern -> Exception
        raise Exception(f"RPC request failed after {retries} attempts: {last_err}")
    
    async def _run_full_analysis_async(
        self,
        address: str,
        chain: str,
        bytecode: str,
        *,
        is_proxy: bool = False,
        implementation_hint: Optional[str] = None,
        proxy_type: Optional[str] = None,
        proxy_source: Optional[str] = None,
    ) -> Dict:
        """Runs all analysis components"""
        
        # 1. Bytecode Analysis
        bytecode_analysis = self.bytecode_analyzer.analyze(bytecode, address)
        opcodes = self.bytecode_analyzer._disassemble(bytecode.replace('0x', ''))
        
        # 2. Vulnerability Detection
        vuln_report = self.vulnerability_detector.detect(bytecode, opcodes)
        
        # 3. Exploit Pattern Recognition
        exploit_detections = self.exploit_detector.detect_exploits(bytecode, opcodes)
        
        # 4. Function & Event Signature Analysis
        selectors = self.function_matcher.extract_selectors_from_bytecode(bytecode)
        interface = self.function_matcher.detect_interface(bytecode, selectors)
        
        # Enrich with real events from standards
        detected_events = []
        for standard in interface.standards:
            if standard in event_signature_matcher.local_db:
                continue
            # Map standard to event topics
            from app.contracts.event_signature_matcher import ERC_EVENT_SIGNATURES
            if standard in ERC_EVENT_SIGNATURES:
                for topic0, sig in ERC_EVENT_SIGNATURES[standard].items():
                    event_sig = event_signature_matcher.resolve_event(topic0)
                    if event_sig:
                        detected_events.append(event_sig.name)
        interface.events = list(set(detected_events)) if detected_events else interface.events
        if is_proxy:
            interface.is_proxy = True
            try:
                # type: ignore[attr-defined]
                interface.implementation_hint = implementation_hint
            except Exception:
                pass
        # UUPS-Heuristik: proxiableUUID() vorhanden -> UUPS
        # Selector von proxiableUUID(): 0x52d1902d
        if (is_proxy or implementation_hint) and any(sel.lower() == "0x52d1902d" for sel in selectors):
            if proxy_type is None:
                proxy_type = "uups"
        
        # 5. Combine all findings
        all_findings = []
        
        # Add bytecode analysis findings
        for finding in bytecode_analysis.findings:
            all_findings.append(ContractRiskIssue(
                id=f"bytecode_{len(all_findings)}",
                address=address,
                kind=finding["type"],
                severity=finding["severity"],
                evidence=finding.get("description", ""),
            ))
        
        # Add vulnerability findings
        for vuln in vuln_report.vulnerabilities:
            all_findings.append(ContractRiskIssue(
                id=f"vuln_{vuln.vuln_type.value}",
                address=address,
                kind=vuln.vuln_type.value,
                severity=vuln.severity.value,
                evidence=f"{vuln.title}: {vuln.description}\nRemediation: {vuln.remediation}",
            ))
        
        # Add exploit detections
        for exploit in exploit_detections:
            all_findings.append(ContractRiskIssue(
                id=f"exploit_{exploit.exploit_name}",
                address=address,
                kind=exploit.category.value,
                severity=exploit.severity,
                evidence=f"{exploit.description}\nIndicators: {', '.join(exploit.indicators)}\nMitigation: {exploit.mitigation}",
            ))
        
        # Upgradeability checks (UUPS/Transparent): presence of upgrade functions without access control
        try:
            upgrade_selectors = {"0x3659cfe6", "0x4f1ef286"}  # upgradeTo, upgradeToAndCall
            access_selectors = {
                "0x8da5cb5b",  # owner()
                "0xf2fde38b",  # transferOwnership(address)
                "0x91d14854",  # hasRole(bytes32,address)
                "0x2f2ff15d",  # grantRole(bytes32,address)
                "0xd547741f",  # revokeRole(bytes32,address)
            }
            sel_lower = {s.lower() for s in selectors}
            has_upgrade = any(s in sel_lower for s in upgrade_selectors)
            has_access = any(s in sel_lower for s in access_selectors)
            if is_proxy and has_upgrade and not has_access:
                all_findings.append(ContractRiskIssue(
                    id=f"upgradeability_unprotected",
                    address=address,
                    kind="unprotected_upgradeability",
                    severity="high",
                    evidence="upgradeTo()/upgradeToAndCall() vorhanden aber keine Owner/AccessControl-Selektoren erkannt",
                ))
        except Exception:
            pass

        # 6. Calculate overall risk score
        risk_score = self._calculate_overall_risk(
            bytecode_analysis,
            vuln_report,
            exploit_detections,
        )
        
        # 7. Generate summary
        summary = self._generate_summary(
            bytecode_analysis,
            vuln_report,
            exploit_detections,
            interface,
        )
        
        result = {
            "address": address,
            "chain": chain,
            "score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "findings": [{
                "id": f.id,
                "kind": f.kind,
                "severity": f.severity,
                "evidence": f.evidence,
            } for f in all_findings],
            "summary": summary,
            "interface": {
                "standards": interface.standards,
                "is_proxy": interface.is_proxy,
                "functions_count": len(interface.functions),
                "top_functions": [{
                    "selector": f.selector,
                    "signature": f.signature,
                    "name": f.name,
                } for f in interface.functions[:10]],
            },
            "statistics": {
                "total_opcodes": bytecode_analysis.features.total_opcodes,
                "unique_opcodes": bytecode_analysis.features.unique_opcodes,
                "complexity_score": bytecode_analysis.features.complexity_score,
                "external_calls": bytecode_analysis.features.external_calls,
                "storage_operations": bytecode_analysis.features.storage_operations,
                "has_selfdestruct": bytecode_analysis.features.selfdestruct_present,
                "delegatecall_count": bytecode_analysis.features.delegatecall_count,
            },
            "vulnerabilities": {
                "total": vuln_report.total_vulnerabilities,
                "critical": vuln_report.critical_count,
                "high": vuln_report.high_count,
                "medium": vuln_report.medium_count,
                "low": vuln_report.low_count,
            },
        }
        # Ergänze Proxy-Metadaten explizit für API-Konsumenten
        result["proxy"] = {
            "is_proxy": is_proxy or interface.is_proxy,
            "implementation": implementation_hint,
            "type": proxy_type,
            "source": proxy_source,
        }
        return result
    
    def _calculate_overall_risk(
        self,
        bytecode_analysis: BytecodeAnalysis,
        vuln_report: VulnerabilityReport,
        exploit_detections: List[ExploitDetection],
    ) -> float:
        """Calculates weighted overall risk score (0.0 - 1.0)"""
        
        # Weighted average
        weights = {
            "bytecode": 0.3,
            "vulnerabilities": 0.4,
            "exploits": 0.3,
        }
        
        # Bytecode risk
        bytecode_risk = bytecode_analysis.risk_score
        
        # Vulnerability risk (based on severity counts)
        vuln_risk = min(1.0, (
            vuln_report.critical_count * 0.3 +
            vuln_report.high_count * 0.2 +
            vuln_report.medium_count * 0.1 +
            vuln_report.low_count * 0.05
        ))
        
        # Exploit risk (average confidence)
        if exploit_detections:
            exploit_risk = sum(e.confidence for e in exploit_detections) / len(exploit_detections)
        else:
            exploit_risk = 0.0
        
        overall = (
            bytecode_risk * weights["bytecode"] +
            vuln_risk * weights["vulnerabilities"] +
            exploit_risk * weights["exploits"]
        )
        
        return round(overall, 3)
    
    def _get_risk_level(self, score: float) -> str:
        """Maps score to risk level"""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "minimal"
    
    def _generate_summary(self, bytecode_analysis, vuln_report, exploit_detections, interface) -> str:
        """Generates human-readable summary"""
        lines = []
        
        # Interface detection
        if interface.standards:
            lines.append(f"Contract implements: {', '.join(interface.standards)}")
        
        if interface.is_proxy:
            lines.append("⚠️ Proxy contract detected - actual logic in implementation")
        
        # Critical findings
        if vuln_report.critical_count > 0:
            lines.append(f"🚨 {vuln_report.critical_count} CRITICAL vulnerabilities found!")
        
        if exploit_detections:
            for exploit in exploit_detections[:3]:  # Top 3
                lines.append(f"⚠️ {exploit.exploit_name} detected (confidence: {exploit.confidence:.0%})")
        
        # Dangerous opcodes
        if bytecode_analysis.features.selfdestruct_present:
            lines.append("⚠️ SELFDESTRUCT present - contract can be destroyed")
        
        if bytecode_analysis.features.delegatecall_count > 0:
            lines.append(f"⚠️ {bytecode_analysis.features.delegatecall_count} DELEGATECALL(s) - can modify state")
        
        # Proxy details
        try:
            if interface.is_proxy:
                if getattr(interface, 'implementation_hint', None):
                    lines.append(f"ℹ️ Proxy implementation: {getattr(interface, 'implementation_hint')}")
                if proxy_type:
                    lines.append(f"ℹ️ Proxy type: {proxy_type}")
                # Hinweis auf ungeschützte Upgradeability
                upgrade_selectors = {"0x3659cfe6", "0x4f1ef286"}
                access_selectors = {"0x8da5cb5b", "0xf2fde38b", "0x91d14854", "0x2f2ff15d", "0xd547741f"}
                sel_lower = {s.lower() for s in selectors}
                if any(s in sel_lower for s in upgrade_selectors) and not any(s in sel_lower for s in access_selectors):
                    lines.append("⚠️ Upgrade-Funktionen ohne erkennbare AccessControl/Ownable gefunden")
        except Exception:
            pass

        # Positive findings
        if not vuln_report.vulnerabilities and not exploit_detections:
            lines.append("✅ No major vulnerabilities or exploits detected")
        
        return "\n".join(lines) if lines else "Analysis complete."


contracts_service = ContractsService()
