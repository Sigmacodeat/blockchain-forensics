#!/bin/bash

# =============================================================================
# Blockchain-Forensics Docker Startup Script
# =============================================================================
# Startet alle Docker-Services in der korrekten Reihenfolge mit Health Checks
# =============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_env() {
    log_info "Überprüfe .env Konfiguration..."
    
    if [ ! -f .env ]; then
        log_error ".env Datei nicht gefunden!"
        log_info "Kopiere .env.example zu .env und fülle die Werte aus:"
        log_info "  cp .env.example .env"
        exit 1
    fi
    
    # Prüfe kritische Variablen
    MISSING_VARS=()
    
    if ! grep -q "GOOGLE_CLIENT_ID=" .env || grep -q "GOOGLE_CLIENT_ID=your_google" .env; then
        MISSING_VARS+=("GOOGLE_CLIENT_ID")
    fi
    
    if ! grep -q "ETHEREUM_RPC_URL=" .env || grep -q "ETHEREUM_RPC_URL=.*YOUR_" .env; then
        MISSING_VARS+=("ETHEREUM_RPC_URL")
    fi
    
    if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=your_openai" .env; then
        MISSING_VARS+=("OPENAI_API_KEY")
    fi
    
    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        log_warning "Folgende Variablen fehlen in .env:"
        for var in "${MISSING_VARS[@]}"; do
            echo "  - $var"
        done
        log_info "Manche Features funktionieren möglicherweise nicht vollständig."
        read -p "Trotzdem fortfahren? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success ".env Konfiguration OK"
    fi
}

check_docker() {
    log_info "Überprüfe Docker..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker nicht installiert!"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker Daemon läuft nicht!"
        exit 1
    fi
    
    log_success "Docker läuft"
}

stop_existing() {
    log_info "Stoppe existierende Container..."
    docker compose down 2>/dev/null || true
    log_success "Alte Container gestoppt"
}

check_ports() {
    log_info "Überprüfe Ports..."
    
    PORTS=(8000 3000 5435 6381 7475 7688 9092 9090 3003 6333 8081 2181 16686 14250)
    PORTS_USED=()
    
    for port in "${PORTS[@]}"; do
        if lsof -i :$port &> /dev/null; then
            PORTS_USED+=("$port")
        fi
    done
    
    if [ ${#PORTS_USED[@]} -gt 0 ]; then
        log_warning "Folgende Ports sind bereits belegt:"
        for port in "${PORTS_USED[@]}"; do
            echo "  - Port $port ($(lsof -i :$port -t | head -1))"
        done
        read -p "Prozesse beenden? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for port in "${PORTS_USED[@]}"; do
                PID=$(lsof -i :$port -t | head -1)
                if [ -n "$PID" ]; then
                    log_info "Beende Prozess auf Port $port (PID: $PID)..."
                    kill -9 $PID 2>/dev/null || true
                fi
            done
            log_success "Ports freigegeben"
        else
            log_error "Bitte beende die Prozesse manuell."
            exit 1
        fi
    else
        log_success "Alle Ports verfügbar"
    fi
}

start_databases() {
    log_info "Starte Datenbanken..."
    
    docker compose up -d zookeeper kafka postgres redis neo4j qdrant
    
    log_info "Warte auf Health Checks (max 60s)..."
    
    TIMEOUT=60
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        HEALTHY=$(docker compose ps --format json | jq -r 'select(.Health == "healthy" or .Service == "qdrant" or .Service == "zookeeper") | .Service' | wc -l)
        TOTAL=6
        
        if [ "$HEALTHY" -eq "$TOTAL" ]; then
            log_success "Alle Datenbanken healthy"
            return 0
        fi
        
        echo -ne "\r  Warte... ($ELAPSED/$TIMEOUT s) [$HEALTHY/$TOTAL services healthy]"
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done
    
    echo
    log_warning "Timeout erreicht. Einige Services könnten noch nicht healthy sein."
    docker compose ps
}

start_schema_registry() {
    log_info "Starte Schema Registry..."
    docker compose up -d schema-registry
    
    log_info "Warte auf Schema Registry (max 20s)..."
    TIMEOUT=20
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if docker compose exec -T schema-registry wget --no-verbose --tries=1 --spider http://localhost:8081/subjects &>/dev/null; then
            log_success "Schema Registry bereit"
            return 0
        fi
        echo -ne "\r  Warte... ($ELAPSED/$TIMEOUT s)"
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done
    echo
    log_warning "Schema Registry nicht erreichbar"
}

start_backend_services() {
    log_info "Starte Backend Services..."
    docker compose up -d backend monitor-worker ml-service
    
    log_info "Warte auf Backend (max 60s)..."
    TIMEOUT=60
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if curl -sf http://localhost:8000/health &>/dev/null; then
            log_success "Backend bereit"
            return 0
        fi
        echo -ne "\r  Warte... ($ELAPSED/$TIMEOUT s)"
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done
    echo
    log_error "Backend nicht erreichbar!"
    log_info "Logs anzeigen: docker compose logs backend"
}

start_frontend() {
    log_info "Starte Frontend..."
    docker compose up -d frontend
    
    log_info "Warte auf Frontend (max 30s)..."
    TIMEOUT=30
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if curl -sf http://localhost:3000 &>/dev/null; then
            log_success "Frontend bereit"
            return 0
        fi
        echo -ne "\r  Warte... ($ELAPSED/$TIMEOUT s)"
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done
    echo
    log_warning "Frontend nicht erreichbar"
}

start_monitoring() {
    log_info "Starte Monitoring Services..."
    docker compose up -d prometheus grafana jaeger
    log_success "Monitoring gestartet"
}

show_status() {
    echo
    log_info "==================================================================="
    log_info "                   🚀 STARTUP COMPLETE                            "
    log_info "==================================================================="
    echo
    
    docker compose ps
    
    echo
    log_info "Services verfügbar unter:"
    echo
    echo "  🌐 Frontend:          http://localhost:3000"
    echo "  🔧 Backend API:       http://localhost:8000"
    echo "  📚 API Docs:          http://localhost:8000/docs"
    echo "  📊 Grafana:           http://localhost:3003 (admin/admin)"
    echo "  📈 Prometheus:        http://localhost:9090"
    echo "  🔍 Jaeger:            http://localhost:16686"
    echo "  🗄️  Neo4j:             http://localhost:7475 (neo4j/forensics_password_change_me)"
    echo "  🔢 Qdrant:            http://localhost:6333/dashboard"
    echo
    log_info "Logs verfolgen: docker compose logs -f"
    log_info "Services stoppen: docker compose down"
    echo
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    clear
    echo "======================================================================="
    echo "        🐳 Blockchain-Forensics Docker Startup"
    echo "======================================================================="
    echo
    
    check_docker
    check_env
    check_ports
    stop_existing
    
    echo
    log_info "Starte Services in korrekter Reihenfolge..."
    echo
    
    start_databases
    sleep 5
    
    start_schema_registry
    sleep 3
    
    start_backend_services
    sleep 5
    
    start_frontend
    sleep 3
    
    start_monitoring
    sleep 3
    
    show_status
    
    log_success "Alle Services gestartet! 🎉"
}

# Run main function
main "$@"
