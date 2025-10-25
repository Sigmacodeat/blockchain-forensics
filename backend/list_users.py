#!/usr/bin/env python3
"""Script zum Anzeigen aller registrierten Benutzer"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blockchain_forensics")

def list_users():
    """Liste alle User aus der Datenbank"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Hole alle User
        result = session.execute(
            text("""
                SELECT id, email, role, created_at, last_login
                FROM users
                ORDER BY created_at DESC
            """)
        )
        users = result.fetchall()
        
        print('\n' + '='*80)
        print(f'REGISTRIERTE KONTEN ({len(users)} gesamt)')
        print('='*80 + '\n')
        
        if not users:
            print("❌ Keine User in der Datenbank gefunden!")
            print("   Nutze 'python create_admin.py' um Test-Accounts zu erstellen.\n")
            return
        
        for user in users:
            user_id, email, role, created_at, last_login = user
            
            # Icon basierend auf Rolle
            icon = "👑" if role == "admin" else "👤"
            
            print(f'{icon} {email}')
            print(f'   ID:              {user_id}')
            print(f'   Rolle:           {role.upper() if role else "N/A"}')
            print(f'   Erstellt:        {created_at}')
            print(f'   Letzter Login:   {last_login or "Noch nie"}')
            print('-' * 80)
            
        # Admin-Konten hervorheben
        admins = [u for u in users if u[2] == 'admin']  # role ist index 2
        if admins:
            print('\n' + '='*80)
            print(f'👑 ADMIN-KONTEN ({len(admins)} gesamt)')
            print('='*80 + '\n')
            for admin in admins:
                print(f'   ✓ {admin[1]} (ID: {admin[0]})')  # email, id
            print()
                
    except Exception as e:
        print(f"\n❌ Fehler beim Abrufen der User: {e}")
        print(f"   DATABASE_URL: {DATABASE_URL}\n")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    print("🔍 User-Liste aus Datenbank\n")
    
    # Prüfe Database-Verbindung
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database-Verbindung OK\n")
    except Exception as e:
        print(f"❌ Database nicht erreichbar: {e}")
        print(f"   DATABASE_URL: {DATABASE_URL}\n")
        exit(1)
    
    list_users()
