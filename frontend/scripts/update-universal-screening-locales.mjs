#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const LOCALES_DIR = path.resolve(__dirname, '..', 'src', 'locales');

const defaultEn = {
  universal_screening: {
    title: 'Universal Wallet Screening',
    subtitle: 'Screen any wallet address across 90+ blockchains simultaneously',
    cross_chain_title: 'Cross-Chain Screening',
    description: 'Enter a wallet address to screen across all supported chains',
    search_placeholder: '0x... or bc1... or any wallet address',
    button_screen: 'Screen',
    button_screening: 'Screening...',
    errors: {
      enter_address: 'Please enter a wallet address',
      screening_failed: 'Screening failed',
      failed_to_screen: 'Failed to screen address'
    },
    export: { json: 'Export JSON', csv: 'Export CSV', pdf: 'Export PDF' },
    jurisdiction: {
      title: 'Jurisdiction',
      options: { all: 'All', ofac: 'OFAC (US)', eu: 'EU', uk: 'UK', un: 'UN' }
    },
    summary: {
      risk_level: 'Risk Level',
      chains_screened: 'Chains Screened',
      found_on_chains: 'Found on {{count}} chains',
      total_activity: 'Total Activity',
      counterparties_count: '{{count}} counterparties',
      performance: 'Performance',
      cross_chain: 'Cross-chain',
      single_chain: 'Single chain'
    },
    alert: { sanctioned: '⚠️ SANCTIONED ENTITY DETECTED - This address appears on sanctions lists' },
    chain_results: {
      title: 'Chain-Specific Results',
      description: 'Detailed breakdown for each blockchain',
      transactions: 'Transactions',
      value_usd: 'Value (USD)',
      counterparties: 'Counterparties',
      sanctioned_badge: 'SANCTIONED',
      more_labels: '+{{count}} more'
    },
    exposure: { title: 'Exposure', direct: 'Direct', indirect: 'Indirect' },
    defi: { title: 'DeFi Insights' },
    attribution_evidence: { title: 'View Attribution Evidence ({{count}})' },
    all_labels: { title: 'All Labels Across Chains' }
  }
};

function deepMerge(target, source) {
  if (typeof source !== 'object' || source === null) return target;
  for (const key of Object.keys(source)) {
    if (
      typeof source[key] === 'object' &&
      source[key] !== null &&
      !Array.isArray(source[key])
    ) {
      if (!target[key] || typeof target[key] !== 'object') target[key] = {};
      deepMerge(target[key], source[key]);
    } else if (target[key] === undefined) {
      target[key] = source[key];
    }
  }
  return target;
}

function readJSON(file) {
  try {
    const raw = fs.readFileSync(file, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to read JSON', file, e.message);
    return null;
  }
}

function writeJSON(file, obj) {
  const content = JSON.stringify(obj, null, 2) + '\n';
  fs.writeFileSync(file, content, 'utf8');
}

function isNodeModules(p) {
  return p.includes(`${path.sep}node_modules${path.sep}`);
}

function collectLocaleFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (isNodeModules(full)) continue;
      files.push(...collectLocaleFiles(full));
    } else if (entry.isFile() && entry.name.endsWith('.json')) {
      files.push(full);
    }
  }
  return files;
}

function ensureNamespace(obj) {
  if (!obj || typeof obj !== 'object') return deepMerge({}, defaultEn);
  if (!obj.universal_screening) obj.universal_screening = {};
  deepMerge(obj.universal_screening, defaultEn.universal_screening);
  return obj;
}

function main() {
  if (!fs.existsSync(LOCALES_DIR)) {
    console.error('Locales directory not found:', LOCALES_DIR);
    process.exit(1);
  }
  const files = collectLocaleFiles(LOCALES_DIR)
    .filter((f) => !isNodeModules(f));

  let updated = 0;
  for (const file of files) {
    const data = readJSON(file);
    if (!data) continue;
    const before = JSON.stringify(data);
    const merged = ensureNamespace(data);
    const after = JSON.stringify(merged);
    if (after !== before) {
      writeJSON(file, merged);
      updated += 1;
      console.log('Updated', path.relative(LOCALES_DIR, file));
    }
  }
  console.log(`Done. Updated ${updated} locale file(s).`);
}

main();
