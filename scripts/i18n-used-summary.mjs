#!/usr/bin/env node
import { execSync } from 'child_process';
import path from 'path';
import process from 'process';

const cwd = process.cwd();
const script = path.join(cwd, 'scripts', 'i18n-used-compare.mjs');
const out = execSync(`node ${script}`, { cwd, encoding: 'utf8', stdio: ['pipe','pipe','inherit'] });
const report = JSON.parse(out);

function printLang(lang) {
  const r = report.langs[lang];
  if (!r || r.error) {
    console.log(`${lang}\tERR`);
    return;
  }
  console.log(`${lang}\tused:${report.used_count}\ttotal:${r.total_keys}\tmissing:${r.missing_count}\textra:${r.extra_count}`);
}

console.log(`base:\t${report.base}`);
printLang('en');
printLang('de');
