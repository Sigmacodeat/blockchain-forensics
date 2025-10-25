# RFC: WP6 – Smart-Contract Risk Engine

## Ziel
Bewertung von Smart Contracts anhand statischer und dynamischer Analysen, mit erklärbaren Findings, Signatur-Datenbank und Exploit-Heuristiken.

## Scope
- Statische Checks: Ownership/Permissions, Proxy/Upgradeability, Pausable/Blacklistable, Dangerous Opcodes/Patterns
- Signatur/Bytecode Similarity: Known-bad/known-good Fingerprints, Libraries, Inheritance
- Dynamisch: Event-/State-Anomalien, Upgrades, Admin-Changes, High-risk parameter usage
- Output: Risk Score + Findings + Remediation Hints (explainable)

## Datenmodell (DB/Pydantic)
- `contract_profile(address, chain, bytecode_hash, proxy, implementation, creator, first_seen)`
- `contract_signature(id, name, fingerprint, risk_tags[], source)`
- `contract_risk_issue(id, address, kind, severity, evidence, created_at)`

## APIs
- `POST /api/v1/contracts/analyze` → {address, chain?} → score + findings
- `GET  /api/v1/contracts/{address}` → Profil, Issues, History

## SLO/SLA
- p95 statische Analyse < 300ms (cached), Bytecode-Fetch mit Retry/Cache

## Sicherheit/Compliance
- Keine Speicherung unnötiger Daten; Hash-basierte Fingerprints
- Auditierbarkeit der Findings (Determinismus, Versionierung)

## Testplan
- Unit: Pattern-Detektoren, Signatur-Matching
- Integration: Fetch→Analyze→Store→Retrieve
- Regression: bekannte Samples (honeypot/rugpull/upgradeable)
