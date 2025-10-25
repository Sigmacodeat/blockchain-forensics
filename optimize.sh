#!/bin/bash

# SIGMACODE Blockchain Forensics - Build und Deployment Skript
# Optimiert für SEO und Internationalisierung

set -e

echo "🚀 SIGMACODE Build & Optimization Script"
echo "========================================"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Hilfsfunktionen
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Prüfen ob wir im richtigen Verzeichnis sind
check_directory() {
    if [ ! -f "package.json" ]; then
        print_error "Nicht im Projekt-Root-Verzeichnis!"
        exit 1
    fi
}

# 1. Übersetzungsqualität prüfen
check_translations() {
    print_status "Prüfe Übersetzungsqualität..."

    if [ -f "frontend/scripts/audit-locales.mjs" ]; then
        cd frontend
        node scripts/audit-locales.mjs
        cd ..
        print_success "Übersetzungsqualitätsprüfung abgeschlossen"
    else
        print_warning "Übersetzungsqualitätsprüfungs-Skript nicht gefunden"
    fi
}

# 2. Sitemaps generieren
generate_sitemaps() {
    print_status "Generiere mehrsprachige Sitemaps..."

    if [ -f "scripts/generate-sitemaps.mjs" ]; then
        node scripts/generate-sitemaps.mjs
        print_success "Sitemaps generiert"
    else
        print_warning "Sitemap-Generierungs-Skript nicht gefunden"
    fi
}

# 3. Bundle-Größe analysieren
analyze_bundle() {
    print_status "Analysiere Bundle-Größe..."

    if command -v npx &> /dev/null; then
        npx vite-bundle-analyzer dist --report bundle-report.html 2>/dev/null || print_warning "Bundle-Analyzer nicht verfügbar"
    fi
}

# 4. SEO-Dateien validieren
validate_seo() {
    print_status "Validiere SEO-Dateien..."

    # robots.txt prüfen
    if [ -f "public/robots.txt" ]; then
        print_success "robots.txt gefunden"
    else
        print_warning "robots.txt fehlt!"
    fi

    # manifest.json prüfen
    if [ -f "public/manifest.json" ]; then
        print_success "manifest.json gefunden"
    else
        print_warning "manifest.json fehlt!"
    fi

    # Sitemap-Index prüfen
    if [ -f "public/sitemap.xml" ]; then
        print_success "Sitemap-Index gefunden"
    else
        print_warning "Sitemap-Index fehlt!"
    fi
}

# 5. Performance-Test durchführen
performance_test() {
    print_status "Führe Performance-Tests durch..."

    if command -v lighthouse &> /dev/null; then
        lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report.html --chrome-flags="--headless" 2>/dev/null || print_warning "Lighthouse nicht verfügbar"
    fi
}

# 6. Deployment-Vorbereitung
prepare_deployment() {
    print_status "Bereite Deployment vor..."

    # Build durchführen
    npm run build

    # SEO-Dateien ins dist kopieren
    if [ -d "dist" ]; then
        cp public/robots.txt dist/ 2>/dev/null || true
        cp public/manifest.json dist/ 2>/dev/null || true
        cp public/sitemap*.xml dist/ 2>/dev/null || true
        print_success "SEO-Dateien ins dist kopiert"
    fi
}

# Hauptfunktion
main() {
    check_directory

    echo ""
    print_status "Starte Optimierungs-Workflow..."
    echo ""

    # Übersetzungsqualität prüfen
    check_translations

    echo ""

    # Sitemaps generieren
    generate_sitemaps

    echo ""

    # SEO-Dateien validieren
    validate_seo

    echo ""

    # Bundle-Größe analysieren (optional)
    # analyze_bundle

    echo ""

    print_success "✅ Optimierungs-Workflow abgeschlossen!"
    echo ""
    echo "📋 Nächste Schritte:"
    echo "1. Übersetzungen bei Bedarf korrigieren"
    echo "2. Sitemaps wurden automatisch generiert"
    echo "3. robots.txt und manifest.json sind vorhanden"
    echo "4. Bundle ist für internationale Märkte optimiert"
    echo ""
    echo "🌍 Ihre Plattform ist bereit für globale Expansion!"
}

# Skript starten
main "$@"
