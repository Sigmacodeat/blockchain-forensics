"""Bridge Contract Registry - Zentrale Verwaltung von Bridge-Contracts und Method-Selectors"""

import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BridgeContract:
    """Bridge Contract Information"""
    address: str
    chain: str
    name: str
    bridge_type: str  # canonical, third_party
    counterpart_chains: List[str]  # Chains this bridge connects to
    method_selectors: List[str]
    added_at: datetime = None
    
    def __post_init__(self):
        self.address = self.address.lower()
        if self.added_at is None:
            self.added_at = datetime.utcnow()


class BridgeRegistry:
    """
    Zentrale Registry für bekannte Bridge-Contracts.
    
    Features:
    - Multi-Chain Bridge-Contract-Verwaltung
    - Method-Selector-Erkennung
    - Dynamische Registrierung zur Laufzeit
    - Query-Interface für Bridge-Erkennung
    """
    
    def __init__(self):
        self._contracts: Dict[str, Dict[str, BridgeContract]] = {}  # {chain: {address: contract}}
        self._method_selectors: Set[str] = set()
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialisiere mit bekannten Bridge-Contracts"""
        
        # Ethereum Bridges
        self.register(BridgeContract(
            address="0x3ee18b2214aff97000d974cf647e7c347e8fa585",
            chain="ethereum",
            name="Wormhole",
            bridge_type="third_party",
            counterpart_chains=["solana", "polygon", "arbitrum", "optimism", "base"],
            method_selectors=["0x0f5287b0"]
        ))
        
        self.register(BridgeContract(
            address="0x8731d54e9d02c286767d56ac03e8037c07e01e98",
            chain="ethereum",
            name="Stargate",
            bridge_type="third_party",
            counterpart_chains=["polygon", "arbitrum", "optimism", "base"],
            method_selectors=["0x1114cd2a"]
        ))
        
        # Polygon Bridges
        self.register(BridgeContract(
            address="0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
            chain="polygon",
            name="Polygon PoS Bridge - RootChainManager",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x3ccfd60b"]
        ))
        
        self.register(BridgeContract(
            address="0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf",
            chain="polygon",
            name="Polygon ERC20 Predicate",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x3ccfd60b", "0xe3dec8fb"]
        ))
        
        # Arbitrum Bridges
        self.register(BridgeContract(
            address="0x72ce9c846789fdb6fc1f34ac4ad25dd9ef7031ef",
            chain="arbitrum",
            name="Arbitrum Gateway Router",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x0f4d14e9", "0x9463df0a"]
        ))
        
        self.register(BridgeContract(
            address="0xa3a7b6f88361f48403514059f1f16c8e78d60eec",
            chain="arbitrum",
            name="Arbitrum ERC20 Gateway",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x2e567b36"]
        ))
        
        # Optimism Bridges
        self.register(BridgeContract(
            address="0x99c9fc46f92e8a1c0dec1b1747d010903e884be1",
            chain="optimism",
            name="Optimism L1 Standard Bridge",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x58a997f6", "0x32b7006d"]
        ))
        
        self.register(BridgeContract(
            address="0x25ace71c97b33cc4729cf772ae268934f7ab5fa1",
            chain="optimism",
            name="Optimism L1 Cross Domain Messenger",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x3dbb202b"]
        ))
        
        # Base Bridges
        self.register(BridgeContract(
            address="0x3154cf16ccdb4c6d922629664174b904d80f2c35",
            chain="base",
            name="Base L1 Standard Bridge",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x32b7006d", "0x58a997f6"]
        ))
        
        self.register(BridgeContract(
            address="0x866e82a600a1414e583f7f13623f1ac5d58b0afa",
            chain="base",
            name="Base L1 Cross Domain Messenger",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0x3dbb202b"]
        ))
        
        logger.info(f"Bridge Registry initialized with {self.get_stats()['total_contracts']} contracts")
    
    def register(self, contract: BridgeContract) -> bool:
        """
        Registriere einen Bridge-Contract
        
        Args:
            contract: BridgeContract-Instanz
            
        Returns:
            True wenn erfolgreich registriert
        """
        chain = contract.chain.lower()
        address = contract.address.lower()
        
        if chain not in self._contracts:
            self._contracts[chain] = {}
        
        self._contracts[chain][address] = contract
        
        # Method Selectors hinzufügen
        for selector in contract.method_selectors:
            self._method_selectors.add(selector.lower())
        
        logger.debug(f"Registered bridge contract: {contract.name} on {chain}")
        return True
    
    def is_bridge_contract(self, address: str, chain: str) -> bool:
        """Prüfe ob eine Adresse ein bekannter Bridge-Contract ist"""
        chain = chain.lower()
        address = address.lower()
        return chain in self._contracts and address in self._contracts[chain]
    
    def is_bridge_method(self, method_selector: str) -> bool:
        """Prüfe ob ein Method-Selector einem Bridge-Contract zugeordnet ist"""
        return method_selector.lower() in self._method_selectors
    
    def get_contract(self, address: str, chain: str) -> Optional[BridgeContract]:
        """Hole Bridge-Contract-Info"""
        chain = chain.lower()
        address = address.lower()
        if chain in self._contracts:
            return self._contracts[chain].get(address)
        return None
    
    def get_contracts_by_chain(self, chain: str) -> List[BridgeContract]:
        """Hole alle Bridge-Contracts für eine Chain"""
        chain = chain.lower()
        if chain in self._contracts:
            return list(self._contracts[chain].values())
        return []
    
    def get_all_contracts(self) -> List[BridgeContract]:
        """Hole alle registrierten Bridge-Contracts"""
        contracts = []
        for chain_contracts in self._contracts.values():
            contracts.extend(chain_contracts.values())
        return contracts
    
    def get_counterpart_chains(self, address: str, chain: str) -> List[str]:
        """Hole die Counterpart-Chains für einen Bridge-Contract"""
        contract = self.get_contract(address, chain)
        if contract:
            return contract.counterpart_chains
        return []
    
    def remove_contract(self, address: str, chain: str) -> bool:
        """Entferne einen Bridge-Contract"""
        chain = chain.lower()
        address = address.lower()
        if chain in self._contracts and address in self._contracts[chain]:
            del self._contracts[chain][address]
            logger.info(f"Removed bridge contract {address} on {chain}")
            return True
        return False
    
    def get_stats(self) -> Dict[str, int]:
        """Hole Registry-Statistiken"""
        total = sum(len(contracts) for contracts in self._contracts.values())
        return {
            "total_contracts": total,
            "total_chains": len(self._contracts),
            "total_selectors": len(self._method_selectors)
        }


# Global Registry-Instanz
bridge_registry = BridgeRegistry()
