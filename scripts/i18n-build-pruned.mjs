#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import process from 'process';

const root = process.cwd();
const srcDir = path.resolve(root, 'frontend', 'src');
const localesDir = path.resolve(srcDir, 'locales');

function walk(dir) {
  const res = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.')) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) res.push(...walk(p));
    else if (e.name.endsWith('.ts') || e.name.endsWith('.tsx')) res.push(p);
  }
  return res;
}

function flatten(obj, prefix = '', out = {}) {
  for (const [k, v] of Object.entries(obj || {})) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object' && !Array.isArray(v)) flatten(v, key, out);
    else out[key] = v;
  }
  return out;
}

function unflatten(flat) {
  const out = {};
  for (const [k, v] of Object.entries(flat)) {
    const parts = k.split('.');
    let cur = out;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) cur[part] = v;
      else cur = (cur[part] ||= {});
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
  return [...used].sort();
}

function readLocale(lang) {
  const fp = path.join(localesDir, `${lang}.json`);
  if (!fs.existsSync(fp)) return {};
  return JSON.parse(fs.readFileSync(fp, 'utf8'));
}

function buildPruned(baseLang = 'en', otherLangs = ['de']) {
  const usedKeys = extractUsedKeys();
  const base = flatten(readLocale(baseLang));
  const out = {};
  out[baseLang] = {};
  for (const lang of otherLangs) out[lang] = {};

  for (const key of usedKeys) {
    // Base value
    const baseVal = key in base ? base[key] : key; // fallback to key string
    out[baseLang][key] = baseVal;

    for (const lang of otherLangs) {
      const flat = flatten(readLocale(lang));
      let val;
      if (key in flat) val = flat[key];
      else val = baseVal; // fallback to base
      out[lang][key] = val;
    }
  }

  // Write pruned files
  const stats = {};
  for (const [lang, flat] of Object.entries(out)) {
    const obj = unflatten(flat);
    const target = path.join(localesDir, `${lang}.pruned.json`);
    fs.writeFileSync(target, JSON.stringify(obj, null, 2) + '\n', 'utf8');
    stats[lang] = { keys: Object.keys(flat).length, file: target };
  }
  return { used: usedKeys.length, stats };
}

function main() {
  const base = (process.argv[2] || 'en').replace(/\.json$/, '');
  const other = (process.argv[3] || 'de').split(',').map(s => s.trim()).filter(Boolean);
  const res = buildPruned(base, other);
  console.log(JSON.stringify({ base, ...res }, null, 2));
}

main();
