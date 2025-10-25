"""
Policy-DSL Beispiel für Exposure-basiertes Alerting
===================================================

Beispiel-Policy für die Alert-Engine, die Exposure-Metriken nutzt.
Aktiviere diese Policy in alert_engine.policy_rules, um Alerts zu testen.
"""

EXAMPLE_EXPOSURE_POLICY = {
    "rules": [
        {
            "name": "high_exposure_alert",
            "description": "Alert on addresses with high exposure share or indirect hops",
            "severity": "high",
            "when": {
                "exposure_share_gte": 0.3,  # Alert wenn Exposure-Anteil >= 30%
                "indirect_hops_lte": 2,     # Nur bei <= 2 indirekten Hops
            },
            "actions": [
                {
                    "type": "create_case",
                    "case_type": "exposure_risk",
                    "priority": "high",
                    "assignee": "auto",
                },
                {
                    "type": "notify",
                    "channels": ["email", "slack"],
                    "recipients": ["compliance@company.com"],
                }
            ],
        },
        {
            "name": "direct_sanctioned_exposure",
            "description": "Critical alert for direct sanctioned exposure",
            "severity": "critical",
            "when": {
                "exposure_share_gte": 0.1,
                "direct_exposure": True,
            },
            "actions": [
                {
                    "type": "escalate",
                    "level": "immediate",
                    "notify": ["legal@company.com", "compliance@company.com"],
                },
                {
                    "type": "block_transaction",
                    "reason": "direct_sanctioned_exposure",
                }
            ],
        }
    ],
    "metadata": {
        "version": "1.0",
        "description": "Exposure-based alerting policies for forensic analysis",
        "last_updated": "2025-10-14",
    }
}

# Nutzung: In alert_engine.py policy_rules überschreiben oder erweitern
# alert_engine.policy_rules = EXAMPLE_EXPOSURE_POLICY
