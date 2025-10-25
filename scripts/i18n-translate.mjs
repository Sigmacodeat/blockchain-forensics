#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import process from 'process';
import https from 'https';

const localesDir = path.resolve(process.cwd(), 'frontend', 'src', 'locales');
// CLI args: <baseLang> <targetsCsv> [--check]
const rawArgs = process.argv.slice(2);
const nonFlags = rawArgs.filter(a => !a.startsWith('--'));
const flags = new Set(rawArgs.filter(a => a.startsWith('--')));
const baseLang = (nonFlags[0] || 'en').replace(/\.json$/, '');
const targetsArg = nonFlags[1] || '';
const targets = targetsArg ? targetsArg.split(',').map(s => s.trim()).filter(Boolean) : [];
const checkMode = flags.has('--check');
const provider = (process.env.I18N_PROVIDER || 'google').toLowerCase(); // 'deepl' | 'google'
const dryRun = process.env.I18N_DRY_RUN === '1';

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
function* walkLeaves(obj, prefix = []) {
  for (const [k, v] of Object.entries(obj)) {
    const keyPath = [...prefix, k];
    if (isObject(v)) {
      yield* walkLeaves(v, keyPath);
    } else {
      yield [keyPath, v];
    }
  }
}
function setAtPath(obj, keyPath, value) {
  let cur = obj;
  for (let i = 0; i < keyPath.length - 1; i++) {
    const k = keyPath[i];
    cur[k] = cur[k] ?? {};
    cur = cur[k];
  }
  cur[keyPath[keyPath.length - 1]] = value;
}

function detectUntranslatedPairs(base, locale) {
  const tasks = [];
  for (const [keyPath, baseVal] of walkLeaves(base)) {
    const cur = keyPath.reduce((o, k) => (o && o[k] !== undefined ? o[k] : undefined), locale);
    const s = String(baseVal);
    let isPlaceholderKeyPath = false;
    if (typeof cur === 'string') {
      const joined = keyPath.join('.');
      if (cur === joined) {
        isPlaceholderKeyPath = true;
      }
    }

    if (cur === undefined || cur === baseVal || isPlaceholderKeyPath) {
      // mark for translation unless value should be skipped
      if (!shouldSkipValue(s)) tasks.push([keyPath, s]);
    }
  }
  return tasks;
}

// Skip obviously non-translatable tokens (keys, identifiers, empty)
function shouldSkipValue(v) {
  if (!v || !v.trim()) return true;
  // key-like tokens (e.g., address_analysis.title)
  if (/^[a-z0-9_.-]+$/i.test(v) && !/[\s]/.test(v)) return true;
  // URLs
  if (/^https?:\/\//i.test(v)) return true;
  // numbers-only or numeric-like
  if (/^\d+(?:[.,]\d+)?$/.test(v.trim())) return true;
  // strings that are only placeholders/tokens (after removing them, nothing meaningful remains)
  const phRegex = /(\{\{\s*[^}]+\s*\}\}|\{\s*[^}]+\s*\}|%\d*\$?[sdif]|:[a-zA-Z_][\w-]*|\{\d+\})/g;
  const stripped = v.replace(phRegex, '').replace(/[^\p{L}\p{N}]+/gu, '').trim();
  if (stripped.length === 0) return true;
  return false;
}

