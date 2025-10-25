.PHONY: help install test security-scan security-test lint format clean docker-up docker-down dev audit-report check-all deploy monitoring performance k8s-deploy helm-deploy backup sdk-ts sdk-py sdk-all sdk-clean sdk-script sdk-example-ts sdk-example-py

# Variablen
PYTHON := python3
PIP := pip3
BACKEND_DIR := backend
FRONTEND_DIR := frontend
OPENAPI_SPEC := backend/docs/openapi.yaml
SDK_TS_DIR := docs/sdk/typescript
SDK_PY_DIR := docs/sdk/python

help: ## Zeige diese Hilfe
	@echo "Blockchain Forensics Platform - Development Commands"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installiere alle Dependencies
	@echo "📦 Installing Backend Dependencies..."
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	cd $(BACKEND_DIR) && $(PIP) install -r requirements-dev.txt
	cd $(BACKEND_DIR) && $(PIP) install -r security-requirements.txt
	@echo "📦 Installing Frontend Dependencies..."
	cd $(FRONTEND_DIR) && npm install
	@echo "✅ Installation abgeschlossen"

test: ## Führe alle Tests aus (Backend + Frontend)
	@echo "🧪 Running All Tests..."
	@./run-all-tests.sh
	@echo "✅ Alle Tests abgeschlossen"

test-backend: ## Führe alle Backend-Tests aus
	@echo "🧪 Running Backend Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "✅ Backend Tests abgeschlossen"

test-backend-unit: ## Führe Backend Unit-Tests aus (schnell)
	@echo "🧪 Running Backend Unit Tests..."
	cd $(BACKEND_DIR) && pytest tests/unit -v -m unit --tb=short
	@echo "✅ Backend Unit Tests abgeschlossen"

test-backend-integration: ## Führe Backend Integration-Tests aus
	@echo "🧪 Running Backend Integration Tests..."
	cd $(BACKEND_DIR) && pytest tests/integration -v -m integration --tb=short
	@echo "✅ Backend Integration Tests abgeschlossen"

test-backend-e2e: ## Führe Backend E2E-Tests aus
	@echo "🧪 Running Backend E2E Tests..."
	cd $(BACKEND_DIR) && pytest tests/e2e -v -m e2e --tb=short
	@echo "✅ Backend E2E Tests abgeschlossen"

test-frontend: ## Führe alle Frontend-Tests aus
	@echo "🧪 Running Frontend Tests..."
	cd $(FRONTEND_DIR) && npm run test && npm run build && npm run test:e2e
	@echo "✅ Frontend Tests abgeschlossen"

test-frontend-unit: ## Führe Frontend Unit-Tests aus
	@echo "🧪 Running Frontend Unit Tests..."
	cd $(FRONTEND_DIR) && npm run test
	@echo "✅ Frontend Unit Tests abgeschlossen"

test-frontend-e2e: ## Führe Frontend E2E-Tests aus
	@echo "🧪 Running Frontend E2E Tests..."
	cd $(FRONTEND_DIR) && npm run test:e2e
	@echo "✅ Frontend E2E Tests abgeschlossen"

test-security: ## Führe Security Tests aus
	@echo "🔒 Running Security Tests..."
	cd $(BACKEND_DIR) && pytest tests/security/ -v --tb=short
	@echo "✅ Security Tests abgeschlossen"

test-agent: ## Führe AI-Agent-Tests aus
	@echo "🤖 Running AI Agent Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v -m agent --tb=short
	@echo "✅ AI Agent Tests abgeschlossen"

test-alert: ## Führe Alert-Engine-Tests aus
	@echo "🚨 Running Alert Engine Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v -m alert --tb=short
	@echo "✅ Alert Engine Tests abgeschlossen"

test-risk: ## Führe Risk-Engine-Tests aus
	@echo "⚠️  Running Risk Engine Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v -m risk --tb=short
	@echo "✅ Risk Engine Tests abgeschlossen"

test-adapter: ## Führe Chain-Adapter-Tests aus
	@echo "🔗 Running Chain Adapter Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v -m adapter --tb=short
	@echo "✅ Chain Adapter Tests abgeschlossen"

