# Demo User Setup Guide

## Quick Demo Access

**Demo Credentials** (create manually or via script):
- **Email**: `demo@sigmacode.io`
- **Password**: `Demo123!`
- **Plan**: Pro
- **Role**: ANALYST

## Option 1: Create via Script (Recommended)

```bash
cd backend
python scripts/create_demo_user.py
```

This script will:
1. Check if demo user already exists
2. Create new demo user with Pro plan
3. Display login credentials

## Option 2: Create via API

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@sigmacode.io",
    "username": "demo_analyst",
    "password": "Demo123!",
    "plan": "pro"
  }'
```

## Option 3: Create via SQL (Direct)

```sql
INSERT INTO users (id, email, username, hashed_password, role, plan, is_active, created_at, updated_at, features, organization)
VALUES (
  gen_random_uuid()::text,
  'demo@sigmacode.io',
  'demo_analyst',
  '$2b$12$...',  -- Use bcrypt to hash 'Demo123!'
  'analyst',
  'pro',
  true,
  NOW(),
  NOW(),
  '["trace","investigator","cases","correlation","analytics","custom-entities"]'::json,
  'SIGMACODE Demo'
);
```

## Login URL

http://localhost:3000/en/login

## Features Accessible with Demo Account

✅ **Included** (Pro Plan):
- Transaction Tracing (20 blockchains)
- Graph Investigator
- Case Management
- Correlation Analysis
- Analytics Dashboard
- Custom Entities
- 20,000 Credits/month

❌ **Not Included**:
- AI Agent (Plus+ required)
- White-Label (Enterprise required)
- Custom Blockchains (Business+ required)

## Notes

- Demo user is created with **Pro plan** to showcase most features
- **ANALYST role** provides access to forensic tools but not admin features
- Perfect for testing and demonstrations
- Can be used in presentations to clients

## Troubleshooting

**"User already exists"**:
- Demo user was already created
- Use the login credentials above

**"Database connection refused"**:
- Start PostgreSQL: `docker-compose up -d postgres`
- Verify database is running: `docker ps`

**"Password incorrect"**:
- Password is case-sensitive: `Demo123!`
- Ensure no extra spaces in password field
