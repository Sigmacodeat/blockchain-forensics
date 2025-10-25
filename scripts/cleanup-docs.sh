#!/bin/bash
# Documentation Cleanup Script
# Verschiebt redundante MD-Dateien ins Archiv

set -e

ARCHIVE_DIR="docs/archive"
ROOT_DIR="/Users/msc/CascadeProjects/blockchain-forensics"

echo "📦 Creating archive directory..."
mkdir -p "$ROOT_DIR/$ARCHIVE_DIR"

# Keep these essential files in root
KEEP_FILES=(
  "README.md"
  "LICENSE.md"
  "CONTRIBUTING.md"
  "CHANGELOG.md"
  "SECURITY.md"
  "CODE_OF_CONDUCT.md"
)

# Create pattern for grep
KEEP_PATTERN=$(printf "|%s" "${KEEP_FILES[@]}")
KEEP_PATTERN=${KEEP_PATTERN:1}  # Remove leading |

echo "🔍 Identifying files to archive..."
cd "$ROOT_DIR"

MOVED_COUNT=0
for file in *.md; do
  # Skip if file doesn't exist (e.g., no .md files)
  [ -e "$file" ] || continue
  
  # Skip if in keep list
  if echo "$file" | grep -qE "^($KEEP_PATTERN)$"; then
    echo "  ✓ Keeping: $file"
    continue
  fi
  
  # Move to archive
  mv "$file" "$ARCHIVE_DIR/"
  MOVED_COUNT=$((MOVED_COUNT + 1))
  
  # Log every 50 files
  if [ $((MOVED_COUNT % 50)) -eq 0 ]; then
    echo "  Archived $MOVED_COUNT files..."
  fi
done

echo ""
echo "✅ Cleanup complete!"
echo "   Archived: $MOVED_COUNT files"
echo "   Kept in root: ${#KEEP_FILES[@]} essential files"
echo ""
echo "📋 Archive location: $ARCHIVE_DIR"

# Create archive index
echo "📝 Creating archive index..."
cat > "$ARCHIVE_DIR/INDEX.md" << 'EOF'
# Documentation Archive

This directory contains historical documentation files that were moved from the project root during cleanup.

## Organization

These files document various development milestones, feature implementations, and project status reports from October 2025.

## Categories

- **Implementation Status**: Files starting with `*_COMPLETE.md`, `*_READY.md`
- **Feature Documentation**: `AI_*`, `CHATBOT_*`, `WALLET_*`, etc.
- **Business Plans**: `APPSUMO_*`, `BUSINESS_*`, `SALES_*`
- **Technical Guides**: `*_GUIDE.md`, `*_SETUP.md`

## Finding Documents

Use `grep -r "keyword" .` to search across all archived documents.

---

**Last updated**: $(date -u +"%Y-%m-%d %H:%M UTC")
**Total archived files**: $MOVED_COUNT
EOF

echo "✅ Archive index created: $ARCHIVE_DIR/INDEX.md"
echo ""
echo "🎯 Root directory is now clean and production-ready!"
