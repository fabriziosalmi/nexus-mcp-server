# 🚀 Nexus MCP Server

**Nexus** is an advanced, modular, and configurable MCP (Model Context Protocol) server that acts as a central hub for integrating a wide range of custom tools, making them available to a Large Language Model (LLM).

## 📖 Quick Navigation

- [📊 Tools Overview](#-tools-and-functions-overview)
- [📋 Complete Tools Table](#-complete-tools-table)
- [🎯 Design Philosophy](#-design-philosophy)
- [🖥️ Web Interface](#️-web-configuration-interface)
- [🚀 Getting Started](#-getting-started)
- [📝 Detailed Tool Documentation](#-detailed-tool-documentation)
- [🐳 Docker Support](#-docker-support)
- [📚 Additional Resources](#-additional-resources)

## 📊 Tools and Functions Overview

🛠️ **Available Tools**: **46**
⚙️ **Total Functions**: **437+**

> 📋 **For detailed tool documentation with examples and parameters, see [TOOLS.md](TOOLS.md)**

## 📋 Complete Tools Table

| Tool | File | Functions | Description |
|------|------|----------|-------------|
| **Encoding Tools** | `encoding_tools.py` | **19** | **Data encoding and decoding (Base64, URL, HTML, Hex)** |
| **Calculator** | `calculator.py` | **16** | **Advanced mathematical operations and calculations** |
| **Cloud Tools** | `cloud_tools.py` | **16** | **Services and APIs for cloud platforms (AWS, Azure, GCP)** |
| **Network Tools** | `network_tools.py` | **15** | **Network diagnostics and utilities** |
| **Code Execution Tools** | `code_execution_tools.py` | **14** | **Secure environments for code execution + Dynamic Tools** |
| **File Converter** | `file_converter.py` | **14** | **Conversion between different file formats** |
| **Docker Tools** | `docker_tools.py` | **13** | **Docker container management** |
| **Network Security Tools** | `network_security_tools.py` | **13** | **Network security scanning** |
| **Regex Tools** | `regex_tools.py` | **13** | **Regular expression utilities** |
| **Security Tools** | `security_tools.py` | **13** | **Security and cryptography utilities** |
| **Code Generation Tools** | `code_generation_tools.py` | **12** | **Code template and structure generation** |
| **Datetime Tools** | `datetime_tools.py` | **12** | **Date and time manipulation** |
| **Image Processing** | `image_processing.py` | **12** | **Image manipulation and analysis** |
| **JSON/YAML Tools** | `json_yaml_tools.py` | **12** | **JSON and YAML manipulation** |
| **Log Analysis Tools** | `log_analysis_tools.py` | **12** | **Log file parsing and analysis** |
| **Markdown Tools** | `markdown_tools.py` | **12** | **Markdown document processing** |
| **Color Tools** | `color_tools.py` | **11** | **Color conversion and analysis** |
| **Crypto Tools** | `crypto_tools.py` | **11** | **Cryptographic functions and hashing** |
| **Data Analysis** | `data_analysis.py` | **11** | **Data processing and statistical analysis** |
| **Database Tools** | `database_tools.py` | **11** | **Database management and queries** |
| **Environment Tools** | `environment_tools.py` | **11** | **Environment variable management** |
| **Git Tools** | `git_tools.py` | **11** | **Git repository management** |
| **Process Management Tools** | `process_management_tools.py` | **11** | **Process control and monitoring** |
| **String Tools** | `string_tools.py` | **11** | **String manipulation functions** |
| **System Info** | `system_info.py` | **11** | **System information and monitoring** |
| **Backup Tools** | `backup_tools.py` | **10** | **Advanced backup and archive management** |
| **Email Tools** | `email_tools.py` | **10** | **Email validation and templates** |
| **Performance Tools** | `performance_tools.py` | **10** | **System performance monitoring** |
| **Audio Processing** | `audio_processing.py` | **9** | **Audio file processing and analysis** |
| **Code Analysis Tools** | `code_analysis_tools.py` | **9** | **Code quality analysis and metrics** |
| **PDF Tools** | `pdf_tools.py` | **9** | **PDF document processing** |
| **Filesystem Reader** | `filesystem_reader.py` | **7** | **Secure file system access** |
| **QR Code Tools** | `qr_code_tools.py` | **7** | **QR code generation and analysis** |
| **Unit Converter** | `unit_converter.py` | **6** | **Unit conversion utilities** |
| **UUID Tools** | `uuid_tools.py` | **6** | **UUID and ID generation** |
| **Validator Tools** | `validator_tools.py` | **5** | **Data validation functions** |
| **Video Processing** | `video_processing.py` | **5** | **Video file processing** |
| **API Testing Tools** | `api_testing_tools.py` | **4** | **REST API testing and documentation** |
| **Async Task Queue** | `async_task_queue.py` | **4** | **Asynchronous queue management for long-running tasks** |
| **Text Analysis Tools** | `text_analysis_tools.py` | **4** | **Sentiment analysis and linguistics** |
| **URL Tools** | `url_tools.py` | **4** | **URL manipulation and validation** |
| **Archive Tools** | `archive_tools.py` | **3** | **ZIP, TAR, 7Z archive management** |
| **Template Tools** | `template_tools.py` | **3** | **Code/config template generation** |
| **Weather Tools** | `weather_tools.py` | **3** | **Weather information** |
| **Web Fetcher** | `web_fetcher.py` | **1** | **Web content retrieval** |
| **Workflow Orchestration** | `workflows.py` | **1** | **Meta-tool for complex workflow orchestration** |

## 🎯 Design Philosophy

- **🎭 Central Orchestration, Distributed Logic**: The main server contains no tool logic, only the responsibility to load and serve them
- **⚙️ Configuration-Driven**: Enable/disable tools via `config.json` file without recompilation
- **🔒 Security First-Class**: Every tool implements rigorous security controls
- **📚 Self-documentation**: Fully documented code for easy maintenance
- **🔄 Workflow Orchestration**: Meta-tools for complex operation chains with a single call
- **🚀 Dynamic Tool Creation**: Runtime generation of custom tools for specific needs
- **🌐 Web UI Management**: Web interface for dynamic management and real-time monitoring

## 🖥️ Web Configuration Interface

**Nexus MCP Server** includes a **modern web interface** for dynamic configuration management without needing to restart the server.

### ✨ Main Features

- **🔧 Tools Dashboard**: View all available tools with checkboxes to enable/disable them
- **📊 Real-time Metrics**: Monitor enabled tools, active sessions, and performance
- **📋 Log Streaming**: Real-time server log display via Server-Sent Events
- **⚡ Hot Reload**: Apply changes without server downtime
- **🎨 Responsive Design**: Modern interface that works on desktop and mobile

### 🚀 Starting the Web Interface

```bash
# Start the UI server on port 8888
python ui_server.py

# Access the web dashboard
# http://localhost:8888
```

### 📸 Screenshots
![claude-desktop](https://raw.githubusercontent.com/fabriziosalmi/nexus-mcp-server/refs/heads/main/nexus-mcp-server-claude-code-desktop.png)

![uuid1](https://raw.githubusercontent.com/fabriziosalmi/nexus-mcp-server/refs/heads/main/generate_uuid_1.png)

![uuid2](https://raw.githubusercontent.com/fabriziosalmi/nexus-mcp-server/refs/heads/main/generate_uuid_2.png)


### 🔗 Complete Documentation

For detailed information about the web interface, see: **[UI_CONFIGURATION.md](UI_CONFIGURATION.md)**

## 🚀 Getting Started

### 📋 Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)

### ⚡ Quick Setup

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

4. **Start the web interface (optional)**
   ```bash
   python ui_server.py
   # Access at http://localhost:8888
   ```

### 🐳 Docker Quick Start

```bash
# Build and run with Docker Compose
docker-compose up nexus-mcp

# Or build manually
docker build -t nexus-mcp-server .
docker run --rm -i nexus-mcp-server
```

### 🔧 Configuration

- Edit `config.json` to enable/disable specific tools
- Use the web interface for dynamic configuration without restarts
- See [Claude Code Configuration](CLAUDE.md) for MCP client setup


## 🐳 Docker Support

Nexus MCP Server includes comprehensive Docker support for easy deployment and isolation:

```bash
# Quick start with Docker Compose
docker-compose up nexus-mcp

# Custom configuration
docker run --rm -i -v "./safe_files:/app/safe_files:rw" nexus-mcp-server:latest
```

For detailed Docker configuration, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 📚 Additional Resources

### 📖 Documentation
- [📋 Complete Tools Reference](TOOLS.md) - Detailed documentation for all 437+ functions
- [🖥️ Web Interface Guide](UI_CONFIGURATION.md) - Web dashboard configuration
- [🐳 Deployment Guide](DEPLOYMENT.md) - Docker and production deployment
- [🔧 Claude Code Setup](CLAUDE.md) - MCP client configuration
- [🚀 Dynamic Tools](DYNAMIC_TOOLS.md) - Runtime tool creation
- [📊 Monitoring](PROMETHEUS_MONITORING.md) - Performance monitoring setup

### 🎯 Key Features
- **120+ Tools** across 17 categories
- **Web Configuration Interface** with real-time monitoring
- **Workflow Orchestration** for complex operations
- **Docker Integration** for secure, isolated execution
- **Dynamic Tool Creation** at runtime
- **Hot Configuration Reload** without server restart

### 🔒 Security Features
- Sandboxed file operations in `safe_files/` directory
- Input validation and sanitization
- Resource limits and timeout protection
- Secure token generation
- Path traversal prevention

### 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines and feel free to submit issues and pull requests.

### 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
**Nexus MCP Server** - Empowering LLMs with advanced tool orchestration and secure execution environments.