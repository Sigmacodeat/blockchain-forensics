#!/usr/bin/env node
/**
 * DEEP SCAN: Prüft ALLE Keys in ALLEN 42 Sprachen
 * Findet englische Fallbacks in JEDER Sprache
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOCALES_DIR = path.join(__dirname, '../frontend/src/locales');

// Englische Wörter/Phrasen die NICHT in anderen Sprachen sein sollten
const ENGLISH_INDICATORS = [
  'Business Plan', 'Funding Rate', 'Duration', 'Total Funding',
  'View', 'Dashboard', 'Settings', 'Search', 'Loading',
  'Error', 'Success', 'Cancel', 'Save', 'Delete',
  'Enterprise', 'Professional', 'Community', 'Free',
  'Quick search', 'Open with', 'Tip:'
];

// Ausnahmen: Begriffe die in vielen Sprachen gleich sind
const ALLOWED_ENGLISH = [
  'Email', 'PDF', 'CSV', 'API', 'OAuth', 'JWT', 'ID',
  'Pro', 'Plus', 'Enterprise', 'AI', 'ML', 'KYT', 'DeFi',
  'Web3', 'NFT', 'DAO', 'ETH', 'BTC', 'USDT'
];

function deepScanObject(obj, path = '', lang = '') {
  const issues = [];
  
  for (const [key, value] of Object.entries(obj)) {
    const currentPath = path ? `${path}.${key}` : key;
    
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      issues.push(...deepScanObject(value, currentPath, lang));
    } else if (typeof value === 'string') {
      // Prüfe auf englische Indikatoren
      for (const indicator of ENGLISH_INDICATORS) {
        if (value.includes(indicator)) {
          // Prüfe ob es eine erlaubte Ausnahme ist
          const isAllowed = ALLOWED_ENGLISH.some(allowed => 
            value === allowed || value.includes(`(${allowed})`)
          );
          
          if (!isAllowed) {
            issues.push({
              path: currentPath,
              value: value.substring(0, 80),
              indicator
            });
          }
        }
      }
    }
  }
  
  return issues;
}

const ALL_LANGUAGES = [
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'pl', name: 'Polski', flag: '🇵🇱' },
  { code: 'cs', name: 'Čeština', flag: '🇨🇿' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'sv', name: 'Svenska', flag: '🇸🇪' },
  { code: 'da', name: 'Dansk', flag: '🇩🇰' },
  { code: 'fi', name: 'Suomi', flag: '🇫🇮' },
  { code: 'nb', name: 'Norsk Bokmål', flag: '🇳🇴' },
  { code: 'nn', name: 'Norsk Nynorsk', flag: '🇳🇴' },
  { code: 'is', name: 'Íslenska', flag: '🇮🇸' },
  { code: 'ga', name: 'Gaeilge', flag: '🇮🇪' },
  { code: 'lb', name: 'Lëtzebuergesch', flag: '🇱🇺' },
  { code: 'rm', name: 'Rumantsch', flag: '🇨🇭' },
  { code: 'ro', name: 'Română', flag: '🇷🇴' },
  { code: 'bg', name: 'Български', flag: '🇧🇬' },
  { code: 'el', name: 'Ελληνικά', flag: '🇬🇷' },
  { code: 'uk', name: 'Українська', flag: '🇺🇦' },
  { code: 'be', name: 'Беларуская', flag: '🇧🇾' },
  { code: 'hu', name: 'Magyar', flag: '🇭🇺' },
  { code: 'sk', name: 'Slovenčina', flag: '🇸🇰' },
  { code: 'sl', name: 'Slovenščina', flag: '🇸🇮' },
  { code: 'sq', name: 'Shqip', flag: '🇦🇱' },
  { code: 'sr', name: 'Српски', flag: '🇷🇸' },
  { code: 'bs', name: 'Bosanski', flag: '🇧🇦' },
  { code: 'mk', name: 'Македонски', flag: '🇲🇰' },
  { code: 'mt', name: 'Malti', flag: '🇲🇹' },
  { code: 'lt', name: 'Lietuvių', flag: '🇱🇹' },
  { code: 'lv', name: 'Latviešu', flag: '🇱🇻' },
  { code: 'et', name: 'Eesti', flag: '🇪🇪' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
  { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'he', name: 'עברית', flag: '🇮🇱' }
];

console.log('🔍 DEEP SCAN: Prüfe ALLE Keys in ALLEN 42 Sprachen\n');
console.log('=' .repeat(70));

const results = [];
let totalIssues = 0;

for (const lang of ALL_LANGUAGES) {
  const filePath = path.join(LOCALES_DIR, `${lang.code}.json`);
  
  if (!fs.existsSync(filePath)) {
    console.log(`${lang.flag} ${lang.name} (${lang.code}): ⚠️  DATEI FEHLT`);
    results.push({ lang, status: 'missing', issues: [] });
    continue;
  }
  
  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    // Englisch überspringen (ist die Original-Sprache)
    if (lang.code === 'en') {
      console.log(`${lang.flag} ${lang.name} (${lang.code}): ✅ OK (Original-Sprache)`);
      results.push({ lang, status: 'ok', issues: [], isOriginal: true });
      continue;
    }
    
    // Deep Scan
    const issues = deepScanObject(data, '', lang.code);
    
    if (issues.length === 0) {
      console.log(`${lang.flag} ${lang.name} (${lang.code}): ✅ OK`);
      results.push({ lang, status: 'ok', issues: [] });
    } else {
      console.log(`${lang.flag} ${lang.name} (${lang.code}): ❌ ${issues.length} PROBLEME`);
      
      // Zeige erste 3 Probleme
      issues.slice(0, 3).forEach(issue => {
        console.log(`   → ${issue.path}: "${issue.value}" (enthält "${issue.indicator}")`);
      });
      
      if (issues.length > 3) {
        console.log(`   ... und ${issues.length - 3} weitere`);
      }
      
      results.push({ lang, status: 'issues', issues });
      totalIssues += issues.length;
    }
  } catch (err) {
    console.log(`${lang.flag} ${lang.name} (${lang.code}): ❌ FEHLER: ${err.message}`);
    results.push({ lang, status: 'error', issues: [], error: err.message });
  }
}

// Zusammenfassung
console.log('\n' + '='.repeat(70));
console.log('\n📊 ZUSAMMENFASSUNG\n');

const ok = results.filter(r => r.status === 'ok').length;
const withIssues = results.filter(r => r.status === 'issues').length;
const errors = results.filter(r => r.status === 'error').length;
const missing = results.filter(r => r.status === 'missing').length;

console.log(`✅ OK: ${ok}/42 (inkl. EN als Original)`);
console.log(`❌ Mit Problemen: ${withIssues}/42`);
console.log(`⚠️  Fehler: ${errors}/42`);
console.log(`⚠️  Fehlend: ${missing}/42`);
console.log(`\n📝 Gesamt gefundene Probleme: ${totalIssues}`);

if (withIssues > 0) {
  console.log('\n🔥 SPRACHEN MIT PROBLEMEN:\n');
  results.filter(r => r.status === 'issues').forEach(r => {
    console.log(`${r.lang.flag} ${r.lang.name} (${r.lang.code}): ${r.issues.length} Probleme`);
  });
}

// Speichere detaillierten Report
const report = {
  timestamp: new Date().toISOString(),
  summary: { ok, withIssues, errors, missing, totalIssues },
  results: results.map(r => ({
    code: r.lang.code,
    name: r.lang.name,
    status: r.status,
    issueCount: r.issues?.length || 0,
    issues: r.issues?.slice(0, 10) // Nur erste 10 pro Sprache
  }))
};

const reportPath = path.join(__dirname, '../I18N_DEEP_SCAN_REPORT.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

console.log(`\n💾 Detaillierter Report: ${reportPath}`);

if (withIssues === 0 && errors === 0 && missing === 0) {
  console.log('\n🎉 PERFEKT: Alle 42 Sprachen sind 100% nativ!');
  process.exit(0);
} else {
  console.log('\n⚠️  Es gibt noch Probleme zu beheben!');
  process.exit(1);
}
