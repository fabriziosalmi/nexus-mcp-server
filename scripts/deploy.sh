#!/bin/bash
# Nexus MCP Server - Deployment Script

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzioni di utility
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

# Banner
echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════╗
║        NEXUS MCP SERVER           ║
║     Deployment & Setup Script     ║
║            v2.0.0                 ║
╚═══════════════════════════════════╝
EOF
echo -e "${NC}"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warning "docker-compose not found, trying docker compose plugin..."
        if ! docker compose version &> /dev/null; then
            log_error "Neither docker-compose nor docker compose plugin found."
            exit 1
        fi
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Check Python (for local development)
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        log_info "Python $PYTHON_VERSION detected"
    else
        log_warning "Python3 not found - Docker deployment only"
    fi
    
    log_success "Prerequisites check completed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    docker build -t nexus-mcp-server:latest .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Setup local development environment
setup_local() {
    log_info "Setting up local development environment..."
    
    # Create virtual environment if not exists
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment and install dependencies
    log_info "Installing dependencies..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create safe_files directory if not exists
    if [ ! -d "safe_files" ]; then
        log_info "Creating safe_files directory..."
        mkdir -p safe_files
        echo "This is a sample file in the secure sandbox directory." > safe_files/esempio.txt
    fi
    
    log_success "Local environment setup completed"
}

# Deploy with Docker Compose
deploy_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Create necessary directories
    mkdir -p logs safe_files
    
    # Start services
    $COMPOSE_CMD up -d nexus-mcp
    
    if [ $? -eq 0 ]; then
        log_success "Docker Compose deployment successful"
        log_info "Service status:"
        $COMPOSE_CMD ps
    else
        log_error "Docker Compose deployment failed"
        exit 1
    fi
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Test with simple calculator operation
    if command -v python3 &> /dev/null && [ -d ".venv" ]; then
        log_info "Testing local deployment..."
        source .venv/bin/activate
        python client.py add '{"a": 5, "b": 3}' > /tmp/test_output.txt 2>&1
        
        if grep -q "8" /tmp/test_output.txt; then
            log_success "Local deployment test passed"
        else
            log_warning "Local deployment test may have issues"
            cat /tmp/test_output.txt
        fi
        rm -f /tmp/test_output.txt
    fi
    
    # Test Docker deployment
    log_info "Testing Docker deployment..."
    docker run --rm nexus-mcp-server:latest python -c "print('Docker test successful')" > /tmp/docker_test.txt 2>&1
    
    if grep -q "successful" /tmp/docker_test.txt; then
        log_success "Docker deployment test passed"
    else
        log_warning "Docker deployment test may have issues"
        cat /tmp/docker_test.txt
    fi
    rm -f /tmp/docker_test.txt
}

# Generate MCP configurations
generate_configs() {
    log_info "Generating MCP configuration files..."
    
    # Get current directory
    CURRENT_DIR=$(pwd)
    
    # Generate Claude Code config with actual path
    cat > mcp-configs/claude-code-generated.json << EOF
{
  "mcpServers": {
    "nexus-local": {
      "command": "python",
      "args": ["multi_server.py"],
      "cwd": "$CURRENT_DIR",
      "env": {
        "PYTHONPATH": "$CURRENT_DIR",
        "MCP_SERVER_NAME": "NexusServer-Local",
        "LOG_LEVEL": "INFO"
      }
    },
    "nexus-docker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--network=host",
        "-v", "$CURRENT_DIR/safe_files:/app/safe_files:rw",
        "-v", "$CURRENT_DIR/config.json:/app/config.json:ro",
        "nexus-mcp-server:latest"
      ],
      "env": {
        "MCP_SERVER_NAME": "NexusServer-Docker"
      }
    }
  }
}
EOF

    log_success "Configuration files generated in mcp-configs/"
}

# Main deployment function
main() {
    case "${1:-help}" in
        "local")
            check_prerequisites
            setup_local
            test_deployment
            generate_configs
            log_success "Local development setup completed!"
            ;;
        "docker")
            check_prerequisites
            build_image
            test_deployment
            generate_configs
            log_success "Docker setup completed!"
            ;;
        "compose")
            check_prerequisites
            build_image
            deploy_compose
            test_deployment
            generate_configs
            log_success "Docker Compose deployment completed!"
            ;;
        "full")
            check_prerequisites
            setup_local
            build_image
            deploy_compose
            test_deployment
            generate_configs
            log_success "Full deployment completed!"
            ;;
        "test")
            test_deployment
            ;;
        "help"|*)
            echo "Usage: $0 {local|docker|compose|full|test|help}"
            echo ""
            echo "Commands:"
            echo "  local   - Setup local development environment"
            echo "  docker  - Build Docker image only"
            echo "  compose - Deploy with Docker Compose"
            echo "  full    - Complete setup (local + docker + compose)"
            echo "  test    - Test current deployment"
            echo "  help    - Show this help message"
            ;;
    esac
}

# Run main function
main "$@"