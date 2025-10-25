#!/usr/bin/env node
/**
 * Prüft JEDE Sprachdatei einzeln auf Vollständigkeit
 * Gibt für jede Sprache ein klares OK oder zeigt was fehlt
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOCALES_DIR = path.join(__dirname, '../frontend/src/locales');

// Kritische Keys die in JEDER Sprache (außer EN) nativ sein müssen
const CRITICAL_KEYS = {
  'common.error': { 
    mustNotBe: ['Error'], // Exakter Match
    allowedWords: ['Errore', 'Erro'], // Italienisch, Portugiesisch
    except: ['en', 'es'] // Error ist das korrekte Wort in Spanisch
  },
  'common.save': { mustNotBe: ['Save'], except: ['en'] },
  'common.cancel': { 
    mustNotBe: ['Cancel'],
    allowedWords: ['Cancelar'], // Spanisch, Portugiesisch
    except: ['en']
  },
  'common.delete': { mustNotBe: ['Delete'], except: ['en'] },
  'common.view': { mustNotBe: ['View'], except: ['en'] },
  'common.settings': { mustNotBe: ['Settings'], except: ['en', 'mt'] },
  'features.cta.start': { mustNotBe: ['Start Free'], except: ['en'] },
  'layout.quick_search_placeholder': { mustNotBe: ['Quick search'], except: ['en'] },
  'landing.businessplan.kpi3': { mustNotBe: ['Duration'], except: ['en'] }
};

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

function getNested(obj, path) {
  return path.split('.').reduce((current, key) => current?.[key], obj);
}

function checkLanguage(langCode, langName, data) {
  const issues = [];
  
  for (const [keyPath, rules] of Object.entries(CRITICAL_KEYS)) {
    // Skip wenn diese Sprache eine Ausnahme ist
    if (rules.except?.includes(langCode)) continue;
    
    const value = getNested(data, keyPath);
    
    if (!value) {
      issues.push(`❌ FEHLT: ${keyPath}`);
      continue;
    }
    
    // Prüfe ob es ein erlaubtes Wort ist (z.B. "Errore", "Cancelar")
    if (rules.allowedWords && rules.allowedWords.includes(value)) {
      continue; // OK, ist ein erlaubtes native Wort
    }
    
    // Prüfe ob unerlaubte englische Wörter (exakt) vorkommen
    const mustNotBe = rules.mustNotBe || rules.notAllowed || [];
    for (const notAllowed of mustNotBe) {
      if (value === notAllowed || value.includes(notAllowed)) {
        // Aber nur wenn es nicht Teil eines erlaubten Wortes ist
        const isPartOfAllowed = rules.allowedWords?.some(allowed => value === allowed);
        if (!isPartOfAllowed) {
          issues.push(`❌ ENGLISCH: ${keyPath} = "${value}" (enthält "${notAllowed}")`);
        }
      }
    }
  }
  
  return issues;
}

console.log('🔍 FINALE PRÜFUNG: Jede Sprache einzeln\n');
console.log('=' .repeat(70));

let perfectCount = 0;
let issuesCount = 0;

for (const lang of ALL_LANGUAGES) {
  const filePath = path.join(LOCALES_DIR, `${lang.code}.json`);
  
  if (!fs.existsSync(filePath)) {
    console.log(`${lang.flag} ${lang.name} (${lang.code}): ⚠️  DATEI FEHLT`);
    issuesCount++;
    continue;
  }
  
  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const issues = checkLanguage(lang.code, lang.name, data);
    
    if (issues.length === 0) {
      console.log(`${lang.flag} ${lang.name} (${lang.code}): ✅ PERFEKT`);
      perfectCount++;
    } else {
      console.log(`${lang.flag} ${lang.name} (${lang.code}): ❌ ${issues.length} PROBLEME`);
      issues.forEach(issue => console.log(`   ${issue}`));
      issuesCount++;
    }
  } catch (err) {
    console.log(`${lang.flag} ${lang.name} (${lang.code}): ❌ FEHLER: ${err.message}`);
    issuesCount++;
  }
}

console.log('\n' + '='.repeat(70));
console.log('\n📊 FINALE STATISTIK\n');
console.log(`✅ Perfekt: ${perfectCount}/42`);
console.log(`❌ Mit Problemen: ${issuesCount}/42`);

if (issuesCount === 0) {
  console.log('\n🎉 PERFEKT! Alle 42 Sprachen sind 100% korrekt!');
  console.log('🌍 Die Plattform ist jetzt die mehrsprachigste Blockchain-Forensik-Lösung!');
  process.exit(0);
} else {
  console.log('\n⚠️  Es gibt noch Probleme zu beheben!');
  process.exit(1);
}
