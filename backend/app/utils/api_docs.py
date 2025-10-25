"""
OpenAPI/Swagger-Dokumentation für Blockchain-Forensik-API

Automatische Generierung von API-Dokumentation aus Code-Kommentaren.
"""

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
import json
import yaml
from pathlib import Path
from typing import Dict

def create_custom_openapi_schema(app: FastAPI) -> Dict:
    """Erstellt benutzerdefiniertes OpenAPI-Schema"""

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Blockchain Forensik API",
        version="1.0.0",
        description="""
        # Blockchain Forensik API

        Vollständige REST-API für Blockchain-Forensik und -Analyse.

        ## Features

        - **Multi-Chain Support**: Ethereum, Bitcoin, Solana, Polygon, BSC u.v.m.
        - **KI-gestützte Analyse**: Automatische Risikobewertung und Mustererkennung
        - **Wallet-Management**: Sichere Multi-Chain-Wallet-Verwaltung
        - **Forensik-Tools**: Umfassende Analyse- und Tracing-Funktionen
        - **Multi-Signature**: Erweiterte Sicherheitsfeatures
        - **Export/Import**: Verschiedene Datenformate unterstützt

        ## Authentifizierung

        Die API verwendet JWT-Tokens für Authentifizierung:

        ```
        Authorization: Bearer <your-jwt-token>
        ```

        ## Rate Limiting

        - Standard: 1000 Requests/Minute pro Benutzer
        - Erhöhte Limits für Enterprise-Kunden verfügbar

        ## Support

        Bei Fragen oder Problemen kontaktieren Sie unser Support-Team.
        """,
        routes=app.routes,
    )

    # Zusätzliche Metadaten hinzufügen
    openapi_schema["info"]["contact"] = {
        "name": "Blockchain Forensik Support",
        "email": "support@blockchain-forensik.com"
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    # Server-Informationen hinzufügen
    openapi_schema["servers"] = [
        {
            "url": "https://api.blockchain-forensik.com/v1",
            "description": "Produktions-Server"
        },
        {
            "url": "https://staging-api.blockchain-forensik.com/v1",
            "description": "Staging-Umgebung"
        },
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Lokale Entwicklung"
        }
    ]

    # Security Schemes definieren
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }

    # Globale Security anwenden
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

def setup_api_documentation(app: FastAPI):
    """Richtet API-Dokumentation ein"""

    # OpenAPI-Schema generieren
    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_json():
        return create_custom_openapi_schema(app)

    @app.get("/openapi.yaml", include_in_schema=False)
    async def get_openapi_yaml():
        schema = create_custom_openapi_schema(app)
        return yaml.dump(schema, default_flow_style=False)

    # Swagger UI
    @app.get("/docs", include_in_schema=False)
    async def get_swagger_ui():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Blockchain Forensik API - Dokumentation",
            swagger_favicon_url="/favicon.ico"
        )

    # ReDoc (alternative Dokumentation)
    @app.get("/redoc", include_in_schema=False)
    async def get_redoc_ui():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Blockchain Forensik API - ReDoc",
            swagger_ui_parameters={"syntaxHighlight": False},
            swagger_favicon_url="/favicon.ico"
        )

    # API-Info-Endpunkt
    @app.get("/api/info", include_in_schema=False)
    async def get_api_info():
        return {
            "name": "Blockchain Forensik API",
            "version": "1.0.0",
            "description": "REST-API für Blockchain-Forensik und -Analyse",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_json": "/openapi.json",
                "openapi_yaml": "/openapi.yaml"
            },
            "features": [
                "Multi-Chain Support (130+ Chains)",
                "KI-gestützte Analyse",
                "Wallet-Management",
                "Forensik-Tools",
                "Multi-Signature",
                "Export/Import",
                "Caching",
                "Rate Limiting",
                "Audit Logging"
            ]
        }

    logger.info("API-Dokumentation eingerichtet")

# Import für YAML-Serialisierung
try:
    import yaml
except ImportError:
    yaml = None

# Fallback für fehlendes yaml
if not yaml:
    class MockYAML:
        @staticmethod
        def dump(data, **kwargs):
            return json.dumps(data, indent=2)

    yaml = MockYAML()

# Import für Logging
import logging
logger = logging.getLogger(__name__)
