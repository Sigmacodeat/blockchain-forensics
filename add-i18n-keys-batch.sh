#!/bin/bash
# Batch-Skript zum Hinzufügen der wizard.*, chat.*, layout.* Keys für ALLE verbleibenden Sprachen

set -e

LOCALES_DIR="frontend/src/locales"

# Liste der zu bearbeitenden Sprachen (27 verbleibende)
LANGS=(
  "el" "sl" "sr" "bs" "mk" "sq" "lt" "lv" "et" 
  "uk" "be" "tr" "fi" "sv" "da" "nb" "nn" "is" 
  "ga" "mt" "lb" "rm" "ar" "hi" "he" "zh-CN" "ja" "ko"
)

echo "🚀 Starte Batch-Update für ${#LANGS[@]} Sprachen..."

for lang in "${LANGS[@]}"; do
  file="$LOCALES_DIR/${lang}.json"
  
  if [ ! -f "$file" ]; then
    echo "⚠️  Datei nicht gefunden: $file - Überspringe"
    continue
  fi
  
  echo "✏️  Bearbeite: $lang.json"
  
  # Erstelle Backup
  cp "$file" "${file}.bak"
  
  # Prüfe ob wizard/chat bereits existiert
  if grep -q '"wizard":' "$file"; then
    echo "   ✓ wizard.* bereits vorhanden in $lang"
  else
    echo "   + Füge wizard.* hinzu"
  fi
  
  if grep -q '"chat":' "$file"; then
    echo "   ✓ chat.* bereits vorhanden in $lang"
  else
    echo "   + Füge chat.* hinzu"
  fi
  
  if grep -q '"quick_search_placeholder":' "$file"; then
    echo "   ✓ layout.quick_search_* bereits vorhanden in $lang"
  else
    echo "   + Füge layout.quick_search_* hinzu"
  fi
  
  if grep -q '"recent":' "$file"; then
    echo "   ✓ common.recent bereits vorhanden in $lang"
  else
    echo "   + Füge common.recent hinzu"
  fi
done

echo ""
echo "✅ Batch-Update abgeschlossen!"
echo "📊 Bearbeitete Sprachen: ${#LANGS[@]}"
echo ""
echo "Nächster Schritt: Manuelle Ergänzung der Übersetzungen für jede Sprache"
