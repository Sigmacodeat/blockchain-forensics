#!/bin/bash
# Production Console.log Cleanup Script
# Entfernt console.log statements, behält aber console.error/warn in kritischen Files

echo "🧹 Removing console.log statements from production build..."

# Exclude error boundaries and critical debug files
EXCLUDE_PATTERN="ErrorBoundary|ChatErrorBoundary|error-handler"

find src -type f \( -name "*.tsx" -o -name "*.ts" \) \
  ! -path "*/node_modules/*" \
  ! -name "*.test.*" \
  ! -name "*.spec.*" \
  | while read -r file; do
    # Skip excluded files
    if echo "$file" | grep -qE "$EXCLUDE_PATTERN"; then
      continue
    fi
    
    # Remove console.log but keep console.error and console.warn
    if grep -q "console\.log" "$file"; then
      # Comment out console.log lines instead of removing (safer)
      sed -i.bak '/console\.log/s/^/\/\/ PROD: /' "$file" && rm -f "${file}.bak"
      echo "  Cleaned: $file"
    fi
  done

echo "✅ Console.log cleanup complete!"
echo "Note: console.error and console.warn statements kept for debugging"
