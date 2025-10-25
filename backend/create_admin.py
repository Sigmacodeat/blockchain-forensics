#!/usr/bin/env python3
"""
Admin Account Creator
Erstellt Admin- und Test-Accounts für die Plattform
"""
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Database URL aus Environment oder Default (Docker: Port 5435)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://forensics:forensics_pass@localhost:5435/blockchain_forensics")

def hash_password(password: str) -> str:
    """Hash password mit bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_admin_accounts():
    """Erstelle Admin und Test-Accounts"""
    
    # Database Connection
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Accounts mit gehashten Passwörtern
        accounts = [
            {
                'email': 'admin@blockchain-forensics.com',
                'password': 'Admin2025!Secure',
                'role': 'admin'
            },
            {
                'email': 'test-user@blockchain-forensics.com',
                'password': 'User2025!',
                'role': 'user'
            },
            {
                'email': 'test-investigator@blockchain-forensics.com',
                'password': 'Investigator2025!',
                'role': 'investigator'
            },
            {
                'email': 'test-analyst@blockchain-forensics.com',
                'password': 'Analyst2025!',
                'role': 'analyst'
            },
        ]
        
        print("🔐 Erstelle Admin- und Test-Accounts...\n")
        
        for account in accounts:
            email = account['email']
            
            # Prüfe ob Account bereits existiert
            result = session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            )
            existing = result.fetchone()
            
            if existing:
                print(f"⏭️  {email} existiert bereits (ID: {existing[0]})")
                continue
            
            # Hash Passwort
            password_hash = hash_password(account['password'])
            
            # Insert User (nur vorhandene Felder: id, email, hashed_password, role, created_at)
            session.execute(
                text("""
                    INSERT INTO users (
                        email, hashed_password, role, created_at
                    ) VALUES (
                        :email, :hashed_password, :role, :created_at
                    )
                """),
                {
                    "email": account['email'],
                    "hashed_password": password_hash,
                    "role": account['role'],
                    "created_at": datetime.utcnow()
                }
            )
            
            print(f"✅ {email} ({account['role']})")
        
        session.commit()
        print("\n🎉 Accounts erfolgreich erstellt!")
        
        # Zeige Login-Informationen
        print("\n" + "="*60)
        print("🔑 LOGIN-INFORMATIONEN")
        print("="*60)
        print("\n👑 Admin-Account:")
        print("  Email:    admin@blockchain-forensics.com")
        print("  Passwort: Admin2025!Secure")
        print("  Rolle:    admin")
        
        print("\n👤 Test-Accounts:")
        for acc in accounts[1:]:
            print(f"\n  {acc['role'].upper()} User:")
            print(f"    Email:    {acc['email']}")
            print(f"    Passwort: {acc['password']}")
        
        print("\n" + "="*60)
        print("🚀 Du kannst dich jetzt anmelden!")
        print("="*60 + "\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Fehler: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🔧 Admin Account Creator\n")
    
    # Prüfe ob Database erreichbar ist
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database-Verbindung OK\n")
    except Exception as e:
        print(f"❌ Database nicht erreichbar: {e}")
        print(f"   DATABASE_URL: {DATABASE_URL}")
        exit(1)
    
    # Erstelle Accounts
    create_admin_accounts()
