"""
DeFi Transaction Interpreter Service

Human-readable interpretation of complex DeFi transactions.
Similar to Chainalysis Reactor's DeFi interpretation feature.

Features:
- Automatic DeFi protocol detection
- Human-readable transaction descriptions
- Complexity analysis
- Risk assessment for DeFi interactions
- Smart contract function decoding
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DeFiProtocol(str, Enum):
    """Supported DeFi protocols"""
    UNISWAP = "uniswap"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    AAVE = "aave"
    COMPOUND = "compound"
    MAKER = "maker"
    BALANCER = "balancer"
    YEARN = "yearn"
    CONVEX = "convex"
    LIDO = "lido"
    ROCKET_POOL = "rocket_pool"
    INSTADAPP = "instadapp"
    DYDX = "dydx"
    GMX = "gmx"
    TORNADO_CASH = "tornado_cash"
    RAILGUN = "railgun"
    UNKNOWN = "unknown"


class TransactionType(str, Enum):
    """DeFi transaction types"""
    SWAP = "swap"
    ADD_LIQUIDITY = "add_liquidity"
    REMOVE_LIQUIDITY = "remove_liquidity"
    STAKE = "stake"
    UNSTAKE = "unstake"
    BORROW = "borrow"
    REPAY = "repay"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    FLASH_LOAN = "flash_loan"
    LIQUIDATION = "liquidation"
    BRIDGE = "bridge"
    WRAP = "wrap"
    UNWRAP = "unwrap"
    APPROVE = "approve"
    MULTI_CALL = "multi_call"
    UNKNOWN = "unknown"


class ComplexityLevel(str, Enum):
    """Transaction complexity levels"""
    SIMPLE = "simple"  # Single action
    MODERATE = "moderate"  # 2-5 actions
    COMPLEX = "complex"  # 6-10 actions
    VERY_COMPLEX = "very_complex"  # 10+ actions


class DeFiInterpreterService:
    """
    DeFi Transaction Interpreter for human-readable descriptions.
    
    Features:
    - Protocol detection via contract address
    - Function signature decoding
    - Multi-step transaction parsing
    - Flash loan detection
    - MEV transaction identification
    """
    
    def __init__(self):
        # Protocol contract addresses (mainnet)
        self.protocol_addresses = {
            # Uniswap V2/V3
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": DeFiProtocol.UNISWAP,  # V2 Router
            "0xe592427a0aece92de3edee1f18e0157c05861564": DeFiProtocol.UNISWAP,  # V3 Router
            
            # SushiSwap
            "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": DeFiProtocol.SUSHISWAP,
            
            # Curve
            "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7": DeFiProtocol.CURVE,
            
            # Aave V2/V3
            "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9": DeFiProtocol.AAVE,
            "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2": DeFiProtocol.AAVE,
            
            # Compound
            "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b": DeFiProtocol.COMPOUND,
            
            # MakerDAO
            "0x9759a6ac90977b93b58547b4a71c78317f391a28": DeFiProtocol.MAKER,
            
            # Lido
            "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": DeFiProtocol.LIDO,
            
            # Privacy protocols
            "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": DeFiProtocol.TORNADO_CASH,
        }
        
        # Function signatures
        self.function_signatures = {
            # Swaps
            "0x38ed1739": "swapExactTokensForTokens",
            "0x18cbafe5": "swapExactTokensForETH",
            "0x7ff36ab5": "swapExactETHForTokens",
            "0x5c11d795": "swapExactTokensForTokensSupportingFeeOnTransferTokens",
            
            # Liquidity
            "0xe8e33700": "addLiquidity",
            "0xf305d719": "addLiquidityETH",
            "0xbaa2abde": "removeLiquidity",
            "0x02751cec": "removeLiquidityETH",
            
            # Lending
            "0xa0712d68": "mint",  # Compound
            "0xdb006a75": "redeem",
            "0xc5ebeaec": "borrow",
            "0x0e752702": "repayBorrow",
            
            # Staking
            "0xa694fc3a": "stake",
            "0x2e1a7d4d": "withdraw",
            
            # Approvals
            "0x095ea7b3": "approve",
            
            # Multi-call
            "0xac9650d8": "multicall",
        }
    
    async def interpret_transaction(
        self,
        tx_hash: str,
        chain: str = "ethereum",
        include_risk: bool = True
    ) -> Dict[str, Any]:
        """
        Interpret a DeFi transaction into human-readable format.
        
        Args:
            tx_hash: Transaction hash
            chain: Blockchain
            include_risk: Include risk assessment
            
        Returns:
            Human-readable interpretation
        """
        # TODO: Fetch transaction data from RPC
        # tx_data = await self._fetch_transaction(tx_hash, chain)
        
        # Mock transaction for demonstration
        tx_data = self._mock_transaction()
        
        # Detect protocol
        protocol = self._detect_protocol(tx_data["to"])
        
        # Decode function
        tx_type = self._decode_function(tx_data["input"][:10])
        
        # Parse actions
        actions = await self._parse_actions(tx_data)
        
        # Calculate complexity
        complexity = self._calculate_complexity(actions)
        
        # Generate human-readable description
        description = self._generate_description(protocol, tx_type, actions)
        
        # Risk assessment
        risk = None
        if include_risk:
            risk = await self._assess_risk(protocol, tx_type, actions, tx_data)
        
        result = {
            "tx_hash": tx_hash,
            "chain": chain,
            "protocol": protocol.value if protocol else "unknown",
            "type": tx_type.value,
            "complexity": complexity.value,
            "description": description,
            "actions": actions,
            "timestamp": tx_data.get("timestamp"),
            "from": tx_data.get("from"),
            "to": tx_data.get("to"),
            "value_usd": tx_data.get("value_usd", 0),
            "gas_used": tx_data.get("gas_used"),
            "risk_assessment": risk,
            "interpreted_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Transaction interpreted: {tx_hash} - {protocol.value if protocol else 'unknown'} - {tx_type.value}")
        
        return result
    
    async def batch_interpret(
        self,
        tx_hashes: List[str],
        chain: str = "ethereum"
    ) -> List[Dict[str, Any]]:
        """
        Batch interpret multiple transactions.
        
        Args:
            tx_hashes: List of transaction hashes
            chain: Blockchain
            
        Returns:
            List of interpretations
        """
        import asyncio
        
        tasks = [
            self.interpret_transaction(tx_hash, chain, include_risk=False)
            for tx_hash in tx_hashes
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        return valid_results
    
    def _detect_protocol(self, contract_address: str) -> Optional[DeFiProtocol]:
        """Detect DeFi protocol by contract address."""
        addr = contract_address.lower() if contract_address else ""
        return self.protocol_addresses.get(addr, None)
    
    def _decode_function(self, function_sig: str) -> TransactionType:
        """Decode function signature to transaction type."""
        sig = function_sig.lower() if function_sig else ""
        
        func_name = self.function_signatures.get(sig, "unknown")
        
        # Map function names to types
        if "swap" in func_name.lower():
            return TransactionType.SWAP
        elif "addliquidity" in func_name.lower():
            return TransactionType.ADD_LIQUIDITY
        elif "removeliquidity" in func_name.lower():
            return TransactionType.REMOVE_LIQUIDITY
        elif "stake" in func_name.lower():
            return TransactionType.STAKE
        elif "withdraw" in func_name.lower() or "unstake" in func_name.lower():
            return TransactionType.UNSTAKE
        elif "borrow" in func_name.lower():
            return TransactionType.BORROW
        elif "repay" in func_name.lower():
            return TransactionType.REPAY
        elif "mint" in func_name.lower() or "deposit" in func_name.lower():
            return TransactionType.DEPOSIT
        elif "redeem" in func_name.lower():
            return TransactionType.WITHDRAW
        elif "approve" in func_name.lower():
            return TransactionType.APPROVE
        elif "multicall" in func_name.lower():
            return TransactionType.MULTI_CALL
        
        return TransactionType.UNKNOWN
    
    async def _parse_actions(self, tx_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse individual actions from transaction."""
        actions = []
        
        # Parse logs/events
        logs = tx_data.get("logs", [])
        
        for log in logs:
            action = self._parse_log(log)
            if action:
                actions.append(action)
        
        # If no logs, create single action from main call
        if not actions:
            actions.append({
                "type": "main_call",
                "description": "Main transaction call",
                "from": tx_data.get("from"),
                "to": tx_data.get("to"),
                "value": tx_data.get("value", 0)
            })
        
        return actions
    
    def _parse_log(self, log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single event log."""
        # Common DeFi events
        topics = log.get("topics", [])
        if not topics:
            return None
        
        event_sig = topics[0].lower() if topics else ""
        
        # Transfer event
        if event_sig == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
            return {
                "type": "transfer",
                "description": "Token transfer",
                "from": topics[1] if len(topics) > 1 else None,
                "to": topics[2] if len(topics) > 2 else None,
                "amount": log.get("data")
            }
        
        # Swap event
        elif event_sig == "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822":
            return {
                "type": "swap",
                "description": "Token swap executed",
                "contract": log.get("address")
            }
        
        return None
    
    def _calculate_complexity(self, actions: List[Dict[str, Any]]) -> ComplexityLevel:
        """Calculate transaction complexity."""
        num_actions = len(actions)
        
        if num_actions == 1:
            return ComplexityLevel.SIMPLE
        elif num_actions <= 5:
            return ComplexityLevel.MODERATE
        elif num_actions <= 10:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX
    
    def _generate_description(
        self,
        protocol: Optional[DeFiProtocol],
        tx_type: TransactionType,
        actions: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable description."""
        protocol_name = protocol.value.replace("_", " ").title() if protocol else "Unknown Protocol"
        
        # Simple descriptions
        descriptions = {
            TransactionType.SWAP: f"Swapped tokens on {protocol_name}",
            TransactionType.ADD_LIQUIDITY: f"Added liquidity to {protocol_name} pool",
            TransactionType.REMOVE_LIQUIDITY: f"Removed liquidity from {protocol_name} pool",
            TransactionType.STAKE: f"Staked tokens on {protocol_name}",
            TransactionType.UNSTAKE: f"Unstaked tokens from {protocol_name}",
            TransactionType.BORROW: f"Borrowed assets from {protocol_name}",
            TransactionType.REPAY: f"Repaid loan on {protocol_name}",
            TransactionType.DEPOSIT: f"Deposited assets into {protocol_name}",
            TransactionType.WITHDRAW: f"Withdrew assets from {protocol_name}",
            TransactionType.FLASH_LOAN: f"Executed flash loan on {protocol_name}",
            TransactionType.LIQUIDATION: f"Liquidation occurred on {protocol_name}",
            TransactionType.APPROVE: f"Approved token spending for {protocol_name}",
        }
        
        base_desc = descriptions.get(tx_type, f"Interacted with {protocol_name}")
        
        # Add complexity note
        if len(actions) > 5:
            base_desc += f" (Complex transaction with {len(actions)} actions)"
        
        return base_desc
    
    async def _assess_risk(
        self,
        protocol: Optional[DeFiProtocol],
        tx_type: TransactionType,
        actions: List[Dict[str, Any]],
        tx_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risk of DeFi transaction."""
        risk_score = 0.0
        risk_factors = []
        
        # Privacy protocol risk
        if protocol in [DeFiProtocol.TORNADO_CASH, DeFiProtocol.RAILGUN]:
            risk_score += 0.8
            risk_factors.append("Privacy protocol usage")
        
        # Flash loan risk
        if tx_type == TransactionType.FLASH_LOAN:
            risk_score += 0.6
            risk_factors.append("Flash loan transaction (potential exploit)")
        
        # Complexity risk
        if len(actions) > 10:
            risk_score += 0.3
            risk_factors.append("Very complex transaction")
        
        # High value risk
        value_usd = tx_data.get("value_usd", 0)
        if value_usd > 100000:
            risk_score += 0.2
            risk_factors.append(f"High value transaction (${value_usd:,.0f})")
        
        # Multi-call risk (potential for obfuscation)
        if tx_type == TransactionType.MULTI_CALL:
            risk_score += 0.4
            risk_factors.append("Multi-call transaction")
        
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": self._generate_risk_recommendations(risk_level, risk_factors)
        }
    
    def _generate_risk_recommendations(
        self,
        risk_level: str,
        risk_factors: List[str]
    ) -> List[str]:
        """Generate risk-based recommendations."""
        recs = []
        
        if risk_level == "high":
            recs.append("⚠️ HIGH RISK - Enhanced due diligence required")
            recs.append("Consider holding funds for review")
        elif risk_level == "medium":
            recs.append("⚠️ MEDIUM RISK - Additional verification recommended")
        
        if "Privacy protocol usage" in risk_factors:
            recs.append("Flag for AML review - privacy protocol usage detected")
        
        if "Flash loan transaction" in risk_factors:
            recs.append("Investigate for potential exploit or MEV activity")
        
        if "Very complex transaction" in risk_factors:
            recs.append("Review all transaction steps for suspicious activity")
        
        return recs
    
    def _mock_transaction(self) -> Dict[str, Any]:
        """Generate mock transaction data for testing."""
        return {
            "hash": "0x1234567890abcdef",
            "from": "0xabc123",
            "to": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap V2
            "input": "0x38ed173900000000",
            "value": "0",
            "value_usd": 1000,
            "gas_used": 150000,
            "timestamp": datetime.utcnow().isoformat(),
            "logs": [
                {
                    "address": "0xuniswap",
                    "topics": ["0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"],
                    "data": "0x..."
                }
            ]
        }
    
    async def get_protocol_stats(self) -> Dict[str, Any]:
        """Get statistics about supported protocols."""
        return {
            "total_protocols": len(set(self.protocol_addresses.values())),
            "protocols": [p.value for p in DeFiProtocol if p != DeFiProtocol.UNKNOWN],
            "total_function_signatures": len(self.function_signatures),
            "supported_transaction_types": [t.value for t in TransactionType if t != TransactionType.UNKNOWN]
        }


# Global service instance
defi_interpreter_service = DeFiInterpreterService()
