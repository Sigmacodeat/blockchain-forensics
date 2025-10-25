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
  const failOnMissing = process.argv.includes('--fail-on-missing');
  const basePath = path.join(localesDir, `${baseLang}.json`);
  if (!fs.existsSync(basePath)) {
    console.error(`Base locale not found: ${basePath}`);
    process.exit(1);
  }
  const base = readJson(basePath);
  const baseFlat = flatten(base);
  const files = fs.readdirSync(localesDir).filter(f => f.endsWith('.json'));

  const rows = [];
  for (const file of files) {
    const lang = file.replace(/\.json$/, '');
    const fp = path.join(localesDir, file);
    try {
      const data = readJson(fp);
      const flat = flatten(data);
      let same = 0, diff = 0, missing = 0;
      for (const [k, v] of Object.entries(baseFlat)) {
        if (!(k in flat)) {
          missing++;
        } else if (flat[k] === v) {
          same++;
        } else {
          diff++;
        }
      }
      const total = Object.keys(baseFlat).length;
      rows.push({ lang, total, translated: diff, fallback_en: same, missing });
    } catch (e) {
      rows.push({ lang, error: e.message });
    }
  }

  rows.sort((a, b) => a.lang.localeCompare(b.lang));

  // Pretty print
  const header = ['lang','total','translated','fallback_en','missing'];
  console.log(header.join('\t'));
  for (const r of rows) {
    if (r.error) {
      console.log(`${r.lang}\tERR\tERR\tERR\tERR (${r.error})`);
    } else {
      console.log(`${r.lang}\t${r.total}\t${r.translated}\t${r.fallback_en}\t${r.missing}`);
    }
  }

  if (failOnMissing) {
    const anyMissing = rows.some(r => !r.error && typeof r.missing === 'number' && r.missing > 0);
    if (anyMissing) {
      console.error('i18n-report: Missing keys detected. Failing due to --fail-on-missing.');
      process.exit(2);
    }
  }
}

main();
