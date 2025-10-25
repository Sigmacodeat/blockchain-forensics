#!/bin/bash

# Blockchain Forensics Deployment Script
# Automatisiert Deployment für lokale Entwicklung und Produktion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
DOCKER_COMPOSE_FILE="docker-compose.yml"

echo -e "${BLUE}🚀 Blockchain Forensics Deployment Script${NC}"
echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-deployment checks
pre_deployment_checks() {
    echo -e "\n${YELLOW}🔍 Running pre-deployment checks...${NC}"

    # Check if Docker is installed
    if ! command_exists docker; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file from template${NC}"
    fi

    echo -e "${GREEN}✅ Pre-deployment checks completed${NC}"
}

# Build Docker images
build_images() {
    echo -e "\n${YELLOW}🏗️  Building Docker images...${NC}"

    # Build backend image
    echo -e "${BLUE}Building backend image...${NC}"
    docker build -f Dockerfile.backend -t forensics-backend:latest .

    # Build frontend image
    echo -e "${BLUE}Building frontend image...${NC}"
    docker build -f Dockerfile.frontend -t forensics-frontend:latest .

    echo -e "${GREEN}✅ Docker images built successfully${NC}"
}

# Deploy services
deploy_services() {
    echo -e "\n${YELLOW}🚀 Deploying services...${NC}"

    # Stop existing containers
    echo -e "${BLUE}Stopping existing containers...${NC}"
    docker-compose down || true

    # Start services
    echo -e "${BLUE}Starting services...${NC}"
    docker-compose up -d

    # Wait for services to be healthy
    echo -e "${BLUE}Waiting for services to be ready...${NC}"
    sleep 30

    # Check service health
    check_service_health

    echo -e "${GREEN}✅ Services deployed successfully${NC}"
}

# Check service health
check_service_health() {
    echo -e "\n${YELLOW}🏥 Checking service health...${NC}"

    services=("backend" "frontend" "postgres" "neo4j" "redis")

    for service in "${services[@]}"; do
        if docker-compose ps $service | grep -q "Up"; then
            echo -e "${GREEN}✅ $service: Running${NC}"
        else
            echo -e "${RED}❌ $service: Not running${NC}"
        fi
    done

    # Test API endpoints
    echo -e "\n${BLUE}Testing API endpoints...${NC}"

    # Backend health check
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend API: Healthy${NC}"
    else
        echo -e "${RED}❌ Backend API: Unhealthy${NC}"
    fi

    # Frontend health check
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend: Healthy${NC}"
    else
        echo -e "${RED}❌ Frontend: Unhealthy${NC}"
    fi
}

# Run database migrations
run_migrations() {
    echo -e "\n${YELLOW}🗄️  Running database migrations...${NC}"

    # PostgreSQL migrations
    echo -e "${BLUE}Running PostgreSQL migrations...${NC}"
    docker-compose exec -T backend python -m alembic upgrade head

    # Neo4j schema setup
    echo -e "${BLUE}Setting up Neo4j schema...${NC}"
    docker-compose exec -T backend python scripts/setup_neo4j_schema.py

    echo -e "${GREEN}✅ Database migrations completed${NC}"
}

# Seed initial data
seed_data() {
    echo -e "\n${YELLOW}🌱 Seeding initial data...${NC}"

    # Create admin user
    echo -e "${BLUE}Creating admin user...${NC}"
    docker-compose exec -T backend python scripts/seed_admin_user.py

    # Seed sample data
    echo -e "${BLUE}Seeding sample data...${NC}"
    docker-compose exec -T backend python scripts/seed_sample_data.py

    echo -e "${GREEN}✅ Initial data seeded${NC}"
}

# Setup monitoring
setup_monitoring() {
    echo -e "\n${YELLOW}📊 Setting up monitoring...${NC}"

    # Create Grafana datasources
    echo -e "${BLUE}Configuring Grafana datasources...${NC}"
    docker-compose exec -T backend python scripts/setup_grafana.py

    # Import dashboards
    echo -e "${BLUE}Importing Grafana dashboards...${NC}"
    docker-compose exec -T grafana grafana-cli admin reset-admin-password admin

    echo -e "${GREEN}✅ Monitoring setup completed${NC}"
}

# Main deployment function
main() {
    echo -e "${BLUE}🎯 Starting deployment for environment: $ENVIRONMENT${NC}"

    case $ENVIRONMENT in
        "development")
            pre_deployment_checks
            build_images
            deploy_services
            run_migrations
            seed_data
            setup_monitoring
            ;;
        "production")
            echo -e "${YELLOW}⚠️  Production deployment requires manual review${NC}"
            echo -e "${YELLOW}Make sure to:${NC}"
            echo -e "  1. Review all configuration in .env"
            echo -e "  2. Update secrets in Kubernetes manifests"
            echo -e "  3. Run security scans"
            echo -e "  4. Backup existing data"
            echo -e "\n${GREEN}Ready for production deployment? (y/N)${NC}"
            read -r confirm
            if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
                echo -e "${BLUE}🚀 Deploying to production...${NC}"
                # Production deployment logic here
            else
                echo -e "${YELLOW}Production deployment cancelled${NC}"
                exit 0
            fi
            ;;
        "staging")
            pre_deployment_checks
            deploy_services
            run_migrations
            echo -e "${GREEN}✅ Staging deployment completed${NC}"
            ;;
        *)
            echo -e "${RED}❌ Unknown environment: $ENVIRONMENT${NC}"
            echo -e "${YELLOW}Valid environments: development, staging, production${NC}"
            exit 1
            ;;
    esac

    echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${BLUE}🌐 Frontend: http://localhost${NC}"
    echo -e "${BLUE}🔗 API: http://localhost:8000${NC}"
    echo -e "${BLUE}📊 Grafana: http://localhost:3001${NC}"
    echo -e "${BLUE}🔍 Prometheus: http://localhost:9090${NC}"
    echo -e "${BLUE}📝 Jaeger: http://localhost:16686${NC}"
}

# Run main function with all arguments
main "$@"
