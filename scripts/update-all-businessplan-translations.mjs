#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOCALES_DIR = path.join(__dirname, '../frontend/src/locales');

const NATIVE = {
  bs: { badge: 'Poslovni Plan i Financiranje', title: '81% Stopa Financiranja · €2,25M Ukupno Financiranje', kpis: 'Metrike Financiranja', kpi1: 'Ukupno Financiranje', kpi2: 'Stopa Financiranja', kpi3: 'Trajanje', cta: 'Pogledaj Poslovni Plan i Financiranje' },
  sr: { badge: 'Poslovni Plan i Finansiranje', title: '81% Stopa Finansiranja · €2,25M Ukupno Finansiranje', kpis: 'Metrike Finansiranja', kpi1: 'Ukupno Finansiranje', kpi2: 'Stopa Finansiranja', kpi3: 'Trajanje', cta: 'Pogledaj Poslovni Plan i Finansiranje' },
  mk: { badge: 'Бизнис План и Финансирање', title: '81% Стапка · €2,25M Вкупно', kpis: 'Метрики', kpi1: 'Вкупно Финансирање', kpi2: 'Стапка', kpi3: 'Траење', cta: 'Погледнете' },
  sq: { badge: 'Plani i Biznesit', title: '81% Norma · €2,25M Total', kpis: 'Matjet', kpi1: 'Financim Total', kpi2: 'Norma', kpi3: 'Kohëzgjatja', cta: 'Shiko Planin' },
  mt: { badge: 'Pjan tan-Negozju', title: '81% Rata · €2,25M Total', kpis: 'Metriċi', kpi1: 'Finanzjament Totali', kpi2: 'Rata', kpi3: 'Dewmien', cta: 'Ara l-Pjan' },
  ga: { badge: 'Plean Gnó', title: '81% Ráta · €2,25M Iomlán', kpis: 'Méadracht', kpi1: 'Maoiniú Iomlán', kpi2: 'Ráta', kpi3: 'Fad', cta: 'Féach Plean' },
  lb: { badge: 'Geschäftsplan', title: '81% Quot · €2,25M Total', kpis: 'Metriken', kpi1: 'Total Finanzéierung', kpi2: 'Quot', kpi3: 'Dauer', cta: 'Plang gesinn' },
  rm: { badge: 'Plan d\'affar', title: '81% Quota · €2,25M Totala', kpis: 'Metrics', kpi1: 'Finanziaziun totala', kpi2: 'Quota', kpi3: 'Durada', cta: 'Guardar plan' },
  is: { badge: 'Viðskiptaáætlun', title: '81% Hlutfall · €2,25M Heildar', kpis: 'Mælingar', kpi1: 'Heildarfjármögnun', kpi2: 'Hlutfall', kpi3: 'Lengd', cta: 'Skoða Áætlun' },
  nn: { badge: 'Forretningsplan', title: '81% Rate · €2,25M Total', kpis: 'Målingar', kpi1: 'Total Finansiering', kpi2: 'Rate', kpi3: 'Varigheit', cta: 'Sjå Plan' },
  ja: { badge: 'ビジネスプラン', title: '81% 資金調達率 · €225万', kpis: '指標', kpi1: '総資金', kpi2: '資金調達率', kpi3: '期間', cta: 'プランを見る' },
  ko: { badge: '사업계획서', title: '81% 자금조달률 · €225만', kpis: '지표', kpi1: '총 자금', kpi2: '자금조달률', kpi3: '기간', cta: '계획서 보기' },
  'zh-CN': { badge: '商业计划', title: '81% 资金比率 · €225万', kpis: '指标', kpi1: '总资金', kpi2: '资金比率', kpi3: '期限', cta: '查看计划' },
  hi: { badge: 'व्यवसाय योजना', title: '81% वित्तपोषण · €2.25M', kpis: 'मेट्रिक्स', kpi1: 'कुल वित्तपोषण', kpi2: 'वित्तपोषण दर', kpi3: 'अवधि', cta: 'योजना देखें' },
  ar: { badge: 'خطة الأعمال', title: '81% معدل التمويل · €2.25M', kpis: 'المقاييس', kpi1: 'التمويل الكلي', kpi2: 'معدل التمويل', kpi3: 'المدة', cta: 'عرض الخطة' },
  he: { badge: 'תוכנית עסקית', title: '81% שיעור מימון · €2.25M', kpis: 'מדדים', kpi1: 'מימון כולל', kpi2: 'שיעור מימון', kpi3: 'משך', cta: 'הצג תוכנית' },
  tr: { badge: 'İş Planı', title: '81% Finansman Oranı · €2,25M', kpis: 'Metrikler', kpi1: 'Toplam Finansman', kpi2: 'Finansman Oranı', kpi3: 'Süre', cta: 'Planı Görüntüle' }
};

let updated = 0;
for (const [lang, trans] of Object.entries(NATIVE)) {
  const file = path.join(LOCALES_DIR, `${lang}.json`);
  if (!fs.existsSync(file)) continue;
  
  try {
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (!data.landing?.businessplan) continue;
    
    Object.assign(data.landing.businessplan, trans);
    fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
    console.log(`✅ ${lang}`);
    updated++;
  } catch (e) {
    console.error(`❌ ${lang}: ${e.message}`);
  }
}

console.log(`\n✅ ${updated} Sprachen mit nativen Übersetzungen aktualisiert!`);
