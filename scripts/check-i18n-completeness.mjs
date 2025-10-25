#!/usr/bin/env node

/**
 * Systematische Prüfung der i18n-Vollständigkeit
 * Findet fehlende Translation-Keys in allen Sprachdateien
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const LOCALES_DIR = path.join(__dirname, '../frontend/src/locales');
const REFERENCE_LANG = 'de'; // Deutsch als Referenz

// Alle unterstützten Sprachen
const LANGUAGES = [
  'en', 'de', 'es', 'fr', 'it', 'pt', 'nl', 'pl', 'cs', 'ru', 'sv', 'da', 'fi',
  'nb', 'nn', 'is', 'ga', 'lb', 'rm', 'ro', 'bg', 'el', 'uk', 'be', 'hu', 'sk',
  'sl', 'sq', 'sr', 'bs', 'mk', 'mt', 'lt', 'lv', 'et', 'ja', 'ko', 'zh-CN',
  'hi', 'tr', 'ar', 'he'
];

// Funktion zum Extrahieren aller Keys aus einem Objekt
function extractKeys(obj, prefix = '') {
  const keys = [];
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      keys.push(...extractKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  
  return keys;
}

// Hauptfunktion
async function checkCompleteness() {
  console.log('🔍 Systematische i18n-Vollständigkeitsprüfung\n');
  console.log('=' .repeat(60));
  
  // Referenz-Datei laden (Deutsch)
  const refPath = path.join(LOCALES_DIR, `${REFERENCE_LANG}.json`);
  
  if (!fs.existsSync(refPath)) {
    console.error(`❌ Referenz-Datei ${refPath} nicht gefunden!`);
    process.exit(1);
  }
  
  const refData = JSON.parse(fs.readFileSync(refPath, 'utf-8'));
  const refKeys = extractKeys(refData).sort();
  
  console.log(`\n📋 Referenz: ${REFERENCE_LANG}.json`);
  console.log(`   Gesamt Keys: ${refKeys.length}\n`);
  
  const missingByLang = {};
  let totalMissing = 0;
  
  // Alle Sprachen durchgehen
  for (const lang of LANGUAGES) {
    if (lang === REFERENCE_LANG) continue;
    
    const langPath = path.join(LOCALES_DIR, `${lang}.json`);
    
    if (!fs.existsSync(langPath)) {
      console.log(`⚠️  ${lang}.json nicht gefunden - wird übersprungen`);
      continue;
    }
    
    const langData = JSON.parse(fs.readFileSync(langPath, 'utf-8'));
    const langKeys = extractKeys(langData);
    const langKeysSet = new Set(langKeys);
    
    const missing = refKeys.filter(key => !langKeysSet.has(key));
    
    if (missing.length > 0) {
      missingByLang[lang] = missing;
      totalMissing += missing.length;
      
      console.log(`\n❌ ${lang}.json: ${missing.length} fehlende Keys`);
      
      // Zeige die ersten 10 fehlenden Keys
      const preview = missing.slice(0, 10);
      preview.forEach(key => console.log(`   - ${key}`));
      
      if (missing.length > 10) {
        console.log(`   ... und ${missing.length - 10} weitere`);
      }
    } else {
      console.log(`\n✅ ${lang}.json: Vollständig`);
    }
  }
  
  // Zusammenfassung
  console.log('\n' + '='.repeat(60));
  console.log('\n📊 ZUSAMMENFASSUNG\n');
  console.log(`Geprüfte Sprachen: ${LANGUAGES.length - 1} (ohne ${REFERENCE_LANG})`);
  console.log(`Sprachen mit fehlenden Keys: ${Object.keys(missingByLang).length}`);
  console.log(`Gesamt fehlende Übersetzungen: ${totalMissing}`);
  
  // Häufigste fehlende Keys
  console.log('\n🔥 HÄUFIGSTE FEHLENDE KEYS:\n');
  
  const keyFrequency = {};
  for (const [lang, keys] of Object.entries(missingByLang)) {
    for (const key of keys) {
      keyFrequency[key] = (keyFrequency[key] || 0) + 1;
    }
  }
  
  const sortedKeys = Object.entries(keyFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20);
  
  sortedKeys.forEach(([key, count]) => {
    console.log(`   ${key}: ${count} Sprachen`);
  });
  
  // Speichere detaillierte Analyse
  const report = {
    timestamp: new Date().toISOString(),
    reference: REFERENCE_LANG,
    totalKeys: refKeys.length,
    languages: LANGUAGES.length - 1,
    missingByLang,
    totalMissing,
    keyFrequency
  };
  
  const reportPath = path.join(__dirname, '../I18N_MISSING_KEYS_REPORT.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  console.log(`\n💾 Detaillierter Report gespeichert: ${reportPath}`);
  
  if (totalMissing > 0) {
    console.log('\n⚠️  Fehlende Übersetzungen gefunden!');
    process.exit(1);
  } else {
    console.log('\n✅ Alle Sprachen sind vollständig!');
    process.exit(0);
  }
}

checkCompleteness().catch(err => {
  console.error('❌ Fehler:', err);
  process.exit(1);
});
