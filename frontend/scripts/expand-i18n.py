#!/usr/bin/env python3
"""
Erweitert minimale i18n-JSON-Dateien mit allen wichtigen Business-Sections
Basierend auf der deutschen Template-Struktur
"""

import json
import os
from pathlib import Path

# Sprachen mit ihren nativen Übersetzungen für Key-Sections
LANGUAGES = {
    'fa': {
        'name': 'فارسی',
        'about': {
            'header': {
                'badge': 'درباره ما',
                'title': 'آینده تحلیل بلاکچین',
                'subtitle': 'ما پلتفرم پیشرو سازمانی برای هوش بلاکچین را توسعه می‌دهیم که به مجریان قانون، VASPها و موسسات مالی در محافظت در برابر جرایم کریپتو کمک می‌کند.'
            },
            'mission': {
                'title': 'مأموریت ما',
                'desc': 'ما تراکنش‌های بلاکچین را شفاف و قابل ردیابی می‌کنیم. هدف ما مبارزه با جرایم کریپتو و ارائه ابزارهای لازم به بازیگران قانونی بازار برای انطباق و کاهش ریسک است.'
            }
        },
        'navigation': {
            'home': 'خانه',
            'features': 'ویژگی‌ها',
            'pricing': 'قیمت‌گذاری',
            'docs': 'مستندات',
            'dashboard': 'داشبورد'
        },
        'trace': {
            'title': 'ردیابی تراکنش',
            'start': 'شروع ردیابی',
            'results': 'نتایج'
        }
    },
    'ur': {
        'name': 'اردو',
        'about': {
            'header': {
                'badge': 'ہمارے بارے میں',
                'title': 'بلاکچین تجزیات کا مستقبل',
                'subtitle': 'ہم قانون نافذ کرنے والے اداروں، VASPs اور مالیاتی اداروں کو کرپٹو جرائم سے تحفظ میں مدد کے لیے بلاکچین انٹیلی جنس کا پیشرو انٹرپرائز پلیٹ فارم تیار کر رہے ہیں۔'
            },
            'mission': {
                'title': 'ہمارا مشن',
                'desc': 'ہم بلاکچین لین دین کو شفاف اور قابل پیمائش بناتے ہیں۔ ہمارا مقصد کرپٹو جرائم سے لڑنا اور قانونی مارکیٹ شرکاء کو تعمیل اور خطرات کم کرنے کے لیے ٹولز فراہم کرنا ہے۔'
            }
        },
        'navigation': {
            'home': 'ہوم',
            'features': 'فیچرز',
            'pricing': 'قیمتیں',
            'docs': 'دستاویزات',
            'dashboard': 'ڈیش بورڈ'
        },
        'trace': {
            'title': 'ٹرانزیکشن ٹریسنگ',
            'start': 'ٹریسنگ شروع کریں',
            'results': 'نتائج'
        }
    },
    'id': {
        'name': 'Bahasa Indonesia',
        'about': {
            'header': {
                'badge': 'Tentang Kami',
                'title': 'Masa Depan Analisis Blockchain',
                'subtitle': 'Kami mengembangkan platform intelijen blockchain tingkat enterprise terkemuka yang membantu penegak hukum, VASPs, dan lembaga keuangan melindungi dari kejahatan kripto.'
            },
            'mission': {
                'title': 'Misi Kami',
                'desc': 'Kami membuat transaksi blockchain transparan dan dapat dilacak. Tujuan kami adalah memerangi kejahatan kripto dan memberikan alat kepada pelaku pasar yang sah untuk memenuhi persyaratan kepatuhan dan meminimalkan risiko.'
            }
        },
        'navigation': {
            'home': 'Beranda',
            'features': 'Fitur',
            'pricing': 'Harga',
            'docs': 'Dokumentasi',
            'dashboard': 'Dasbor'
        },
        'trace': {
            'title': 'Pelacakan Transaksi',
            'start': 'Mulai Pelacakan',
            'results': 'Hasil'
        }
    },
    'vi': {
        'name': 'Tiếng Việt',
        'about': {
            'header': {
                'badge': 'Về chúng tôi',
                'title': 'Tương lai của phân tích Blockchain',
                'subtitle': 'Chúng tôi phát triển nền tảng trí tuệ blockchain doanh nghiệp hàng đầu giúp cơ quan thực thi pháp luật, VASPs và tổ chức tài chính bảo vệ khỏi tội phạm tiền điện tử.'
            },
            'mission': {
                'title': 'Sứ mệnh của chúng tôi',
                'desc': 'Chúng tôi làm cho các giao dịch blockchain trở nên minh bạch và có thể truy vết. Mục tiêu của chúng tôi là chống tội phạm tiền điện tử và cung cấp các công cụ cho các bên tham gia thị trường hợp pháp để đáp ứng yêu cầu tuân thủ và giảm thiểu rủi ro.'
            }
        },
        'navigation': {
            'home': 'Trang chủ',
            'features': 'Tính năng',
            'pricing': 'Giá cả',
            'docs': 'Tài liệu',
            'dashboard': 'Bảng điều khiển'
        },
        'trace': {
            'title': 'Truy vết giao dịch',
            'start': 'Bắt đầu truy vết',
            'results': 'Kết quả'
        }
    },
    'th': {
        'name': 'ไทย',
        'about': {
            'header': {
                'badge': 'เกี่ยวกับเรา',
                'title': 'อนาคตของการวิเคราะห์บล็อกเชน',
                'subtitle': 'เราพัฒนาแพลตฟอร์มข่าวกรองบล็อกเชนระดับองค์กรชั้นนำที่ช่วยหน่วยงานบังคับใช้กฎหมาย VASPs และสถาบันการเงินในการป้องกันอาชญากรรมคริปโต'
            },
            'mission': {
                'title': 'พันธกิจของเรา',
                'desc': 'เราทำให้ธุรกรรมบล็อกเชนโปร่งใสและสามารถติดตามได้ เป้าหมายของเราคือการต่อสู้กับอาชญากรรมคริปโตและมอบเครื่องมือให้กับผู้เข้าร่วมตลาดที่ถูกกฎหมายเพื่อปฏิบัติตามข้อกำหนดและลดความเสี่ยง'
            }
        },
        'navigation': {
            'home': 'หน้าหลัก',
            'features': 'คุณสมบัติ',
            'pricing': 'ราคา',
            'docs': 'เอกสาร',
            'dashboard': 'แดชบอร์ด'
        },
        'trace': {
            'title': 'การติดตามธุรกรรม',
            'start': 'เริ่มการติดตาม',
            'results': 'ผลลัพธ์'
        }
    },
    'bn': {
        'name': 'বাংলা',
        'about': {
            'header': {
                'badge': 'আমাদের সম্পর্কে',
                'title': 'ব্লকচেইন বিশ্লেষণের ভবিষ্যৎ',
                'subtitle': 'আমরা শীর্ষস্থানীয় এন্টারপ্রাইজ ব্লকচেইন ইন্টেলিজেন্স প্ল্যাটফর্ম তৈরি করছি যা আইন প্রয়োগকারী সংস্থা, VASPs এবং আর্থিক প্রতিষ্ঠানগুলিকে ক্রিপ্টো অপরাধ থেকে রক্ষা করতে সাহায্য করে।'
            },
            'mission': {
                'title': 'আমাদের লক্ষ্য',
                'desc': 'আমরা ব্লকচেইন লেনদেনকে স্বচ্ছ এবং ট্রেসযোগ্য করি। আমাদের লক্ষ্য হল ক্রিপ্টো অপরাধের বিরুদ্ধে লড়াই করা এবং বৈধ বাজার অংশগ্রহণকারীদের সম্মতি পূরণ এবং ঝুঁকি কমানোর জন্য সরঞ্জাম প্রদান করা।'
            }
        },
        'navigation': {
            'home': 'হোম',
            'features': 'বৈশিষ্ট্য',
            'pricing': 'মূল্য',
            'docs': 'ডকুমেন্টেশন',
            'dashboard': 'ড্যাশবোর্ড'
        },
        'trace': {
            'title': 'ট্রানজেকশন ট্রেসিং',
            'start': 'ট্রেসিং শুরু করুন',
            'results': 'ফলাফল'
        }
    }
}

def expand_locale(lang_code, translations):
    """Erweitert eine minimale Locale-Datei mit zusätzlichen Sections"""
    locale_path = Path(__file__).parent.parent / 'src' / 'locales' / f'{lang_code}.json'
    
    # Lade existierende Datei
    with open(locale_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    
    # Merge mit neuen Übersetzungen (existing hat Priorität)
    merged = {**translations, **existing}
    
    # Speichere erweiterte Version
    with open(locale_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Erweitert: {lang_code}.json")

def main():
    print("Erweitere i18n-Dateien mit Business-Sections...\n")
    
    for lang_code, data in LANGUAGES.items():
        expand_locale(lang_code, data)
    
    print(f"\n✅ Alle {len(LANGUAGES)} Sprachen erweitert!")
    print("\nNächste Schritte:")
    print("1. npm run build --prefix frontend")
    print("2. Review in Browser testen")

if __name__ == '__main__':
    main()
