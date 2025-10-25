# Sealed Secrets (Beispiel)

Dieses Verzeichnis enthält Beispiele für Sealed Secrets Manifeste, um produktive Secrets sicher im Git zu versionieren.

## Voraussetzungen
- Sealed Secrets Controller im Cluster installiert
- `kubeseal` CLI lokal
- Public Key des Controllers exportiert (`kubeseal --fetch-cert`)

## Erstellung eines Sealed Secret

1. Temporäre Secret-Datei erstellen (wird nicht committed):
```bash
echo -n 'sk_live_xxx' | kubectl create secret generic forensics-secrets-tmp \
  --namespace blockchain-forensics \
  --from-literal=stripe-secret=/dev/stdin \
  --dry-run=client -o yaml > /tmp/stripe-secret.yaml
```

2. Versiegeln:
```bash
kubeseal --format yaml \
  --cert ./controller-public-key.crt \
  < /tmp/stripe-secret.yaml \
  > stripe-secret.sealed.yaml
```

3. Commit `stripe-secret.sealed.yaml` in dieses Verzeichnis und löschen Sie die temporäre Datei:
```bash
rm /tmp/stripe-secret.yaml
```

4. Apply im Cluster:
```bash
kubectl apply -f stripe-secret.sealed.yaml
```

## Hinweise
- Legen Sie für unterschiedliche Provider (Stripe, OpenAI, DB-Passwörter) separate Sealed Secrets an.
- Rotationen: Neues Secret erzeugen, erneut versiegeln, anwenden; Deployments ziehen die neuen Werte automatisch bei Re-Deploy.
- Für TLS-Zertifikate nutzen Sie bevorzugt cert-manager (Let’s Encrypt). Sealed Secrets sind für Applikations‑Secrets gedacht.
