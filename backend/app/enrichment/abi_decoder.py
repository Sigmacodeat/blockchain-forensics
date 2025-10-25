"""ABI Decoder for Smart Contract Interactions"""

import logging
from typing import Optional, Dict, Any, List
try:
    from eth_abi import decode as _abi_decode
    _ABI_AVAILABLE = True
except Exception:
    _ABI_AVAILABLE = False
    _abi_decode = None  # type: ignore
try:
    from eth_utils import function_signature_to_4byte_selector  # noqa: F401
except Exception:
    function_signature_to_4byte_selector = None  # type: ignore

logger = logging.getLogger(__name__)


class ABIDecoder:
    """Decode contract method calls and events using ABI"""
    
    # Common ERC20 method signatures
    ERC20_SIGNATURES = {
        "0xa9059cbb": {
            "name": "transfer",
            "inputs": ["address", "uint256"],
            "type": "function"
        },
        "0x23b872dd": {
            "name": "transferFrom",
            "inputs": ["address", "address", "uint256"],
            "type": "function"
        },
        "0x095ea7b3": {
            "name": "approve",
            "inputs": ["address", "uint256"],
            "type": "function"
        },
    }
    
    # Common event signatures
    EVENT_SIGNATURES = {
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": {
            "name": "Transfer",
            "inputs": ["address", "address", "uint256"],
            "indexed": [True, True, False]
        },
        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": {
            "name": "Approval",
            "inputs": ["address", "address", "uint256"],
            "indexed": [True, True, False]
        },
        # ERC721 Transfer(address indexed from, address indexed to, uint256 indexed tokenId)
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef:erc721": {
            "name": "ERC721_Transfer",
            "inputs": ["address", "address", "uint256"],
            "indexed": [True, True, True]
        },
        # ERC1155 TransferSingle(address indexed operator, address indexed from, address indexed to, uint256 id, uint256 value)
        "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62": {
            "name": "TransferSingle",
            "inputs": ["address", "address", "address", "uint256", "uint256"],
            "indexed": [True, True, True, False, False]
        },
        # ERC1155 TransferBatch(address indexed operator, address indexed from, address indexed to, uint256[] ids, uint256[] values)
        "0x4a39dc06d4c0dbc64b70b3e6d7a7ee3b910b6cce6c6c7f7a3ebd6b49300a9fbb": {
            "name": "TransferBatch",
            "inputs": ["address", "address", "address", "uint256[]", "uint256[]"],
            "indexed": [True, True, True, False, False]
        },
    }
    
    def __init__(self):
        self.method_cache: Dict[str, Dict] = {}
        self.event_cache: Dict[str, Dict] = {}
        self._selector_name_cache: Dict[str, str] = {}
        self._load_common_signatures()
    
    def _load_common_signatures(self):
        """Load common contract signatures"""
        self.method_cache.update(self.ERC20_SIGNATURES)
        self.event_cache.update(self.EVENT_SIGNATURES)
        logger.info(f"Loaded {len(self.method_cache)} method signatures")
    
    def decode_method_call(self, input_data: str) -> Optional[Dict[str, Any]]:
        """
        Decode contract method call from input data
        
        Args:
            input_data: Hex string of transaction input (0x...)
        
        Returns:
            {
                'method': 'transfer',
                'params': {'to': '0x...', 'amount': 1000},
                'raw_params': [...]
            }
        """
        if not input_data or len(input_data) < 10:
            return None
        
        try:
            # Extract method selector (first 4 bytes)
            method_selector = input_data[:10].lower()
            
            # Look up signature
            signature = self.method_cache.get(method_selector)
            if not signature:
                # Try resolving via 4byte.directory (best-effort)
                resolved_name = self._resolve_selector_name(method_selector)
                if resolved_name:
                    signature = {
                        'name': resolved_name,
                        'inputs': [],
                        'type': 'function',
                    }
                    # Cache minimal signature to avoid repeated lookups
                    self.method_cache[method_selector] = signature
                else:
                    logger.debug(f"Unknown method selector: {method_selector}")
                    return {
                        'method': method_selector,
                        'params': {},
                        'raw_params': []
                    }
            
            # Decode parameters
            param_data = input_data[10:]  # Remove selector
            if not param_data or param_data == '0x':
                return {
                    'method': signature['name'],
                    'params': {},
                    'raw_params': []
                }
            
            # Remove '0x'
            param_bytes = bytes.fromhex(param_data)
            # Decode only if ABI lib available; otherwise return raw
            if _ABI_AVAILABLE and _abi_decode is not None:
                decoded = _abi_decode(signature['inputs'], param_bytes)
            else:
                # Graceful fallback without raising in test/env without eth_abi
                decoded = []
            
            # Format parameters
            params = {}
            for i, (input_type, value) in enumerate(zip(signature['inputs'], decoded)):
                if input_type == 'address':
                    params[f'param_{i}'] = f"0x{value.hex()}" if isinstance(value, bytes) else value
                else:
                    params[f'param_{i}'] = value
            
            return {
                'method': signature['name'],
                'params': params,
                'raw_params': list(decoded)
            }
            
        except Exception as e:
            logger.error(f"Error decoding method call: {e}")
            return None

    def _resolve_selector_name(self, selector: str) -> Optional[str]:
        """Resolve a 4-byte method selector to a function name via 4byte.directory API.
        Returns the most common text_signature or None on failure.
        """
        try:
            sel = (selector or '').lower()
            if sel in self._selector_name_cache:
                return self._selector_name_cache[sel]
            # Only valid selectors start with 0x and have length 10
            if not (isinstance(sel, str) and sel.startswith('0x') and len(sel) == 10):
                return None
            import os
            # Avoid external calls in explicit TEST_MODE
            if os.environ.get('TEST_MODE') == '1':
                return None
            import httpx
            url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={sel}"
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                results = data.get('results') or []
                if not results:
                    return None
                # Pick the most common or first signature
                # API returns objects with 'text_signature', 'created_at', etc.
                name = results[0].get('text_signature')
                if isinstance(name, str) and name:
                    # Extract function name without parameters for display if needed
                    fn = name.split('(')[0]
                    self._selector_name_cache[sel] = fn
                    return fn
                return None
        except Exception:
            return None
    
    def decode_log(self, log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Decode event log
        
        Args:
            log: {
                'topics': ['0x...', ...],
                'data': '0x...',
                'address': '0x...'
            }
        
        Returns:
            {
                'event': 'Transfer',
                'params': {...},
                'contract': '0x...'
            }
        """
        if not log.get('topics'):
            return None
        
        try:
            # First topic is event signature
            event_signature = log['topics'][0].hex() if isinstance(log['topics'][0], bytes) else log['topics'][0]
            event_signature = event_signature.lower()
            
            # Look up signature (special handling for ERC721 Transfer which reuses ERC20 hash with 3rd indexed)
            signature = self.event_cache.get(event_signature)
            if not signature and len(log.get('topics', [])) >= 4:
                # Try ERC721 variant key
                signature = self.event_cache.get(event_signature + ":erc721")
            if not signature:
                logger.debug(f"Unknown event signature: {event_signature}")
                return None
            
            # Decode indexed and non-indexed parameters
            indexed_params: List[Any] = []
            for i, (indexed, topic) in enumerate(zip(signature['indexed'], log['topics'][1:])):
                if indexed:
                    # Decode indexed parameter
                    topic_hex = topic.hex() if isinstance(topic, bytes) else str(topic)
                    topic_bytes = bytes.fromhex(topic_hex.replace('0x', ''))
                    
                    input_type = signature['inputs'][i]
                    if input_type == 'address':
                        # Address is right-padded in topic
                        indexed_params.append(f"0x{topic_bytes[-20:].hex()}")
                    else:
                        indexed_params.append(int.from_bytes(topic_bytes, 'big'))
            
            # Decode non-indexed parameters from data
            non_indexed_types = [t for t, indexed in zip(signature['inputs'], signature['indexed']) if not indexed]
            data_hex = (log.get('data') or '0x')
            data_bytes = bytes.fromhex(str(data_hex).replace('0x', '')) if data_hex and data_hex != '0x' else b''
            
            non_indexed_params: List[Any] = []
            if non_indexed_types:
                if data_bytes and _ABI_AVAILABLE and _abi_decode is not None:
                    try:
                        decoded_tuple = _abi_decode(non_indexed_types, data_bytes)
                        non_indexed_params = list(decoded_tuple)
                    except Exception:
                        non_indexed_params = []
                # Fallback: fill defaults to avoid index errors (e.g., tests without eth_abi)
                if len(non_indexed_params) < len(non_indexed_types):
                    for t in non_indexed_types[len(non_indexed_params):]:
                        if t.startswith('uint') or t.startswith('int'):
                            non_indexed_params.append(0)
                        elif t == 'address':
                            non_indexed_params.append('0x' + '00'*20)
                        else:
                            non_indexed_params.append(None)
            
            # Combine parameters
            params = {}
            indexed_idx = 0
            non_indexed_idx = 0
            
            for i, indexed in enumerate(signature['indexed']):
                if indexed:
                    if indexed_idx < len(indexed_params):
                        params[f'param_{i}'] = indexed_params[indexed_idx]
                    else:
                        params[f'param_{i}'] = None
                    indexed_idx += 1
                else:
                    if non_indexed_idx < len(non_indexed_params):
                        params[f'param_{i}'] = non_indexed_params[non_indexed_idx]
                    else:
                        params[f'param_{i}'] = None
                    non_indexed_idx += 1
            
            return {
                'event': signature['name'],
                'params': params,
                'contract': log.get('address')
            }
            
        except Exception as e:
            logger.error(f"Error decoding log: {e}")
            return None
    
    def add_custom_signature(self, selector: str, signature: Dict[str, Any]):
        """Add custom method signature"""
        self.method_cache[selector.lower()] = signature
        logger.info(f"Added custom signature: {selector} -> {signature['name']}")
    
    def add_custom_event(self, signature_hash: str, event: Dict[str, Any]):
        """Add custom event signature"""
        self.event_cache[signature_hash.lower()] = event
        logger.info(f"Added custom event: {signature_hash} -> {event['name']}")


# Singleton instance
abi_decoder = ABIDecoder()


def decode_input(input_data: str, contract_address: Optional[str] = None) -> Dict[str, Any]:
    """Compatibility wrapper for API: decode input data and normalize response shape.
    Returns keys: function_name, function_signature, parameters, decoded.
    """
    try:
        result = abi_decoder.decode_method_call(input_data)
        if not result:
            return {
                "function_name": None,
                "function_signature": None,
                "parameters": None,
                "decoded": False,
            }
        return {
            "function_name": result.get("method"),
            # For now, use method name as signature if exact signature unknown
            "function_signature": result.get("method"),
            "parameters": result.get("params"),
            "decoded": True,
        }
    except Exception as e:
        logger.error(f"decode_input error: {e}")
        return {
            "function_name": None,
            "function_signature": None,
            "parameters": None,
            "decoded": False,
        }