test-bridge: ## Führe Bridge-Detection-Tests aus
	@echo "🌉 Running Bridge Detection Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v -m bridge --tb=short
	@echo "✅ Bridge Detection Tests abgeschlossen"

test-clustering: ## Führe Clustering/ML-Tests aus
	@echo "🧠 Running Clustering/ML Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v -m clustering --tb=short
	@echo "✅ Clustering/ML Tests abgeschlossen"

test-fast: ## Führe nur schnelle Tests aus (Unit)
	@echo "⚡ Running Fast Tests..."
	cd $(BACKEND_DIR) && pytest tests/ -v -m "unit and not slow" --tb=short
	@echo "✅ Schnelle Tests abgeschlossen"

test-watch: ## Führe Tests im Watch-Mode aus
	@echo "👀 Running Tests in Watch Mode..."
	cd $(BACKEND_DIR) && pytest-watch tests/ -v

test-coverage: ## Generiere Coverage-Report
	@echo "📊 Generating Coverage Report..."
	cd $(BACKEND_DIR) && pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
	@echo "✅ Coverage Report: $(BACKEND_DIR)/htmlcov/index.html"

security-scan: ## Führe vollständiges Security Audit durch
	@echo "🔒 Starting Security Audit..."
	./scripts/run-security-audit.sh
	@echo "✅ Security Audit abgeschlossen"

bandit: ## Führe Bandit Security Scan durch
	@echo "📝 Running Bandit..."
	cd $(BACKEND_DIR) && bandit -r app/ -f txt

safety: ## Prüfe Dependencies auf Vulnerabilities
	@echo "📦 Running Safety Check..."
	cd $(BACKEND_DIR) && safety check

semgrep: ## Führe Semgrep SAST durch
	@echo "🔍 Running Semgrep..."
	semgrep --config=.semgrep.yml --verbose backend/app/

secrets: ## Prüfe auf hardcoded Secrets
	@echo "🔐 Running Secrets Detection..."
	detect-secrets scan --all-files

lint: ## Führe Linting durch
	@echo "🔍 Running Linters..."
	cd $(BACKEND_DIR) && flake8 app/ tests/
	cd $(BACKEND_DIR) && mypy app/
	@echo "✅ Linting abgeschlossen"

format: ## Formatiere Code
	@echo "✨ Formatting Code..."
	cd $(BACKEND_DIR) && black app/ tests/
	@echo "✅ Formatting abgeschlossen"

