#!/usr/bin/env node

/**
 * Findet hardcodierten deutschen Text in React-Komponenten
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { glob } from 'glob';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_DIR = path.join(__dirname, '../frontend/src');

// Deutsche Wörter als Indikatoren
const GERMAN_INDICATORS = [
  'Förderung', 'Mio', 'Businessplan', 'Österreichische',
  'Geschäftsführung', 'zusätzliche', 'Laufzeit', 'Fördergeber',
  'Volumen', 'Quote', 'weibliche', 'Geschäftsführung',
  'Fördereinreichung', 'gesteigert', 'Bereit für'
];

async function findHardcodedText() {
  console.log('🔍 Suche nach hardcodiertem deutschen Text\n');
  console.log('=' .repeat(60));
  
  // Finde alle .tsx und .ts Dateien (außer .d.ts)
  const files = await glob('**/*.{ts,tsx}', {
    cwd: FRONTEND_DIR,
    ignore: ['**/*.d.ts', '**/node_modules/**', '**/dist/**', '**/build/**'],
    absolute: true
  });
  
  const filesWithHardcodedText = new Map();
  
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf-8');
    const lines = content.split('\n');
    
    const matches = [];
    
    lines.forEach((line, index) => {
      // Skip Kommentare
      if (line.trim().startsWith('//') || line.trim().startsWith('*')) {
        return;
      }
      
      // Prüfe auf deutsche Indikatoren
      for (const indicator of GERMAN_INDICATORS) {
        if (line.includes(indicator)) {
          // Prüfe ob es NICHT in t('...') ist
          const tFunctionRegex = /t\s*\(\s*['"]/g;
          const indicatorIndex = line.indexOf(indicator);
          
          // Finde den nächsten t(' vor dem Indicator
          let hasTFunction = false;
          const beforeIndicator = line.substring(0, indicatorIndex);
          
          if (beforeIndicator.match(tFunctionRegex)) {
            // Prüfe ob der Indicator innerhalb eines t() Calls ist
            const openParens = (beforeIndicator.match(/t\s*\(/g) || []).length;
            const closeParens = (beforeIndicator.match(/\)/g) || []).length;
            
            if (openParens > closeParens) {
              hasTFunction = true;
            }
          }
          
          if (!hasTFunction) {
            matches.push({
              line: index + 1,
              content: line.trim(),
              indicator
            });
            break; // Nur ein Match pro Zeile
          }
        }
      }
    });
    
    if (matches.length > 0) {
      const relativePath = path.relative(FRONTEND_DIR, file);
      filesWithHardcodedText.set(relativePath, matches);
    }
  }
  
  // Ergebnisse ausgeben
  if (filesWithHardcodedText.size === 0) {
    console.log('\n✅ Keine hardcodierten deutschen Texte gefunden!\n');
    return;
  }
  
  console.log(`\n🚨 ${filesWithHardcodedText.size} Dateien mit hardcodiertem Text gefunden:\n`);
  
  for (const [file, matches] of filesWithHardcodedText.entries()) {
    console.log(`\n📄 ${file} (${matches.length} Zeilen)`);
    console.log('─'.repeat(60));
    
    matches.slice(0, 5).forEach(match => {
      console.log(`   Zeile ${match.line}: ${match.content.substring(0, 80)}...`);
    });
    
    if (matches.length > 5) {
      console.log(`   ... und ${matches.length - 5} weitere Zeilen`);
    }
  }
  
  // Zusammenfassung
  console.log('\n' + '='.repeat(60));
  console.log('\n📊 ZUSAMMENFASSUNG\n');
  
  const totalMatches = Array.from(filesWithHardcodedText.values())
    .reduce((sum, matches) => sum + matches.length, 0);
  
  console.log(`Betroffene Dateien: ${filesWithHardcodedText.size}`);
  console.log(`Gesamt Zeilen mit hardcodiertem Text: ${totalMatches}`);
  
  // Top-Dateien
  console.log('\n🔥 TOP 5 DATEIEN:\n');
  
  const sortedFiles = Array.from(filesWithHardcodedText.entries())
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 5);
  
  sortedFiles.forEach(([file, matches]) => {
    console.log(`   ${matches.length} Zeilen: ${file}`);
  });
  
  // Speichere detaillierten Report
  const report = {
    timestamp: new Date().toISOString(),
    filesChecked: files.length,
    filesWithHardcodedText: filesWithHardcodedText.size,
    totalMatches,
    details: Object.fromEntries(filesWithHardcodedText)
  };
  
  const reportPath = path.join(__dirname, '../I18N_HARDCODED_TEXT_REPORT.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  console.log(`\n💾 Detaillierter Report: ${reportPath}`);
  console.log('\n⚠️  Bitte diese Texte mit i18n-Keys ersetzen!');
}

findHardcodedText().catch(err => {
  console.error('❌ Fehler:', err);
  process.exit(1);
});
