#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import process from 'process';

const localesDir = path.resolve(process.cwd(), 'frontend', 'src', 'locales');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, obj) {
  const content = JSON.stringify(obj, null, 2) + '\n';
  fs.writeFileSync(filePath, content, 'utf8');
}

function isObject(x) {
  return x && typeof x === 'object' && !Array.isArray(x);
}

function mergeWithBase(base, target) {
  // Ensure target follows exactly the base keys and shape
  const result = Array.isArray(base) ? [] : {};
  for (const key of Object.keys(base)) {
    const bVal = base[key];
    const tVal = target ? target[key] : undefined;
    if (isObject(bVal)) {
      result[key] = mergeWithBase(bVal, isObject(tVal) ? tVal : {});
    } else {
      result[key] = tVal === undefined ? bVal : tVal;
    }
  }
  return result;
}

function main() {
  const baseLang = (process.argv[2] || 'en').replace(/\.json$/, '');
  const basePath = path.join(localesDir, `${baseLang}.json`);
  if (!fs.existsSync(basePath)) {
    console.error(`Base locale not found: ${basePath}`);
    process.exit(1);
  }
  const base = readJson(basePath);
  const files = fs.readdirSync(localesDir).filter(f => f.endsWith('.json'));

  for (const file of files) {
    const fp = path.join(localesDir, file);
    if (file === `${baseLang}.json`) continue;

    try {
      const current = readJson(fp);
      const merged = mergeWithBase(base, current);
      writeJson(fp, merged);
      console.log(`Synced ${file} against ${baseLang}.json`);
    } catch (e) {
      console.error(`Failed to process ${file}:`, e.message);
      // Auto-repair: reset invalid/ unparsable locale to base
      try {
        writeJson(fp, base);
        console.log(`Reset ${file} to ${baseLang}.json due to parse error`);
      } catch (e2) {
        console.error(`Failed to reset ${file}:`, e2.message);
      }
    }
  }
}

main();
