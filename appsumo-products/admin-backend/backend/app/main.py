from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import os
import hmac
import hashlib
import json

from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./appsumo_admin.db")
APPSUMO_WEBHOOK_SECRET = os.getenv("APPSUMO_WEBHOOK_SECRET", "dev-secret")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

class AppSumoEvent(Base):
    __tablename__ = "appsumo_events"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True)
    event_type = Column(String, index=True)
    payload = Column(JSON)
    received_at = Column(DateTime, default=datetime.utcnow)

class AppSumoLicense(Base):
    __tablename__ = "appsumo_licenses"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    product = Column(String, index=True)
    tier = Column(Integer)
    status = Column(String, default="active")
    code = Column(String)
    activated_at = Column(DateTime)
    __table_args__ = (UniqueConstraint('email', 'product', name='uix_email_product'),)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AppSumo Admin Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WebhookAck(BaseModel):
    success: bool
    event_id: Optional[str] = None

class KpiResponse(BaseModel):
    total_events: int
    total_licenses: int
    active_licenses: int
    refunded_licenses: int
    by_product: Dict[str, Dict[str, int]]

@app.get("/")
def root():
    return {"message": "AppSumo Admin Backend", "status": "running", "version": "1.0.0"}

@app.get("/health")
def health():
    with SessionLocal() as db:
        ev = db.query(AppSumoEvent).count()
        lc = db.query(AppSumoLicense).count()
    return {"status": "healthy", "events": ev, "licenses": lc}

# Simple HMAC validator (sha256 over raw body with shared secret)
def verify_signature(raw_body: bytes, signature: str) -> bool:
    if not signature:
        return False
    digest = hmac.new(APPSUMO_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    # Support either plain hex or header like "sha256=..."
    expected = f"sha256={digest}"
    return hmac.compare_digest(signature, expected) or hmac.compare_digest(signature, digest)

@app.post("/api/appsumo/webhooks", response_model=WebhookAck)
async def appsumo_webhooks(request: Request):
    raw = await request.body()
    sig = request.headers.get("X-AppSumo-Signature") or request.headers.get("X-Hub-Signature") or ""
    if not verify_signature(raw, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_id = data.get("id") or data.get("event_id") or f"evt_{hashlib.md5(raw).hexdigest()}"
    event_type = data.get("type", "unknown")

    with SessionLocal() as db:
        # Idempotency: skip if already processed
        existing = db.query(AppSumoEvent).filter(AppSumoEvent.event_id == event_id).one_or_none()
        if existing:
            return WebhookAck(success=True, event_id=event_id)

        db.add(AppSumoEvent(event_id=event_id, event_type=event_type, payload=data))

        # Process license changes
        payload = data.get("data", {})
        email = payload.get("email")
        product = payload.get("product")
        tier = payload.get("tier") or payload.get("plan_tier")
        code = payload.get("code")

        if email and product:
            lic = db.query(AppSumoLicense).filter(AppSumoLicense.email == email, AppSumoLicense.product == product).one_or_none()
            if event_type in ("redeemed", "activated", "upgraded"):
                if not lic:
                    lic = AppSumoLicense(email=email, product=product)
                    db.add(lic)
                lic.status = "active"
                lic.tier = int(tier) if tier else lic.tier
                lic.code = code or lic.code
                lic.activated_at = lic.activated_at or datetime.utcnow()
            elif event_type in ("refunded", "cancelled"):
                if lic:
                    lic.status = "refunded" if event_type == "refunded" else "cancelled"
        db.commit()

    return WebhookAck(success=True, event_id=event_id)

@app.get("/api/admin/kpis", response_model=KpiResponse)
async def get_kpis():
    with SessionLocal() as db:
        total_events = db.query(AppSumoEvent).count()
        total_licenses = db.query(AppSumoLicense).count()
        active_licenses = db.query(AppSumoLicense).filter(AppSumoLicense.status == "active").count()
        refunded_licenses = db.query(AppSumoLicense).filter(AppSumoLicense.status == "refunded").count()
        # breakdown by product and status
        rows = db.execute(
            """
            SELECT product, status, COUNT(*) as c
            FROM appsumo_licenses
            GROUP BY product, status
            """
        )
        by_product: Dict[str, Dict[str, int]] = {}
        for product, status, c in rows:
            by_product.setdefault(product or "unknown", {}).update({status or "unknown": c})
    return KpiResponse(
        total_events=total_events,
        total_licenses=total_licenses,
        active_licenses=active_licenses,
        refunded_licenses=refunded_licenses,
        by_product=by_product,
    )
