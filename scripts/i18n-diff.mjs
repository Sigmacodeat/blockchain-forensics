#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import process from 'process';

const localesDir = path.resolve(process.cwd(), 'frontend', 'src', 'locales');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
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

function main() {
  const baseLang = (process.argv[2] || 'en').replace(/\.json$/, '');
  const targetLang = (process.argv[3] || 'de').replace(/\.json$/, '');
  const basePath = path.join(localesDir, `${baseLang}.json`);
  const targetPath = path.join(localesDir, `${targetLang}.json`);
  if (!fs.existsSync(basePath) || !fs.existsSync(targetPath)) {
    console.error('Missing base or target locale file');
    process.exit(1);
  }
  const base = readJson(basePath);
  const target = readJson(targetPath);
  const baseFlat = flatten(base);
  const targetFlat = flatten(target);

  const fallbackKeys = [];
  for (const [k, v] of Object.entries(baseFlat)) {
    if (k in targetFlat && targetFlat[k] === v) {
      fallbackKeys.push(k);
    }
  }

  console.log(`# Fallback keys in ${targetLang} (equal to ${baseLang})`);
  for (const k of fallbackKeys) console.log(k);
}

main();
