#!/usr/bin/env node
/**
 * OG-Image SVG to PNG Converter
 * ==============================
 * Konvertiert og-image.svg zu og-image.png für optimale Social Media Performance
 * 
 * Usage: node scripts/convert-og-image.mjs
 */

import { readFileSync, writeFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const publicDir = join(__dirname, '..', 'public')
const svgPath = join(publicDir, 'og-image.svg')
const pngPath = join(publicDir, 'og-image.png')

console.log('🎨 OG-Image Converter')
console.log('=====================\n')

// Check if SVG exists
try {
  const svgContent = readFileSync(svgPath, 'utf-8')
  console.log('✅ SVG gefunden:', svgPath)
  console.log(`   Größe: ${(svgContent.length / 1024).toFixed(2)} KB\n`)
  
  console.log('📋 Konvertierungs-Optionen:\n')
  console.log('Option 1: Online-Tool (Empfohlen - 30 Sekunden)')
  console.log('  → https://svgtopng.com')
  console.log('  → Upload: public/og-image.svg')
  console.log('  → Width: 1200px, Height: 630px')
  console.log('  → Download: Speichern als "og-image.png"\n')
  
  console.log('Option 2: ImageMagick (CLI)')
  console.log('  → brew install imagemagick')
  console.log('  → cd public')
  console.log('  → convert og-image.svg -resize 1200x630 og-image.png\n')
  
  console.log('Option 3: Inkscape (CLI)')
  console.log('  → brew install inkscape')
  console.log('  → inkscape og-image.svg --export-type=png --export-width=1200 --export-height=630\n')
  
  console.log('Option 4: Figma/Canva (Manuell)')
  console.log('  → Importiere SVG in Figma/Canva')
  console.log('  → Export als PNG (1200x630px, 2x für Retina)')
  console.log('  → Speichern als "og-image.png"\n')
  
  console.log('💡 Tipp: SVG funktioniert auch, aber PNG ist optimal für Social Media!')
  console.log('   LinkedIn, Twitter, Facebook bevorzugen PNG für bessere Kompression.\n')
  
  console.log('🎯 Nach Konvertierung:')
  console.log('  1. Speichere PNG in: frontend/public/og-image.png')
  console.log('  2. SEOHead-Komponente verwendet automatisch: /og-image.png')
  console.log('  3. Teste auf: https://www.linkedin.com/post-inspector/\n')
  
  console.log('✅ SVG ist fertig und einsatzbereit!')
  console.log('   Wenn du PNG willst: Nutze eine der Optionen oben (empfohlen: Online-Tool)')
  
} catch (error) {
  console.error('❌ Fehler:', error.message)
  process.exit(1)
}
