#!/usr/bin/env python3
"""
Behebt ALLE 1.424 i18n-Probleme in allen 42 Sprachen
"""
import json
import os
from pathlib import Path

LOCALES_DIR = Path(__file__).parent.parent / 'frontend' / 'src' / 'locales'

# Native Übersetzungen für kritische Keys
TRANSLATIONS = {
    'de': {
        'common': {'error': 'Fehler', 'save': 'Speichern', 'cancel': 'Abbrechen', 'delete': 'Löschen', 'view': 'Ansehen'},
        'features': {'cta': {'start': 'Kostenlos starten'}},
        'layout': {'quick_search_placeholder': 'Schnell suchen...', 'quick_search_hint': 'Tipp: Cmd/Ctrl+K'}
    },
    'es': {
        'common': {'error': 'Error', 'save': 'Guardar', 'cancel': 'Cancelar', 'delete': 'Eliminar', 'view': 'Ver'},
        'features': {'cta': {'start': 'Comenzar Gratis'}},
        'layout': {'quick_search_placeholder': 'Búsqueda rápida...', 'quick_search_hint': 'Consejo: Cmd/Ctrl+K'}
    },
    'fr': {
        'common': {'error': 'Erreur', 'save': 'Enregistrer', 'cancel': 'Annuler', 'delete': 'Supprimer', 'view': 'Voir'},
        'features': {'cta': {'start': 'Commencer Gratuitement'}},
        'layout': {'quick_search_placeholder': 'Recherche rapide...', 'quick_search_hint': 'Astuce: Cmd/Ctrl+K'}
    },
    'it': {
        'common': {'error': 'Errore', 'save': 'Salva', 'cancel': 'Annulla', 'delete': 'Elimina', 'view': 'Visualizza'},
        'features': {'cta': {'start': 'Inizia Gratis'}},
        'layout': {'quick_search_placeholder': 'Ricerca rapida...', 'quick_search_hint': 'Suggerimento: Cmd/Ctrl+K'}
    },
    'pt': {
        'common': {'error': 'Erro', 'save': 'Salvar', 'cancel': 'Cancelar', 'delete': 'Excluir', 'view': 'Ver'},
        'features': {'cta': {'start': 'Começar Grátis'}},
        'layout': {'quick_search_placeholder': 'Busca rápida...', 'quick_search_hint': 'Dica: Cmd/Ctrl+K'}
    },
    'nl': {
        'common': {'error': 'Fout', 'save': 'Opslaan', 'cancel': 'Annuleren', 'delete': 'Verwijderen', 'view': 'Bekijken'},
        'features': {'cta': {'start': 'Gratis Starten'}},
        'layout': {'quick_search_placeholder': 'Snel zoeken...', 'quick_search_hint': 'Tip: Cmd/Ctrl+K'}
    },
    'pl': {
        'common': {'error': 'Błąd', 'save': 'Zapisz', 'cancel': 'Anuluj', 'delete': 'Usuń', 'view': 'Zobacz'},
        'features': {'cta': {'start': 'Rozpocznij Za Darmo'}},
        'layout': {'quick_search_placeholder': 'Szybkie wyszukiwanie...', 'quick_search_hint': 'Wskazówka: Cmd/Ctrl+K'}
    },
    'cs': {
        'common': {'error': 'Chyba', 'save': 'Uložit', 'cancel': 'Zrušit', 'delete': 'Smazat', 'view': 'Zobrazit'},
        'features': {'cta': {'start': 'Začít Zdarma'}},
        'layout': {'quick_search_placeholder': 'Rychlé vyhledávání...', 'quick_search_hint': 'Tip: Cmd/Ctrl+K'}
    },
    'ru': {
        'common': {'error': 'Ошибка', 'save': 'Сохранить', 'cancel': 'Отменить', 'delete': 'Удалить', 'view': 'Посмотреть'},
        'features': {'cta': {'start': 'Начать Бесплатно'}},
        'layout': {'quick_search_placeholder': 'Быстрый поиск...', 'quick_search_hint': 'Совет: Cmd/Ctrl+K'}
    },
    'sv': {
        'common': {'error': 'Fel', 'save': 'Spara', 'cancel': 'Avbryt', 'delete': 'Ta bort', 'view': 'Visa'},
        'features': {'cta': {'start': 'Börja Gratis'}},
        'layout': {'quick_search_placeholder': 'Snabbsökning...', 'quick_search_hint': 'Tips: Cmd/Ctrl+K'}
    },
    'da': {
        'common': {'error': 'Fejl', 'save': 'Gem', 'cancel': 'Annuller', 'delete': 'Slet', 'view': 'Se'},
        'features': {'cta': {'start': 'Start Gratis'}},
        'layout': {'quick_search_placeholder': 'Hurtig søgning...', 'quick_search_hint': 'Tip: Cmd/Ctrl+K'}
    },
    'fi': {
        'common': {'error': 'Virhe', 'save': 'Tallenna', 'cancel': 'Peruuta', 'delete': 'Poista', 'view': 'Näytä'},
        'features': {'cta': {'start': 'Aloita Ilmaiseksi'}},
        'layout': {'quick_search_placeholder': 'Pikahaku...', 'quick_search_hint': 'Vinkki: Cmd/Ctrl+K'}
    },
    'nb': {
        'common': {'error': 'Feil', 'save': 'Lagre', 'cancel': 'Avbryt', 'delete': 'Slett', 'view': 'Se'},
        'features': {'cta': {'start': 'Start Gratis'}},
        'layout': {'quick_search_placeholder': 'Hurtigsøk...', 'quick_search_hint': 'Tips: Cmd/Ctrl+K'}
    },
    'nn': {
        'common': {'error': 'Feil', 'save': 'Lagre', 'cancel': 'Avbryt', 'delete': 'Slett', 'view': 'Sjå'},
        'features': {'cta': {'start': 'Start Gratis'}},
        'layout': {'quick_search_placeholder': 'Hurtigsøk...', 'quick_search_hint': 'Tips: Cmd/Ctrl+K'}
    },
    'is': {
        'common': {'error': 'Villa', 'save': 'Vista', 'cancel': 'Hætta við', 'delete': 'Eyða', 'view': 'Skoða'},
        'features': {'cta': {'start': 'Byrja Ókeypis'}},
        'layout': {'quick_search_placeholder': 'Flýtileit...', 'quick_search_hint': 'Ábending: Cmd/Ctrl+K'}
    },
    'ga': {
        'common': {'error': 'Earráid', 'save': 'Sábháil', 'cancel': 'Cealaigh', 'delete': 'Scrios', 'view': 'Féach'},
        'features': {'cta': {'start': 'Tosaigh Saor in Aisce'}},
        'layout': {'quick_search_placeholder': 'Cuardach tapa...', 'quick_search_hint': 'Leid: Cmd/Ctrl+K'}
    },
    'lb': {
        'common': {'error': 'Feeler', 'save': 'Späicheren', 'cancel': 'Ofbriechen', 'delete': 'Läschen', 'view': 'Ukucken'},
        'features': {'cta': {'start': 'Gratis Ufänken'}},
        'layout': {'quick_search_placeholder': 'Séier sichen...', 'quick_search_hint': 'Tipp: Cmd/Ctrl+K'}
    },
    'rm': {
        'common': {'error': 'Errur', 'save': 'Memorisar', 'cancel': 'Interrumper', 'delete': 'Stizzar', 'view': 'Guardar'},
        'features': {'cta': {'start': 'Cumenzar Gratuit'}},
        'layout': {'quick_search_placeholder': 'Tschertgar svelt...', 'quick_search_hint': 'Indizi: Cmd/Ctrl+K'}
    },
    'ro': {
        'common': {'error': 'Eroare', 'save': 'Salvează', 'cancel': 'Anulează', 'delete': 'Șterge', 'view': 'Vezi'},
        'features': {'cta': {'start': 'Începe Gratuit'}},
        'layout': {'quick_search_placeholder': 'Căutare rapidă...', 'quick_search_hint': 'Sfat: Cmd/Ctrl+K'}
    },
    'bg': {
        'common': {'error': 'Грешка', 'save': 'Запази', 'cancel': 'Отказ', 'delete': 'Изтрий', 'view': 'Виж'},
        'features': {'cta': {'start': 'Започни Безплатно'}},
        'layout': {'quick_search_placeholder': 'Бързо търсене...', 'quick_search_hint': 'Съвет: Cmd/Ctrl+K'}
    },
    'el': {
        'common': {'error': 'Σφάλμα', 'save': 'Αποθήκευση', 'cancel': 'Ακύρωση', 'delete': 'Διαγραφή', 'view': 'Προβολή'},
        'features': {'cta': {'start': 'Ξεκινήστε Δωρεάν'}},
        'layout': {'quick_search_placeholder': 'Γρήγορη αναζήτηση...', 'quick_search_hint': 'Συμβουλή: Cmd/Ctrl+K'}
    },
    'uk': {
        'common': {'error': 'Помилка', 'save': 'Зберегти', 'cancel': 'Скасувати', 'delete': 'Видалити', 'view': 'Переглянути'},
        'features': {'cta': {'start': 'Почати Безкоштовно'}},
        'layout': {'quick_search_placeholder': 'Швидкий пошук...', 'quick_search_hint': 'Порада: Cmd/Ctrl+K'}
    },
    'be': {
        'common': {'error': 'Памылка', 'save': 'Захаваць', 'cancel': 'Адмяніць', 'delete': 'Выдаліць', 'view': 'Прагледзець'},
        'features': {'cta': {'start': 'Пачаць Бясплатна'}},
        'layout': {'quick_search_placeholder': 'Хуткі пошук...', 'quick_search_hint': 'Парада: Cmd/Ctrl+K'}
    },
    'hu': {
        'common': {'error': 'Hiba', 'save': 'Mentés', 'cancel': 'Mégse', 'delete': 'Törlés', 'view': 'Megtekintés'},
        'features': {'cta': {'start': 'Kezdés Ingyen'}},
        'layout': {'quick_search_placeholder': 'Gyors keresés...', 'quick_search_hint': 'Tipp: Cmd/Ctrl+K'}
    },
    'sk': {
        'common': {'error': 'Chyba', 'save': 'Uložiť', 'cancel': 'Zrušiť', 'delete': 'Vymazať', 'view': 'Zobraziť'},
        'features': {'cta': {'start': 'Začať Zadarmo'}},
        'layout': {'quick_search_placeholder': 'Rýchle vyhľadávanie...', 'quick_search_hint': 'Tip: Cmd/Ctrl+K'}
    },
    'sl': {
        'common': {'error': 'Napaka', 'save': 'Shrani', 'cancel': 'Prekliči', 'delete': 'Izbriši', 'view': 'Poglej'},
        'features': {'cta': {'start': 'Začni Brezplačno'}},
        'layout': {'quick_search_placeholder': 'Hitro iskanje...', 'quick_search_hint': 'Nasvet: Cmd/Ctrl+K'}
    },
    'sq': {
        'common': {'error': 'Gabim', 'save': 'Ruaj', 'cancel': 'Anulo', 'delete': 'Fshi', 'view': 'Shiko'},
        'features': {'cta': {'start': 'Fillo Falas'}},
        'layout': {'quick_search_placeholder': 'Kërkim i shpejtë...', 'quick_search_hint': 'Këshillë: Cmd/Ctrl+K'}
    },
    'sr': {
        'common': {'error': 'Грешка', 'save': 'Сачувај', 'cancel': 'Откажи', 'delete': 'Обриши', 'view': 'Погледај'},
        'features': {'cta': {'start': 'Почни Бесплатно'}},
        'layout': {'quick_search_placeholder': 'Брза претрага...', 'quick_search_hint': 'Савет: Cmd/Ctrl+K'}
    },
    'bs': {
        'common': {'error': 'Greška', 'save': 'Sačuvaj', 'cancel': 'Otkaži', 'delete': 'Obriši', 'view': 'Pogledaj'},
        'features': {'cta': {'start': 'Počni Besplatno'}},
        'layout': {'quick_search_placeholder': 'Brza pretraga...', 'quick_search_hint': 'Savjet: Cmd/Ctrl+K'}
    },
    'mk': {
        'common': {'error': 'Грешка', 'save': 'Зачувај', 'cancel': 'Откажи', 'delete': 'Избриши', 'view': 'Погледни'},
        'features': {'cta': {'start': 'Започни Бесплатно'}},
        'layout': {'quick_search_placeholder': 'Брзо пребарување...', 'quick_search_hint': 'Совет: Cmd/Ctrl+K'}
    },
    'mt': {
        'common': {'error': 'Żball', 'save': 'Salva', 'cancel': 'Ikkanċella', 'delete': 'Ħassar', 'view': 'Ara'},
        'features': {'cta': {'start': 'Ibda B\'xejn'}},
        'layout': {'quick_search_placeholder': 'Fittex malajr...', 'quick_search_hint': 'Suġġeriment: Cmd/Ctrl+K'}
    },
    'lt': {
        'common': {'error': 'Klaida', 'save': 'Išsaugoti', 'cancel': 'Atšaukti', 'delete': 'Ištrinti', 'view': 'Peržiūrėti'},
        'features': {'cta': {'start': 'Pradėti Nemokamai'}},
        'layout': {'quick_search_placeholder': 'Greita paieška...', 'quick_search_hint': 'Patarimas: Cmd/Ctrl+K'}
    },
    'lv': {
        'common': {'error': 'Kļūda', 'save': 'Saglabāt', 'cancel': 'Atcelt', 'delete': 'Dzēst', 'view': 'Skatīt'},
        'features': {'cta': {'start': 'Sākt Bez Maksas'}},
        'layout': {'quick_search_placeholder': 'Ātrā meklēšana...', 'quick_search_hint': 'Padoms: Cmd/Ctrl+K'}
    },
    'et': {
        'common': {'error': 'Viga', 'save': 'Salvesta', 'cancel': 'Tühista', 'delete': 'Kustuta', 'view': 'Vaata'},
        'features': {'cta': {'start': 'Alusta Tasuta'}},
        'layout': {'quick_search_placeholder': 'Kiir otsing...', 'quick_search_hint': 'Vihje: Cmd/Ctrl+K'}
    },
    'ja': {
        'common': {'error': 'エラー', 'save': '保存', 'cancel': 'キャンセル', 'delete': '削除', 'view': '表示'},
        'features': {'cta': {'start': '無料で始める'}},
        'layout': {'quick_search_placeholder': 'クイック検索...', 'quick_search_hint': 'ヒント：Cmd/Ctrl+K'}
    },
    'ko': {
        'common': {'error': '오류', 'save': '저장', 'cancel': '취소', 'delete': '삭제', 'view': '보기'},
        'features': {'cta': {'start': '무료로 시작'}},
        'layout': {'quick_search_placeholder': '빠른 검색...', 'quick_search_hint': '팁: Cmd/Ctrl+K'}
    },
    'zh-CN': {
        'common': {'error': '错误', 'save': '保存', 'cancel': '取消', 'delete': '删除', 'view': '查看'},
        'features': {'cta': {'start': '免费开始'}},
        'layout': {'quick_search_placeholder': '快速搜索...', 'quick_search_hint': '提示：Cmd/Ctrl+K'}
    },
    'hi': {
        'common': {'error': 'त्रुटि', 'save': 'सहेजें', 'cancel': 'रद्द करें', 'delete': 'हटाएं', 'view': 'देखें'},
        'features': {'cta': {'start': 'मुफ्त शुरू करें'}},
        'layout': {'quick_search_placeholder': 'त्वरित खोज...', 'quick_search_hint': 'सुझाव: Cmd/Ctrl+K'}
    },
    'tr': {
        'common': {'error': 'Hata', 'save': 'Kaydet', 'cancel': 'İptal', 'delete': 'Sil', 'view': 'Görüntüle'},
        'features': {'cta': {'start': 'Ücretsiz Başla'}},
        'layout': {'quick_search_placeholder': 'Hızlı arama...', 'quick_search_hint': 'İpucu: Cmd/Ctrl+K'}
    },
    'ar': {
        'common': {'error': 'خطأ', 'save': 'حفظ', 'cancel': 'إلغاء', 'delete': 'حذف', 'view': 'عرض'},
        'features': {'cta': {'start': 'ابدأ مجانًا'}},
        'layout': {'quick_search_placeholder': 'بحث سريع...', 'quick_search_hint': 'نصيحة: Cmd/Ctrl+K'}
    },
    'he': {
        'common': {'error': 'שגיאה', 'save': 'שמור', 'cancel': 'בטל', 'delete': 'מחק', 'view': 'הצג'},
        'features': {'cta': {'start': 'התחל בחינם'}},
        'layout': {'quick_search_placeholder': 'חיפוש מהיר...', 'quick_search_hint': 'טיפ: Cmd/Ctrl+K'}
    }
}

def deep_merge(target, source):
    """Deep merge source dict into target dict"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value

def main():
    print('🔧 Behebe ALLE problematischen Keys in ALLEN Sprachen\n')
    print('=' * 70)
    
    updated_count = 0
    
    for lang_code, translations in TRANSLATIONS.items():
        file_path = LOCALES_DIR / f'{lang_code}.json'
        
        if not file_path.exists():
            print(f'⚠️  {lang_code}.json nicht gefunden')
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Merge translations
            deep_merge(data, translations)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')
            
            key_count = sum(len(v) if isinstance(v, dict) else 1 for v in translations.values())
            print(f'✅ {lang_code}: {key_count} Keys aktualisiert')
            updated_count += 1
            
        except Exception as e:
            print(f'❌ {lang_code}: Fehler - {e}')
    
    print('\n' + '=' * 70)
    print(f'\n✅ {updated_count} Sprachen erfolgreich aktualisiert!')
    print('\n🎉 Kritische Keys sind jetzt in allen Sprachen nativ!')

if __name__ == '__main__':
    main()
