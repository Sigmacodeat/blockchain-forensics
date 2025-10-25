# Streaming Schemas & Producer

- Ordner: `app/streaming/`
- Producer: `producer.py` (No-Op in TEST/OFFLINE/ohne Kafka-Konfig)
- Avro-Schemas: `schemas/canonical_event.avsc`, `schemas/trace_request.avsc`

## Topics (Vorschlag)
- `ingest.events` (CanonicalEvent)
- `trace.requests` (TraceRequest)
- `enrich.results` (frei, analog CanonicalEvent-Subset)
- `alerts.events` (frei, Rule-Engine-Ausgaben)

## CanonicalEvent (Avro)
Siehe `schemas/canonical_event.avsc`. Felder entsprechen `app/schemas/canonical_event.py::CanonicalEventAvroSchema.SCHEMA`.

Zeitstempel als `timestamp-millis`. Dezimalwerte als Strings.

## TraceRequest (Avro)
Siehe `schemas/trace_request.avsc`. Operation (`op`) als Enum: `trace | taint | cluster`.

## Verwendung Producer
```python
from app.streaming.producer import producer

producer.send({
    "event_id": "eth_tx_...",
    "chain": "ethereum",
    ...
})
producer.flush()
```

Aktiv nur, wenn `KAFKA_BOOTSTRAP_SERVERS` gesetzt und weder `TEST_MODE` noch `OFFLINE_MODE` aktiv sind.
