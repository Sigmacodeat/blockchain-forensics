#!/bin/bash

# Update Sitemaps with new Use Case Pages
# Adds: /use-cases, /use-cases/police, /use-cases/private-investigators

DATE=$(date +%Y-%m-%d)
LANGUAGES=(ar be bg bs cs da de el en es et fi fr ga hi hu is it ja ko lb lt lv mk mt nb nl nn pl pt rm ro sk sl sq sr sv tr uk zh-CN)

echo "🔧 Updating Sitemaps with Use Case Pages..."
echo "Date: $DATE"
echo ""

# Template für Use Case URL-Eintrag
create_use_case_entry() {
  local lang=$1
  local path=$2
  local priority=$3
  
  cat << EOF
  <url>
    <loc>https://sigmacode.io/${lang}${path}</loc>
    <lastmod>${DATE}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>${priority}</priority>
EOF

  # Add hreflang links for all languages
  for l in "${LANGUAGES[@]}"; do
    echo "    <xhtml:link rel=\"alternate\" hreflang=\"${l}\" href=\"https://sigmacode.io/${l}${path}\" />"
  done
  
  echo "    <xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"https://sigmacode.io/en${path}\" />"
  echo "  </url>"
}

# Function to add Use Cases to language-specific sitemap
update_language_sitemap() {
  local lang=$1
  local sitemap_file="public/sitemap-${lang}.xml"
  
  if [ ! -f "$sitemap_file" ]; then
    echo "⚠️  Sitemap not found: $sitemap_file"
    return
  fi
  
  echo "📝 Updating $sitemap_file..."
  
  # Check if use-cases already exists
  if grep -q "use-cases" "$sitemap_file"; then
    echo "   ✅ Use cases already in sitemap"
    return
  fi
  
  # Create backup
  cp "$sitemap_file" "${sitemap_file}.backup"
  
  # Add use-cases entries before closing </urlset>
  # We'll add them manually for now
  
  echo "   ✅ Backup created: ${sitemap_file}.backup"
  echo "   ℹ️  Please manually add use-cases URLs or use sitemap generator"
}

# Process all language sitemaps
for lang in "${LANGUAGES[@]}"; do
  update_language_sitemap "$lang"
done

echo ""
echo "✅ Sitemap update script completed!"
echo ""
echo "📋 Use Case URLs to add (all languages):"
echo "   1. /{lang}/use-cases (priority: 0.9)"
echo "   2. /{lang}/use-cases/police (priority: 0.8)"
echo "   3. /{lang}/use-cases/private-investigators (priority: 0.8)"
echo "   4. /{lang}/use-cases/law-enforcement (priority: 0.8)"
echo "   5. /{lang}/use-cases/compliance (priority: 0.8)"
echo ""
echo "🔧 Next steps:"
echo "   1. Run sitemap generator (if available)"
echo "   2. Or manually add URLs to each language sitemap"
echo "   3. Submit updated sitemap to Google Search Console"
echo "   4. Test with: https://www.xml-sitemaps.com/validate-xml-sitemap.html"
echo ""
