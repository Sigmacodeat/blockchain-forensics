from flask import Flask, request, Response
from .verify import verify_webhook_v2, verify_webhook_legacy
import json
import os

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "replace-me")


def normalize_headers(hdrs):
    return {k.lower(): v for k, v in hdrs.items()}


@app.post("/webhook")
def webhook() -> Response:
    raw = request.get_data()  # bytes
    headers = normalize_headers(request.headers)
    ok = verify_webhook_v2(raw, headers, WEBHOOK_SECRET) or verify_webhook_legacy(
        raw, headers, WEBHOOK_SECRET
    )
    if not ok:
        return Response("invalid signature", status=400)

    # event = json.loads(raw)
    return Response("ok", status=200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3002")))
