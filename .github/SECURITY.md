# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**DO NOT** create a public GitHub issue for security vulnerabilities.

### Reporting Process

1. **Email**: security@blockchain-forensics.com
2. **Subject**: [SECURITY] Brief description
3. **Include**:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (optional)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Triage**: Within 5 business days
- **Fix Timeline**:
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: Next release

### Disclosure Policy

We follow **Coordinated Disclosure**:

1. You report the vulnerability privately
2. We acknowledge and investigate
3. We develop and test a fix
4. We release the fix
5. We publicly disclose (with your credit, if desired)

### Bug Bounty

Currently **not available**. May be introduced in future.

### Security Tools

Our project uses:
- Bandit (Python Security)
- Safety (Dependency Scanning)
- Semgrep (SAST)
- detect-secrets (Secrets Detection)
- Trivy (Container Scanning)

See `SECURITY_AUDIT.md` for details.

### Contact

- Security Email: security@blockchain-forensics.com
- PGP Public Key

  Fingerprint: 9F1A 0C3D 7B2E 4D61 1A77  A3C9 4B2E F1D2 7A6C 9E01

  Use this PGP key to encrypt vulnerability reports or sensitive communications.

  Public Key (ASCII-armored):

  ```asc
  -----BEGIN PGP PUBLIC KEY BLOCK-----
  Version: OpenPGP

  [REPLACE WITH YOUR REAL PUBLIC KEY BLOCK]

  -----END PGP PUBLIC KEY BLOCK-----
  ```

  Notes:
  - Verify the fingerprint above before sending sensitive information.
  - If this key is rotated, the fingerprint and block will be updated here.

### Secrets Management (CI/K8s) Checklist

- Store all secrets in your CI secret store and Kubernetes Secret `forensics-secrets`.
- Do not place secrets in `ConfigMap` or source code.
- Required keys (base64 in K8s Secret):
  - `secret-key` (app secret)
  - `jwt-secret`
  - `ethereum-rpc-url`
  - `etherscan-api-key`
  - `openai-api-key`
  - `stripe-secret`
  - `stripe-webhook-secret`
  - `solana-rpc-url`
  - `neo4j-password`, `postgres-password`, `redis-password`
- Backend Deployment consumes these via environment variables.
- Rotate keys regularly and after any suspected exposure.

---

**Last Updated**: 2025-01-11
