#!/usr/bin/env node
/*
 Updates locale JSONs with keys found in TSX pages using t('key', 'Fallback').
 - Sources: LandingPage, FeaturesPage, AboutPage, PricingPage
 - Locales dir: frontend/src/locales/*.json
 - Behavior: for en.json use fallback as value if missing; for others copy en value when missing
*/
const fs = require('fs');
const path = require('path');

const projectRoot = process.cwd();
const sources = [
  'frontend/src/pages/LandingPage.tsx',
  'frontend/src/pages/FeaturesPage.tsx',
  'frontend/src/pages/AboutPage.tsx',
  'frontend/src/pages/PricingPage.tsx',
  'frontend/src/pages/LoginPage.tsx',
  'frontend/src/pages/RegisterPage.tsx',
  'frontend/src/pages/ForgotPasswordPage.tsx',
  'frontend/src/pages/AdminPage.tsx',
  'frontend/src/pages/MonitoringAlertsPage.tsx',
  'frontend/src/pages/MainDashboard.tsx',
  'frontend/src/pages/PerformanceDashboard.tsx',
  'frontend/src/pages/SecurityComplianceDashboard.tsx',
  'frontend/src/pages/GraphAnalyticsPage.tsx',
  'frontend/src/pages/WebAnalyticsPage.tsx',
];
const localesDir = 'frontend/src/locales';

function read(file) {
  return fs.readFileSync(path.join(projectRoot, file), 'utf8');
}

function ensureDeep(obj, keyPath) {
  const parts = keyPath.split('.');
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const p = parts[i];
    if (typeof cur[p] !== 'object' || cur[p] === null || Array.isArray(cur[p])) {
      cur[p] = {};
    }
    cur = cur[p];
  }
  return { parent: cur, last: parts[parts.length - 1] };
}

function setByPath(obj, keyPath, value) {
  const { parent, last } = ensureDeep(obj, keyPath);
  if (parent[last] === undefined) parent[last] = value;
}

function getByPath(obj, keyPath) {
  return keyPath.split('.').reduce((a, k) => (a && a[k] !== undefined ? a[k] : undefined), obj);
}

// Extract keys from code: t('key', 'Fallback') or t("key", "Fallback")
const keyMap = new Map(); // key -> fallback
const re = /\bt\(\s*['"]([A-Za-z0-9_.-]+)['"]\s*,\s*['"]([^'"\\]*?(?:\\.[^'"\\]*?)*?)['"]/g;
for (const rel of sources) {
  const code = read(rel);
  let m;
  while ((m = re.exec(code))) {
    const key = m[1];
    const fallbackRaw = m[2].replace(/\\"/g, '"').replace(/\\'/g, "'");
    if (!keyMap.has(key)) keyMap.set(key, fallbackRaw);
  }
}

// Load locales
const localeFiles = fs.readdirSync(path.join(projectRoot, localesDir)).filter(f => f.endsWith('.json'));
if (localeFiles.length === 0) {
  console.error('No locale JSON files found');
  process.exit(1);
}

function sortObjectKeysDeep(obj) {
  if (Array.isArray(obj)) return obj.map(sortObjectKeysDeep);
  if (obj && typeof obj === 'object') {
    const sorted = {};
    Object.keys(obj).sort().forEach(k => { sorted[k] = sortObjectKeysDeep(obj[k]); });
    return sorted;
  }
  return obj;
}

const enPath = path.join(projectRoot, localesDir, 'en.json');
const en = JSON.parse(fs.readFileSync(enPath, 'utf8'));
let enAdded = 0;
for (const [key, fallback] of keyMap.entries()) {
  if (getByPath(en, key) === undefined) {
    setByPath(en, key, fallback || key);
    enAdded++;
  }
}
fs.writeFileSync(enPath, JSON.stringify(sortObjectKeysDeep(en), null, 2) + '\n');

let totalAdded = enAdded;

for (const lf of localeFiles) {
  if (lf === 'en.json') continue;
  const p = path.join(projectRoot, localesDir, lf);
  const raw = fs.readFileSync(p, 'utf8');
  let obj;
  if (raw.trim() === 'SAME_AS_EN') {
    // Start with empty object and fill from en
    obj = {};
  } else {
    obj = JSON.parse(raw);
  }
  let added = 0;
  for (const [key] of keyMap.entries()) {
    if (getByPath(obj, key) === undefined) {
      const val = getByPath(en, key);
      setByPath(obj, key, val !== undefined ? val : key);
      added++;
    }
  }
  if (added > 0) {
    fs.writeFileSync(p, JSON.stringify(sortObjectKeysDeep(obj), null, 2) + '\n');
  }
  totalAdded += added;
  console.log(`${lf}: +${added}`);
}

console.log(`en.json: +${enAdded}`);
console.log(`total added: +${totalAdded}`);
