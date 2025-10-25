#!/usr/bin/env python3
"""
Stellt sicher, dass en.json die minimalen i18n-Schlüssel enthält (chat, wizard, layout),
damit Backfill auf andere Sprachen greifen kann.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN_FILE = ROOT / 'src' / 'locales' / 'en.json'

MINIMAL = {
  "chat": {
    "title": "Chat",
    "placeholder": "Type your message...",
    "send": "Send",
    "retry": "Retry",
    "loading": "Connecting..."
  },
  "wizard": {
    "title": "Setup Wizard",
    "next": "Next",
    "prev": "Back",
    "finish": "Finish"
  },
  "layout": {
    "header": {
      "title": "SIGMACODE",
      "nav": {
        "home": "Home",
        "features": "Features",
        "pricing": "Pricing",
        "docs": "Docs"
      }
    },
    "footer": {
      "company": "Company",
      "legal": "Legal",
      "privacy": "Privacy",
      "terms": "Terms"
    }
  }
}

def deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict):
            if k not in dst or not isinstance(dst.get(k), dict):
                dst[k] = {}
            deep_merge(dst[k], v)
        else:
            if k not in dst:
                dst[k] = v


def main():
    data = json.loads(EN_FILE.read_text(encoding='utf-8'))
    deep_merge(data, MINIMAL)
    EN_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print("en.json minimal keys ensured.")

if __name__ == '__main__':
    main()
