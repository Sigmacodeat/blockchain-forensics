# i18n Configuration for AppSumo Products

## Supported Languages
- en: English (Default)
- de: Deutsch
- es: Español
- fr: Français
- it: Italiano
- pt: Português

## Product Pages to Translate
1. wallet-guardian
2. transaction-inspector
3. analytics-pro
4. nft-manager
5. complete-security
6. defi-tracker
7. ai-contract-audit
8. nft-fraud-guardian
9. chatbot-pro
10. power-suite
11. tax-reporter
12. agency-reseller
13. trader-pack

## Translation Keys Structure
Each product page has these sections:
- hero.headline
- hero.subheadline
- hero.cta
- features.title
- features.items.[].title
- features.items.[].description
- benefits.title
- benefits.items.[]
- pricing.tiers.[].name
- pricing.tiers.[].price
- pricing.tiers.[].features.[]
- faq.title
- faq.items.[].question
- faq.items.[].answer
- footer.contact
- footer.legal

## Implementation
- Use i18n library (react-i18next)
- hreflang tags for SEO
- Locale-specific URLs: /products/wallet-guardian/de
- Default redirects: /products/wallet-guardian → /products/wallet-guardian/en
