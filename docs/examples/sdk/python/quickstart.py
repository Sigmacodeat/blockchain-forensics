from pathlib import Path
import os
import sys

# Add generated SDK to path (adjust if installed as a package)
sdk_path = Path(__file__).resolve().parents[3] / 'docs' / 'sdk' / 'python'
sys.path.append(str(sdk_path))

from blockchain_forensics_sdk import ApiClient, Configuration, DefaultApi  # type: ignore


def main() -> None:
    cfg = Configuration()
    cfg.host = os.getenv('API_URL', 'http://localhost:8000/api/v1')
    if api_key := os.getenv('API_KEY'):
        cfg.api_key['X-API-Key'] = api_key
    if token := os.getenv('API_TOKEN'):
        cfg.access_token = token

    with ApiClient(cfg) as client:
        api = DefaultApi(client)
        res = api.api_v1_system_health_get()
        print(res)


if __name__ == '__main__':
    main()
