#!/usr/bin/env python3
"""
WebSocket Smoke Test für Production Readiness
Testet alle WS-Endpunkte mit Authentifizierung
"""

import asyncio
import json
import websockets
import jwt
import os
from datetime import datetime, timedelta

# Test-Konfiguration
WS_BASE = "ws://localhost:8000"
JWT_SECRET = "test-secret-key"  # Aus .env

def create_test_jwt(plan="community"):
    """Erstelle Test-JWT Token"""
    payload = {
        "user_id": "test-user",
        "plan": plan,
        "email": "test@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def test_ws_endpoint(endpoint, token=None, headers=None):
    """Teste einzelnen WS-Endpunkt"""
    uri = f"{WS_BASE}{endpoint}"

    # Header für Auth
    ws_headers = {}
    if token:
        ws_headers["Authorization"] = f"Bearer {token}"
    elif headers:
        ws_headers.update(headers)

    try:
        async with websockets.connect(uri, extra_headers=ws_headers) as websocket:
            # Sende Ping
            await websocket.send(json.dumps({"type": "ping"}))

            # Warte auf Pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)

            if data.get("type") == "pong":
                print(f"✅ {endpoint}: Verbindung erfolgreich")
                return True
            else:
                print(f"❌ {endpoint}: Unerwartete Antwort: {data}")
                return False

    except websockets.exceptions.ConnectionClosedError as e:
        if e.code == 4401:
            print(f"❌ {endpoint}: Authentifizierung fehlgeschlagen (4401)")
            return False
        else:
            print(f"❌ {endpoint}: Verbindung geschlossen ({e.code})")
            return False
    except Exception as e:
        print(f"❌ {endpoint}: Fehler - {str(e)}")
        return False

async def main():
    """Haupt-Test-Funktion"""
    print("🚀 WebSocket Production Smoke Test")
    print("=" * 50)

    # Test ohne Auth (sollte 4401 zurückgeben)
    print("\n1. Test ohne Authentifizierung:")
    await test_ws_endpoint("/api/v1/ws/alerts")

    # Test mit ungültigem Token
    print("\n2. Test mit ungültigem Token:")
    await test_ws_endpoint("/api/v1/ws/alerts", token="invalid-token")

    # Test mit gültigem Token
    print("\n3. Test mit gültigem Token (community):")
    token = create_test_jwt("community")
    await test_ws_endpoint("/api/v1/ws/alerts", token=token)
    await test_ws_endpoint("/api/v1/ws/room/test", token=token)
    await test_ws_endpoint("/api/v1/ws", token=token)

    # Test mit API-Key (falls konfiguriert)
    print("\n4. Test mit API-Key:")
    # Simuliere API-Key Header
    api_headers = {"x-api-key": "test-api-key"}
    await test_ws_endpoint("/api/v1/ws/alerts", headers=api_headers)

    print("\n" + "=" * 50)
    print("✅ Smoke Test abgeschlossen")

if __name__ == "__main__":
    asyncio.run(main())
