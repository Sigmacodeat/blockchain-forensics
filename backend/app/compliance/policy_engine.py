"""
Compliance Policy Engine
=========================

Dynamic compliance policy evaluation:
- Jurisdiction-specific rules
- Transaction threshold policies
- Risk-based decision making
- Policy versioning
- Audit trail
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PolicyRule:
    """Single policy rule"""
    rule_id: str
    name: str
    jurisdiction: str
    rule_type: str  # threshold, sanctions, risk_score, travel_rule
    condition: Dict[str, Any]
    action: str  # allow, deny, review, alert
    priority: int = 50
    enabled: bool = True


@dataclass
class PolicyDecision:
    """Policy evaluation result"""
    allowed: bool
    action: str
    matched_rules: List[str]
    reasons: List[str]
    risk_level: str
    requires_review: bool = False


class PolicyEngine:
    """Evaluates compliance policies"""
    
    def __init__(self, policy_dir: Optional[str] = None):
        self.policies: Dict[str, PolicyRule] = {}
        self.policy_dir = policy_dir or ".policies"
        self._load_policies()
    
    def _load_policies(self):
        """Load policies from directory"""
        try:
            policy_path = Path(self.policy_dir)
            if not policy_path.exists():
                logger.warning(f"Policy directory not found: {self.policy_dir}")
                self._load_default_policies()
                return
            
            for file in policy_path.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for rule_data in data:
                                rule = self._parse_rule(rule_data)
                                if rule:
                                    self.policies[rule.rule_id] = rule
                        elif isinstance(data, dict):
                            rule = self._parse_rule(data)
                            if rule:
                                self.policies[rule.rule_id] = rule
                except Exception as e:
                    logger.error(f"Error loading policy {file}: {e}")
            
            logger.info(f"Loaded {len(self.policies)} policies")
        except Exception as e:
            logger.error(f"Error loading policies: {e}")
            self._load_default_policies()
    
    def _parse_rule(self, data: Dict) -> Optional[PolicyRule]:
        """Parse policy rule from dict"""
        try:
            return PolicyRule(
                rule_id=data["rule_id"],
                name=data["name"],
                jurisdiction=data.get("jurisdiction", "GLOBAL"),
                rule_type=data["rule_type"],
                condition=data["condition"],
                action=data["action"],
                priority=data.get("priority", 50),
                enabled=data.get("enabled", True)
            )
        except Exception as e:
            logger.error(f"Error parsing rule: {e}")
            return None
    
    def _load_default_policies(self):
        """Load hardcoded default policies"""
        defaults = [
            PolicyRule(
                rule_id="GLOBAL_SANCTIONS_BLOCK",
                name="Block Sanctioned Entities",
                jurisdiction="GLOBAL",
                rule_type="sanctions",
                condition={"sanctions_hit": True},
                action="deny",
                priority=100
            ),
            PolicyRule(
                rule_id="US_TRAVEL_RULE",
                name="US Travel Rule Threshold",
                jurisdiction="US",
                rule_type="travel_rule",
                condition={"amount_usd": {"gte": 1000}},
                action="require_travel_rule",
                priority=90
            ),
            PolicyRule(
                rule_id="EU_TRAVEL_RULE",
                name="EU Travel Rule Threshold",
                jurisdiction="EU",
                rule_type="travel_rule",
                condition={"amount_usd": {"gte": 1000}},
                action="require_travel_rule",
                priority=90
            ),
            PolicyRule(
                rule_id="HIGH_RISK_REVIEW",
                name="High Risk Manual Review",
                jurisdiction="GLOBAL",
                rule_type="risk_score",
                condition={"risk_score": {"gte": 70}},
                action="review",
                priority=80
            ),
            PolicyRule(
                rule_id="CRITICAL_RISK_BLOCK",
                name="Critical Risk Block",
                jurisdiction="GLOBAL",
                rule_type="risk_score",
                condition={"risk_score": {"gte": 90}},
                action="deny",
                priority=95
            )
        ]
        
        for rule in defaults:
            self.policies[rule.rule_id] = rule
    
    def evaluate(
        self,
        transaction: Dict[str, Any],
        jurisdiction: str = "GLOBAL"
    ) -> PolicyDecision:
        """Evaluate transaction against policies"""
        matched_rules: List[str] = []
        reasons: List[str] = []
        actions: List[str] = []
        
        # Get applicable rules (jurisdiction + global)
        applicable = [
            rule for rule in self.policies.values()
            if rule.enabled and (
                rule.jurisdiction == jurisdiction or
                rule.jurisdiction == "GLOBAL"
            )
        ]
        
        # Sort by priority (higher first)
        applicable.sort(key=lambda r: r.priority, reverse=True)
        
        # Evaluate each rule
        for rule in applicable:
            if self._matches(transaction, rule.condition):
                matched_rules.append(rule.rule_id)
                reasons.append(rule.name)
                actions.append(rule.action)
        
        # Determine final action (most restrictive wins)
        final_action = self._resolve_actions(actions)
        
        # Determine risk level
        risk_score = transaction.get("risk_score", 0)
        if risk_score >= 90:
            risk_level = "critical"
        elif risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return PolicyDecision(
            allowed=(final_action not in ["deny", "block"]),
            action=final_action,
            matched_rules=matched_rules,
            reasons=reasons,
            risk_level=risk_level,
            requires_review=(final_action == "review")
        )
    
    def _matches(self, data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Check if data matches condition"""
        for key, value in condition.items():
            if key not in data:
                return False
            
            data_val = data[key]
            
            # Direct equality
            if not isinstance(value, dict):
                if data_val != value:
                    return False
                continue
            
            # Comparison operators
            if "gte" in value:
                if not (data_val >= value["gte"]):
                    return False
            if "gt" in value:
                if not (data_val > value["gt"]):
                    return False
            if "lte" in value:
                if not (data_val <= value["lte"]):
                    return False
            if "lt" in value:
                if not (data_val < value["lt"]):
                    return False
            if "eq" in value:
                if data_val != value["eq"]:
                    return False
        
        return True
    
    def _resolve_actions(self, actions: List[str]) -> str:
        """Resolve multiple actions to single action (most restrictive)"""
        if not actions:
            return "allow"
        
        # Priority: deny > block > review > alert > allow
        if "deny" in actions or "block" in actions:
            return "deny"
        if "review" in actions:
            return "review"
        if "alert" in actions:
            return "alert"
        if "require_travel_rule" in actions:
            return "require_travel_rule"
        
        return "allow"
    
    def add_policy(self, rule: PolicyRule) -> None:
        """Add or update policy rule"""
        self.policies[rule.rule_id] = rule
        logger.info(f"Policy added/updated: {rule.rule_id}")
    
    def get_policy(self, rule_id: str) -> Optional[PolicyRule]:
        """Get policy by ID"""
        return self.policies.get(rule_id)
    
    def list_policies(
        self,
        jurisdiction: Optional[str] = None,
        rule_type: Optional[str] = None
    ) -> List[PolicyRule]:
        """List policies with optional filters"""
        result = list(self.policies.values())
        
        if jurisdiction:
            result = [r for r in result if r.jurisdiction == jurisdiction or r.jurisdiction == "GLOBAL"]
        
        if rule_type:
            result = [r for r in result if r.rule_type == rule_type]
        
        return result


# Global instance
policy_engine = PolicyEngine()
