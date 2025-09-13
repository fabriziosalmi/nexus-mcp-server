# 🚀 Nexus MCP Server

**Nexus** is an advanced, modular, and configurable MCP (Model Context Protocol) server that acts as a central hub for integrating a wide range of custom tools, making them available to Large Language Models (LLMs) like Claude and VS Code Copilot.

## 📖 Quick Navigation

- [🎯 Key Features](#-key-features)
- [📸 Screenshots](#-screenshots)
- [⚡ Quick Start](#-quick-start)
- [🔧 VS Code Setup](#-vs-code-setup)
- [🤖 Claude Desktop Setup](#-claude-desktop-setup)
- [🖥️ Web Interface](#️-web-configuration-interface)
- [🐳 Docker Support](#-docker-support)
- [📋 Tools Overview](#-tools-overview)
- [📚 Documentation](#-documentation)

## 🎯 Key Features

### 🛠️ **120+ Tools** across 17 categories
- **Mathematical Operations**: Advanced calculator, statistics, financial calculations
- **Security & Cryptography**: Password generation, encryption, vulnerability scanning
- **Code Generation**: Project scaffolding, API generation, design patterns
- **File Operations**: Format conversion, archiving, PDF processing
- **System Management**: Process monitoring, Docker integration, Git operations
- **Network Tools**: Security scanning, DNS lookups, website analysis
- **Data Processing**: JSON/YAML manipulation, text analysis, validation

### ⚡ **Advanced Capabilities**
- **Dynamic Tool Creation**: Create custom tools on-the-fly using `create_and_run_tool`
- **Web Configuration Interface**: Real-time tool management without restarts
- **Docker Integration**: Secure, isolated execution environments
- **Hot Reload**: Update configurations without server downtime
- **Multi-Client Support**: Works with VS Code, Claude Desktop, and HTTP API

### 🔒 **Security First**
- Sandboxed file operations in `safe_files/` directory
- Input validation and sanitization
- Resource limits and timeout protection
- Path traversal prevention

## 📸 Screenshots

### Claude Desktop Integration
![Claude Desktop Integration](https://raw.githubusercontent.com/fabriziosalmi/nexus-mcp-server/refs/heads/main/nexus-mcp-server-claude-code-desktop.png)

### Tool Usage Examples
![UUID Generation Example 1](https://raw.githubusercontent.com/fabriziosalmi/nexus-mcp-server/refs/heads/main/generate_uuid_1.png)

![UUID Generation Example 2](https://raw.githubusercontent.com/fabriziosalmi/nexus-mcp-server/refs/heads/main/generate_uuid_2.png)

## ⚡ Quick Start

### 📋 Prerequisites
- **Python 3.8+**
- **VS Code** (for VS Code integration) or **Claude Desktop** (for Claude integration)
- **Docker** (optional, for containerized deployment)

### 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fabriziosalmi/nexus-mcp-server.git
   cd nexus-mcp-server
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the MCP server**
   ```bash
   python multi_server.py
   ```

4. **Test the installation**
   ```bash
   python client.py add '{"a": 42, "b": 8}'
   # Expected output: {"result": 50.0}
   ```

## 🔧 VS Code Setup

### Step 1: Install MCP Extension
1. Open VS Code
2. Go to Extensions (`Ctrl/Cmd + Shift + X`)
3. Search for "Model Context Protocol" or "MCP"
4. Install the official MCP extension

### Step 2: Configure Settings
Add to your VS Code `settings.json`:

```json
{
  "mcp.servers": {
    "nexus": {
      "command": "python",
      "args": ["multi_server.py"],
      "cwd": "/absolute/path/to/nexus-mcp-server",
      "env": {
        "PYTHONPATH": "/absolute/path/to/nexus-mcp-server",
        "MCP_SERVER_NAME": "NexusServer",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Step 3: Connect and Use
1. Open Command Palette (`Ctrl/Cmd + Shift + P`)
2. Run "MCP: Connect to Server"
3. Select "nexus" from the list
4. Use tools in Copilot Chat: `@mcp generate_uuid4 {}`

### Troubleshooting VS Code
- **Server not starting**: Ensure Python path is correct and dependencies are installed
- **Tools not available**: Check VS Code Output panel → "Model Context Protocol" for errors
- **Permission errors**: Verify the `nexus-mcp-server` directory has proper read permissions

## 🤖 Claude Desktop Setup

### Step 1: Locate Configuration File
Find your Claude Desktop configuration directory:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

### Step 2: Add Server Configuration
Create or update the configuration file:

```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["multi_server.py"],
      "cwd": "/absolute/path/to/nexus-mcp-server",
      "env": {
        "PYTHONPATH": "/absolute/path/to/nexus-mcp-server",
        "MCP_SERVER_NAME": "NexusServer",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop
1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. Verify connection by asking Claude to use a tool: "Generate a UUID for me"

### Alternative: Minimal Configuration
For testing with fewer tools, use the minimal configuration:

```bash
cp claude_desktop_config_minimal.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

This provides 8 essential tools: Calculator, Crypto, DateTime, Encoding, String, System Info, UUID, and Validator tools.

### Troubleshooting Claude Desktop
- **Server not connecting**: Check the absolute paths in the configuration
- **Module not found errors**: Ensure virtual environment is activated and dependencies installed
- **Permission denied**: Make sure the directory and files are readable
- **Check logs**: Look for `[nexus]` entries in Claude Desktop's application logs

## 🖥️ Web Configuration Interface

**Nexus MCP Server** includes a **modern web interface** for dynamic configuration management without needing to restart the server.

### ✨ Features
- **🔧 Tools Dashboard**: View and enable/disable tools with checkboxes
- **📊 Real-time Metrics**: Monitor enabled tools, active sessions, and performance
- **📋 Log Streaming**: Real-time server log display via Server-Sent Events
- **⚡ Hot Reload**: Apply changes without server downtime
- **🎨 Responsive Design**: Works on desktop and mobile

### 🚀 Starting the Web Interface
```bash
# Start the UI server on port 8888
python ui_server.py

# Access the web dashboard
open http://localhost:8888
```

### 🔧 Using the Interface
1. **View Available Tools**: See all tools in the left panel
2. **Enable/Disable Tools**: Use checkboxes to select tools
3. **Apply Changes**: Click "Apply Changes" to update configuration
4. **Monitor Metrics**: Watch real-time metrics in the right panel
5. **View Logs**: Monitor server activity in the bottom panel

## 🐳 Docker Support

Nexus MCP Server includes comprehensive Docker support for easy deployment and isolation:

### Quick Start with Docker
```bash
# Build and run with Docker Compose
docker-compose up nexus-mcp

# Or build manually
docker build -t nexus-mcp-server .
docker run --rm -i nexus-mcp-server
```

### Custom Configuration
```bash
# Run with custom volume mapping
docker run --rm -i \
  -v "./safe_files:/app/safe_files:rw" \
  -v "./config.json:/app/config.json:ro" \
  nexus-mcp-server:latest
```

### Environment Variables
```bash
# Configure the container
export PYTHONUNBUFFERED=1
export MCP_SERVER_NAME=NexusServer
export LOG_LEVEL=INFO
```

## 📋 Tools Overview

🛠️ **Available Tools**: **120+**
⚙️ **Total Functions**: **500+**

### 🗂️ Tool Categories

| Category | Tools | Description |
|----------|--------|-------------|
| **Mathematical** | Calculator, Statistics, Unit Converter | Advanced calculations, statistical analysis, unit conversions |
| **Security** | Crypto Tools, Security Scanner, Password Generator | Encryption, vulnerability scanning, secure token generation |
| **Development** | Code Generator, Git Tools, Docker Manager | Project scaffolding, version control, container management |
| **File Operations** | File Converter, Archive Tools, PDF Processor | Format conversion, compression, document processing |
| **System** | System Info, Process Manager, Performance Monitor | System monitoring, resource management, performance analysis |
| **Network** | Network Tools, Security Scanner, DNS Lookup | Network diagnostics, security assessment, connectivity tools |
| **Data Processing** | JSON/YAML Tools, Text Analysis, Data Validator | Data manipulation, text processing, validation |
| **String Operations** | String Tools, Regex Engine, Encoding/Decoding | Text manipulation, pattern matching, encoding conversion |

> 📋 **For complete tool documentation with examples and parameters, see [TOOLS.md](TOOLS.md)**

### 🚀 Key Features

#### Dynamic Tool Creation
Create custom tools on-the-fly with `create_and_run_tool`:
```python
# Example: Custom date converter
code = '''
from datetime import datetime
custom_date = "20250907-143022"
date_part, time_part = custom_date.split('-')
dt = datetime(int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8]),
              int(time_part[:2]), int(time_part[2:4]), int(time_part[4:6]))
print(f"ISO format: {dt.isoformat()}")
'''
result = create_and_run_tool(code, timeout=30, memory_limit_mb=64)
```

#### HTTP API Access
Access tools via REST API from any programming language:
```bash
# Example API calls
curl -X POST http://localhost:9999/tools/add/execute \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"a": 15, "b": 27}}'

curl http://localhost:9999/tools/generate_uuid4/execute
```

#### Monitoring & Observability
- **Prometheus Metrics**: Built-in metrics for monitoring tool usage
- **Real-time Logs**: Live log streaming via web interface
- **Performance Tracking**: Execution time and error rate monitoring

## 📚 Documentation

### 📋 Main Documentation
- **[TOOLS.md](TOOLS.md)** - Complete tools reference with 500+ functions, usage examples, and technical details

### 🔧 Advanced Features Documentation
- **[Dynamic Tools](DYNAMIC_TOOLS.md)** - Runtime tool creation with `create_and_run_tool`
- **[Enhanced API](ENHANCED_API.md)** - REST API access for any programming language
- **[Web Interface](UI_CONFIGURATION.md)** - Advanced web dashboard configuration and API endpoints

### 🚀 Deployment & Operations
- **[Docker Deployment](DEPLOYMENT.md)** - Production deployment guides, Docker configurations, and best practices
- **[Prometheus Monitoring](PROMETHEUS_MONITORING.md)** - Production monitoring, metrics, and observability setup

## 🎯 Core Design Principles

- **🎭 Modular Architecture**: Distributed tool logic with central orchestration
- **⚙️ Configuration-Driven**: Enable/disable tools via `config.json` without recompilation
- **🔒 Security First**: Rigorous security controls in every tool
- **📚 Self-Documenting**: Comprehensive documentation and examples
- **🔄 Workflow Support**: Meta-tools for complex operation chains
- **🚀 Runtime Flexibility**: Dynamic tool creation and hot configuration reload

## 🔒 Security Features

- **Sandboxed Operations**: File operations restricted to `safe_files/` directory
- **Input Validation**: Comprehensive sanitization of all parameters
- **Resource Limits**: Memory, CPU, and timeout protection
- **Path Traversal Prevention**: Secure file access controls
- **Docker Isolation**: Optional containerized execution for enhanced security

## 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines and feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Nexus MCP Server** - Empowering LLMs with advanced tool orchestration and secure execution environments.