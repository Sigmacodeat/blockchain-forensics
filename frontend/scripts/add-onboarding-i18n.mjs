#!/usr/bin/env node
/**
 * Adds onboarding translation keys to all 43 locale files
 * - German gets proper translations
 * - Other languages get English placeholders (for later translation)
 */

import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const localesDir = join(__dirname, '../src/locales');

// Onboarding translations
const onboardingTranslations = {
  en: {
    back: 'Back',
    close: 'Close',
    finish: 'Finish',
    next: 'Next',
    open: 'Open dialog',
    skip: 'Skip tour',
    restart: 'Restart tour',
    restart_short: 'Restart tour',
    welcome_title: 'Welcome to Blockchain Forensics!',
    welcome_message: 'Would you like to take a quick tour through the dashboard?',
    maybe_later: 'Maybe later',
    start_tour: 'Start tour',
  },
  de: {
    back: 'Zurück',
    close: 'Schließen',
    finish: 'Fertig',
    next: 'Weiter',
    open: 'Dialog öffnen',
    skip: 'Tour überspringen',
    restart: 'Tour wiederholen',
    restart_short: 'Tour wiederholen',
    welcome_title: 'Willkommen bei Blockchain Forensics!',
    welcome_message: 'Möchtest du eine kurze Tour durch das Dashboard machen?',
    maybe_later: 'Später',
    start_tour: 'Tour starten',
  },
  fr: {
    back: 'Retour',
    close: 'Fermer',
    finish: 'Terminer',
    next: 'Suivant',
    open: 'Ouvrir dialogue',
    skip: 'Ignorer visite',
    restart: 'Redémarrer visite',
    restart_short: 'Redémarrer visite',
    welcome_title: 'Bienvenue sur Blockchain Forensics !',
    welcome_message: 'Souhaitez-vous faire une visite rapide du tableau de bord ?',
    maybe_later: 'Plus tard',
    start_tour: 'Démarrer visite',
  },
  es: {
    back: 'Atrás',
    close: 'Cerrar',
    finish: 'Finalizar',
    next: 'Siguiente',
    open: 'Abrir diálogo',
    skip: 'Omitir tour',
    restart: 'Reiniciar tour',
    restart_short: 'Reiniciar tour',
    welcome_title: '¡Bienvenido a Blockchain Forensics!',
    welcome_message: '¿Quieres hacer un recorrido rápido por el panel?',
    maybe_later: 'Más tarde',
    start_tour: 'Iniciar tour',
  },
  it: {
    back: 'Indietro',
    close: 'Chiudi',
    finish: 'Fine',
    next: 'Avanti',
    open: 'Apri dialogo',
    skip: 'Salta tour',
    restart: 'Riavvia tour',
    restart_short: 'Riavvia tour',
    welcome_title: 'Benvenuto in Blockchain Forensics!',
    welcome_message: 'Vuoi fare un tour rapido del pannello?',
    maybe_later: 'Forse più tardi',
    start_tour: 'Inizia tour',
  },
  pt: {
    back: 'Voltar',
    close: 'Fechar',
    finish: 'Finalizar',
    next: 'Próximo',
    open: 'Abrir diálogo',
    skip: 'Pular tour',
    restart: 'Reiniciar tour',
    restart_short: 'Reiniciar tour',
    welcome_title: 'Bem-vindo ao Blockchain Forensics!',
    welcome_message: 'Gostaria de fazer um tour rápido pelo painel?',
    maybe_later: 'Talvez mais tarde',
    start_tour: 'Iniciar tour',
  },
  nl: {
    back: 'Terug',
    close: 'Sluiten',
    finish: 'Voltooien',
    next: 'Volgende',
    open: 'Dialoog openen',
    skip: 'Tour overslaan',
    restart: 'Tour herstarten',
    restart_short: 'Tour herstarten',
    welcome_title: 'Welkom bij Blockchain Forensics!',
    welcome_message: 'Wil je een snelle tour door het dashboard maken?',
    maybe_later: 'Misschien later',
    start_tour: 'Tour starten',
  },
};

// All 43 supported locales
const locales = [
  'ar', 'be', 'bg', 'bs', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr', 'ga',
  'hi', 'hu', 'is', 'it', 'ja', 'ko', 'he', 'lb', 'lt', 'lv', 'mk', 'mt', 'nb', 'nl',
  'nn', 'pl', 'pt', 'rm', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sv', 'tr', 'uk', 'zh-CN'
];

let processed = 0;
let skipped = 0;

for (const locale of locales) {
  const filePath = join(localesDir, `${locale}.json`);
  
  try {
    // Read existing file
    const content = readFileSync(filePath, 'utf-8');
    const json = JSON.parse(content);
    
    // Check if onboarding key already exists
    if (json.onboarding) {
      console.log(`⏭️  Skipping ${locale}.json - onboarding key already exists`);
      skipped++;
      continue;
    }
    
    // Add onboarding translations
    // Use specific translation if available, otherwise use English
    json.onboarding = onboardingTranslations[locale] || onboardingTranslations.en;
    
    // Write back to file (pretty-printed with 2-space indent)
    writeFileSync(filePath, JSON.stringify(json, null, 2) + '\n', 'utf-8');
    
    console.log(`✅ Updated ${locale}.json`);
    processed++;
  } catch (error) {
    console.error(`❌ Error processing ${locale}.json:`, error.message);
  }
}

console.log(`\n📊 Summary:`);
console.log(`   ✅ Processed: ${processed} files`);
console.log(`   ⏭️  Skipped: ${skipped} files`);
console.log(`   📝 Total locales: ${locales.length}`);
console.log(`\n✨ Onboarding i18n setup complete!`);
console.log(`\n💡 Next steps:`);
console.log(`   1. Review translated files`);
console.log(`   2. Replace English placeholders with proper translations`);
console.log(`   3. Test in different languages: npm run dev`);
