#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import process from 'process';

const root = process.cwd();
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

// Regex-Muster für i18n-Schlüssel
const patterns = [
  /\bt\(\s*['\"]([^'\"]+)['\"]/g,            // t('key') oder t("key")
  /\bi18n\.t\(\s*['\"]([^'\"]+)['\"]/g,     // i18n.t('key')
  /\bi18next\.t\(\s*['\"]([^'\"]+)['\"]/g,  // i18next.t('key')
  /i18nKey\s*=\s*['\"]([^'\"]+)['\"]/g,       // <Trans i18nKey="key">
];

function extractFromFile(file) {
  const txt = fs.readFileSync(file, 'utf8');
  const keys = new Set();
  for (const re of patterns) {
    let m;
    while ((m = re.exec(txt)) !== null) {
      if (m[1]) keys.add(m[1]);
    }
  }
  return [...keys];
}

function main() {
  const files = walk(srcDir);
  const used = new Set();
  for (const f of files) {
    for (const k of extractFromFile(f)) used.add(k);
  }
  const out = {
    count: used.size,
    keys: [...used].sort(),
  };
  console.log(JSON.stringify(out, null, 2));
}

main();
