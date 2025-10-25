# RFC: WP5 – Intel Sharing Network (Beacon-ähnlich)

## Ziel
Föderiertes, mandantenfähiges Threat/Intel-Sharing zwischen Teilnehmern (LEAs, VASPs, Institutionen) mit Governance, TLP-Klassifikation und Auditierbarkeit.

## Scope
- Datenarten: Labels, IOCs, Active Alerts, Sightings, Case-References
- Föderation: Opt-in Publish/Subscribe, Mandanten-Isolation, Signaturen
- Governance: Policies, Moderation, TLP (WHITE/GREEN/AMBER/RED)
- Privacy: Pseudonymisierung/Anonymisierung, Redaktionsregeln

## Datenmodell (DB/Pydantic)
- `intel_event(id, type[label|ioc|alert|sighting], payload, tlp, publisher, signature, ts)`
- `intel_subscription(id, tenant_id, kinds[], filters, created_at)`
- `intel_policy(id, name, rules, approvers[], status)`

## APIs
- `POST /api/v1/intel/publish` → signierte Events
- `POST /api/v1/intel/subscribe` → Filter/Arten
- `GET  /api/v1/intel/policies` → Governance-Status

## Sicherheit/Compliance
- Event-Signaturen (Ed25519), Replay-Schutz, Nonce
- RBAC-Rollen: Publisher, Moderator, Auditor
- Data residency per Tenant, Export-Controls

## SLO/SLA
- Fanout < 2s p95, 10k subs skalierbar via Kafka/WebSockets

## Testplan
- Unit: Signaturen, Policy-Checks, Filter
- Integration: Publish→Fanout→Subscriber
- Load: 10k Abonnenten, Backpressure/Retry
