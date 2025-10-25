#!/usr/bin/env node
/**
 * Adds Financial Institutions Use Case i18n keys to all 42 languages
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const LOCALES_DIR = path.join(__dirname, '..', 'frontend', 'src', 'locales');

// All 42 supported languages
const LANGUAGES = [
  'en', 'de', 'es', 'fr', 'it', 'pt', 'nl', 'pl', 'cs', 'ru', 'sv', 'da',
  'fi', 'nb', 'nn', 'is', 'ga', 'lb', 'rm', 'ro', 'bg', 'el', 'uk', 'be',
  'hu', 'sk', 'sl', 'sq', 'sr', 'bs', 'mk', 'mt', 'lt', 'lv', 'et', 'ja',
  'ko', 'zh-CN', 'hi', 'tr', 'ar', 'he'
];

// Translation templates for each language
const TRANSLATIONS = {
  en: {
    use_case_financial_institutions: {
      hero: {
        badge: "For Banks & Fintech",
        title: "Crypto Risk Management for Banks",
        subtitle: "Enterprise-Grade Blockchain Forensics for Financial Institutions. Real-Time Transaction Monitoring, KYC/AML Compliance, Travel Rule Implementation. FATF-compliant and Bank-Grade Security.",
        demo_button: "Request Demo",
        pricing_button: "Enterprise Pricing"
      },
      stats: {
        transaction_screening: "< 100ms Transaction Screening",
        blockchain_networks: "35+ Blockchain Networks",
        uptime_sla: "99.9% Uptime SLA",
        iso_certified: "ISO 27001 Certified"
      },
      challenges: {
        title: "Your Banking Challenges with Crypto",
        customer_onboarding: {
          challenge: "Crypto-onboarding Customers",
          solution: "KYC/AML for Crypto Assets",
          description: "Expand your banking for crypto-affine customers. Fully automated KYC/AML for Bitcoin, Ethereum, Stablecoins.",
          features: ["Wallet Screening", "Source of Funds", "Ongoing Monitoring"]
        },
        regulatory_compliance: {
          challenge: "Regulatory Compliance",
          solution: "FATF/BaFin-compliant",
          description: "Meet all regulatory requirements: Travel Rule, Sanctions Screening, MiCA-compliant.",
          features: ["FATF Travel Rule", "9 Sanctions Lists", "MiCA ready"]
        },
        transaction_monitoring: {
          challenge: "Transaction Monitoring",
          solution: "Real-Time Risk Scoring",
          description: "Monitor your customers' crypto transactions in real-time. Automatic flagging for High-Risk Activities.",
          features: ["Real-Time Alerts", "ML Risk Scoring", "Auto-SAR"]
        },
        fraud_prevention: {
          challenge: "Fraud Prevention",
          solution: "Scam/Fraud Detection",
          description: "Protect your customers from crypto scams, phishing, ransomware. Proactive warnings for suspicious transfers.",
          features: ["Scam Detection", "Ransomware Tracker", "Phishing Alerts"]
        },
        cross_border_payments: {
          challenge: "Cross-Border Payments",
          solution: "VASP-Verification",
          description: "Verify receiving VASPs for cross-border crypto payments. Travel Rule Messages automatically.",
          features: ["VASP Directory", "IVMS101 Format", "Auto-Verification"]
        },
        audit_reporting: {
          challenge: "Audit & Reporting",
          solution: "Regulator-Ready Reports",
          description: "Automatically generate compliance reports for BaFin, ECB, EBA. Complete audit trails.",
          features: ["BaFin Reports", "Audit Trails", "CSV/PDF Export"]
        }
      },
      workflow: {
        title: "Crypto-Banking Workflow",
        customer_onboarding: {
          step: "Customer Onboarding",
          description: "Customer wants to use crypto banking services",
          auto: "KYC/AML Check incl. Wallet Screening",
          time: "< 5 Min"
        },
        wallet_verification: {
          step: "Wallet Verification",
          description: "Customer's crypto wallets are analyzed: Source of Funds, Risk Score, Sanctions",
          auto: "Automatic Wallet Screening (35+ Chains)",
          time: "< 30 Sec"
        },
        ongoing_monitoring: {
          step: "Ongoing Monitoring",
          description: "Continuous monitoring of all customer crypto transactions",
          auto: "Real-Time Transaction Monitoring",
          time: "< 100ms/TX"
        },
        risk_assessment: {
          step: "Risk Assessment",
          description: "For suspicious transactions: Automatic Risk Scoring & Alerting",
          auto: "ML-based Risk Scoring",
          time: "Instant"
        },
        compliance_reporting: {
          step: "Compliance Reporting",
          description: "Automatic SAR generation for Suspicious Activity, regular compliance reports",
          auto: "Auto-SAR & BaFin Reports",
          time: "Daily"
        }
      },
      enterprise_features: {
        title: "Enterprise-Grade Features for Banks",
        bank_grade_security: {
          title: "Bank-Grade Security",
          description: "ISO 27001, SOC 2 Type II, GDPR-compliant. Multi-factor Authentication, Role-based Access Control."
        },
        uptime_sla: {
          title: "99.9% Uptime SLA",
          description: "Enterprise SLA with guaranteed availability. 24/7 Support, Disaster Recovery, Redundant Infrastructure."
        },
        white_label: {
          title: "White-Label Solution",
          description: "Fully branded solution for your bank. Custom Domain, Logo, Colors. API-First Architecture."
        },
        on_premise: {
          title: "On-Premise Deployment",
          description: "Hosted in your own infrastructure. Full data control. Dedicated Support."
        },
        multi_entity: {
          title: "Multi-Entity Support",
          description: "Manage multiple banking entities in one platform. Consolidated Reporting, Shared Intelligence."
        },
        custom_integration: {
          title: "Custom Integration",
          description: "Integration with your Core Banking System. REST API, Webhooks, CSV Import/Export."
        }
      },
      cta: {
        title: "Enterprise Demo for Your Bank",
        subtitle: "Free demo including custom integration consulting. See how we automate your crypto compliance.",
        demo_button: "Request Enterprise Demo",
        contact_button: "Contact"
      }
    }
  },
  de: {
    use_case_financial_institutions: {
      hero: {
        badge: "Für Banken & Fintech",
        title: "Crypto-Risk-Management für Banken",
        subtitle: "Enterprise-Grade Blockchain-Forensik für Financial Institutions. Real-Time Transaction Monitoring, KYC/AML-Compliance, Travel Rule Implementation. FATF-konform und Bank-Grade-Security.",
        demo_button: "Demo anfragen",
        pricing_button: "Enterprise-Preise"
      },
      stats: {
        transaction_screening: "< 100ms Transaction Screening",
        blockchain_networks: "35+ Blockchain Networks",
        uptime_sla: "99.9% Uptime SLA",
        iso_certified: "ISO 27001 Certified"
      },
      challenges: {
        title: "Ihre Banking-Herausforderungen mit Crypto",
        customer_onboarding: {
          challenge: "Crypto-onboarding Kunden",
          solution: "KYC/AML für Crypto-Assets",
          description: "Erweitern Sie Ihr Banking für Crypto-affine Kunden. Vollautomatisches KYC/AML für Bitcoin, Ethereum, Stablecoins.",
          features: ["Wallet-Screening", "Source of Funds", "Ongoing Monitoring"]
        },
        regulatory_compliance: {
          challenge: "Regulatory Compliance",
          solution: "FATF/BaFin-konform",
          description: "Erfüllen Sie alle regulatorischen Anforderungen: Travel Rule, Sanctions Screening, MiCA-compliant.",
          features: ["FATF Travel Rule", "9 Sanctions Lists", "MiCA ready"]
        },
        transaction_monitoring: {
          challenge: "Transaction Monitoring",
          solution: "Real-Time Risk Scoring",
          description: "Überwachen Sie Crypto-Transaktionen Ihrer Kunden in Echtzeit. Automatic flagging bei High-Risk Activities.",
          features: ["Real-Time Alerts", "ML Risk Scoring", "Auto-SAR"]
        },
        fraud_prevention: {
          challenge: "Fraud Prevention",
          solution: "Scam/Fraud Detection",
          description: "Schützen Sie Ihre Kunden vor Crypto-Scams, Phishing, Ransomware. Proaktive Warnungen bei verdächtigen Transfers.",
          features: ["Scam Detection", "Ransomware Tracker", "Phishing Alerts"]
        },
        cross_border_payments: {
          challenge: "Cross-Border Payments",
          solution: "VASP-Verification",
          description: "Verifizieren Sie empfangende VASPs bei grenzüberschreitenden Crypto-Zahlungen. Travel Rule Messages automatisch.",
          features: ["VASP Directory", "IVMS101 Format", "Auto-Verification"]
        },
        audit_reporting: {
          challenge: "Audit & Reporting",
          solution: "Regulator-Ready Reports",
          description: "Generieren Sie automatisch Compliance-Reports für BaFin, ECB, EBA. Vollständige Audit Trails.",
          features: ["BaFin Reports", "Audit Trails", "CSV/PDF Export"]
        }
      },
      workflow: {
        title: "Crypto-Banking Workflow",
        customer_onboarding: {
          step: "Customer Onboarding",
          description: "Kunde möchte Crypto-Banking-Services nutzen",
          auto: "KYC/AML-Check inkl. Wallet-Screening",
          time: "< 5 Min"
        },
        wallet_verification: {
          step: "Wallet Verification",
          description: "Kundens Crypto-Wallets werden analysiert: Source of Funds, Risk-Score, Sanctions",
          auto: "Automatic Wallet-Screening (35+ Chains)",
          time: "< 30 Sek"
        },
        ongoing_monitoring: {
          step: "Ongoing Monitoring",
          description: "Kontinuierliche Überwachung aller Crypto-Transaktionen des Kunden",
          auto: "Real-Time Transaction Monitoring",
          time: "< 100ms/TX"
        },
        risk_assessment: {
          step: "Risk Assessment",
          description: "Bei auffälligen Transaktionen: Automatic Risk Scoring & Alerting",
          auto: "ML-basiertes Risk Scoring",
          time: "Instant"
        },
        compliance_reporting: {
          step: "Compliance Reporting",
          description: "Automatic SAR-Generation bei Suspicious Activity, regelmäßige Compliance-Reports",
          auto: "Auto-SAR & BaFin-Reports",
          time: "Täglich"
        }
      },
      enterprise_features: {
        title: "Enterprise-Grade Features für Banks",
        bank_grade_security: {
          title: "Bank-Grade Security",
          description: "ISO 27001, SOC 2 Type II, GDPR-compliant. Multi-factor Authentication, Role-based Access Control."
        },
        uptime_sla: {
          title: "99.9% Uptime SLA",
          description: "Enterprise-SLA mit garantierter Verfügbarkeit. 24/7 Support, Disaster Recovery, Redundant Infrastructure."
        },
        white_label: {
          title: "White-Label Solution",
          description: "Vollständig gebrandete Lösung für Ihre Bank. Custom Domain, Logo, Farben. API-First Architecture."
        },
        on_premise: {
          title: "On-Premise Deployment",
          description: "Hosted in Ihrer eigenen Infrastructure. Volle Datenkontrolle. Dedicated Support."
        },
        multi_entity: {
          title: "Multi-Entity Support",
          description: "Verwalten Sie mehrere Banking-Entities in einer Plattform. Consolidated Reporting, Shared Intelligence."
        },
        custom_integration: {
          title: "Custom Integration",
          description: "Integration mit Ihrem Core Banking System. REST API, Webhooks, CSV Import/Export."
        }
      },
      cta: {
        title: "Enterprise-Demo für Ihre Bank",
        subtitle: "Kostenlose Demo inkl. Custom Integration-Beratung. Sehen Sie wie wir Ihre Crypto-Compliance automatisieren.",
        demo_button: "Enterprise-Demo anfragen",
        contact_button: "Kontakt"
      }
    }
  }
};

// Auto-translate function (simplified - uses English as base for other languages)
function getTranslationForLanguage(lang) {
  if (TRANSLATIONS[lang]) {
    return TRANSLATIONS[lang];
  }
  
  // For other languages, use English as base (you would normally use a translation API)
  return TRANSLATIONS.en;
}

async function main() {
  console.log('🌍 Adding Financial Institutions i18n keys to all 42 languages...\n');

  let successCount = 0;
  let errorCount = 0;

  for (const lang of LANGUAGES) {
    try {
      const filePath = path.join(LOCALES_DIR, `${lang}.json`);
      
      // Read existing file
      const content = await fs.readFile(filePath, 'utf-8');
      const data = JSON.parse(content);

      // Add new keys (only if not already present)
      if (!data.use_case_financial_institutions) {
        const translation = getTranslationForLanguage(lang);
        data.use_case_financial_institutions = translation.use_case_financial_institutions;

        // Write back with pretty formatting
        await fs.writeFile(filePath, JSON.stringify(data, null, 2) + '\n', 'utf-8');
        console.log(`✅ ${lang}.json - Added use_case_financial_institutions keys`);
        successCount++;
      } else {
        console.log(`⏭️  ${lang}.json - Keys already exist, skipping`);
      }
    } catch (error) {
      console.error(`❌ ${lang}.json - Error: ${error.message}`);
      errorCount++;
    }
  }

  console.log(`\n📊 Summary:`);
  console.log(`   ✅ Success: ${successCount}`);
  console.log(`   ❌ Errors: ${errorCount}`);
  console.log(`   ⏭️  Skipped: ${LANGUAGES.length - successCount - errorCount}`);
  console.log(`\n🎉 Done! Run 'npm run dev' to test the translations.`);
}

main().catch(console.error);
