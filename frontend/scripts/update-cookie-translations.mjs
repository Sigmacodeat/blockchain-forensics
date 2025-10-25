#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const LOCALES_DIR = path.join(__dirname, '../src/locales')

// Top languages to update with native cookie translations
const TARGETS = ['it','pt','nl','sv','fi','pl','cs','da','ko','ja','zh-CN','tr','ru','uk','nb']

// Keys to ensure exist
const KEYS = [
  'banner_aria','title','title_short','description','privacy_link','terms_link','imprint_link','only_necessary','accept_all','preferences','save_preferences','manage','analytics_title','analytics_desc','marketing_title','marketing_desc','all_optional_title','all_optional_desc'
]

const MAP = {
  it: {
    banner_aria: 'Banner cookie',
    title: 'Cookie e privacy',
    title_short: 'Cookie',
    description: 'Usiamo cookie essenziali per il funzionamento del sito. I cookie opzionali di analisi ci aiutano a capire e migliorare l’uso. Puoi accettare tutti i cookie o consentire solo quelli necessari. Puoi modificare la scelta in qualsiasi momento nelle impostazioni.',
    privacy_link: 'Informativa privacy', terms_link: 'Termini di servizio', imprint_link: 'Note legali',
    only_necessary: 'Solo necessari', accept_all: 'Accetta tutti', preferences: 'Preferenze', save_preferences: 'Salva preferenze', manage: 'Impostazioni cookie',
    analytics_title: 'Cookie di analisi', analytics_desc: "Ci aiutano a capire l'utilizzo per migliorare il sito.",
    marketing_title: 'Cookie di marketing', marketing_desc: 'Abilitano contenuti e offerte personalizzate.',
    all_optional_title: 'Attiva tutti gli opzionali', all_optional_desc: 'Attiva sia i cookie di analisi che di marketing.'
  },
  pt: {
    banner_aria: 'Banner de cookies', title: 'Cookies e privacidade', title_short: 'Cookies',
    description: 'Usamos cookies essenciais para operar este site. Cookies opcionais de análise ajudam a entender e melhorar o uso. Você pode aceitar todos os cookies ou permitir apenas os necessários. Você pode alterar sua escolha a qualquer momento nas configurações.',
    privacy_link: 'Política de privacidade', terms_link: 'Termos de serviço', imprint_link: 'Aviso legal',
    only_necessary: 'Apenas necessários', accept_all: 'Aceitar todos', preferences: 'Preferências', save_preferences: 'Salvar preferências', manage: 'Configurações de cookies',
    analytics_title: 'Cookies de análise', analytics_desc: 'Ajuda a entender o uso para melhorar o site.',
    marketing_title: 'Cookies de marketing', marketing_desc: 'Permite conteúdo e ofertas personalizadas.',
    all_optional_title: 'Ativar todos os opcionais', all_optional_desc: 'Ativa cookies de análise e marketing.'
  },
  nl: {
    banner_aria: 'Cookiebanner', title: 'Cookies en privacy', title_short: 'Cookies',
    description: 'We gebruiken essentiële cookies om deze website te laten werken. Optionele analyse-cookies helpen ons gebruik te begrijpen en te verbeteren. Je kunt alle cookies accepteren of alleen noodzakelijke toestaan. Je keuze kun je later in de instellingen aanpassen.',
    privacy_link: 'Privacyverklaring', terms_link: 'Servicevoorwaarden', imprint_link: 'Colofon',
    only_necessary: 'Alleen noodzakelijke', accept_all: 'Alles accepteren', preferences: 'Voorkeuren', save_preferences: 'Voorkeuren opslaan', manage: 'Cookie-instellingen',
    analytics_title: 'Analyse-cookies', analytics_desc: 'Helpt ons gebruik te begrijpen om de site te verbeteren.',
    marketing_title: 'Marketingcookies', marketing_desc: 'Maakt gepersonaliseerde inhoud en aanbiedingen mogelijk.',
    all_optional_title: 'Alle optionele inschakelen', all_optional_desc: 'Schakelt zowel analyse- als marketingcookies in.'
  },
  sv: {
    banner_aria: 'Cookiebanner', title: 'Cookies och integritet', title_short: 'Cookies',
    description: 'Vi använder nödvändiga cookies för att driva webbplatsen. Valfria analyscookies hjälper oss att förstå och förbättra användningen. Du kan acceptera alla cookies eller endast tillåta nödvändiga. Du kan ändra ditt val när som helst i inställningarna.',
    privacy_link: 'Integritetspolicy', terms_link: 'Användarvillkor', imprint_link: 'Impressum',
    only_necessary: 'Endast nödvändiga', accept_all: 'Acceptera alla', preferences: 'Inställningar', save_preferences: 'Spara inställningar', manage: 'Cookie-inställningar',
    analytics_title: 'Analyscookies', analytics_desc: 'Hjälper oss förstå användning och förbättra webbplatsen.',
    marketing_title: 'Marknadsföringscookies', marketing_desc: 'Möjliggör personligt innehåll och erbjudanden.',
    all_optional_title: 'Aktivera alla valfria', all_optional_desc: 'Aktiverar både analys- och marknadsföringscookies.'
  },
  fi: {
    banner_aria: 'Evästeilmoitus', title: 'Evästeet ja tietosuoja', title_short: 'Evästeet',
    description: 'Käytämme välttämättömiä evästeitä sivuston toimintaan. Valinnaiset analytiikkaevästeet auttavat meitä ymmärtämään käyttöä ja parantamaan sivustoa. Voit hyväksyä kaikki evästeet tai sallia vain välttämättömät. Voit muuttaa valintaa milloin tahansa asetuksissa.',
    privacy_link: 'Tietosuojaseloste', terms_link: 'Käyttöehdot', imprint_link: 'Juridiset tiedot',
    only_necessary: 'Vain välttämättömät', accept_all: 'Hyväksy kaikki', preferences: 'Asetukset', save_preferences: 'Tallenna asetukset', manage: 'Evästeasetukset',
    analytics_title: 'Analytiikkaevästeet', analytics_desc: 'Auttaa ymmärtämään käyttöä sivuston parantamiseksi.',
    marketing_title: 'Markkinointievästeet', marketing_desc: 'Mahdollistaa personoidun sisällön ja tarjoukset.',
    all_optional_title: 'Ota kaikki valinnaiset käyttöön', all_optional_desc: 'Ottaa käyttöön analytiikka- ja markkinointievästeet.'
  },
  pl: {
    banner_aria: 'Baner cookie', title: 'Pliki cookie i prywatność', title_short: 'Cookies',
    description: 'Używamy niezbędnych plików cookie do działania tej strony. Opcjonalne pliki cookie analityczne pomagają nam zrozumieć i ulepszać korzystanie. Możesz zaakceptować wszystkie pliki cookie lub zezwolić tylko na niezbędne. W każdej chwili możesz zmienić wybór w ustawieniach.',
    privacy_link: 'Polityka prywatności', terms_link: 'Warunki świadczenia usług', imprint_link: 'Informacje prawne',
    only_necessary: 'Tylko niezbędne', accept_all: 'Akceptuj wszystkie', preferences: 'Preferencje', save_preferences: 'Zapisz preferencje', manage: 'Ustawienia plików cookie',
    analytics_title: 'Pliki cookie analityczne', analytics_desc: 'Pomagają zrozumieć użycie w celu ulepszenia strony.',
    marketing_title: 'Pliki cookie marketingowe', marketing_desc: 'Umożliwia spersonalizowane treści i oferty.',
    all_optional_title: 'Włącz wszystkie opcjonalne', all_optional_desc: 'Włącza zarówno analityczne, jak i marketingowe pliki cookie.'
  },
  cs: {
    banner_aria: 'Banner cookies', title: 'Cookies a soukromí', title_short: 'Cookies',
    description: 'Používáme nezbytné soubory cookie pro provoz tohoto webu. Volitelné analytické soubory cookie nám pomáhají porozumět používání a zlepšovat web. Můžete přijmout všechny soubory cookie nebo povolit pouze nezbytné. Svou volbu můžete kdykoli změnit v nastavení.',
    privacy_link: 'Zásady ochrany osobních údajů', terms_link: 'Podmínky služby', imprint_link: 'Právní informace',
    only_necessary: 'Pouze nezbytné', accept_all: 'Přijmout vše', preferences: 'Předvolby', save_preferences: 'Uložit předvolby', manage: 'Nastavení souborů cookie',
    analytics_title: 'Analytické soubory cookie', analytics_desc: 'Pomáhají nám porozumět používání a zlepšovat web.',
    marketing_title: 'Marketingové soubory cookie', marketing_desc: 'Umožňují personalizovaný obsah a nabídky.',
    all_optional_title: 'Povolit všechny volitelné', all_optional_desc: 'Povolí analytické i marketingové cookies.'
  },
  da: {
    banner_aria: 'Cookiebanner', title: 'Cookies og privatliv', title_short: 'Cookies',
    description: 'Vi bruger nødvendige cookies til at drive dette websted. Valgfrie analyse-cookies hjælper os med at forstå og forbedre brugen. Du kan acceptere alle cookies eller kun tillade nødvendige. Du kan ændre dit valg når som helst i indstillingerne.',
    privacy_link: 'Privatlivspolitik', terms_link: 'Servicevilkår', imprint_link: 'Juridiske oplysninger',
    only_necessary: 'Kun nødvendige', accept_all: 'Acceptér alle', preferences: 'Indstillinger', save_preferences: 'Gem indstillinger', manage: 'Cookieindstillinger',
    analytics_title: 'Analyse-cookies', analytics_desc: 'Hjælper os med at forstå brugen og forbedre webstedet.',
    marketing_title: 'Marketing-cookies', marketing_desc: 'Muliggør personligt indhold og tilbud.',
    all_optional_title: 'Aktivér alle valgfrie', all_optional_desc: 'Aktiverer både analyse- og marketingcookies.'
  },
  ko: {
    banner_aria: '쿠키 배너', title: '쿠키 및 개인정보', title_short: '쿠키',
    description: '이 웹사이트 운영에는 필수 쿠키를 사용합니다. 선택적 분석 쿠키는 사용 현황을 이해하고 개선하는 데 도움을 줍니다. 모든 쿠키를 허용하거나 필요한 쿠키만 허용할 수 있으며, 설정에서 언제든지 변경할 수 있습니다.',
    privacy_link: '개인정보 처리방침', terms_link: '서비스 이용약관', imprint_link: '법적 고지',
    only_necessary: '필수만', accept_all: '모두 허용', preferences: '설정', save_preferences: '설정 저장', manage: '쿠키 설정',
    analytics_title: '분석 쿠키', analytics_desc: '사이트 개선을 위해 사용 현황을 이해하는 데 도움을 줍니다.',
    marketing_title: '마케팅 쿠키', marketing_desc: '맞춤형 콘텐츠와 오퍼를 제공합니다.',
    all_optional_title: '선택 항목 모두 활성화', all_optional_desc: '분석 및 마케팅 쿠키를 모두 활성화합니다.'
  },
  ja: {
    banner_aria: 'クッキーバナー', title: 'Cookie とプライバシー', title_short: 'Cookie',
    description: '当サイトの運営には必須の Cookie を使用しています。任意の分析 Cookie は利用状況の理解と改善に役立ちます。すべての Cookie を許可するか、必要なもののみを許可できます。設定でいつでも変更できます。',
    privacy_link: 'プライバシーポリシー', terms_link: '利用規約', imprint_link: '特定商取引法に基づく表記',
    only_necessary: '必須のみ', accept_all: 'すべて許可', preferences: '設定', save_preferences: '設定を保存', manage: 'Cookie 設定',
    analytics_title: '分析用 Cookie', analytics_desc: '利用状況を理解しサイトの改善に役立ちます。',
    marketing_title: 'マーケティング用 Cookie', marketing_desc: 'パーソナライズされたコンテンツやオファーを可能にします。',
    all_optional_title: 'オプションをすべて有効化', all_optional_desc: '分析とマーケティングの Cookie を有効化します。'
  },
  'zh-CN': {
    banner_aria: 'Cookie 横幅', title: 'Cookie 与隐私', title_short: 'Cookie',
    description: '我们使用必要的 Cookie 以运行本网站。可选的分析 Cookie 有助于我们了解并改进使用情况。您可以接受所有 Cookie 或仅允许必要的 Cookie。您可在设置中随时更改选择。',
    privacy_link: '隐私政策', terms_link: '服务条款', imprint_link: '法律声明',
    only_necessary: '仅必要', accept_all: '全部接受', preferences: '首选项', save_preferences: '保存首选项', manage: 'Cookie 设置',
    analytics_title: '分析类 Cookie', analytics_desc: '帮助我们了解使用情况以改进网站。',
    marketing_title: '营销类 Cookie', marketing_desc: '启用个性化内容和优惠。',
    all_optional_title: '启用所有可选项', all_optional_desc: '启用分析和营销类 Cookie。'
  },
  tr: {
    banner_aria: 'Çerez bildirimi', title: 'Çerezler ve gizlilik', title_short: 'Çerezler',
    description: 'Bu siteyi çalıştırmak için gerekli çerezleri kullanıyoruz. İsteğe bağlı analiz çerezleri, kullanımı anlamamıza ve iyileştirmemize yardımcı olur. Tüm çerezleri kabul edebilir veya yalnızca gerekli olanlara izin verebilirsiniz. Seçiminizi ayarlardan istediğiniz zaman değiştirebilirsiniz.',
    privacy_link: 'Gizlilik politikası', terms_link: 'Hizmet şartları', imprint_link: 'Yasal bildirim',
    only_necessary: 'Yalnızca gerekli', accept_all: 'Tümünü kabul et', preferences: 'Ayarlar', save_preferences: 'Ayarları kaydet', manage: 'Çerez ayarları',
    analytics_title: 'Analiz çerezleri', analytics_desc: 'Kullanımı anlamamıza ve siteyi iyileştirmemize yardımcı olur.',
    marketing_title: 'Pazarlama çerezleri', marketing_desc: 'Kişiselleştirilmiş içerik ve teklifler sağlar.',
    all_optional_title: 'Tüm isteğe bağlıları etkinleştir', all_optional_desc: 'Analiz ve pazarlama çerezlerini etkinleştirir.'
  },
  ru: {
    banner_aria: 'Баннер cookie', title: 'Cookie и конфиденциальность', title_short: 'Cookie',
    description: 'Мы используем необходимые cookie для работы сайта. Необязательные аналитические cookie помогают понять использование и улучшить сайт. Вы можете принять все cookie или разрешить только необходимые. Вы можете изменить выбор в настройках в любое время.',
    privacy_link: 'Политика конфиденциальности', terms_link: 'Условия обслуживания', imprint_link: 'Юридическая информация',
    only_necessary: 'Только необходимые', accept_all: 'Принять все', preferences: 'Настройки', save_preferences: 'Сохранить настройки', manage: 'Настройки cookie',
    analytics_title: 'Аналитические cookie', analytics_desc: 'Помогают понять использование для улучшения сайта.',
    marketing_title: 'Маркетинговые cookie', marketing_desc: 'Включают персонализированный контент и предложения.',
    all_optional_title: 'Включить все необязательные', all_optional_desc: 'Включает аналитические и маркетинговые cookie.'
  },
  uk: {
    banner_aria: 'Банер cookie', title: 'Cookie та конфіденційність', title_short: 'Cookie',
    description: 'Ми використовуємо необхідні файли cookie для роботи цього сайту. Необов’язкові аналітичні cookie допомагають зрозуміти використання та покращити сайт. Ви можете прийняти всі cookie або дозволити лише необхідні. Своє рішення можна змінити будь-коли в налаштуваннях.',
    privacy_link: 'Політика конфіденційності', terms_link: 'Умови надання послуг', imprint_link: 'Юридична інформація',
    only_necessary: 'Лише необхідні', accept_all: 'Прийняти всі', preferences: 'Налаштування', save_preferences: 'Зберегти налаштування', manage: 'Налаштування cookie',
    analytics_title: 'Аналітичні cookie', analytics_desc: 'Допомагають зрозуміти використання для покращення сайту.',
    marketing_title: 'Маркетингові cookie', marketing_desc: 'Дозволяють персоналізований контент і пропозиції.',
    all_optional_title: 'Увімкнути всі необов’язкові', all_optional_desc: 'Увімкнути аналітичні та маркетингові cookie.'
  },
  nb: {
    banner_aria: 'Informasjonskapselbanner', title: 'Informasjonskapsler og personvern', title_short: 'Cookies',
    description: 'Vi bruker nødvendige informasjonskapsler for å drive dette nettstedet. Valgfrie analyse-kapsler hjelper oss å forstå og forbedre bruken. Du kan godta alle kapsler eller kun tillate nødvendige. Du kan endre valget når som helst i innstillingene.',
    privacy_link: 'Personvernerklæring', terms_link: 'Vilkår for bruk', imprint_link: 'Juridisk informasjon',
    only_necessary: 'Kun nødvendige', accept_all: 'Godta alle', preferences: 'Innstillinger', save_preferences: 'Lagre innstillinger', manage: 'Cookie-innstillinger',
    analytics_title: 'Analyse-kapsler', analytics_desc: 'Hjelper oss å forstå bruken for å forbedre nettstedet.',
    marketing_title: 'Markedsføringskapsler', marketing_desc: 'Muliggjør personlig innhold og tilbud.',
    all_optional_title: 'Aktiver alle valgfrie', all_optional_desc: 'Aktiverer både analyse- og markedsføringskapsler.'
  },
}

function updateLang(lang){
  const f = path.join(LOCALES_DIR, `${lang}.json`)
  if (!fs.existsSync(f)) return false
  const data = JSON.parse(fs.readFileSync(f,'utf8'))
  data.cookie = data.cookie || {}
  const src = MAP[lang]
  if (!src) return false
  let changed = false
  for (const k of KEYS){
    const val = src[k]
    if (val && data.cookie[k] !== val){ data.cookie[k] = val; changed = true }
  }
  if (changed){ fs.writeFileSync(f, JSON.stringify(data, null, 2) + '\n') }
  return changed
}

let updated = 0
for (const lang of TARGETS){ if (updateLang(lang)) { updated++ ; console.log('updated', lang) } }
console.log(`Done. Updated ${updated} languages.`)
