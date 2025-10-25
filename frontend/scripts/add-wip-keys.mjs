#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const LOCALES_DIR = path.join(__dirname, '../src/locales')

const WIP_TRANSLATIONS = {
  en: {
    title: 'Coming soon',
    desc: 'This feature is still under development.',
    cta: 'Learn more'
  },
  de: {
    title: 'Bald verfügbar',
    desc: 'Dieses Feature befindet sich noch in der Entwicklung.',
    cta: 'Mehr erfahren'
  },
  fr: {
    title: 'Bientôt disponible',
    desc: 'Cette fonctionnalité est en cours de développement.',
    cta: 'En savoir plus'
  },
  es: {
    title: 'Próximamente',
    desc: 'Esta función aún está en desarrollo.',
    cta: 'Más información'
  },
  it: {
    title: 'In arrivo',
    desc: 'Questa funzionalità è in fase di sviluppo.',
    cta: 'Scopri di più'
  },
  pt: {
    title: 'Em breve',
    desc: 'Este recurso ainda está em desenvolvimento.',
    cta: 'Saiba mais'
  },
  nl: {
    title: 'Binnenkort beschikbaar',
    desc: 'Deze functie is nog in ontwikkeling.',
    cta: 'Meer informatie'
  },
  sv: {
    title: 'Kommer snart',
    desc: 'Denna funktion utvecklas fortfarande.',
    cta: 'Läs mer'
  },
  fi: {
    title: 'Tulossa pian',
    desc: 'Tämä ominaisuus on vielä kehitysvaiheessa.',
    cta: 'Lue lisää'
  },
  da: {
    title: 'Kommer snart',
    desc: 'Denne funktion er stadig under udvikling.',
    cta: 'Læs mere'
  },
  nb: {
    title: 'Kommer snart',
    desc: 'Denne funksjonen er fortsatt under utvikling.',
    cta: 'Les mer'
  },
  pl: {
    title: 'Już wkrótce',
    desc: 'Ta funkcja jest w trakcie opracowywania.',
    cta: 'Dowiedz się więcej'
  },
  cs: {
    title: 'Již brzy',
    desc: 'Tato funkce je stále ve vývoji.',
    cta: 'Více informací'
  },
  ru: {
    title: 'Скоро',
    desc: 'Эта функция находится в разработке.',
    cta: 'Подробнее'
  },
  tr: {
    title: 'Çok yakında',
    desc: 'Bu özellik hâlâ geliştirme aşamasında.',
    cta: 'Daha fazlası'
  },
  uk: {
    title: 'Незабаром',
    desc: 'Ця функція ще розробляється.',
    cta: 'Дізнатися більше'
  },
  hi: {
    title: 'जल्द आ रहा है',
    desc: 'यह फीचर अभी विकासाधीन है।',
    cta: 'और जानें'
  },
  ja: {
    title: '近日公開',
    desc: 'この機能は現在開発中です。',
    cta: '詳細'
  },
  ko: {
    title: '곧 제공 예정',
    desc: '이 기능은 아직 개발 중입니다.',
    cta: '자세히 보기'
  },
  'zh-CN': {
    title: '即将上线',
    desc: '该功能仍在开发中。',
    cta: '了解更多'
  },
  ar: {
    title: 'قريباً',
    desc: 'هذه الميزة قيد التطوير.',
    cta: 'اعرف المزيد'
  },
}

function loadJSON(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'))
}
function saveJSON(p, obj) {
  fs.writeFileSync(p, JSON.stringify(obj, null, 2) + '\n')
}

const files = fs.readdirSync(LOCALES_DIR).filter(f => f.endsWith('.json'))
let updated = 0

for (const f of files) {
  const fp = path.join(LOCALES_DIR, f)
  const lang = f.replace('.json', '')
  const data = loadJSON(fp)
  
  if (!data.common) data.common = {}
  if (!data.common.wip) {
    const translations = WIP_TRANSLATIONS[lang] || WIP_TRANSLATIONS.en
    data.common.wip = translations
    saveJSON(fp, data)
    updated++
    console.log(`Updated ${f}`)
  }
}

console.log(`Done. Added common.wip to ${updated} locale files.`)