function httpsRequest(options, body) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, res => {
      let data = '';
      res.on('data', chunk => (data += chunk));
      res.on('end', () => {
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ status: res.statusCode, data });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function translateDeepl(texts, targetLang) {
  const key = process.env.DEEPL_API_KEY;
  if (!key) throw new Error('DEEPL_API_KEY missing');
  const params = new URLSearchParams();
  for (const t of texts) params.append('text', t);
  params.append('target_lang', targetLang.toUpperCase());
  // prefer EN as source
  params.append('source_lang', 'EN');
  const res = await httpsRequest({
    method: 'POST',
    hostname: 'api-free.deepl.com',
    path: '/v2/translate',
    headers: {
      'Authorization': `DeepL-Auth-Key ${key}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  }, params.toString());
  const json = JSON.parse(res.data);
  return json.translations.map(t => t.text);
}

async function translateGoogle(texts, targetLang) {
  const key = process.env.GOOGLE_API_KEY;
  if (!key) throw new Error('GOOGLE_API_KEY missing');
  const body = JSON.stringify({ q: texts, target: targetLang, source: 'en', format: 'text' });
  const res = await httpsRequest({
    method: 'POST',
    hostname: 'translation.googleapis.com',
    path: `/language/translate/v2?key=${key}`,
    headers: { 'Content-Type': 'application/json' },
  }, body);
  const json = JSON.parse(res.data);
  return json.data.translations.map(t => t.translatedText);
}

const langMap = {
  // ISO to provider target codes (fallback to same code)
  'zh-CN': { deepl: 'ZH', google: 'zh-CN' },
  'en': { deepl: 'EN', google: 'en' },
  'de': { deepl: 'DE', google: 'de' },
  'es': { deepl: 'ES', google: 'es' },
  'fr': { deepl: 'FR', google: 'fr' },
  'it': { deepl: 'IT', google: 'it' },
  'nl': { deepl: 'NL', google: 'nl' },
  'pt': { deepl: 'PT-PT', google: 'pt' },
  'pt-BR': { deepl: 'PT-BR', google: 'pt-BR' },
  'ru': { deepl: 'RU', google: 'ru' },
  'pl': { deepl: 'PL', google: 'pl' },
  'ja': { deepl: 'JA', google: 'ja' },
  'ko': { deepl: 'KO', google: 'ko' },
  // fallback mapping handled below
};

async function translateBatch(texts, target) {
  if (dryRun) return texts.map(t => t); // no-op
  const codes = langMap[target] || { deepl: target, google: target };
  if (provider === 'deepl') return translateDeepl(texts, codes.deepl || target);
  if (provider === 'google') return translateGoogle(texts, codes.google || target);
  throw new Error(`Unknown provider: ${provider}`);
}

async function processLocale(base, targetCode) {
  const targetPath = path.join(localesDir, `${targetCode}.json`);
  if (!fs.existsSync(targetPath)) {
    console.warn(`Skipping ${targetCode}: file not found`);
    return;
  }
  const target = readJson(targetPath);
  const tasks = detectUntranslatedPairs(base, target);
  if (tasks.length === 0) {
    console.log(`No untranslated keys for ${targetCode}`);
    return;
  }
  if (checkMode) {
    console.log(`[check] ${targetCode}: ${tasks.length} keys need translation`);
    for (const [keyPath] of tasks) {
      console.log(` - ${keyPath.join('.')}`);
    }
    return;
  }
  console.log(`Translating ${tasks.length} keys to ${targetCode} using ${provider}${dryRun ? ' (dry-run)' : ''}`);

  const batchSize = 40;
  for (let i = 0; i < tasks.length; i += batchSize) {
    const slice = tasks.slice(i, i + batchSize);
    const inputsRaw = slice.map(([, v]) => v);
    // Mask placeholders like {{amount}} to prevent provider from altering them
    const maskMaps = [];
    const inputs = inputsRaw.map((t, idx) => {
      const { masked, map } = maskPlaceholders(String(t));
      maskMaps[idx] = map;
      return masked;
    });
    let outputs;
    try {
      outputs = await translateBatch(inputs, targetCode);
    } catch (e) {
      console.error(`Batch ${i / batchSize} failed for ${targetCode}:`, e.message);
      // simple retry once
      try {
        outputs = await translateBatch(inputs, targetCode);
      } catch (e2) {
        console.error(`Retry failed for ${targetCode}:`, e2.message);
        outputs = inputs; // fallback keep EN
      }
    }
    for (let j = 0; j < slice.length; j++) {
      const [keyPath] = slice[j];
      const out = outputs[j] ?? inputs[j];
      const restored = unmaskPlaceholders(String(out), maskMaps[j]);
      setAtPath(target, keyPath, restored);
    }
  }
  writeJson(targetPath, target);
  console.log(`Updated ${targetCode}.json`);
}

// --- Placeholder masking utilities ---
function maskPlaceholders(text) {
  const map = [];
  let idx = 0;
  // Combined placeholder patterns: {{var}}, {var}, %s/%1$s, {0}, :name
  const regex = /(\{\{\s*[^}]+\s*\}\}|\{\s*[^}]+\s*\}|%\d*\$?[sdif]|:[a-zA-Z_][\w-]*|\{\d+\})/g;
  const masked = String(text).replace(regex, (m) => {
    const token = `__PH_${idx++}__`;
    map.push({ token, value: m });
    return token;
  });
  return { masked, map };
}

function unmaskPlaceholders(text, map = []) {
  let out = text;
  for (const { token, value } of map) {
    out = out.replaceAll(token, value);
  }
  return out;
}

async function main() {
  const basePath = path.join(localesDir, `${baseLang}.json`);
  if (!fs.existsSync(basePath)) {
    console.error(`Base locale not found: ${basePath}`);
    process.exit(1);
  }
  const base = readJson(basePath);
  const all = fs.readdirSync(localesDir).filter(f => f.endsWith('.json')).map(f => f.replace(/\.json$/, ''));
  const targetList = targets.length ? targets : all.filter(l => l !== baseLang);

  // parallel with limit
  const limit = Number(process.env.I18N_MAX_CONCURRENCY || 3);
  const queue = [...targetList];
  const workers = Array.from({ length: Math.min(limit, queue.length) }, async () => {
    while (queue.length) {
      const lang = queue.shift();
      await processLocale(base, lang);
    }
  });
  await Promise.all(workers);
  console.log('Done');
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
