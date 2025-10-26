#!/bin/bash
# AppSumo Blog Integration Setup Script
# Integriert Blog-System in AppSumo-Produkte

set -e

# Configuration
APPSUMO_PRODUCT=${1:-"wallet-guardian"}
TARGET_DIR="appsumo-products/$APPSUMO_PRODUCT"

echo "🚀 Setting up Blog integration for AppSumo product: $APPSUMO_PRODUCT"

# Check if product exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Product directory not found: $TARGET_DIR"
    echo "Available products:"
    ls appsumo-products/ | grep -v README
    exit 1
fi

# Create blog content directory
mkdir -p "$TARGET_DIR/content/blog/en"
mkdir -p "$TARGET_DIR/frontend/public/blog"

# Copy base blog configuration
cp -r "content/blog/sample-article.json" "$TARGET_DIR/content/blog/en/welcome-$APPSUMO_PRODUCT.json"

# Update tenant in sample article
sed -i.bak "s/\"tenant\": null/\"tenant\": \"$APPSUMO_PRODUCT\"/g" "$TARGET_DIR/content/blog/en/welcome-$APPSUMO_PRODUCT.json"
sed -i.bak "s/Sample Article/Welcome to $APPSUMO_PRODUCT Blog/g" "$TARGET_DIR/content/blog/en/welcome-$APPSUMO_PRODUCT.json"
sed -i.bak "s/sample-article/welcome-$APPSUMO_PRODUCT/g" "$TARGET_DIR/content/blog/en/welcome-$APPSUMO_PRODUCT.json"

# Create tenant-specific package.json scripts
cat > "$TARGET_DIR/frontend/package-blog.json" << EOF
{
  "scripts": {
    "blog:translate": "node ../../../scripts/blog-translate.mjs --tenant=$APPSUMO_PRODUCT",
    "blog:index": "node ../../../scripts/blog-build-index.mjs --tenant=$APPSUMO_PRODUCT",
    "blog:rss": "node ../../../scripts/blog-rss.mjs --tenant=$APPSUMO_PRODUCT",
    "blog:build": "npm run blog:translate && npm run blog:index && npm run blog:rss",
    "seo:generate": "node ../../../scripts/generate-sitemaps.mjs --tenant=$APPSUMO_PRODUCT"
  }
}
EOF

# Create .env template
cat > "$TARGET_DIR/.env.blog.example" << EOF
# Blog System Environment Variables for $APPSUMO_PRODUCT

# Translation APIs (choose one or both)
DEEPL_API_KEY=your_deepl_api_key_here
GOOGLE_API_KEY=your_google_translate_api_key_here

# Site Configuration
VITE_SITE_URL=https://$APPSUMO_PRODUCT.forensics.ai
VITE_TENANT=$APPSUMO_PRODUCT

# Content Settings
BLOG_LANGS=en,de,fr,es  # Languages to generate for this tenant
BLOG_TENANT=$APPSUMO_PRODUCT

# Deployment
DEPLOY_TARGET=netlify  # netlify, vercel, cloudflare
DEPLOY_SITE_ID=your_deployment_site_id

# Analytics (optional)
GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
EOF

# Create tenant-specific README
cat > "$TARGET_DIR/BLOG_README.md" << EOF
# Blog System for $APPSUMO_PRODUCT

This directory contains the blog integration for the $APPSUMO_PRODUCT AppSumo product.

## Directory Structure

\`\`\`
$TARGET_DIR/
├── content/blog/           # Blog articles (English originals)
│   └── en/
├── frontend/public/blog/   # Generated translations & feeds
├── .env.blog.example       # Environment variables template
└── BLOG_README.md          # This file
\`\`\`

## Setup

1. **Copy environment variables:**
   \`\`\`bash
   cp .env.blog.example .env.local
   \`\`\`

2. **Edit environment variables:**
   - Set API keys for translation
   - Configure VITE_SITE_URL for your domain
   - Adjust BLOG_LANGS for supported languages

3. **Create your first article:**
   Edit \`content/blog/en/welcome-$APPSUMO_PRODUCT.json\` or create new articles.

4. **Build the blog:**
   \`\`\`bash
   # From $TARGET_DIR/frontend/
   npm run --package=../package-blog.json blog:build

   # Or manually:
   BLOG_TENANT=$APPSUMO_PRODUCT node ../../../../scripts/blog-translate.mjs
   BLOG_TENANT=$APPSUMO_PRODUCT node ../../../../scripts/blog-build-index.mjs
   BLOG_TENANT=$APPSUMO_PRODUCT node ../../../../scripts/blog-rss.mjs
   \`\`\`

## URLs

- **Blog List:** \`/en/projects/$APPSUMO_PRODUCT/blog\`
- **Article:** \`/en/projects/$APPSUMO_PRODUCT/blog/article-slug\`
- **RSS Feed:** \`/blog/rss-en.xml\`
- **Sitemap:** \`/sitemap-en.xml\`

## Deployment

The blog system generates static files that can be deployed to any CDN:

\`\`\`bash
# Build frontend with blog
npm run build:optimized

# Files are generated in frontend/dist/
# Deploy the dist/ directory to your CDN
\`\`\`

## Customization

### Branding
- Update colors in \`frontend/src/styles/\`
- Add logo to \`frontend/public/images/\`
- Customize meta tags in blog components

### Languages
- Add new locales to \`frontend/src/locales/\`
- Update BLOG_LANGS in .env
- Run translation for new languages

### Content
- Articles are stored as JSON in \`content/blog/en/\`
- All fields are documented in the main blog manual
- Use \`tenant: "$APPSUMO_PRODUCT"\` for tenant-specific articles

## Support

- **Main Documentation:** \`../../../docs/blog-system-manual.md\`
- **CI/CD Runbook:** \`../../../docs/blog-ci-cd-runbook.md\`
- **Issues:** Create GitHub issues with label 'blog'

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| \`DEEPL_API_KEY\` | DeepL API key for translations | No* |
| \`GOOGLE_API_KEY\` | Google Translate API key | No* |
| \`VITE_SITE_URL\` | Your domain URL | Yes |
| \`BLOG_LANGS\` | Languages to generate (comma-separated) | No |
| \`BLOG_TENANT\` | Tenant identifier | Yes |

*At least one translation API key required for multi-language support
EOF

# Create symlink to main scripts for convenience
ln -sf "../../../scripts" "$TARGET_DIR/scripts"

# Update main .gitignore to exclude tenant-specific files
if ! grep -q "appsumo-products/*/frontend/public/blog/" .gitignore; then
    echo "# AppSumo tenant blog files" >> .gitignore
    echo "appsumo-products/*/frontend/public/blog/" >> .gitignore
    echo "appsumo-products/*/.env.blog.local" >> .gitignore
fi

echo "✅ Blog integration setup completed for $APPSUMO_PRODUCT"
echo ""
echo "📝 Next steps:"
echo "1. Copy .env.blog.example to .env.local and configure"
echo "2. Edit the sample article in content/blog/en/"
echo "3. Run 'npm run blog:build' from frontend/"
echo "4. Read BLOG_README.md for detailed instructions"
echo ""
echo "📚 Documentation:"
echo "- Main manual: docs/blog-system-manual.md"
echo "- CI/CD: docs/blog-ci-cd-runbook.md"
echo "- Tenant README: $TARGET_DIR/BLOG_README.md"
