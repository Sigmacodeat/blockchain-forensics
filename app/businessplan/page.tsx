'use client';

import React from 'react';

export default function BusinessPlanPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-4">
          Businessplan & Förderung
        </h1>
        <p className="text-xl text-muted-foreground">
          Laden Sie unseren vollständigen Businessplan und Informationen zu Fördermöglichkeiten herunter.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="border rounded-lg p-6 shadow-sm">
          <div className="mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              📄 Businessplan
            </h2>
            <p className="text-sm text-muted-foreground mt-2">
              Umfassender Businessplan mit Finanzprognosen und Marktanalyse
            </p>
          </div>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Unser detaillierter Businessplan enthält:
            </p>
            <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
              <li>Marktanalyse und Wettbewerbsvorteile</li>
              <li>Finanzprognosen für 5 Jahre</li>
              <li>Technologische Roadmap</li>
              <li>Team- und Organisationsstruktur</li>
            </ul>
            <button className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
              📥 Businessplan herunterladen
            </button>
          </div>
        </div>

        <div className="border rounded-lg p-6 shadow-sm">
          <div className="mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              📄 Fördermöglichkeiten
            </h2>
            <p className="text-sm text-muted-foreground mt-2">
              Informationen zu verfügbaren Förderprogrammen und Investitionsmöglichkeiten
            </p>
          </div>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Wir bieten verschiedene Fördermöglichkeiten:
            </p>
            <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
              <li>Seed Investment Runden</li>
              <li>Strategische Partnerschaften</li>
              <li>Government Grants</li>
              <li>VC Funding Opportunities</li>
            </ul>
            <button className="w-full border border-gray-300 px-4 py-2 rounded-md hover:bg-gray-50 transition-colors">
              🔗 Fördermöglichkeiten ansehen
            </button>
          </div>
        </div>
      </div>

      <div className="mt-12">
        <div className="border rounded-lg p-6 shadow-sm">
          <div className="mb-4">
            <h2 className="text-xl font-semibold">Kontakt für Investoren</h2>
            <p className="text-sm text-muted-foreground mt-2">
              Für Investitionsanfragen und weitere Informationen
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-semibold mb-2">Kontaktinformationen</h4>
              <p className="text-sm text-muted-foreground">
                E-Mail: investors@sigmacode.com
              </p>
              <p className="text-sm text-muted-foreground">
                Telefon: +49 123 456789
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Büro</h4>
              <p className="text-sm text-muted-foreground">
                SIGMACODE Blockchain Forensics GmbH
              </p>
              <p className="text-sm text-muted-foreground">
                Tech Street 123
              </p>
              <p className="text-sm text-muted-foreground">
                10115 Berlin, Germany
              </p>
            </div>
          </div>
          <div className="mt-6">
            <button className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors">
              Investor Relations kontaktieren
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
