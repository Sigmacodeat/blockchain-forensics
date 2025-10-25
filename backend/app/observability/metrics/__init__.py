"""
Observability Metrics Package
Re-export der bestehenden Prometheus-Metriken aus `app.metrics`.
Ermöglicht schrittweise Migration der Importe auf `app.observability.metrics`.
"""
# Hinweis: Re-Export ohne lokale Neudefinitionen, um doppelte Registrierung zu vermeiden
from app.metrics import *  # noqa: F401,F403
