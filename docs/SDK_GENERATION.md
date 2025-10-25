# SDK-Generierung (TypeScript & Python)

Dieses Dokument beschreibt, wie aus der OpenAPI-Spezifikation (`backend/docs/openapi.yaml`) Client-SDKs generiert werden.

## Voraussetzungen

- Docker installiert (empfohlen) oder lokal `openapi-generator-cli`
- Zugriff auf das Repo mit `backend/docs/openapi.yaml`

## TypeScript SDK (Fetch)

Mit Docker (keine lokale Installation nötig):

```bash
docker run --rm -v "$(pwd)":/local openapitools/openapi-generator-cli generate \
  -i /local/backend/docs/openapi.yaml \
  -g typescript-fetch \
  -o /local/docs/sdk/typescript \
  --additional-properties=supportsES6=true,typescriptThreePlus=true
```

Ergebnis liegt in `docs/sdk/typescript/`.

Optional `basePath`/`servers` zur Laufzeit setzen (Prod/Sandbox).

## Python SDK (urllib3)

```bash
docker run --rm -v "$(pwd)":/local openapitools/openapi-generator-cli generate \
  -i /local/backend/docs/openapi.yaml \
  -g python \
  -o /local/docs/sdk/python \
  --additional-properties=packageName=blockchain_forensics_sdk
```

## Makefile Targets (Empfohlen)

Alternativ stehen komfortable Makefile-Targets bereit (setzen Docker voraus):

```bash
# TypeScript SDK generieren
make sdk-ts

# Python SDK generieren
make sdk-py

# Beide SDKs generieren
make sdk-all

# Generierte SDK-Verzeichnisse löschen
make sdk-clean
```

Die OpenAPI-Quelle ist `backend/docs/openapi.yaml`. Ergebnisse werden in `docs/sdk/typescript/` bzw. `docs/sdk/python/` abgelegt.

Installation lokal testen:

```bash
pip install -e docs/sdk/python
```

## Benutzung (Examples)

### TypeScript (Fetch)

```ts
// Beispiel: Nutzung in einer Vite/React-App
import { Configuration, DefaultApi } from './docs/sdk/typescript'

const api = new DefaultApi(
  new Configuration({
    basePath: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    headers: {
      // JWT oder API Key
      Authorization: `Bearer ${yourJwt}`,
      'X-API-Key': yourApiKey,
    },
  })
)

async function demo() {
  const res = await api.apiV1SystemHealthGet()
  console.log(res)
}
```

Hinweise:
- Base-URL sollte auf `/api/v1` verweisen (z. B. `http://localhost:8000/api/v1`).
- In CI/Prod per ENV konfigurieren (`VITE_API_URL`).

### Python

```python
from docs.sdk.python import blockchain_forensics_sdk

cfg = blockchain_forensics_sdk.Configuration()
cfg.host = 'http://localhost:8000/api/v1'
cfg.api_key['X-API-Key'] = 'your-api-key'
cfg.access_token = 'your-jwt-bearer'

with blockchain_forensics_sdk.ApiClient(cfg) as api_client:
    api = blockchain_forensics_sdk.DefaultApi(api_client)
    res = api.api_v1_system_health_get()
    print(res)
```

Hinweise:
- Auth: JWT (Bearer) und/oder `X-API-Key` je nach Endpoint.
- Für anonyme Endpunkte (z. B. `/metrics/webvitals`) ist keine Auth erforderlich.

## Hinweise

- OpenAPI `servers` sind bereits gesetzt: Prod `https://api.sigmacode.io/api/v1`, Sandbox `https://sandbox.api.sigmacode.io/api/v1`, Dev `http://localhost:8000/api/v1`.
- Auth: JWT (Bearer) + `X-API-Key`. Für anonyme Endpunkte (z. B. `/metrics/webvitals`) ist keine Auth erforderlich.
- Versionierung: `v1`. Breaking Changes bitte mit `v2` einführen.

## Release-Workflow

SDK-Releases werden über Tags ausgelöst. Format: `sdk-vX.Y.Z`.

```bash
git tag sdk-v0.1.0
git push --tags
```

Workflow `/.github/workflows/sdk-release.yml`:
- Validiert OpenAPI
- Generiert TS & Python SDK
- Injiziert Version aus Tag in `package.json` bzw. `pyproject.toml`
- Lädt ZIP-Artefakte im GitHub Release hoch

## Quickstart-Beispiele

Beispiele liegen unter `docs/examples/sdk/`.

### TypeScript

Datei: `docs/examples/sdk/typescript/quickstart.ts`

```bash
export API_URL=http://localhost:8000/api/v1
export API_TOKEN=...
export API_KEY=...
node docs/examples/sdk/typescript/quickstart.ts
```

### Python

Datei: `docs/examples/sdk/python/quickstart.py`

```bash
export API_URL=http://localhost:8000/api/v1
export API_TOKEN=...
export API_KEY=...
python3 docs/examples/sdk/python/quickstart.py
```

## Publishing (optional)

- TypeScript: `npm publish` (privates Registry/Org empfohlen)
- Python: `build` + `twine upload` zu TestPyPI/PyPI

## Automatisierung (CI/CD)

- In eurem CI-Workflow einen Schritt hinzufügen, der die Generierung triggert und Artefakte als Build-Outputs veröffentlicht.
