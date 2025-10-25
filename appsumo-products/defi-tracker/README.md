# defi-tracker

## Status: Production Ready ✅

Features implemented:
- Full Dashboard
- Real Features
- API Integration
- Beautiful UI

Launch: http://localhost:300X

## Optional: Main Backend Integration (Forensic Trace)

Enable proxy to the main platform for real forensic tracing:

1) Configure env in `backend/.env`:
```
MAIN_BACKEND_URL=http://host.docker.internal:8001
# Optional if protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Available proxy endpoints:
```
POST  /api/trace/start           # Start forensic trace
GET   /api/trace/{id}/report     # Download JSON/CSV/PDF report
```
