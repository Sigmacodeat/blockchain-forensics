#!/usr/bin/env python3
import json
import os

# Base translations template
base_template = {
    "hero": {
        "headline": "",
        "subheadline": "",
        "cta": "Get Lifetime Deal"
    },
    "features": {
        "title": "Key Features",
        "items": []
    },
    "pricing": {
        "tiers": [
            {"name": "Basic", "price": "$59", "features": []},
            {"name": "Pro", "price": "$119", "features": []},
            {"name": "Enterprise", "price": "$199", "features": []}
        ]
    },
    "faq": {
        "title": "Frequently Asked Questions",
        "items": []
    }
}

products = [
    "wallet-guardian", "transaction-inspector", "analytics-pro", 
    "nft-manager", "complete-security", "defi-tracker", 
    "ai-contract-audit", "nft-fraud-guardian", "chatbot-pro", 
    "power-suite", "tax-reporter", "agency-reseller", "trader-pack"
]

languages = ["en", "de", "es", "fr", "it", "pt"]

# Generate full translations structure
translations = {}
for lang in languages:
    translations[lang] = {"products": {}}
    for product in products:
        translations[lang]["products"][product] = base_template.copy()

# Save to file
with open('translations-full.json', 'w', encoding='utf-8') as f:
    json.dump(translations, f, indent=2, ensure_ascii=False)

print("Generated translations structure for 13 products × 6 languages")
