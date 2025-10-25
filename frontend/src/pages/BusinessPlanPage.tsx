import React from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import LinkLocalized from '@/components/LinkLocalized'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ArrowRight, Shield, LineChart, CheckCircle2, Globe, Scale, FileText } from 'lucide-react'

export default function BusinessPlanPage() {
  const { t } = useTranslation()
  usePageMeta(
    t('businessplan.seo.title', 'Businessplan & Förderung | SIGMACODE Blockchain Forensics'),
    t('businessplan.seo.description', 'Unser Businessplan, Förderstrategie und Roadmap – transparent, messbar und auf Enterprise-Value ausgerichtet.')
  )

  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <div className="border-b">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 py-16">
          <div className="max-w-4xl mx-auto text-center">
            <Badge className="mb-3" variant="scan-border">{t('businessplan.header.badge', 'Businessplan & Förderung')}</Badge>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              {t('businessplan.header.title', 'Planbar zum Marktführer in Blockchain-Forensik')}
            </h1>
            <p className="text-sm text-muted-foreground mb-2">SIGMACODE · Blockchain Forensics</p>
            <p className="text-lg text-muted-foreground mb-6">
              {t('businessplan.header.subtitle', 'Konsequent umsetzbare Roadmap mit klaren Meilensteinen, validierten Use-Cases und belastbaren KPIs – für Law Enforcement, VASPs und Finanzinstitute.')}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <LinkLocalized to="/contact">
                <Button size="lg" variant="gradient">
                  {t('businessplan.cta.contact', 'Kontakt aufnehmen')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </LinkLocalized>
              <LinkLocalized to="/pricing">
                <Button size="lg" variant="outline">
                  {t('businessplan.cta.pricing', 'Pricing ansehen')}
                </Button>
              </LinkLocalized>
            </div>
          </div>
        </div>
      </div>

      {/* Value Pillars */}
      <div className="py-16">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <PillarCard
              icon={<Shield className="h-8 w-8 text-primary" />}
              title={t('businessplan.pillars.enterprise.title', 'Enterprise-Grade Plattform')}
              description={t('businessplan.pillars.enterprise.desc', 'Security by Design (RBAC, Audit, Idempotenz), Observability, Kafka-Streaming, Neo4j Graph-Analytics – produktionsreif und skalierbar.')}
            />
            <PillarCard
              icon={<LineChart className="h-8 w-8 text-primary" />}
              title={t('businessplan.pillars.metrics.title', 'KPIs & messbare Outcomes')}
              description={t('businessplan.pillars.metrics.desc', 'Klar definierte Meilensteine: Nutzerwachstum, Coverage (100+ Chains), ML-Genauigkeit, Alert-Latenz, Recovery-Fälle, Enterprise-Deals.')}
            />
            <PillarCard
              icon={<Scale className="h-8 w-8 text-primary" />}
              title={t('businessplan.pillars.compliance.title', 'Compliance & Trust')}
              description={t('businessplan.pillars.compliance.desc', 'GDPR, Sanktions-Screening (OFAC, UN, EU, UK), gerichtsverwertbare Evidenz, Audit Trails – regulatorisch belastbar.')}
            />
          </div>
        </div>
      </div>

      {/* Roadmap */}
      <div className="py-16 bg-muted/30">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-5xl mx-auto text-center mb-10">
            <Badge className="mb-3" variant="scan-border">{t('businessplan.roadmap.badge', 'Roadmap')}</Badge>
            <h2 className="text-4xl font-bold mb-3">{t('businessplan.roadmap.title', 'Von PoC zu Enterprise – fokussiert in Phasen')}</h2>
            <p className="text-muted-foreground text-lg">{t('businessplan.roadmap.subtitle', 'Pragmatische, inkrementelle Auslieferung mit validierten Kundensegmenten und klaren Deliverables je Phase.')}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <StageCard
              title={t('businessplan.stage.p0.title', 'Phase 0: PoC & Demo')}
              bullets={[
                t('businessplan.stage.p0.b1', 'Ethereum-Tracing, Risk Scoring, UI-Demo, AI-Agent PoC'),
                t('businessplan.stage.p0.b2', 'Neo4j + TimescaleDB + Kafka lokal'),
                t('businessplan.stage.p0.b3', 'E2E-Smoketests, erste Partner-Demos'),
              ]}
            />
            <StageCard
              title={t('businessplan.stage.p1.title', 'Phase 1: Multi-Chain & Compliance')}
              bullets={[
                t('businessplan.stage.p1.b1', '40+ Chains, Cross-Chain Bridges, Universal Screening'),
                t('businessplan.stage.p1.b2', 'Gerichtsverwertbare Reports, Evidence Vault'),
                t('businessplan.stage.p1.b3', 'Pilotkunden in LE/Banken, SLAs & Support'),
              ]}
            />
            <StageCard
              title={t('businessplan.stage.p2.title', 'Phase 2: Scale & Enterprise')}
              bullets={[
                t('businessplan.stage.p2.b1', 'Automatisiertes KYT, SOAR, Alert-Policies v2'),
                t('businessplan.stage.p2.b2', 'Hochverfügbarkeit, On-Prem/Hybrid Deployments'),
                t('businessplan.stage.p2.b3', 'Zertifizierungen (ISO/SOC), internationale Expansion'),
              ]}
            />
          </div>
        </div>
      </div>

      {/* Proof & References */}
      <div className="py-16">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-10">
              <Badge className="mb-4" variant="scan-border">{t('businessplan.proof.badge', 'Validierungen')}</Badge>
              <h2 className="text-4xl font-bold mb-4">{t('businessplan.proof.title', 'Was bereits steht')}</h2>
              <p className="text-lg text-muted-foreground">{t('businessplan.proof.subtitle', 'Produkt-Substanz statt Slides: produktionsnahe Architektur, umfassende Test-Suite, Demo-Systeme und reale Integrationen.')}</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              <ProofCard
                title={t('businessplan.proof.t1', 'Architektur & Codequalität')}
                points={[
                  t('businessplan.proof.t1.p1', 'FastAPI, Kafka, Neo4j, TimescaleDB, Qdrant, Redis produktionsbereit'),
                  t('businessplan.proof.t1.p2', 'Prometheus/Grafana, Sentry, Health/Ready/Liveness'),
                  t('businessplan.proof.t1.p3', '95%+ Testabdeckung angestrebt, E2E-Smoketests'),
                ]}
              />
              <ProofCard
                title={t('businessplan.proof.t2', 'Funktionale Tiefe')}
                points={[
                  t('businessplan.proof.t2.p1', 'Tracing-Engine, Bridge-Detection, Universal Screening, ML Risk-Scoring'),
                  t('businessplan.proof.t2.p2', 'Evidence Vault, Case Management, Reports (PDF/GraphML/CSV)'),
                  t('businessplan.proof.t2.p3', 'AI-Agent Workflows (LangChain), Chat/Docs RAG'),
                ]}
              />
            </div>

            <div className="mt-12 text-center">
              <LinkLocalized to="/about">
                <Button size="lg" variant="outline" className="inline-flex items-center">
                  <Globe className="h-4 w-4 mr-2" />
                  {t('businessplan.links.learn_more', 'Mehr über uns')}
                </Button>
              </LinkLocalized>
              <a
                className="inline-flex items-center ml-3 text-primary hover:underline"
                href="/docs/business/BUSINESS_PLAN_2025.md"
                target="_blank"
                rel="noopener noreferrer"
              >
                <FileText className="h-4 w-4 mr-2" /> {t('businessplan.links.open_doc', 'Businessplan (Dokument) öffnen')}
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="py-16 border-t">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-4">{t('businessplan.final.title', 'Lass uns gemeinsam Verantwortung übernehmen')}</h2>
            <p className="text-lg text-muted-foreground mb-8">{t('businessplan.final.subtitle', 'Wir helfen, Krypto-Kriminalität zu bekämpfen – mit Technologie, die wirklich wirkt.')}</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <LinkLocalized to="/contact">
                <Button size="xl" variant="gradient">
                  {t('businessplan.final.cta.contact', 'Kontakt aufnehmen')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </LinkLocalized>
              <LinkLocalized to="/register">
                <Button size="xl" variant="outline">
                  {t('businessplan.final.cta.register', 'Jetzt starten')}
                </Button>
              </LinkLocalized>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PillarCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <Card className="border-2">
      <CardContent className="pt-6">
        <div className="text-primary mb-4">{icon}</div>
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
      </CardContent>
    </Card>
  )
}

function StageCard({ title, bullets }: { title: string; bullets: string[] }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <h3 className="text-lg font-semibold mb-3">{title}</h3>
        <div className="space-y-2">
          {bullets.map((b, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span>{b}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function ProofCard({ title, points }: { title: string; points: string[] }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <h3 className="text-lg font-semibold mb-3">{title}</h3>
        <ul className="space-y-2">
          {points.map((p, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-primary mt-0.5" />
              <span>{p}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
