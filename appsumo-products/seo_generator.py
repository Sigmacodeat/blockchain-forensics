#!/usr/bin/env python3
"""
SEO Generator for AppSumo Products
Generates hreflang tags, structured data, and sitemaps
"""

import json
import os
from datetime import datetime

# Configuration
BASE_URL = "https://blockchain-forensics.com"
PRODUCTS = [
    "wallet-guardian", "transaction-inspector", "analytics-pro",
    "nft-manager", "complete-security", "defi-tracker",
    "ai-contract-audit", "nft-fraud-guardian", "chatbot-pro",
    "power-suite", "tax-reporter", "agency-reseller", "trader-pack"
]
LANGUAGES = ["en", "de", "es", "fr", "it", "pt"]
DEFAULT_LANG = "en"

def generate_hreflang_tags(product_slug):
    """Generate hreflang tags for a product"""
    tags = []

    # x-default (English)
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}/products/{product_slug}" />')

    # All language variants
    for lang in LANGUAGES:
        if lang == DEFAULT_LANG:
            url = f"{BASE_URL}/products/{product_slug}"
        else:
            url = f"{BASE_URL}/products/{product_slug}/{lang}"
        tags.append(f'<link rel="alternate" hreflang="{lang}" href="{url}" />')

    return "\n".join(tags)

def generate_structured_data(product_slug, product_data):
    """Generate JSON-LD structured data for a product"""
    structured_data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product_data.get("name", product_slug.replace("-", " ").title()),
        "description": product_data.get("description", ""),
        "brand": {
            "@type": "Brand",
            "name": "Blockchain Forensics"
        },
        "offers": [
            {
                "@type": "Offer",
                "price": tier["price"].replace("$", "").replace("€", ""),
                "priceCurrency": "USD" if "$" in tier["price"] else "EUR",
                "availability": "https://schema.org/InStock",
                "priceValidUntil": "2026-12-31"
            } for tier in product_data.get("pricing", {}).get("tiers", [])
        ],
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web Browser",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.8",
            "reviewCount": "127"
        }
    }
    return json.dumps(structured_data, indent=2)

def generate_sitemap(language):
    """Generate sitemap for a specific language"""
    urlset = ['<?xml version="1.0" encoding="UTF-8"?>']
    urlset.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for product in PRODUCTS:
        if language == DEFAULT_LANG:
            url = f"{BASE_URL}/products/{product}"
        else:
            url = f"{BASE_URL}/products/{product}/{language}"

        urlset.extend([
            '  <url>',
            f'    <loc>{url}</loc>',
            f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.9</priority>',
            '  </url>'
        ])

    urlset.append('</urlset>')
    return "\n".join(urlset)

def main():
    # Create output directories
    os.makedirs("seo_output/hreflang", exist_ok=True)
    os.makedirs("seo_output/structured-data", exist_ok=True)
    os.makedirs("seo_output/sitemaps", exist_ok=True)

    # Load product data (simplified)
    product_data = {}
    for product in PRODUCTS:
        product_data[product] = {
            "name": product.replace("-", " ").title(),
            "description": f"Professional {product.replace('-', ' ')} for crypto analysis",
            "pricing": {
                "tiers": [
                    {"price": "$59"},
                    {"price": "$119"},
                    {"price": "$199"}
                ]
            }
        }

    # Generate hreflang tags for each product
    for product in PRODUCTS:
        hreflang_html = generate_hreflang_tags(product)
        with open(f"seo_output/hreflang/{product}.html", "w") as f:
            f.write(f"<!-- hreflang tags for {product} -->\n{hreflang_html}\n")

    # Generate structured data for each product
    for product in PRODUCTS:
        structured_json = generate_structured_data(product, product_data[product])
        with open(f"seo_output/structured-data/{product}.json", "w") as f:
            f.write(f"<!-- Structured data for {product} -->\n<script type=\"application/ld+json\">\n{structured_json}\n</script>\n")

    # Generate sitemaps for each language
    for lang in LANGUAGES:
        sitemap_xml = generate_sitemap(lang)
        with open(f"seo_output/sitemaps/sitemap-{lang}.xml", "w") as f:
            f.write(sitemap_xml)

    # Generate master sitemap index
    master_sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    master_sitemap.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for lang in LANGUAGES:
        master_sitemap.extend([
            '  <sitemap>',
            f'    <loc>{BASE_URL}/sitemap-{lang}.xml</loc>',
            f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>',
            '  </sitemap>'
        ])
    master_sitemap.append('</sitemapindex>')

    with open("seo_output/sitemaps/sitemap.xml", "w") as f:
        f.write("\n".join(master_sitemap))

    print("✅ SEO assets generated:")
    print(f"   - hreflang tags: {len(PRODUCTS)} files")
    print(f"   - Structured data: {len(PRODUCTS)} files")
    print(f"   - Sitemaps: {len(LANGUAGES)} + 1 master file")
    print("\n📁 Output in seo_output/ directory")

if __name__ == "__main__":
    main()