clean: ## Räume Build-Artefakte auf
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(BACKEND_DIR)/htmlcov 2>/dev/null || true
	rm -rf security-reports/*.json 2>/dev/null || true
	@echo "✅ Cleanup abgeschlossen"

docker-up: ## Starte Docker Services
	@echo "🐳 Starting Docker Services..."
	docker-compose up -d
	@echo "✅ Docker Services gestartet"

docker-down: ## Stoppe Docker Services
	@echo "🐳 Stopping Docker Services..."
	docker-compose down
	@echo "✅ Docker Services gestoppt"

dev: docker-up ## Starte Development Environment
	@echo "🚀 Starting Development Environment..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Neo4j: http://localhost:7474"

deploy: ## Deploy mit automatisiertem Script
	@echo "🚀 Deploying with automated script..."
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh development

monitoring: ## Zeige Monitoring-URLs
	@echo "📊 Monitoring dashboards:"
	@echo "  Grafana: http://localhost:3001 (admin/admin)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Jaeger: http://localhost:16686"
	@echo "  Loki: http://localhost:3100"

performance: ## Zeige Performance-Metriken
	@echo "📈 Performance monitoring:"
	@echo "  System Health: http://localhost:8000/api/v1/system/health"
	@echo "  Performance Dashboard: http://localhost:8000/api/v1/performance/monitoring/dashboard"
	@echo "  Metrics: http://localhost:8000/api/v1/performance/monitoring/metrics"

k8s-deploy: ## Deploy zu Kubernetes
	@echo "☸️  Deploying to Kubernetes..."
	kubectl apply -f infra/kubernetes/base-manifests.yaml
	@echo "✅ Kubernetes deployment initiated"

helm-deploy: ## Deploy mit Helm
	@echo "🎯 Deploying with Helm..."
	helm upgrade --install forensics ./infra/helm/blockchain-forensics \
		--namespace blockchain-forensics \
		--create-namespace \
		--values infra/helm/blockchain-forensics/values.yaml
	@echo "✅ Helm deployment initiated"

backup: ## Erstelle Backups
	@echo "💾 Creating backups..."
	docker-compose exec postgres pg_dump -U forensics blockchain_forensics > backups/postgres_$$(date +%Y%m%d_%H%M%S).sql
	docker-compose exec neo4j neo4j-admin database dump --to-path=/backups neo4j
	docker-compose exec redis redis-cli SAVE
	@echo "✅ Backups created"

audit-report: ## Generiere Security Audit Report
	@echo "📊 Generating Security Audit Report..."
	cd $(BACKEND_DIR) && $(PYTHON) -c "import asyncio; from app.security.audit import SecurityAuditor; asyncio.run(SecurityAuditor('.').run_full_audit())"

check-all: lint test test-security security-scan ## Führe alle Checks durch
	@echo "✅ Alle Checks abgeschlossen!"


# --- SDK Generierung (OpenAPI) ---
sdk-ts: ## Generiere TypeScript SDK (fetch)
	@echo "🛠️  Generiere TypeScript SDK aus $(OPENAPI_SPEC) ..."
	docker run --rm -v "$(PWD)":/local openapitools/openapi-generator-cli generate \
	  -i /local/$(OPENAPI_SPEC) \
	  -g typescript-fetch \
	  -o /local/$(SDK_TS_DIR) \
	  --additional-properties=supportsES6=true,typescriptThreePlus=true
	@echo "✅ TypeScript SDK in $(SDK_TS_DIR)"

sdk-py: ## Generiere Python SDK (urllib3)
	@echo "🛠️  Generiere Python SDK aus $(OPENAPI_SPEC) ..."
	docker run --rm -v "$(PWD)":/local openapitools/openapi-generator-cli generate \
	  -i /local/$(OPENAPI_SPEC) \
	  -g python \
	  -o /local/$(SDK_PY_DIR) \
	  --additional-properties=packageName=blockchain_forensics_sdk
	@echo "✅ Python SDK in $(SDK_PY_DIR)"

sdk-clean: ## Lösche generierte SDKs
	@echo "🧹 Entferne generierte SDK-Verzeichnisse..."
	rm -rf $(SDK_TS_DIR) $(SDK_PY_DIR) 2>/dev/null || true
	@echo "✅ SDK-Verzeichnisse bereinigt"

sdk-all: sdk-ts sdk-py ## Generiere beide SDKs
	@echo "🎉 SDK-Generierung abgeschlossen"

sdk-script: ## Generiere SDKs via scripts/generate-sdks.sh
	@echo "🛠️  Generiere SDKs via Skript..."
	chmod +x scripts/generate-sdks.sh
	bash scripts/generate-sdks.sh
	@echo "✅ SDKs generiert (Script)"

sdk-example-ts: ## Führe TypeScript Quickstart Beispiel aus (setzt API_URL voraus)
	@if [ -z "$$API_URL" ]; then echo "⚠️  Bitte API_URL setzen, z.B. export API_URL=http://localhost:8000/api/v1"; exit 1; fi
	@echo "▶️  Running TS Quickstart with API_URL=$$API_URL"
	node docs/examples/sdk/typescript/quickstart.ts

sdk-example-py: ## Führe Python Quickstart Beispiel aus (setzt API_URL voraus)
	@if [ -z "$$API_URL" ]; then echo "⚠️  Bitte API_URL setzen, z.B. export API_URL=http://localhost:8000/api/v1"; exit 1; fi
	@echo "▶️  Running Python Quickstart with API_URL=$$API_URL"
	python3 docs/examples/sdk/python/quickstart.py
