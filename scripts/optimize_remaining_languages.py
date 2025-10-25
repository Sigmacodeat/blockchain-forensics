#!/usr/bin/env python3
"""
Automatische Optimierung aller verbleibenden Sprachpakete für Startup-Ton
"""
import json
import os
from pathlib import Path

# Mapping: alte formelle CTA → neue Startup CTA
CTA_OPTIMIZATIONS = {
    # Baltikum
    'lv': {'demo': 'Pieteikties demo', 'title': 'Sākt tagad'},  # Lettisch
    'et': {'demo': 'Broneeri demo', 'title': 'Alusta kohe'},  # Estnisch
    
    # Nordisch
    'nb': {'demo': 'Bestill demo', 'title': 'Start nå'},  # Norwegisch Bokmål
    'nn': {'demo': 'Bestill demo', 'title': 'Start no'},  # Norwegisch Nynorsk
    'is': {'demo': 'Panta sýniútgáfu', 'title': 'Byrja núna'},  # Isländisch
    
    # Weitere EU
    'ga': {'demo': 'Cuir in áirithe demo', 'title': 'Tosaigh anois'},  # Irisch
    'mt': {'demo': 'Irriżerva demo', 'title': 'Ibda issa'},  # Maltesisch
    'lb': {'demo': 'Demo reservéieren', 'title': 'Elo ufänken'},  # Luxemburgisch
    'rm': {'demo': 'Reservar demo', 'title': 'Cumenzar ussa'},  # Rätoromanisch
    'uk': {'demo': 'Замовити demo', 'title': 'Почати зараз'},  # Ukrainisch
    'be': {'demo': 'Замовіць demo', 'title': 'Пачаць зараз'},  # Weißrussisch
    
    # MENA
    'ar': {'demo': 'احجز عرضًا توضيحيًا', 'title': 'ابدأ الآن'},  # Arabisch
    'he': {'demo': 'הזמן הדגמה', 'title': 'התחל עכשיו'},  # Hebräisch
    'hi': {'demo': 'डेमो बुक करें', 'title': 'अभी शुरू करें'},  # Hindi
    
    # Asien
    'ko': {'demo': '데모 예약', 'title': '지금 시작'},  # Koreanisch
}

def optimize_language(lang_code, optimizations):
    """Optimiert eine Sprache mit neuen CTA-Texten"""
    file_path = Path(f'frontend/src/locales/{lang_code}.json')
    
    if not file_path.exists():
        print(f"⚠️  {lang_code}.json nicht gefunden")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Aktualisiere CTAs
        if 'about' in data and 'cta' in data['about']:
            if 'demo' in optimizations:
                data['about']['cta']['demo'] = optimizations['demo']
            if 'title' in optimizations:
                data['about']['cta']['title'] = optimizations['title']
        
        # Schreibe zurück
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {lang_code}.json optimiert")
        return True
    except Exception as e:
        print(f"❌ {lang_code}.json Fehler: {e}")
        return False

def main():
    print("🚀 Automatische Optimierung aller verbleibenden Sprachen...\n")
    
    os.chdir('/Users/msc/CascadeProjects/blockchain-forensics')
    
    success_count = 0
    for lang_code, opts in CTA_OPTIMIZATIONS.items():
        if optimize_language(lang_code, opts):
            success_count += 1
    
    print(f"\n🎯 Fertig! {success_count}/{len(CTA_OPTIMIZATIONS)} Sprachen optimiert")

if __name__ == '__main__':
    main()
