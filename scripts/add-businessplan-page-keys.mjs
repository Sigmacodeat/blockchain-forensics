#!/usr/bin/env node

/**
 * Fügt ALLE businessplan Page Keys zu allen Sprachdateien hinzu
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const LOCALES_DIR = path.join(__dirname, '../frontend/src/locales');

// Übersetzungen für businessplan (komplette Page)
const TRANSLATIONS = {
  de: {
    seo: {
      title: 'Businessplan & Förderung 2025-2027 | €2,25 Mio. Förderung bei 81% Quote',
      description: 'Detaillierter Businessplan mit FFG Basisprogramm, AWS und Wirtschaftsagentur Wien: €2,25 Mio. Förderung (81% Quote) für KI-gestützte Blockchain-Forensik über 24 Monate.'
    },
    hero: {
      badge: 'Österreichische Förderungen 2025-2027',
      title: 'Blockchain Forensics Platform',
      subtitle: 'KI-gestützte Forensik für Strafverfolgung & Compliance',
      print_button: 'Drucken / PDF',
      print_aria: 'Seite drucken oder als PDF speichern',
      timeline_button: 'Zur Timeline',
      timeline_aria: 'Zu Meilensteinen und Timeline springen',
      total_funding: 'Förderung',
      funding_rate: 'Förderquote',
      duration: 'Laufzeit',
      months: 'Monate'
    },
    executive: {
      title: 'Executive Summary',
      subtitle: 'Projekt auf einen Blick',
      goals_title: 'Projektziele',
      goals: {
        chains: 'Blockchain-Abdeckung: 7 → 32+ Chains (+360%)',
        labels: 'Entity-Datenbank: 500 → 10.000+ Labels (+1.900%)',
        features: 'Enterprise-Features: KYT, Travel Rule, VASP',
        customers: '100+ Pilotkunden, €500k ARR nach 24 Monaten'
      },
      usps_title: 'Alleinstellungsmerkmale',
      usps: {
        ai: 'KI-Agenten - weltweit einzigartig',
        price: '95% günstiger - €25k vs. €500k/Jahr',
        opensource: 'Open Source - einziger Anbieter',
        eu: 'Made in EU - GDPR-konform'
      }
    },
    funding: {
      title: 'Optimale Förderstrategie',
      subtitle: 'Multi-Förder-Ansatz mit weiblicher Geschäftsführung',
      female_leadership: 'Weibliche Geschäftsführung',
      additional_funding: '+485.000 Zusatzförderung!',
      table: {
        provider: 'Fördergeber',
        volume: 'Volumen',
        funding: 'Förderung',
        rate: 'Quote',
        form: 'Form',
        total: 'GESAMT'
      },
      providers: {
        ffg: 'FFG Basisprogramm',
        ffg_form: 'Zuschuss + Darlehen',
        vienna_bonus: '+ Wien-Bonus',
        vienna_bonus_form: 'Zuschuss',
        wirtschaftsagentur: 'Wirtschaftsagentur Wien',
        frauen_bonus: '+ Frauen-Boni',
        aws_ai: 'AWS AI-Adoption',
        aws_knowledge: 'AWS AI-Wissen',
        aws_seed: 'AWS Seedfinancing',
        new_badge: 'NEU'
      },
      summary: {
        non_refundable: 'Nicht-rückzahlbar',
        grants_percent: '(72% Zuschüsse)',
        loan: 'Darlehen',
        loan_details: '(28%, 1,75% p.a.)'
      },
      optimization: {
        title: 'Optimierung erfolgreich!',
        text: 'Durch weibliche Geschäftsführung und KI-Fokus: +485.000 zusätzliche Förderung',
        rate_increase: 'Von 68% auf 81% Förderquote gesteigert!'
      }
    },
    workpackages: {
      title: '8 Work Packages',
      subtitle: 'Strukturierte Projektabwicklung über 24 Monate',
      total_budget: 'Gesamt-Budget:',
      infrastructure: '+ 100k Infrastruktur = 2.850.000 Total',
      details_title: 'Detaillierte Work Packages'
    },
    milestones: {
      title: 'Meilensteine (verbindlich)',
      subtitle: 'Kritische Erfolgsfaktoren über 24 Monate',
      table: {
        month: 'Monat',
        milestone: 'Meilenstein',
        kpis: 'KPIs',
        proof: 'Nachweis',
        caption: 'Übersicht der Meilensteine mit KPIs und Nachweisen'
      },
      phases: {
        phase1: 'Phase 1 Complete',
        phase2: 'Phase 2 Complete',
        phase3: 'Phase 3 Complete',
        end: 'Projekt-Ende'
      }
    },
    market: {
      title: 'Marktpotential',
      subtitle: '€5,8 Mrd. bis 2030 (CAGR 18,3%)',
      tam_desc: 'Global 2030',
      sam_desc: 'DACH + EU',
      som_desc: '1% nach 5 Jahren',
      targets_title: 'Zielgruppen',
      targets: {
        law: '200+ EU-Strafverfolgungsbehörden',
        exchanges: '5.000+ Krypto-Börsen weltweit',
        banks: '10.000+ Banken/Finanzinstitute',
        lawyers: '50.000+ Anwaltskanzleien'
      },
      revenue_title: 'Revenue Forecast',
      breakeven: 'Break-Even:',
      growth: 'Launch'
    },
    cta: {
      badge: '85-90% Bewilligungschance',
      title: 'Bereit für Fördereinreichung',
      subtitle: 'Mit weiblicher Geschäftsführung und KI-Fokus: 2,25 Mio. Förderung bei 81% Quote',
      start_button: 'Projekt starten',
      next_steps: {
        ffg: {
          title: 'FFG Basisprogramm',
          deadline: '15. Nov 2025',
          status: 'Priority'
        },
        wirtschaft: {
          title: 'Wirtschaftsagentur',
          deadline: '31. Dez 2025',
          status: 'Ready'
        },
        aws: {
          title: 'AWS AI-Adoption',
          deadline: 'Q4 2025',
          status: 'New'
        }
      }
    }
  },
  en: {
    seo: {
      title: 'Business Plan & Funding 2025-2027 | €2.25M Funding at 81% Rate',
      description: 'Detailed business plan with FFG Base Program, AWS and Vienna Business Agency: €2.25M funding (81% rate) for AI-powered blockchain forensics over 24 months.'
    },
    hero: {
      badge: 'Austrian Funding Programs 2025-2027',
      title: 'Blockchain Forensics Platform',
      subtitle: 'AI-powered forensics for law enforcement & compliance',
      print_button: 'Print / PDF',
      print_aria: 'Print page or save as PDF',
      timeline_button: 'To Timeline',
      timeline_aria: 'Jump to milestones and timeline',
      total_funding: 'Total Funding',
      funding_rate: 'Funding Rate',
      duration: 'Duration',
      months: 'months'
    },
    executive: {
      title: 'Executive Summary',
      subtitle: 'Project at a glance',
      goals_title: 'Project Goals',
      goals: {
        chains: 'Blockchain coverage: 7 → 32+ chains (+360%)',
        labels: 'Entity database: 500 → 10,000+ labels (+1,900%)',
        features: 'Enterprise features: KYT, Travel Rule, VASP',
        customers: '100+ pilot customers, €500k ARR after 24 months'
      },
      usps_title: 'Unique Selling Points',
      usps: {
        ai: 'AI Agents - globally unique',
        price: '95% cheaper - €25k vs. €500k/year',
        opensource: 'Open Source - only provider',
        eu: 'Made in EU - GDPR compliant'
      }
    },
    funding: {
      title: 'Optimal Funding Strategy',
      subtitle: 'Multi-funding approach with female leadership',
      female_leadership: 'Female Leadership',
      additional_funding: '+€485,000 Additional Funding!',
      table: {
        provider: 'Funding Provider',
        volume: 'Volume',
        funding: 'Funding',
        rate: 'Rate',
        form: 'Form',
        total: 'TOTAL'
      },
      providers: {
        ffg: 'FFG Base Program',
        ffg_form: 'Grant + Loan',
        vienna_bonus: '+ Vienna Bonus',
        vienna_bonus_form: 'Grant',
        wirtschaftsagentur: 'Vienna Business Agency',
        frauen_bonus: '+ Women Bonuses',
        aws_ai: 'AWS AI Adoption',
        aws_knowledge: 'AWS AI Knowledge',
        aws_seed: 'AWS Seed Financing',
        new_badge: 'NEW'
      },
      summary: {
        non_refundable: 'Non-refundable',
        grants_percent: '(72% grants)',
        loan: 'Loan',
        loan_details: '(28%, 1.75% p.a.)'
      },
      optimization: {
        title: 'Optimization successful!',
        text: 'Through female leadership and AI focus: +€485,000 additional funding',
        rate_increase: 'Increased from 68% to 81% funding rate!'
      }
    },
    workpackages: {
      title: '8 Work Packages',
      subtitle: 'Structured project execution over 24 months',
      total_budget: 'Total Budget:',
      infrastructure: '+ 100k Infrastructure = 2,850,000 Total',
      details_title: 'Detailed Work Packages'
    },
    milestones: {
      title: 'Milestones (binding)',
      subtitle: 'Critical success factors over 24 months',
      table: {
        month: 'Month',
        milestone: 'Milestone',
        kpis: 'KPIs',
        proof: 'Proof',
        caption: 'Overview of milestones with KPIs and proofs'
      },
      phases: {
        phase1: 'Phase 1 Complete',
        phase2: 'Phase 2 Complete',
        phase3: 'Phase 3 Complete',
        end: 'Project End'
      }
    },
    market: {
      title: 'Market Potential',
      subtitle: '€5.8B by 2030 (CAGR 18.3%)',
      tam_desc: 'Global 2030',
      sam_desc: 'DACH + EU',
      som_desc: '1% after 5 years',
      targets_title: 'Target Groups',
      targets: {
        law: '200+ EU law enforcement agencies',
        exchanges: '5,000+ crypto exchanges worldwide',
        banks: '10,000+ banks/financial institutions',
        lawyers: '50,000+ law firms'
      },
      revenue_title: 'Revenue Forecast',
      breakeven: 'Break-Even:',
      growth: 'Launch'
    },
    cta: {
      badge: '85-90% approval chance',
      title: 'Ready for funding application',
      subtitle: 'With female leadership and AI focus: €2.25M funding at 81% rate',
      start_button: 'Start Project',
      next_steps: {
        ffg: {
          title: 'FFG Base Program',
          deadline: 'Nov 15, 2025',
          status: 'Priority'
        },
        wirtschaft: {
          title: 'Business Agency',
          deadline: 'Dec 31, 2025',
          status: 'Ready'
        },
        aws: {
          title: 'AWS AI Adoption',
          deadline: 'Q4 2025',
          status: 'New'
        }
      }
    }
  }
};

// Fallback für alle anderen Sprachen (Englisch)
const FALLBACK = TRANSLATIONS.en;

// Alle Sprachen
const ALL_LANGUAGES = [
  'de', 'en', 'es', 'fr', 'it', 'pt', 'nl', 'pl', 'cs', 'ru', 'sv', 'da', 'fi',
  'nb', 'nn', 'is', 'ga', 'lb', 'rm', 'ro', 'bg', 'el', 'uk', 'be', 'hu', 'sk',
  'sl', 'sq', 'sr', 'bs', 'mk', 'mt', 'lt', 'lv', 'et', 'ja', 'ko', 'zh-CN',
  'hi', 'tr', 'ar', 'he'
];

async function addBusinessplanPageKeys() {
  console.log('🔧 Füge businessplan Page Keys zu allen Sprachdateien hinzu\n');
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
      
      // Sicherstellen dass "businessplan" existiert
      if (!data.businessplan) {
        data.businessplan = {};
      }
      
      // Keys hinzufügen (überschreibt alte wenn vorhanden)
      const translation = TRANSLATIONS[lang] || FALLBACK;
      Object.assign(data.businessplan, translation);
      
      // Zurückschreiben
      fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n');
      
      console.log(`✅ ${lang}.json: businessplan Keys aktualisiert`);
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

addBusinessplanPageKeys().catch(err => {
  console.error('❌ Kritischer Fehler:', err);
  process.exit(1);
});
