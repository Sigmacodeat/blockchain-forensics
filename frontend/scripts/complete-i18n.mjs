#!/usr/bin/env node
/**
 * Complete I18n Script
 * Copies missing automation, privacyDemixing, useCases, and tour sections
 * from de.json to all 50 language files
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const LOCALES_DIR = path.join(__dirname, '../public/locales');

// Reference sections from de.json
const REFERENCE_SECTIONS = {
  automation: {
    "title": "Automation",
    "subtitle": "Regeln definieren, automatisch Cases erstellen, Traces starten und Reports generieren. Mit Simulation testen.",
    "settings": {
      "title": "Einstellungen",
      "description": "Automationsregeln und Schwellwerte",
      "enabled": "Aktiviert",
      "enabledDesc": "Automation aktivieren/deaktivieren",
      "riskThreshold": "Risikoschwelle",
      "riskThresholdValue": "Risikoschwelle: {{value}}",
      "riskThresholdTooltip": "Ab diesem Risikoscore (0-1) werden Automations ausgelöst. Empfehlung: 0.60-0.80.",
      "riskThresholdHelp": "Höhere Schwellen reduzieren False Positives, können aber wichtige Treffer verpassen.",
      "minAmount": "Minimaler Betrag (USD)",
      "minAmountTooltip": "Nur Transaktionen über diesem USD-Betrag werden berücksichtigt.",
      "minAmountHelp": "Nur Transaktionen über diesem USD-Betrag werden berücksichtigt.",
      "traceDepth": "Auto-Trace Tiefe (0-10)",
      "traceDepthHelp": "Höhere Tiefe erhöht Laufzeit und Kosten; Empfehlung: 3-5.",
      "autoCreateCase": "Automatisch Cases erstellen",
      "reportTemplate": "Report-Vorlage",
      "reportTemplates": {
        "standard": "Standard",
        "legal": "Legal (gerichtsfest)",
        "summary": "Executive Summary"
      },
      "save": "Speichern",
      "saving": "Speichern..."
    },
    "simulation": {
      "title": "Simulation",
      "description": "Vorab prüfen, wie viele Cases/Traces ausgelöst würden",
      "hours": "Zeitraum (Stunden)",
      "sample": "Stichprobe",
      "simulate": "Simulieren",
      "simulating": "Simuliere...",
      "results": {
        "evaluated": "Geprüft",
        "createCases": "Cases erstellen",
        "triggerTraces": "Traces auslösen",
        "highPriority": "Hohe Priorität"
      }
    },
    "recent": {
      "title": "Letzte Auto-Investigate Jobs",
      "description": "Neueste Einträge aus der Worker-Queue",
      "noJobs": "Keine Jobs vorhanden",
      "chain": "Chain",
      "depth": "Tiefe",
      "status": {
        "done": "Erledigt",
        "queued": "In Warteschlange",
        "failed": "Fehlgeschlagen"
      }
    }
  },
  privacyDemixing: {
    "title": "Tornado Cash Demixing",
    "subtitle": "De-Anonymisierung von Mixer-Transaktionen mit KI-gestützter Forensik",
    "description": "Fortschrittliche Demixing-Technologie zur Verfolgung von Geldern durch Tornado Cash und andere Privacy-Protokolle",
    "form": {
      "address": "Wallet-Adresse",
      "addressPlaceholder": "0x...",
      "chain": "Blockchain",
      "timeWindow": "Zeitfenster (Stunden)",
      "maxHops": "Maximale Sprünge",
      "startButton": "Demixing-Analyse starten",
      "analyzing": "Analysiere..."
    },
    "chains": {
      "ethereum": "Ethereum",
      "bsc": "BNB Smart Chain",
      "polygon": "Polygon"
    },
    "results": {
      "title": "Analyse-Ergebnisse",
      "confidence": "Konfidenz-Score",
      "depositsFound": "Gefundene Einzahlungen",
      "likelyWithdrawals": "Wahrscheinliche Abhebungen",
      "uniqueAddresses": "Eindeutige Adressen",
      "deposits": "Tornado Cash Einzahlungen",
      "withdrawals": "Identifizierte Abhebungen",
      "paths": "Post-Mixer Pfade",
      "pool": "Pool",
      "viewTx": "Transaktion anzeigen",
      "match": "Übereinstimmung",
      "noResults": "Keine Ergebnisse gefunden",
      "noResultsDesc": "Versuche, deine Suchparameter anzupassen"
    },
    "error": {
      "title": "Analyse-Fehler",
      "generic": "Ein Fehler ist während der Analyse aufgetreten",
      "invalidAddress": "Bitte gib eine gültige Wallet-Adresse ein",
      "networkError": "Netzwerkfehler. Bitte versuche es erneut."
    },
    "features": {
      "aiPowered": "KI-gestützte Analyse",
      "realTime": "Echtzeit-Verarbeitung",
      "multiChain": "Multi-Chain-Unterstützung",
      "forensicGrade": "Forensik-Grade Ergebnisse"
    },
    "info": {
      "howItWorks": "So funktioniert's",
      "step1": "Gib die Wallet-Adresse ein, die mit Tornado Cash interagiert hat",
      "step2": "Unsere KI analysiert Transaktionsmuster und Timing",
      "step3": "Machine Learning identifiziert wahrscheinliche Abhebungs-Adressen",
      "step4": "Verfolge Gelder über mehrere Sprünge bis zum Endziel"
    }
  }
  ,
  useCases: {
    "title": "Anwendungsfälle",
    "subtitle": "Konkrete Workflows für verschiedene Zielgruppen",
    "items": {
      "financialInstitutions": {
        "title": "Finanzinstitute",
        "desc": "Kundenüberwachung, KYT, Case Management und Berichte"
      },
      "lawEnforcement": {
        "title": "Strafverfolgung",
        "desc": "Tracing, Evidenzsicherung, gerichtsfeste Reports"
      },
      "exchanges": {
        "title": "Börsen",
        "desc": "Ein- und Auszahlungs-Überwachung, Sanktions-Checks"
      },
      "defiProtocols": {
        "title": "DeFi Protokolle",
        "desc": "Exploit-Analyse, Asset-Recovery und Monitoring"
      },
      "compliance": {
        "title": "Compliance",
        "desc": "Travel Rule, Risk Scoring und Audit-Trails"
      },
      "analytics": {
        "title": "Analytics",
        "desc": "Token-Flows, Clustering und Netzwerk-Analysen"
      }
    }
  },
  tour: {
    "title": "Geführte Tour",
    "subtitle": "Lerne die wichtigsten Bereiche in wenigen Schritten kennen",
    "steps": {
      "welcome": {
        "title": "Willkommen",
        "desc": "Kurze Einführung in Dashboard, Tracing und Cases"
      },
      "navigation": {
        "title": "Navigation",
        "desc": "Linke Sidebar für Forensik-Bereiche und Filter"
      },
      "createCase": {
        "title": "Case erstellen",
        "desc": "Neue Untersuchung anlegen und Team zuweisen"
      },
      "filters": {
        "title": "Filter & Suche",
        "desc": "Schnell die relevanten Cases und Transaktionen finden"
      },
      "investigator": {
        "title": "Investigator Graph",
        "desc": "Adressen, Cluster und Pfade visuell analysieren"
      },
      "reports": {
        "title": "Reports",
        "desc": "Gerichtsfeste Berichte mit Evidenz generieren"
      },
      "finish": {
        "title": "Fertig",
        "desc": "Du bist startklar – viel Erfolg bei den Analysen!"
      }
    },
    "buttons": {
      "next": "Weiter",
      "prev": "Zurück",
      "skip": "Überspringen",
      "done": "Fertig"
    }
  }
};

async function main() {
  const files = fs.readdirSync(LOCALES_DIR).filter(f => f.endsWith('.json'));
  
  let updated = 0;
  let errors = 0;

  for (const file of files) {
    try {
      const filePath = path.join(LOCALES_DIR, file);
      const content = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      
      let modified = false;
      
      // Add missing sections
      for (const [key, value] of Object.entries(REFERENCE_SECTIONS)) {
        if (!content[key]) {
          content[key] = value;
          modified = true;
          console.log(`✅ Added '${key}' to ${file}`);
        }
      }
      
      if (modified) {
        fs.writeFileSync(filePath, JSON.stringify(content, null, 2) + '\n', 'utf8');
        updated++;
      }
    } catch (error) {
      console.error(`❌ Error processing ${file}:`, error.message);
      errors++;
    }
  }

  console.log(`\n📊 Summary:`);
  console.log(`   Updated: ${updated} files`);
  console.log(`   Errors: ${errors} files`);
  console.log(`   Total: ${files.length} files`);
}

main().catch(console.error);
