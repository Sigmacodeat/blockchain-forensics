from .service import sanctions_service, SanctionsService
try:
    # Expose query_labels_by_address for tests to patch
    from app.repos.labels_repo import query_labels_by_address  # type: ignore
except Exception:
    # Fallback no-op for environments without repos
    def query_labels_by_address(*args, **kwargs):  # type: ignore
        return []

# Expose availability flag for tests to patch
_SANCTIONS_AVAILABLE = True
