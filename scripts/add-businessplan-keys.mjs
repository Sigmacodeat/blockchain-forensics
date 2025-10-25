#!/usr/bin/env node

/**
 * Fügt fehlende landing.businessplan Keys zu allen Sprachdateien hinzu
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const LOCALES_DIR = path.join(__dirname, '../frontend/src/locales');

// Übersetzungen für landing.businessplan
const TRANSLATIONS = {
  de: {
    badge: 'Businessplan & Förderung',
    title: '81% Förderquote · €2,25 Mio Förderung',
    subtitle: 'Österreichische Förderungen optimiert: FFG, Wirtschaftsagentur, AWS – inkl. Timeline, Work Packages und Meilensteine',
    kpis: 'Förder-Kennzahlen',
    kpi1: 'Gesamtförderung',
    kpi2: 'Förderquote',
    kpi3: 'Laufzeit',
    cta: 'Zum Businessplan & Förderung'
  },
  en: {
    badge: 'Business Plan & Funding',
    title: '81% Funding Rate · €2.25M Total Funding',
    subtitle: 'Austrian funding programs optimized: FFG, Vienna Business Agency, AWS – incl. timeline, work packages and milestones',
    kpis: 'Funding Metrics',
    kpi1: 'Total Funding',
    kpi2: 'Funding Rate',
    kpi3: 'Duration',
    cta: 'View Business Plan & Funding'
  },
  es: {
    badge: 'Plan de Negocios y Financiación',
    title: '81% Tasa de Financiación · €2,25M Financiación Total',
    subtitle: 'Programas de financiación austriacos optimizados: FFG, Agencia de Negocios de Viena, AWS – incl. cronograma, paquetes de trabajo e hitos',
    kpis: 'Métricas de Financiación',
    kpi1: 'Financiación Total',
    kpi2: 'Tasa de Financiación',
    kpi3: 'Duración',
    cta: 'Ver Plan de Negocios y Financiación'
  },
  fr: {
    badge: 'Plan d\'Affaires & Financement',
    title: '81% Taux de Financement · €2,25M Financement Total',
    subtitle: 'Programmes de financement autrichiens optimisés : FFG, Agence des Affaires de Vienne, AWS – incl. calendrier, lots de travail et jalons',
    kpis: 'Métriques de Financement',
    kpi1: 'Financement Total',
    kpi2: 'Taux de Financement',
    kpi3: 'Durée',
    cta: 'Voir Plan d\'Affaires & Financement'
  },
  it: {
    badge: 'Piano Aziendale & Finanziamenti',
    title: '81% Tasso di Finanziamento · €2,25M Finanziamento Totale',
    subtitle: 'Programmi di finanziamento austriaci ottimizzati: FFG, Agenzia Economica di Vienna, AWS – incl. cronologia, pacchetti di lavoro e traguardi',
    kpis: 'Metriche di Finanziamento',
    kpi1: 'Finanziamento Totale',
    kpi2: 'Tasso di Finanziamento',
    kpi3: 'Durata',
    cta: 'Visualizza Piano Aziendale & Finanziamenti'
  },
  pt: {
    badge: 'Plano de Negócios & Financiamento',
    title: '81% Taxa de Financiamento · €2,25M Financiamento Total',
    subtitle: 'Programas de financiamento austríacos otimizados: FFG, Agência de Negócios de Viena, AWS – incl. cronograma, pacotes de trabalho e marcos',
    kpis: 'Métricas de Financiamento',
    kpi1: 'Financiamento Total',
    kpi2: 'Taxa de Financiamento',
    kpi3: 'Duração',
    cta: 'Ver Plano de Negócios & Financiamento'
  },
  nl: {
    badge: 'Bedrijfsplan & Financiering',
    title: '81% Financieringspercentage · €2,25M Totale Financiering',
    subtitle: 'Oostenrijkse financieringsprogramma\'s geoptimaliseerd: FFG, Weens Zakelijk Agentschap, AWS – incl. tijdlijn, werkpakketten en mijlpalen',
    kpis: 'Financieringsstatistieken',
    kpi1: 'Totale Financiering',
    kpi2: 'Financieringspercentage',
    kpi3: 'Duur',
    cta: 'Bekijk Bedrijfsplan & Financiering'
  },
  pl: {
    badge: 'Plan Biznesowy i Finansowanie',
    title: '81% Stopa Finansowania · €2,25M Całkowite Finansowanie',
    subtitle: 'Zoptymalizowane programy finansowania austriackiego: FFG, Wiedeńska Agencja Biznesu, AWS – zawiera harmonogram, pakiety robocze i kamienie milowe',
    kpis: 'Wskaźniki Finansowania',
    kpi1: 'Całkowite Finansowanie',
    kpi2: 'Stopa Finansowania',
    kpi3: 'Czas Trwania',
    cta: 'Zobacz Plan Biznesowy i Finansowanie'
  },
  cs: {
    badge: 'Obchodní Plán & Financování',
    title: '81% Míra Financování · €2,25M Celkové Financování',
    subtitle: 'Optimalizované rakouské financovací programy: FFG, Vídeňská obchodní agentura, AWS – včetně časové osy, pracovních balíčků a milníků',
    kpis: 'Metriky Financování',
    kpi1: 'Celkové Financování',
    kpi2: 'Míra Financování',
    kpi3: 'Trvání',
    cta: 'Zobrazit Obchodní Plán & Financování'
  },
  ru: {
    badge: 'Бизнес-План и Финансирование',
    title: '81% Ставка Финансирования · €2,25M Общее Финансирование',
    subtitle: 'Оптимизированные австрийские программы финансирования: FFG, Венское Бизнес-Агентство, AWS – вкл. график, рабочие пакеты и контрольные точки',
    kpis: 'Показатели Финансирования',
    kpi1: 'Общее Финансирование',
    kpi2: 'Ставка Финансирования',
    kpi3: 'Продолжительность',
    cta: 'Посмотреть Бизнес-План и Финансирование'
  },
  // Für alle anderen Sprachen: Englisch als Fallback
  _fallback: {
    badge: 'Business Plan & Funding',
    title: '81% Funding Rate · €2.25M Total Funding',
    subtitle: 'Austrian funding programs optimized: FFG, Vienna Business Agency, AWS – incl. timeline, work packages and milestones',
    kpis: 'Funding Metrics',
    kpi1: 'Total Funding',
    kpi2: 'Funding Rate',
    kpi3: 'Duration',
    cta: 'View Business Plan & Funding'
  }
};

// Alle Sprachen
const ALL_LANGUAGES = [
  'de', 'en', 'es', 'fr', 'it', 'pt', 'nl', 'pl', 'cs', 'ru', 'sv', 'da', 'fi',
  'nb', 'nn', 'is', 'ga', 'lb', 'rm', 'ro', 'bg', 'el', 'uk', 'be', 'hu', 'sk',
  'sl', 'sq', 'sr', 'bs', 'mk', 'mt', 'lt', 'lv', 'et', 'ja', 'ko', 'zh-CN',
  'hi', 'tr', 'ar', 'he'
];

async function addBusinessplanKeys() {
  console.log('🔧 Füge landing.businessplan Keys zu allen Sprachdateien hinzu\n');
  console.log('=' .repeat(60));
  
  let successCount = 0;
  let skipCount = 0;
  let errorCount = 0;
  
  for (const lang of ALL_LANGUAGES) {
    const filePath = path.join(LOCALES_DIR, `${lang}.json`);
    
    if (!fs.existsSync(filePath)) {
      console.log(`⚠️  ${lang}.json nicht gefunden - überspringe`);
      skipCount++;
      continue;
    }
    
    try {
      // Datei laden
      const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      
      // Prüfen ob landing.businessplan schon existiert
      if (data.landing && data.landing.businessplan) {
        console.log(`✓ ${lang}.json: landing.businessplan existiert bereits`);
        skipCount++;
        continue;
      }
      
      // landing-Objekt sicherstellen
      if (!data.landing) {
        data.landing = {};
      }
      
      // businessplan Keys hinzufügen
      const translation = TRANSLATIONS[lang] || TRANSLATIONS._fallback;
      data.landing.businessplan = translation;
      
      // Zurückschreiben (mit 2 Spaces Indentation für Lesbarkeit)
      fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n');
      
      console.log(`✅ ${lang}.json: landing.businessplan Keys hinzugefügt`);
      successCount++;
      
    } catch (err) {
      console.error(`❌ ${lang}.json: Fehler - ${err.message}`);
      errorCount++;
    }
  }
  
  // Zusammenfassung
  console.log('\n' + '='.repeat(60));
  console.log('\n📊 ZUSAMMENFASSUNG\n');
  console.log(`✅ Erfolgreich aktualisiert: ${successCount}`);
  console.log(`⏭️  Übersprungen: ${skipCount}`);
  console.log(`❌ Fehler: ${errorCount}`);
  console.log(`📝 Gesamt verarbeitet: ${ALL_LANGUAGES.length}`);
  
  if (errorCount > 0) {
    console.log('\n⚠️  Es gab Fehler! Bitte überprüfen.');
    process.exit(1);
  } else {
    console.log('\n✅ Alle Dateien erfolgreich aktualisiert!');
    process.exit(0);
  }
}

addBusinessplanKeys().catch(err => {
  console.error('❌ Kritischer Fehler:', err);
  process.exit(1);
});
