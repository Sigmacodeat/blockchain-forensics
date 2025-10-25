#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import process from 'process';

const root = process.cwd();
const localesDir = path.resolve(root, 'frontend', 'src', 'locales');
const usedKeysPath = null; // not needed, we will re-use extractor inline
const srcDir = path.resolve(root, 'frontend', 'src');

const fileGlobs = ['.ts', '.tsx'];

function walk(dir) {
  const res = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.')) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      res.push(...walk(p));
    } else if (fileGlobs.some(ext => e.name.endsWith(ext))) {
      res.push(p);
    }
  }
  return res;
}

function flatten(obj, prefix = '', out = {}) {
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      flatten(v, key, out);
    } else {
      out[key] = v;
    }
  }
  return out;
}

// Regex patterns for i18n keys
const patterns = [
  /\bt\(\s*['\"]([^'\"]+)['\"]/g,
  /\bi18n\.t\(\s*['\"]([^'\"]+)['\"]/g,
  /\bi18next\.t\(\s*['\"]([^'\"]+)['\"]/g,
  /i18nKey\s*=\s*['\"]([^'\"]+)['\"]/g,
];

function extractUsedKeys() {
  const files = walk(srcDir);
  const used = new Set();
  for (const f of files) {
    const txt = fs.readFileSync(f, 'utf8');
    for (const re of patterns) {
      let m;
      while ((m = re.exec(txt)) !== null) {
        if (m[1]) used.add(m[1]);
      }
    }
  }
  return used;
}

function readLocale(lang) {
  const fp = path.join(localesDir, `${lang}.json`);
  if (!fs.existsSync(fp)) return null;
  return JSON.parse(fs.readFileSync(fp, 'utf8'));
}

function main() {
  const base = (process.argv[2] || 'en').replace(/\.json$/, '');
  const langs = ['en','de'];
  const used = extractUsedKeys();
  const usedList = [...used].sort();

  const report = { used_count: used.size, base, langs: {} };

  for (const lang of langs) {
    const data = readLocale(lang);
    if (!data) { report.langs[lang] = { error: 'missing file' }; continue; }
    const flat = flatten(data);
    const keys = new Set(Object.keys(flat));
    const missing = usedList.filter(k => !keys.has(k));
    const extra = [...keys].filter(k => !used.has(k));
    report.langs[lang] = {
      total_keys: keys.size,
      missing_count: missing.length,
      extra_count: extra.length,
      missing_keys: missing,
      extra_sample: extra.sort().slice(0, 50)
    };
  }

  console.log(JSON.stringify(report, null, 2));
}

main();
