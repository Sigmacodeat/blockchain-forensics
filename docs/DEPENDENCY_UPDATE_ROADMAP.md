# Dependency Update Roadmap

**Status**: Pre-Launch Production Ready
**Last Updated**: 2025-10-20

## Philosophy

For production launch, we prioritize **stability and testing** over bleeding-edge versions. All current dependencies are:
- ✅ Security-vetted (no critical CVEs)
- ✅ Production-tested
- ✅ API-stable

## Post-Launch Update Plan

### Phase 1: Security-Critical Updates (Week 1-2)
Priority: HIGH - Update immediately after launch if CVEs are discovered.

**Backend**:
- `aiohttp`: 3.9.1 → 3.13.1 (Security fixes in 3.11+)
- `asyncpg`: 0.29.0 → 0.30.0 (Performance improvements)

**Frontend**:
- All packages: No critical CVEs detected
- Monitor: npm audit daily

### Phase 2: Minor Version Bumps (Month 1-2)
Priority: MEDIUM - Update after 2-4 weeks of stable production.

**Backend**:
- `alembic`: 1.13.1 → 1.17.0 (Migration improvements)
- `langchain`: 0.1.0 → Latest stable (API changes review needed)
- `pydantic`: 2.5.3 → 2.10+ (Performance)

**Frontend**:
- `@tanstack/react-query`: 5.17.9 → 5.latest
- `framer-motion`: 10.18.0 → Latest (animation improvements)
- `lucide-react`: 0.307.0 → Latest (more icons)

### Phase 3: Major Version Upgrades (Month 3-6)
Priority: LOW - Plan carefully, extensive testing required.

**Frontend**:
- ⚠️ **React 18 → 19**: Breaking changes, requires:
  - Full regression testing
  - Server Components migration plan
  - Concurrent rendering review
- ⚠️ **Storybook 8 → 9**: UI changes, component testing review
- ⚠️ **ESLint 8 → 9**: Config migration

**Backend**:
- ⚠️ **Python 3.10 → 3.12**: Performance gains, type hints improvements
- Review all async/await patterns

## Update Process

1. **Stage**: Update in `dev` branch first
2. **Test**: Run full test suite + manual QA
3. **Monitor**: Check error logs for 48h
4. **Deploy**: Gradual rollout with feature flags
5. **Rollback**: Keep previous version containers ready

## Security Monitoring

```bash
# Backend (weekly)
cd backend && pip-audit

# Frontend (weekly)
cd frontend && npm audit

# Docker images (monthly)
docker scout cves blockchain-forensics:latest
```

## Excluded from Updates

These packages are **intentionally pinned** due to breaking changes or instability:

- `web3==6.15.1`: Stable API, no breaking changes needed
- `neo4j==5.16.0`: Database driver compatibility
- `torch>=2.0.0`: ML models trained on this version

## Notes

- Always check CHANGELOG before updating
- Test crypto payment flows after any `web3` updates
- Verify Neo4j queries after driver updates
- AI agent tools must be regression-tested after `langchain` updates

---

**Next Review**: 2025-11-20 (1 month after launch)
