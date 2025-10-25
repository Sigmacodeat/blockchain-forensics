#!/usr/bin/env node
/**
 * Merge analytics.json into main translation.json files
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const LOCALES_DIR = path.join(__dirname, '../public/locales');

const LANGUAGES = [
  'en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'pl', 'cs', 'ru', 'uk', 'sv', 
  'da', 'no', 'fi', 'el', 'tr', 'ar', 'he', 'ja', 'ko', 'zh', 'zh-TW', 'hi'
];

let mergedCount = 0;

LANGUAGES.forEach(lang => {
  const analyticsPath = path.join(LOCALES_DIR, lang, 'analytics.json');
  const mainPath = path.join(LOCALES_DIR, `${lang}.json`);
  
  // Skip if analytics.json doesn't exist
  if (!fs.existsSync(analyticsPath)) {
    return;
  }
  
  // Read both files
  const analyticsData = JSON.parse(fs.readFileSync(analyticsPath, 'utf-8'));
  let mainData = {};
  
  if (fs.existsSync(mainPath)) {
    mainData = JSON.parse(fs.readFileSync(mainPath, 'utf-8'));
  }
  
  // Merge analytics into main
  mainData = { ...mainData, ...analyticsData };
  
  // Write back
  fs.writeFileSync(mainPath, JSON.stringify(mainData, null, 2), 'utf-8');
  mergedCount++;
  console.log(`✓ Merged ${lang}/analytics.json → ${lang}.json`);
});

console.log(`\n✅ Merged analytics for ${mergedCount} languages!`);
