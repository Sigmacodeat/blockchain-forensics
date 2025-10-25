import React from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import { Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import {
  Shield,
  Target,
  Users,
  TrendingUp,
  Award,
  Globe,
  CheckCircle2,
  ArrowRight,
  Zap,
  Lock,
  Heart
} from 'lucide-react'

export default function AboutPage() {
  const { t } = useTranslation()
  usePageMeta(
    t('about.seo.title', 'Über uns | SIGMACODE Blockchain Forensics'),
    t('about.seo.description', 'Wir bauen die führende Enterprise-Plattform für Blockchain-Forensik: Compliance, Ermittlungen und Intelligence weltweit.')
  )
  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <div className="border-b">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6 py-16">
          <div className="max-w-4xl mx-auto text-center">
            <Badge className="mb-3" variant="scan-border">{t('about.header.badge', 'Über uns')}</Badge>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              {t('about.header.title', 'Die Zukunft der Blockchain-Forensik')}
            </h1>
            <p className="text-sm text-muted-foreground mb-2">SIGMACODE · Blockchain Forensics</p>
            <p className="text-lg text-muted-foreground mb-6">
              {t('about.header.subtitle', 'Wir entwickeln die führende Enterprise-Plattform für Blockchain Intelligence, die Law Enforcement, VASPs und Finanzinstitute beim Schutz vor Krypto-Kriminalität unterstützt.')}
            </p>
          </div>
        </div>
      </div>

      {/* Mission & Vision */}
      <div className="py-16">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid md:grid-cols-2 gap-12 max-w-6xl mx-auto">
            <Card className="border-2">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <Target className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold">{t('about.mission.title', 'Unsere Mission')}</h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">{t('about.mission.desc', 'Wir machen Blockchain-Transaktionen transparent und nachvollziehbar. Unser Ziel ist es, Krypto-Kriminalität zu bekämpfen und legitimen Marktteilnehmern die Werkzeuge zu geben, um Compliance-Anforderungen zu erfüllen und Risiken zu minimieren.')}</p>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    <TrendingUp className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold">{t('about.vision.title', 'Unsere Vision')}</h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">{t('about.vision.desc', 'Eine Welt, in der Blockchain-Technologie ihr volles Potenzial entfalten kann – transparent, sicher und compliant. Wir schaffen die Infrastruktur für eine Zukunft, in der digitale Assets mainstream werden, ohne Kriminalität zu fördern.')}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Values */}
      <div className="py-16 bg-muted/30">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-4xl mx-auto text-center mb-12">
            <Badge className="mb-4" variant="scan-border">{t('about.values.badge', 'Unsere Werte')}</Badge>
            <h2 className="text-4xl font-bold mb-4">
              {t('about.values.title', 'Was uns antreibt')}
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <ValueCard
              icon={<Shield className="h-10 w-10" />}
              title={t('about.values.trust.title', 'Vertrauen & Sicherheit')}
              description={t('about.values.trust.desc', 'Enterprise-Grade Security mit SOC2/ISO27001-Zertifizierungen. Ihre Daten sind bei uns sicher.')}
            />
            <ValueCard
              icon={<Zap className="h-10 w-10" />}
              title={t('about.values.innovation.title', 'Innovation')}
              description={t('about.values.innovation.desc', 'Cutting-Edge-Technologie: AI/ML, Graph Analytics und Real-Time Processing für die besten Ergebnisse.')}
            />
            <ValueCard
              icon={<Heart className="h-10 w-10" />}
              title={t('about.values.customer.title', 'Kundenorientierung')}
              description={t('about.values.customer.desc', 'Enger Austausch mit Law Enforcement und Industrie. Ihre Anforderungen sind unsere Roadmap.')}
            />
            <ValueCard
              icon={<Lock className="h-10 w-10" />}
              title={t('about.values.compliance.title', 'Compliance First')}
              description={t('about.values.compliance.desc', 'GDPR, eIDAS, OFAC-konform. Wir verstehen regulatorische Anforderungen und bauen sie ein.')}
            />
            <ValueCard
              icon={<Globe className="h-10 w-10" />}
              title={t('about.values.global.title', 'Global Reach')}
              description={t('about.values.global.desc', '100+ Blockchains, Multi-Language-Support und internationale Sanktionslisten abgedeckt.')}
            />
            <ValueCard
              icon={<Users className="h-10 w-10" />}
              title={t('about.values.team.title', 'Teamwork')}
              description={t('about.values.team.desc', 'Interdisziplinäres Team aus Forensik-Experten, Entwicklern und Compliance-Spezialisten.')}
            />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="py-16">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <Badge className="mb-4" variant="scan-border">{t('about.stats.badge', 'In Zahlen')}</Badge>
              <h2 className="text-4xl font-bold mb-4">
                {t('about.stats.title', 'Unser Impact')}
              </h2>
            </div>

            <div className="grid md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-5xl font-bold text-primary mb-2">$12.6B+</div>
                <div className="text-sm text-muted-foreground">{t('about.stats.recovered_assets', 'Recovered Assets')}</div>
                <div className="text-xs text-muted-foreground mt-1">{t('about.stats.supported_by_tech', 'unterstützt durch unsere Technologie')}</div>
              </div>
              <div>
                <div className="text-5xl font-bold text-primary mb-2">500+</div>
                <div className="text-sm text-muted-foreground">{t('about.stats.enterprise_customers', 'Enterprise Kunden')}</div>
                <div className="text-xs text-muted-foreground mt-1">{t('about.stats.worldwide', 'weltweit')}</div>
              </div>
              <div>
                <div className="text-5xl font-bold text-primary mb-2">100+</div>
                <div className="text-sm text-muted-foreground">{t('about.stats.blockchains', 'Blockchains')}</div>
                <div className="text-xs text-muted-foreground mt-1">{t('about.stats.supported', 'unterstützt')}</div>
              </div>
              <div>
                <div className="text-5xl font-bold text-primary mb-2">99.9%</div>
                <div className="text-sm text-muted-foreground">{t('about.stats.uptime', 'Uptime')}</div>
                <div className="text-xs text-muted-foreground mt-1">{t('about.stats.sla_guaranteed', 'garantiert per SLA')}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Team & Expertise */}
      <div className="py-16 bg-muted/30">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <Badge className="mb-4" variant="scan-border">{t('about.team.badge', 'Expertise')}</Badge>
              <h2 className="text-4xl font-bold mb-4">
                {t('about.team.title', 'Unser Team')}
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                {t('about.team.subtitle', 'Experten aus Blockchain-Forensik, Law Enforcement, FinTech und Machine Learning')}
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <ExpertiseCard
                icon={<Shield className="h-8 w-8" />}
                title={t('about.team.forensics.title', 'Forensik-Experten')}
                description={t('about.team.forensics.desc', 'Ex-Law-Enforcement mit jahrelanger Erfahrung in Crypto-Crime-Investigations')}
                highlights={[t('about.team.forensics.h1', 'FBI/BKA Alumni'), t('about.team.forensics.h2', 'Darknet Takedowns'), t('about.team.forensics.h3', 'Asset Recovery')]}
              />
              <ExpertiseCard
                icon={<Zap className="h-8 w-8" />}
                title={t('about.team.tech.title', 'Tech-Spezialisten')}
                description={t('about.team.tech.desc', 'Engineers von Top-Tech-Unternehmen mit Blockchain-Expertise')}
                highlights={[t('about.team.tech.h1', 'Ex-FAANG'), t('about.team.tech.h2', 'Blockchain Core Devs'), t('about.team.tech.h3', 'Security Experts')]}
              />
              <ExpertiseCard
                icon={<Award className="h-8 w-8" />}
                title={t('about.team.compliance.title', 'Compliance & Legal')}
                description={t('about.team.compliance.desc', 'Regulierungs-Experten für AML/CFT und internationale Sanktionen')}
                highlights={[t('about.team.compliance.h1', 'Ex-Regulators'), t('about.team.compliance.h2', 'AML Specialists'), t('about.team.compliance.h3', 'Legal Counsel')]}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Customers & Trust */}
      <div className="py-16">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <Badge className="mb-4" variant="scan-border">{t('about.trust.badge', 'Vertrauen')}</Badge>
              <h2 className="text-4xl font-bold mb-4">
                {t('about.trust.title', 'Wer uns vertraut')}
              </h2>
              <p className="text-xl text-muted-foreground">
                {t('about.trust.subtitle', 'Führende Organisationen weltweit setzen auf unsere Technologie')}
              </p>
            </div>

            <div className="grid md:grid-cols-4 gap-8">
              <CustomerCard title={t('about.trust.le.title', 'Law Enforcement')} description={t('about.trust.le.desc', 'FBI, Europol, nationale Strafverfolgungsbehörden')} />
              <CustomerCard title={t('about.trust.ce.title', 'Crypto Exchanges')} description={t('about.trust.ce.desc', 'Top-10-Exchanges für AML und Transaction Monitoring')} />
              <CustomerCard title={t('about.trust.fi.title', 'Banken & FinTechs')} description={t('about.trust.fi.desc', 'Tier-1-Banken mit Crypto-Exposure')} />
              <CustomerCard title={t('about.trust.reg.title', 'Regulatoren')} description={t('about.trust.reg.desc', 'Finanzaufsichtsbehörden für Market Surveillance')} />
            </div>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="py-16 border-t">
        <div className="container mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-4">{t('about.cta.title', 'Werde Teil der Lösung')}</h2>
            <p className="text-lg text-muted-foreground mb-8">{t('about.cta.subtitle', 'Starte jetzt mit einer kostenlosen Demo oder kontaktiere unser Team')}</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <LinkLocalized to="/register">
                <Button size="xl" variant="gradient">
                  {t('about.cta.demo', 'Demo anfragen')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </LinkLocalized>
              <LinkLocalized to="/pricing">
                <Button size="xl" variant="outline">
                  {t('about.cta.pricing', 'Pricing ansehen')}
                </Button>
              </LinkLocalized>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface ValueCardProps {
  icon: React.ReactNode
  title: string
  description: string
}

function ValueCard({ icon, title, description }: ValueCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-primary mb-4">{icon}</div>
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}

interface ExpertiseCardProps {
  icon: React.ReactNode
  title: string
  description: string
  highlights: string[]
}

function ExpertiseCard({ icon, title, description, highlights }: ExpertiseCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-primary mb-4">{icon}</div>
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4">{description}</p>
        <div className="space-y-2">
          {highlights.map((h, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span>{h}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

interface CustomerCardProps {
  title: string
  description: string
}

function CustomerCard({ title, description }: CustomerCardProps) {
  return (
    <Card className="text-center">
      <CardContent className="pt-6">
        <h4 className="text-lg font-semibold mb-2">{title}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}
