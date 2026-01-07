#!/bin/bash
set -e

# Mission42 Timesheet Deployment Script
# This script helps deploy the application using either Docker or systemd

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/mission42-timesheet"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_env_file() {
    if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
        log_error ".env.production file not found!"
        log_info "Please create .env.production from .env.example"
        exit 1
    fi
}

deploy_docker() {
    log_info "Starting Docker deployment..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed. Please install docker-compose first."
        exit 1
    fi

    check_env_file

    # Create necessary directories
    log_info "Creating directories..."
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/ssl"
    mkdir -p "$PROJECT_ROOT/pocketbase/pb_data"
    mkdir -p "$PROJECT_ROOT/pocketbase/pb_migrations"

    # Check if SSL certificates exist
    if [ ! -f "$PROJECT_ROOT/ssl/fullchain.pem" ] || [ ! -f "$PROJECT_ROOT/ssl/privkey.pem" ]; then
        log_warning "SSL certificates not found in ssl/ directory"
        log_info "You can use self-signed certificates for testing:"
        log_info "  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\"
        log_info "    -keyout ssl/privkey.pem -out ssl/fullchain.pem"
    fi

    # Copy environment file
    cp "$PROJECT_ROOT/.env.production" "$PROJECT_ROOT/.env"

    # Build and start containers
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"
    docker-compose build

    log_info "Starting services..."
    docker-compose up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check service status
    docker-compose ps

    log_success "Docker deployment complete!"
    log_info "Services:"
    log_info "  - PocketBase Admin: http://localhost:8090/_/"
    log_info "  - FastAPI: http://localhost:8000"
    log_info "  - API Docs: http://localhost:8000/docs"
    log_info ""
    log_info "To view logs: docker-compose logs -f"
    log_info "To stop: docker-compose down"
}

deploy_systemd() {
    log_info "Starting systemd deployment..."

    check_root
    check_env_file

    # Check if Python 3.11+ is installed
    if ! command -v python3.11 &> /dev/null; then
        log_error "Python 3.11+ is not installed"
        exit 1
    fi

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_error "uv package manager is not installed"
        log_info "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # Create www-data user if it doesn't exist
    if ! id -u www-data &> /dev/null; then
        log_info "Creating www-data user..."
        useradd -r -s /bin/false www-data
    fi

    # Create installation directory
    log_info "Creating installation directory..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/pocketbase"

    # Copy project files
    log_info "Copying project files..."
    cp -r "$PROJECT_ROOT/app" "$INSTALL_DIR/"
    cp -r "$PROJECT_ROOT/scripts" "$INSTALL_DIR/"
    cp "$PROJECT_ROOT/pyproject.toml" "$INSTALL_DIR/"
    cp "$PROJECT_ROOT/uv.lock" "$INSTALL_DIR/"
    cp "$PROJECT_ROOT/.env.production" "$INSTALL_DIR/"

    # Copy or download PocketBase
    if [ -f "$PROJECT_ROOT/pocketbase/pocketbase" ]; then
        log_info "Copying PocketBase binary..."
        cp "$PROJECT_ROOT/pocketbase/pocketbase" "$INSTALL_DIR/pocketbase/"
    else
        log_info "Downloading PocketBase..."
        cd "$INSTALL_DIR/pocketbase"
        bash "$PROJECT_ROOT/scripts/download_pocketbase.sh"
    fi

    # Copy migrations if they exist
    if [ -d "$PROJECT_ROOT/pocketbase/pb_migrations" ]; then
        cp -r "$PROJECT_ROOT/pocketbase/pb_migrations" "$INSTALL_DIR/pocketbase/"
    fi

    # Setup Python virtual environment
    log_info "Setting up Python environment..."
    cd "$INSTALL_DIR"
    uv venv
    source .venv/bin/activate
    uv sync --frozen

    # Set permissions
    log_info "Setting permissions..."
    chown -R www-data:www-data "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/pocketbase/pocketbase"

    # Install systemd service files
    log_info "Installing systemd services..."
    cp "$PROJECT_ROOT/systemd/pocketbase.service" /etc/systemd/system/
    cp "$PROJECT_ROOT/systemd/mission42-api.service" /etc/systemd/system/

    # Reload systemd
    log_info "Reloading systemd..."
    systemctl daemon-reload

    # Enable and start services
    log_info "Enabling services..."
    systemctl enable pocketbase mission42-api

    log_info "Starting services..."
    systemctl start pocketbase
    sleep 5
    systemctl start mission42-api

    # Check service status
    log_info "Checking service status..."
    systemctl status pocketbase --no-pager
    systemctl status mission42-api --no-pager

    log_success "Systemd deployment complete!"
    log_info "Services:"
    log_info "  - PocketBase Admin: http://localhost:8090/_/"
    log_info "  - FastAPI: http://localhost:8000"
    log_info "  - API Docs: http://localhost:8000/docs"
    log_info ""
    log_info "To view logs:"
    log_info "  sudo journalctl -u pocketbase -f"
    log_info "  sudo journalctl -u mission42-api -f"
    log_info ""
    log_info "To stop services:"
    log_info "  sudo systemctl stop pocketbase mission42-api"
}

show_usage() {
    echo "Mission42 Timesheet Deployment Script"
    echo ""
    echo "Usage: $0 [docker|systemd]"
    echo ""
    echo "Options:"
    echo "  docker    Deploy using Docker Compose"
    echo "  systemd   Deploy using systemd services (requires root)"
    echo ""
    echo "Examples:"
    echo "  $0 docker              # Deploy with Docker"
    echo "  sudo $0 systemd        # Deploy with systemd"
}

# Main script
case "$1" in
    docker)
        deploy_docker
        ;;
    systemd)
        deploy_systemd
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
