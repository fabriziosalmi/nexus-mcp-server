# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## 🚀 Repository Overview

Nexus MCP Server is a modular, configurable Model Context Protocol (MCP) server that acts as a central hub for integrating a wide range of custom tools, making them available to Large Language Models (LLMs).

## 🛠️ Build and Development Commands

### Local Development Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Docker Setup
```bash
# Build Docker image
docker build -t nexus-mcp-server:latest .

# Run with Docker Compose
docker-compose up -d nexus-mcp

# Test container
docker run --rm -i -v "./safe_files:/app/safe_files:rw" nexus-mcp-server:latest python client.py add '{"a": 10, "b": 5}'
```

### Running the Server
```bash
# Start the main MCP server
python multi_server.py

# Start the UI server (on port 8888)
python ui_server.py
```

### Testing
Testing tool functions:
```bash
# Basic calculator test
python client.py add '{"a": 42, "b": 8}'

# Crypto tools test
python client.py generate_hash '{"text": "Hello World", "algorithm": "sha256"}'

# System info test
python client.py system_overview '{}'
```

## 🏗️ Architecture Overview

### Core Components
- **Multi-server (`multi_server.py`)**: Main MCP server implementation
- **HTTP Server (`http_server.py`)**: HTTP interface for tool access
- **UI Server (`ui_server.py`)**: Web UI for configuration management
- **Client (`client.py`)**: CLI client for testing and tool interaction

### Tools Organization
Tools are organized in the `tools/` directory by functionality:
- **Core Tools**: Calculator, system info, basic utilities
- **Security Tools**: Crypto, network security, validation
- **File Operations**: File handling, conversion, archiving
- **Code Tools**: Analysis, generation, execution
- **System Tools**: Process management, monitoring
- **Integration Tools**: Docker, Git, cloud services

### Configuration
- Main server config in `config.json`
- Claude-specific config in `mcp-configs/claude-code-config.json`
- Environment-specific Docker compose files (`docker-compose.yml`, `docker-compose.mcp.yml`)

## 🔒 Security Model

1. **Sandbox Security**
   - File operations restricted to `safe_files/` directory
   - Path traversal protection
   - Input validation on all parameters
   - Secure token generation

2. **Docker Isolation**
   - Resource limits and containerization
   - Network isolation where needed
   - Non-root execution

## 🎯 Development Rules

1. **Tool Development**
   - Maintain tool categorization in the `tools/` directory
   - Follow security guidelines for file access and execution
   - Document new tools in README.md and UI_CONFIGURATION.md

2. **Deployment**
   - Prefer Alpine Linux for pipelines
   - Install binaries directly on Ubuntu without Docker containers
   - For Gitea runner, use VM configuration with IP 192.168.100.133 when available

## 🔍 Common Development Tasks

1. **Adding New Tools**
   - Add tool file in appropriate category under `tools/`
   - Update tool list in `README.md`
   - Configure tool in `config.json`
   - Add test cases in examples/

2. **Configuration Changes**
   - Update `config.json` for tool configuration
   - Use web UI (port 8888) for dynamic configuration
   - Update corresponding Docker environment if needed

3. **Monitoring**
   - Check logs in real-time via UI
   - Monitor system metrics through monitoring.py
   - Use Prometheus metrics when available

## 🪄 Key Tool Categories

The server provides several key tool categories:

1. **Core Utilities**
   - Mathematical operations
   - String manipulation
   - Data validation

2. **Security Tools**
   - Cryptographic functions
   - Network security
   - Data validation

3. **Development Tools**
   - Code generation
   - Git operations
   - Docker management

4. **System Tools**
   - Process management
   - System monitoring
   - Resource tracking

Each tool category follows strict security guidelines and supports both synchronous and asynchronous operations where appropriate.
