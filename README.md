# 🚀 Nexus MCP Server

**Nexus** is an advanced, modular, and configurable MCP (Model Context Protocol) server that acts as a central hub for integrating a wide range of custom tools, making them available to a Large Language Model (LLM).

## 📊 Tools and Functions Overview

🛠️ **Available Tools**: **46**  
⚙️ **Total Functions**: **437+**

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

![Configuration Dashboard](https://github.com/user-attachments/assets/474943df-d52e-46af-abc1-505f52800b48)
*Main dashboard with all available tools*

![Applied Configuration](https://github.com/user-attachments/assets/cfcda072-80be-4130-a7e9-1ec09dfbb117)
*Example configuration with only 3 tools enabled (calculator, crypto_tools, system_info)*

### 🔗 Complete Documentation

For detailed information about the web interface, see: **[UI_CONFIGURATION.md](UI_CONFIGURATION.md)**

## 📦 Available Tools

### 🧮 Calculator (`calculator.py`)
**Basic mathematical operations**
- `add(a, b)` - Addition
- `multiply(a, b)` - Multiplication

## 📝 Advanced Calculator

Complete mathematical calculation system with advanced functions, number theory, statistics, and secure expression evaluation.

### Main Features

- **Basic Operations**: Fundamental arithmetic with security controls
- **Advanced Functions**: Trigonometry, logarithms, roots, powers
- **Number Theory**: GCD, LCM, factorization, prime numbers
- **Statistics**: Mean, median, standard deviation, variance
- **Unit Conversions**: Length, weight, temperature, volume, time
- **Financial Calculations**: Simple and compound interest
- **Expression Evaluation**: Secure parser for complex expressions
- **Mathematical Constants**: Access to important constants

### Available Tools

#### Basic Operations

##### `add(a, b)` & `multiply(a, b)`
Fundamental arithmetic operations (existing).

##### `subtract(a, b)`
```json
{
  "name": "subtract",
  "arguments": {"a": 10, "b": 3}
}
```

##### `divide(a, b)`
Division with security controls and detailed information.
```json
{
  "name": "divide",
  "arguments": {"a": 15, "b": 4}
}
```
**Output**: `{"result": 3.75, "remainder": 3, "is_integer": false}`

#### Advanced Operations

##### `power(base, exponent)`
Power calculation with overflow protection.
```json
{
  "name": "power",
  "arguments": {"base": 2, "exponent": 10}
}
```

##### `square_root(number)`
```json
{
  "name": "square_root",
  "arguments": {"number": 16}
}
```

##### `nth_root(number, n)`
N-th root with support for odd roots of negative numbers.
```json
{
  "name": "nth_root",
  "arguments": {"number": 27, "n": 3}
}
```

##### `factorial(n)`
```json
{
  "name": "factorial",
  "arguments": {"n": 5}
}
```

#### Trigonometric Functions

##### `trigonometric_functions(angle, unit, functions)`
```json
{
  "name": "trigonometric_functions",
  "arguments": {
    "angle": 45,
    "unit": "degrees",
    "functions": ["sin", "cos", "tan", "cot", "sec", "csc"]
  }
}
```

**Supported units**: `radians`, `degrees`
**Functions**: `sin`, `cos`, `tan`, `cot`, `sec`, `csc`

#### Logarithms

##### `logarithms(number, base)`
```json
{
  "name": "logarithms",
  "arguments": {"number": 100, "base": 10}
}
```
**Output**: Logarithms in natural, base 10, base 2, and specified base.

#### Statistics

##### `statistics_functions(numbers, operation)`
```json
{
  "name": "statistics_functions",
  "arguments": {
    "numbers": [1, 2, 3, 4, 5, 5, 6],
    "operation": "all"
  }
}
```

**Available operations**:
- `mean`: Arithmetic mean
- `median`: Median
- `mode`: Mode
- `stdev`: Standard deviation
- `variance`: Variance
- `range`: Range (max - min)
- `all`: All statistics

#### Number Theory

##### `number_theory(a, b, operation)`
```json
{
  "name": "number_theory",
  "arguments": {"a": 48, "b": 18, "operation": "gcd"}
}
```

**Operations**:
- `gcd`: Greatest Common Divisor
- `lcm`: Least Common Multiple
- `prime_factors`: Prime factorization
- `is_prime`: Primality test

#### Unit Conversions

##### `unit_converter(value, from_unit, to_unit, unit_type)`
```json
{
  "name": "unit_converter",
  "arguments": {
    "value": 100,
    "from_unit": "meter",
    "to_unit": "foot",
    "unit_type": "length"
  }
}
```

**Supported unit types**:

**Length**: `meter`, `kilometer`, `centimeter`, `millimeter`, `inch`, `foot`, `yard`, `mile`

**Weight**: `kilogram`, `gram`, `pound`, `ounce`, `ton`

**Temperature**: `celsius`, `fahrenheit`, `kelvin`

**Volume**: `liter`, `milliliter`, `gallon`, `quart`, `pint`, `cup`

**Time**: `second`, `minute`, `hour`, `day`, `week`, `year`

#### Financial Calculations

##### `financial_calculator(principal, rate, time, calculation_type, compound_frequency)`
```json
{
  "name": "financial_calculator",
  "arguments": {
    "principal": 1000,
    "rate": 5,
    "time": 3,
    "calculation_type": "compound_interest",
    "compound_frequency": 12
  }
}
```

**Calculation types**:
- `simple_interest`: Simple interest
- `compound_interest`: Compound interest
- `present_value`: Present value

#### Expression Evaluation

##### `expression_evaluator(expression, variables)`
```json
{
  "name": "expression_evaluator",
  "arguments": {
    "expression": "2 * pi * r + sqrt(x**2 + y**2)",
    "variables": {"r": 5, "x": 3, "y": 4}
  }
}
```

**Available functions**:
- Arithmetic: `+`, `-`, `*`, `/`, `**`, `%`
- Mathematical: `sin`, `cos`, `tan`, `log`, `sqrt`, `exp`, `abs`
- Constants: `pi`, `e`
- Custom: User-defined variables

**Security features**:
- Isolated execution environment
- Whitelist of allowed functions
- Rigorous input validation
- Prevention of injection attacks

#### Mathematical Constants

##### `mathematical_constants()`
```json
{
  "name": "mathematical_constants",
  "arguments": {}
}
```

**Included constants**:
- π (pi): 3.14159...
- e (euler): 2.71828...
- φ (golden ratio): 1.61803...
- √2, √3
- γ (Euler-Mascheroni): 0.57721...

### Advanced Usage Examples

#### Complex Multi-step Calculation
```json
// 1. Calculate circle area
{
  "name": "expression_evaluator",
  "arguments": {
    "expression": "pi * r**2",
    "variables": {"r": 5}
  }
}

// 2. Statistics on dataset
{
  "name": "statistics_functions",
  "arguments": {
    "numbers": [78.5, 113.1, 50.3, 201.1, 153.9],
    "operation": "all"
  }
}

// 3. Convert result
{
  "name": "unit_converter",
  "arguments": {
    "value": 78.5,
    "from_unit": "meter",
    "to_unit": "foot",
    "unit_type": "length"
  }
}
```

#### Financial Analysis
```json
// Compare simple vs compound interest
{
  "name": "financial_calculator",
  "arguments": {
    "principal": 10000,
    "rate": 7.5,
    "time": 10,
    "calculation_type": "compound_interest",
    "compound_frequency": 4
  }
}
```

#### Geometry Problems
```json
{
  "name": "expression_evaluator",
  "arguments": {
    "expression": "sqrt((x2-x1)**2 + (y2-y1)**2)",
    "variables": {"x1": 0, "y1": 0, "x2": 3, "y2": 4}
  }
}
```

### Security Controls

- **Overflow Protection**: Limits on operations that could cause overflow
- **Division by Zero**: Automatic handling of division by zero
- **Input Validation**: Rigorous validation of all inputs
- **Safe Evaluation**: Isolated environment for expression evaluation
- **Error Handling**: Complete error handling with informative messages

### Precision and Limits

- **Decimal Precision**: 50 significant digits for high-precision calculations
- **Factorial**: Limited to n ≤ 170 to avoid overflow
- **Powers**: Automatic controls to avoid overly large results
- **Expressions**: Maximum length and allowed characters controlled

## 🚀 Dynamic One-Time Tools (Advanced Feature)

**Nexus** includes the revolutionary **Dynamic One-Time Tools** feature - the most advanced capability that allows LLMs to create custom tools on-the-fly for specific tasks that don't have existing solutions.

### 🚀 `create_and_run_tool` Function

This breakthrough feature enables LLMs to write Python code for specific tasks and execute it in a completely isolated, secure environment:

```python
create_and_run_tool(python_code: str, timeout: int = 60, memory_limit_mb: int = 128)
```

### 🔒 Security Features
- **Docker Isolation**: Complete environment isolation using Docker containers
- **Code Security Validation**: Blocks dangerous operations before execution
- **Resource Limits**: Memory (32-512MB), CPU (0.5 cores), Time (10-300s)
- **Network Isolation**: Zero network access during execution
- **Non-root Execution**: Unprivileged user execution
- **Read-only Filesystem**: Limited filesystem access

### 🎯 Use Cases
- **Data Format Conversion**: Convert proprietary or legacy formats
- **Mathematical Computations**: Complex calculations not covered by existing tools
- **Custom Text Processing**: Specific parsing and analysis requirements
- **Algorithm Implementation**: One-off algorithms for unique problems
- **Long-tail Problems**: Any computational task not covered by existing tools

### 💡 Example Usage

```python
# Convert custom timestamp format
code = """
from datetime import datetime
custom_timestamp = "20250907T143022Z"
dt = datetime.strptime(custom_timestamp, "%Y%m%dT%H%M%SZ")
print(f"ISO: {dt.isoformat()}")
print(f"Readable: {dt.strftime('%B %d, %Y at %I:%M %p')}")
"""

result = create_and_run_tool(code, timeout=30, memory_limit_mb=64)
```

**This represents the pinnacle of agentic capabilities** - true on-demand tool creation for any computational task within security constraints.

📖 **[Complete Documentation: DYNAMIC_TOOLS.md](DYNAMIC_TOOLS.md)**

## 🚀 Quick Start

### Automatic Deployment (Recommended)

```bash
# Clone the project
git clone <repository-url> nexus-mcp-server
cd nexus-mcp-server

# Complete deployment with automatic script
./scripts/deploy.sh full

# Or specific deployment:
./scripts/deploy.sh local    # Local environment only
./scripts/deploy.sh docker   # Docker only
./scripts/deploy.sh compose  # Docker Compose
```

### 1. Local Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Docker Setup

```bash
# Build Docker image
docker build -t nexus-mcp-server:latest .

# Start with Docker Compose
docker-compose up -d nexus-mcp

# Test container
docker run --rm -i nexus-mcp-server:latest python -c "print('OK')"
```

### 3. Usage

```bash
# Local
python client.py <tool_name> '<json_arguments>'

# Docker
docker run --rm -i -v "./safe_files:/app/safe_files:rw" nexus-mcp-server:latest python client.py <tool> '<args>'
```

### 3. Usage Examples

```bash
# Calculator
python client.py add '{"a": 42, "b": 8}'
python client.py multiply '{"a": 7, "b": 6}'

# Crypto Tools
python client.py generate_hash '{"text": "Hello World", "algorithm": "sha256"}'
python client.py generate_random_token '{"length": 16, "encoding": "hex"}'

# String Tools  
python client.py string_case_convert '{"text": "Hello World", "case_type": "snake"}'
python client.py string_stats '{"text": "The quick brown fox jumps over the lazy dog"}'

# DateTime Tools
python client.py current_timestamp '{}'
python client.py date_to_unix '{"date_string": "2024-12-25 15:30:00"}'

# UUID Tools
python client.py generate_uuid4 '{}'
python client.py generate_nanoid '{"length": 12, "alphabet": "lowercase"}'

# Encoding Tools
python client.py base64_encode '{"text": "Hello, Nexus!"}'
python client.py json_format '{"json_string": "{\\"name\\":\\"test\\",\\"value\\":123}"}'

# Validator Tools
python client.py validate_email '{"email": "user@example.com"}'
python client.py validate_url '{"url": "https://www.example.com/path?query=1"}'

# System Info
python client.py system_overview '{}'
python client.py memory_usage '{}'
python client.py running_processes '{"limit": 5}'

# Filesystem Reader
python client.py read_safe_file '{"filename": "example.txt"}'

# Web Fetcher  
python client.py fetch_url_content '{"url": "https://httpbin.org/json"}'

# Network Tools
python client.py ping_host '{"host": "8.8.8.8", "count": 4}'
python client.py dns_lookup '{"hostname": "example.com", "record_type": "A"}'
python client.py check_website_status '{"url": "https://www.example.com"}'
python client.py get_public_ip '{}'

# Security Tools
python client.py generate_secure_password '{"length": 16, "include_symbols": true}'
python client.py password_strength_check '{"password": "MyPassword123!"}'
python client.py generate_api_key '{"length": 32, "format_type": "hex"}'

# Network Security Tools
python client.py ip_threat_intelligence '{"ip_address": "8.8.8.8"}'
python client.py scan_security_headers '{"url": "https://example.com"}'
python client.py discover_subdomains '{"domain": "example.com", "wordlist_size": "small"}'
python client.py grab_service_banner '{"host": "example.com", "port": 80}'
python client.py analyze_certificate_chain '{"domain": "example.com", "port": 443"}'

# Performance Tools
python client.py benchmark_function_performance '{"code": "sum(range(1000))", "iterations": 1000}'
python client.py monitor_system_performance '{"duration_seconds": 5}'
python client.py analyze_memory_usage '{}'

# Data Analysis Tools
python client.py statistical_analysis '{"numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}'
python client.py text_analysis '{"text": "This is a sample text for analysis."}'

# Unit Converter Tools
python client.py convert_length '{"value": 100, "from_unit": "cm", "to_unit": "m"}'
python client.py convert_temperature '{"value": 100, "from_unit": "C", "to_unit": "F"}'
python client.py convert_weight '{"value": 1000, "from_unit": "g", "to_unit": "kg"}'
python client.py list_available_units '{}'

# QR Code Tools
python client.py generate_qr_code '{"text": "Hello World", "size": 200}'
python client.py generate_qr_code_url '{"url": "https://github.com", "size": 250}'
python client.py generate_qr_code_wifi '{"ssid": "MyWiFi", "password": "password123", "security": "WPA"}'
python client.py analyze_qr_content '{"content": "https://www.example.com"}'

# Regex Tools
python client.py regex_test '{"pattern": "[0-9]+", "text": "Ho 25 anni e 30 euro"}'
python client.py regex_replace '{"pattern": "[0-9]+", "text": "Ho 25 anni", "replacement": "XXX"}'
python client.py regex_extract_emails '{"text": "Contatta mario@example.com o lucia@test.it"}'
python client.py regex_common_patterns '{}'

# File Converter Tools
python client.py csv_to_json '{"csv_content": "name,age\\nMario,30\\nLucia,25", "delimiter": ","}'
python client.py json_to_csv '{"json_content": "[{\\"name\\": \\"Mario\\", \\"age\\": 30}]"}'
python client.py detect_file_format '{"content": "{\\"test\\": \\"json\\"}"}'
python client.py conversion_help '{}'

# PDF Tools
python client.py pdf_text_extraction_guide '{}'
python client.py pdf_tools_info '{}'

# Cloud Platform Tools
python client.py aws_service_status '{"service": "all", "region": "us-east-1"}'
python client.py azure_service_status '{"service": "compute", "region": "East US"}'
python client.py gcp_service_status '{"service": "all", "region": "us-central1"}'
python client.py cloudflare_dns_lookup '{"domain": "example.com", "record_type": "A"}'
python client.py digitalocean_status_check '{}'
python client.py cloud_cost_calculator '{"service_type": "compute", "usage_hours": 730, "instance_type": "medium"}'
python client.py cloud_health_checker '{"endpoints": ["https://api.example.com", "https://status.example.com"]}'
python client.py cloud_security_scanner '{"config_text": "{\\"Action\\": \\"*\\", \\"Resource\\": \\"*\\"}", "cloud_provider": "aws"}'
python client.py multi_cloud_resource_tracker '{"resources": [{"provider": "aws", "type": "ec2", "name": "web-server", "region": "us-east-1"}]}'
python client.py cloud_config_validator '{"config_text": "{\\"AWSTemplateFormatVersion\\": \\"2010-09-09\\"}", "config_type": "json"}'

# Environment Tools (NEW)
python client.py manage_environment_variables '{"action": "list"}'
python client.py manage_environment_variables '{"action": "get", "variable_name": "PATH"}'
python client.py manage_environment_variables '{"action": "set", "variables": {"CUSTOM_VAR": "value123"}}'
python client.py create_environment_file '{"env_type": "env", "variables": {"DB_HOST": "localhost", "DB_PORT": "5432"}}'
python client.py analyze_system_environment '{}'
python client.py backup_restore_environment '{"action": "backup", "variables": ["PATH", "HOME", "USER"]}'
python client.py validate_configuration_file '{"file_path": "/path/to/config.json", "config_type": "json"}'

# Backup Tools (NEW)  
python client.py create_archive '{"source_path": "/path/to/backup", "archive_type": "zip", "exclude_patterns": ["*.tmp", "*.log"]}'
python client.py extract_archive '{"archive_path": "/path/to/archive.zip", "verify_integrity": true}'
python client.py create_backup_manifest '{"backup_path": "/backup/dir", "source_paths": ["/home/user/docs"]}'
python client.py verify_backup_integrity '{"manifest_path": "/backup/manifest.json"}'
python client.py compress_files '{"file_paths": ["/file1.txt", "/file2.txt"], "algorithm": "gzip", "compression_level": 6}'

# Async Task Queue (NEW - ASYNCHRONOUS TASK MANAGEMENT)
python client.py queue_long_running_task '{"name": "Long Sleep Task", "description": "Task that sleeps for 30 seconds", "task_type": "sleep", "duration": 30}'
python client.py queue_long_running_task '{"name": "CPU Intensive", "description": "CPU-intensive task", "task_type": "cpu_intensive", "duration": 15}'
python client.py queue_long_running_task '{"name": "IO Operations", "description": "Task with I/O operations", "task_type": "io_intensive", "duration": 10}'
python client.py queue_long_running_task '{"name": "Custom Task", "description": "Custom task", "task_type": "custom", "custom_data": "custom data"}'
python client.py get_task_status '{"task_id": "task-uuid"}'
python client.py list_all_tasks '{"status_filter": "running", "limit": 10}'
python client.py list_all_tasks '{"status_filter": "completed", "limit": 5}'
python client.py cancel_task '{"task_id": "task-uuid"}'
python client.py remove_task '{"task_id": "task-uuid"}'
python client.py get_queue_info '{}'
python client.py cleanup_completed_tasks '{"max_age_hours": 12}'

# Log Analysis Tools (NEW)
python client.py parse_log_file '{"file_path": "/var/log/access.log", "log_format": "auto", "max_lines": 1000}'
python client.py analyze_log_patterns '{"log_data": [...], "pattern_type": "errors"}'
python client.py generate_log_report '{"log_data": [...], "report_type": "summary"}'
python client.py filter_log_entries '{"log_data": [...], "filters": {"level": "ERROR", "message_contains": "timeout"}}'
python client.py export_log_analysis '{"analysis_data": {...}, "export_format": "html"}'

# Workflow Orchestration (NEW - META-TOOL)
python client.py analyze_repository '{"url": "https://github.com/user/repo.git", "analysis_depth": "standard"}'
python client.py analyze_repository '{"url": "https://github.com/user/repo.git", "analysis_depth": "deep"}'

# Database Tools
python client.py create_sqlite_database '{"database_name": "test_db", "tables": [{"name": "users", "columns": [{"name": "id", "type": "INTEGER", "primary_key": true}, {"name": "name", "type": "TEXT"}]}]}'
python client.py validate_sql_query '{"query": "SELECT * FROM users WHERE id = 1", "database_type": "sqlite"}'
python client.py execute_safe_query '{"database_path": "/tmp/test.db", "query": "SELECT COUNT(*) FROM users"}'

# Docker Tools
python client.py check_docker_status '{}'
python client.py list_docker_containers '{"status": "running"}'
python client.py list_docker_images '{}'
python client.py validate_dockerfile '{"dockerfile_content": "FROM python:3.9\\nCOPY . /app\\nWORKDIR /app"}'

# Git Tools
python client.py analyze_git_repository '{"repo_path": "."}'
python client.py git_diff_analysis '{"file_path": "README.md", "staged": false}'
python client.py git_commit_history '{"limit": 10}'
python client.py generate_gitignore '{"language": "python", "additional_patterns": ["*.custom"]}'

# Process Management Tools
python client.py list_processes_by_criteria '{"criteria": "cpu_usage", "limit": 10}'
python client.py monitor_process '{"pid": 1234, "duration": 30}'
python client.py execute_with_limits '{"command": "echo hello", "timeout": 10, "memory_limit_mb": 50}'
python client.py analyze_system_resources '{}'

# Code Execution Tools (Dynamic Tools)
python client.py execute_python_code '{"code": "print(\\"Hello World\\")", "timeout": 30}'
python client.py create_and_run_tool '{"python_code": "import datetime\\nprint(datetime.datetime.now())", "timeout": 60}'
python client.py validate_python_syntax '{"code": "def hello(): return \\"world\\"", "strict_mode": true}'
## 🚀 Code Generation Tools

Complete suite for automatic code generation, project scaffolding, design patterns, and documentation with multi-language and framework support.

### Main Features

- **Class & API Generation**: Generate classes, REST endpoints, models
- **Database Schema**: SQL schemas, migrations, ORM models
- **Project Scaffolding**: Complete project structures with frameworks
- **Design Patterns**: GoF and architectural pattern implementations
- **Frontend Components**: React, Vue, Angular, Svelte components
- **API Documentation**: OpenAPI, Postman, Markdown
- **CI/CD Pipelines**: GitHub Actions, GitLab CI, Jenkins
- **Code Modernization**: Refactoring and legacy conversion
- **Docker & Config**: Dockerfile, multi-environment configurations

### Available Tools

#### Base Generation

##### `generate_python_class`
Generates complete Python classes with methods and documentation.

**Parameters:**
- `class_name` (str): Class name (PascalCase)
- `attributes` (List[str]): List of class attributes
- `methods` (List[str]): List of methods to generate
- `parent_class` (str): Parent class (optional)

**Example:**
```json
{
  "name": "generate_python_class",
  "arguments": {
    "class_name": "UserManager",
    "attributes": ["users", "database_connection"],
    "methods": ["add_user", "remove_user", "find_user", "update_user"],
    "parent_class": "BaseManager"
  }
}
```

##### `generate_api_endpoints`
Generates complete REST endpoints for resource.

**Parameters:**
- `resource_name` (str): Resource name (e.g., "user", "product")
- `operations` (List[str]): HTTP operations (GET, POST, PUT, DELETE)
- `framework` (str): Web framework (`flask`, `fastapi`, `django`)

**Example:**
```json
{
  "name": "generate_api_endpoints",
  "arguments": {
    "resource_name": "product",
    "operations": ["GET", "POST", "PUT", "DELETE"],
    "framework": "fastapi"
  }
}
```

#### Database & Schema

##### `generate_database_schema`
Generates database schema with migrations and ORM models.

**Parameters:**
- `table_name` (str): Table name
- `fields` (List[Dict]): Fields with type, constraints, indices
- `database_type` (str): DBMS (`postgresql`, `mysql`, `sqlite`, `mongodb`)
- `include_migrations` (bool): Include migration script

**Example:**
```json
{
  "name": "generate_database_schema",
  "arguments": {
    "table_name": "users",
    "fields": [
      {"name": "id", "type": "uuid", "primary_key": true},
      {"name": "email", "type": "string", "unique": true, "not_null": true},
      {"name": "name", "type": "string", "not_null": true},
      {"name": "created_at", "type": "datetime", "default": "NOW()"},
      {"name": "is_active", "type": "boolean", "default": true}
    ],
    "database_type": "postgresql",
    "include_migrations": true
  }
}
```

#### Project Scaffolding

##### `generate_project_scaffold`
Generates complete project structure with framework.

**Parameters:**
- `project_name` (str): Project name
- `project_type` (str): Type (`web`, `api`, `cli`, `desktop`, `microservice`)
- `framework` (str): Specific framework
- `features` (List[str]): Features to include

**Supported Project Types:**
- **Web**: `react`, `vue`, `angular`, `svelte`
- **API**: `fastapi`, `flask`, `express`, `spring`
- **CLI**: `click`, `argparse`, `typer`
- **Microservice**: `fastapi`, `spring-boot`, `express`

**Available Features:**
- `auth`: Authentication system
- `database`: Database setup
- `tests`: Test structure
- `docker`: Containerization
- `github_actions`: CI/CD
- `typescript`: TypeScript support
- `redux`: State management
- `tailwind`: CSS framework

**Example:**
```json
{
  "name": "generate_project_scaffold",
  "arguments": {
    "project_name": "ecommerce-api",
    "project_type": "api",
    "framework": "fastapi",
    "features": ["auth", "database", "tests", "docker", "github_actions"]
  }
}
```

#### Design Patterns

##### `generate_design_pattern`
Implements common design patterns with documentation.

**Supported Patterns:**
- **Creational**: Singleton, Factory, Builder, Prototype
- **Structural**: Adapter, Decorator, Facade, Proxy
- **Behavioral**: Observer, Strategy, Command, State

**Example:**
```json
{
  "name": "generate_design_pattern",
  "arguments": {
    "pattern_name": "observer",
    "language": "python",
    "class_names": ["NewsAgency", "NewsChannel"],
    "custom_params": {"event_types": ["breaking", "sports", "weather"]}
  }
}
```

#### Frontend Components

##### `generate_frontend_component`
Genera componenti frontend con styling e test.

**Framework Supported:**
- **React**: Functional, Class, Hooks
- **Vue**: Composition API, Options API
- **Angular**: Component, Service, Module
- **Svelte**: Component con stores

**Styling Options:**
- `css`: CSS vanilla
- `scss`: Sass/SCSS
- `styled-components`: CSS-in-JS
- `tailwind`: Tailwind CSS
- `module.css`: CSS Modules

**Example:**
```json
{
  "name": "generate_frontend_component",
  "arguments": {
    "component_name": "ProductCard",
    "framework": "react",
    "component_type": "functional",
    "props": [
      {"name": "product", "type": "object", "required": true},
      {"name": "onAddToCart", "type": "function", "required": false},
      {"name": "showDescription", "type": "boolean", "default": true}
    ],
    "styling": "styled-components"
  }
}
```

#### Documentation

##### `generate_api_documentation`
Genera documentazione API completa con esempi.

**Supported Formats:**
- **OpenAPI**: Specifica OpenAPI 3.0
- **Postman**: Collection Postman
- **Markdown**: Documentazione Markdown
- **Insomnia**: Collection Insomnia

**Example:**
```json
{
  "name": "generate_api_documentation",
  "arguments": {
    "api_name": "E-commerce API",
    "endpoints": [
      {
        "path": "/products",
        "method": "GET",
        "description": "Get all products",
        "parameters": [
          {"name": "limit", "type": "integer", "in": "query"},
          {"name": "category", "type": "string", "in": "query"}
        ],
        "responses": {
          "200": {"description": "Success", "schema": "ProductList"}
        }
      }
    ],
    "doc_format": "openapi",
    "include_examples": true
  }
}
```

#### CI/CD & DevOps

##### `generate_cicd_pipeline`
Genera pipeline CI/CD per diverse piattaforme.

**Piattaforme Supportate:**
- **GitHub Actions**: Workflow YAML
- **GitLab CI**: .gitlab-ci.yml
- **Jenkins**: Jenkinsfile
- **Azure DevOps**: Pipeline YAML

**Deployment Target:**
- `docker`: Container deployment
- `kubernetes`: K8s deployment
- `aws`: AWS services
- `heroku`: Heroku deployment
- `vercel`: Vercel deployment

**Example:**
```json
{
  "name": "generate_cicd_pipeline",
  "arguments": {
    "project_name": "my-web-app",
    "platform": "github_actions",
    "language": "python",
    "stages": ["build", "test", "deploy"],
    "deployment_target": "docker"
  }
}
```

##### `generate_dockerfile_template`
Genera Dockerfile ottimizzati per linguaggio.

**Example:**
```json
{
  "name": "generate_dockerfile_template",
  "arguments": {
    "base_image": "python:3.11-slim",
    "language": "python",
    "port": 8000
  }
}
```

#### Testing

##### `generate_test_template`
Genera template test unitari e integrazione.

**Framework Supported:**
- **Python**: unittest, pytest
- **JavaScript**: Jest, Mocha, Cypress
- **Java**: JUnit, TestNG

**Example:**
```json
{
  "name": "generate_test_template",
  "arguments": {
    "test_type": "unit",
    "class_name": "UserService",
    "methods": ["create_user", "authenticate", "update_profile"],
    "framework": "pytest"
  }
}
```

#### Code Modernization

##### `modernize_legacy_code`
Modernizza e refactorizza codice legacy.

**Tipi di Modernizzazione:**
- `refactor`: Refactoring same language
- `convert`: Conversione linguaggio
- `optimize`: Ottimizzazione performance

**Example:**
```json
{
  "name": "modernize_legacy_code",
  "arguments": {
    "legacy_code": "old_python_code_here",
    "source_language": "python2",
    "target_language": "python3",
    "modernization_type": "convert"
  }
}
```

#### Configuration

##### `generate_config_file`
Genera file configurazione multi-ambiente.

**Supported Formats:**
- `json`: Configurazione JSON
- `yaml`: File YAML
- `ini`: File INI/CFG
- `env`: Environment variables

**Example:**
```json
{
  "name": "generate_config_file",
  "arguments": {
    "config_type": "yaml",
    "application_name": "my-app",
    "environment": "production"
  }
}
```

### Esempi di Utilizzo Avanzato

#### Sviluppo Full-Stack Completo
```json
// 1. Genera progetto backend
{
  "name": "generate_project_scaffold",
  "arguments": {
    "project_name": "task-manager-api",
    "project_type": "api",
    "framework": "fastapi",
    "features": ["auth", "database", "tests", "docker"]
  }
}

// 2. Genera schema database
{
  "name": "generate_database_schema",
  "arguments": {
    "table_name": "tasks",
    "fields": [
      {"name": "id", "type": "uuid", "primary_key": true},
      {"name": "title", "type": "string", "not_null": true},
      {"name": "completed", "type": "boolean", "default": false}
    ],
    "database_type": "postgresql"
  }
}

// 3. Genera frontend
{
  "name": "generate_project_scaffold",
  "arguments": {
    "project_name": "task-manager-ui",
    "project_type": "web",
    "framework": "react",
    "features": ["typescript", "tailwind", "tests"]
  }
}

// 4. Genera pipeline CI/CD
{
  "name": "generate_cicd_pipeline",
  "arguments": {
    "project_name": "task-manager",
    "platform": "github_actions",
    "language": "python",
    "stages": ["build", "test", "deploy"]
  }
}
```

#### Microservizi con Documentazione
```json
// 1. Genera microservizio
{
  "name": "generate_project_scaffold",
  "arguments": {
    "project_name": "user-service",
    "project_type": "microservice",
    "framework": "fastapi",
    "features": ["auth", "database", "docker", "monitoring"]
  }
}

// 2. Genera API documentation
{
  "name": "generate_api_documentation",
  "arguments": {
    "api_name": "User Service API",
    "endpoints": [...],
    "doc_format": "openapi"
  }
}
```

#### Sistema Enterprise
```json
// 1. Design pattern per architettura
{
  "name": "generate_design_pattern",
  "arguments": {
    "pattern_name": "facade",
    "language": "python",
    "class_names": ["PaymentFacade", "PaymentGateway"]
  }
}

// 2. Database schema complesso
{
  "name": "generate_database_schema",
  "arguments": {
    "table_name": "orders",
    "fields": [...],
    "database_type": "postgresql",
    "include_migrations": true
  }
}
```

### Best Practices

1. **Naming Conventions**: Usa PascalCase per classi, snake_case per funzioni
2. **Project Structure**: Segui convenzioni framework per organizzazione
3. **Documentation**: Genera sempre documentazione con esempi
4. **Testing**: Include test per ogni componente generato
5. **Security**: Usa pattern sicuri e validation input
6. **Performance**: Ottimizza query database e componenti
7. **Maintainability**: Genera codice pulito e ben documentato
8. **CI/CD**: Setup pipeline dal primo commit

### Template Personalizzati

Il sistema supporta template personalizzati per:
- **Aziende**: Standard aziendali specifici
- **Team**: Convenzioni team development
- **Progetti**: Template progetto ricorrenti
- **Architetture**: Pattern architetturali custom

# 🎨 Color Tools

Complete suite for professional color management with color theory, accessibility, psychology, and design tools.

### Main Features

- **Format Conversions**: Hex, RGB, HSL, HSV with professional precision
- **Palette Generation**: Harmonic schemes based on color theory
- **Accessibility**: WCAG contrast analysis and colorblindness simulation
- **Gradient Creator**: Gradient generation with customizable easing
- **Color Psychology**: Analysis of meaning and emotional impact
- **Color Matching**: Named color search in professional databases
- **Temperature Analysis**: Warm/cool color classification
- **Export Tools**: Export for design software

### Available Tools

#### Basic Conversions and Analysis

##### `convert_color_format`
Converts colors between formats with complete information.

**Parameters:**
- `color` (str): Colore sorgente (hex, rgb, nome)
- `target_format` (str): Formato destinazione

**Supported Formats:**
- **HEX**: `#FF0000`, `#ff0000`
- **RGB**: `rgb(255,0,0)`, `255,0,0`
- **HSL**: Hue, Saturation, Lightness
- **HSV**: Hue, Saturation, Value
- **Nomi**: red, green, blue, etc.

**Example:**
```json
{
  "name": "convert_color_format",
  "arguments": {
    "color": "#3498db",
    "target_format": "hsl"
  }
}
```

##### `analyze_color_contrast`
Analisi contrasto WCAG per accessibilità.

**Example:**
```json
{
  "name": "analyze_color_contrast",
  "arguments": {
    "color1": "#000000",
    "color2": "#FFFFFF"
  }
}
```

**Standard WCAG:**
- **AA Normal**: Contrasto ≥ 4.5:1
- **AA Large**: Contrasto ≥ 3.0:1  
- **AAA Normal**: Contrasto ≥ 7.0:1
- **AAA Large**: Contrasto ≥ 4.5:1

#### Palette e Schemi Colore

##### `generate_color_palette`
Genera palette armoniose secondo teoria del colore.

**Tipi di Palette:**
- `complementary`: Colori opposti sulla ruota
- `triadic`: 3 colori equidistanti (120°)
- `analogous`: Colori adiacenti
- `monochromatic`: Variazioni stesso colore

##### `generate_color_scheme`
Schemi colore professionali avanzati.

**Schemi Disponibili:**
- **Monochromatica**: Variazioni luminosità/saturazione
- **Analogous**: Colori adiacenti (±30°)
- **Complementary**: Colore opposto + variazioni
- **Triadic**: 3 colori a 120° di distanza
- **Tetradica**: 4 colori in quadrato/rettangolo
- **Split Complementary**: Base + 2 colori adiacenti al complementare

**Example:**
```json
{
  "name": "generate_color_scheme",
  "arguments": {
    "base_color": "#E74C3C",
    "scheme_type": "triadic",
    "count": 6
  }
}
```

#### Gradienti e Interpolazione

##### `generate_gradient`
Generazione gradienti con curve di easing.

**Parameters:**
- `start_color` (str): Colore iniziale
- `end_color` (str): Colore finale  
- `steps` (int): Numero step (3-20)
- `gradient_type` (str): Tipo easing

**Tipi di Easing:**
- `linear`: Transizione lineare
- `ease-in`: Accelerazione graduale
- `ease-out`: Decelerazione graduale
- `ease-in-out`: Accelerazione poi decelerazione

**Example:**
```json
{
  "name": "generate_gradient",
  "arguments": {
    "start_color": "#FF6B6B",
    "end_color": "#4ECDC4", 
    "steps": 7,
    "gradient_type": "ease-in-out"
  }
}
```

**Output include:**
- Step intermedi con posizione
- CSS `linear-gradient()` e `radial-gradient()`
- Analisi armonia cromatica

##### `color_mixer`
Miscelazione precisa di due colori.

**Example:**
```json
{
  "name": "color_mixer",
  "arguments": {
    "color1": "#FF0000",
    "color2": "#0000FF",
    "ratio": 0.3
  }
}
```

#### Accessibilità e Inclusività

##### `simulate_color_blindness`
Simulazione visione daltonismo per test accessibilità.

**Tipi di Daltonismo:**
- **Protanopia**: Cecità al rosso (~1% uomini)
- **Deuteranopia**: Cecità al verde (~1% uomini)
- **Tritanopia**: Cecità al blu (~0.003% popolazione)
- **Achromatopsia**: Visione monocromatica (rara)

**Example:**
```json
{
  "name": "simulate_color_blindness",
  "arguments": {
    "colors": ["#FF0000", "#00FF00", "#0000FF"],
    "blindness_type": "deuteranopia"
  }
}
```

**Output include:**
- Colori simulati per ciascun tipo
- Score di differenza percettiva
- Raccomandazioni accessibilità

#### Psicologia e Significato

##### `analyze_color_psychology`
Analisi psicologica e significato culturale dei colori.

**Example:**
```json
{
  "name": "analyze_color_psychology",
  "arguments": {
    "colors": ["#E74C3C", "#3498DB", "#2ECC71"]
  }
}
```

**Analisi include:**
- **Emozioni Associate**: Sentimenti evocati
- **Tratti Caratteristici**: Personalità e attributi
- **Casi d'Uso**: Settori e applicazioni ideali
- **Analisi Combinazione**: Effetto dei colori insieme
- **Mood Generale**: Atmosfera complessiva

##### `analyze_color_temperature`
Classificazione temperatura cromatica.

**Categorie:**
- **Caldi**: Rosso, arancione, giallo (energia, passione)
- **Freddi**: Blu, verde, viola (calma, professionalità)
- **Neutri**: Grigi, beige (equilibrio, versatilità)

#### Ricerca e Matching

##### `find_closest_named_color`
Trova colore nominato più simile.

**Database Supported:**
- **CSS**: Colori web standard
- **Pantone**: Sistema colori professionale
- **RAL**: Standard europeo industriale
- **X11**: Colori sistema Unix/Linux

**Example:**
```json
{
  "name": "find_closest_named_color",
  "arguments": {
    "color": "#FF6B6B",
    "color_system": "css"
  }
}
```

#### Export e Integrazione

##### `export_color_palette`
Esportazione palette per software di design.

**Formati di Export:**
- **CSS**: Variabili CSS custom properties
- **SCSS**: Variabili Sass/SCSS
- **JSON**: Formato programmatico
- **ASE**: Adobe Swatch Exchange (info)
- **GPL**: GIMP Palette
- **XML**: Formato XML generico

**Example:**
```json
{
  "name": "export_color_palette",
  "arguments": {
    "colors": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57"],
    "export_format": "css",
    "palette_name": "Summer Vibes"
  }
}
```

### Esempi di Utilizzo Avanzato

#### Design System Completo
```json
// 1. Genera schema colore primario
{
  "name": "generate_color_scheme",
  "arguments": {
    "base_color": "#2C3E50",
    "scheme_type": "analogous",
    "count": 5
  }
}

// 2. Testa accessibilità
{
  "name": "analyze_color_contrast",
  "arguments": {
    "color1": "#2C3E50",
    "color2": "#FFFFFF"
  }
}

// 3. Simula daltonismo
{
  "name": "simulate_color_blindness",
  "arguments": {
    "colors": ["#2C3E50", "#3498DB", "#E74C3C"],
    "blindness_type": "deuteranopia"
  }
}

// 4. Esporta per sviluppo
{
  "name": "export_color_palette",
  "arguments": {
    "colors": ["#2C3E50", "#3498DB", "#E74C3C"],
    "export_format": "css",
    "palette_name": "Brand Colors"
  }
}
```

#### Analisi Brand Identity
```json
// 1. Analizza psicologia colori brand
{
  "name": "analyze_color_psychology",
  "arguments": {
    "colors": ["#FF6B35", "#004225", "#F7931E"]
  }
}

// 2. Classifica temperatura
{
  "name": "analyze_color_temperature",
  "arguments": {
    "colors": ["#FF6B35", "#004225", "#F7931E"]
  }
}

// 3. Genera gradienti per UI
{
  "name": "generate_gradient",
  "arguments": {
    "start_color": "#FF6B35",
    "end_color": "#F7931E",
    "steps": 5,
    "gradient_type": "ease-out"
  }
}
```

#### Sviluppo Interfaccia Accessibile
```json
// 1. Verifica contrasti multipli
{
  "name": "analyze_color_contrast",
  "arguments": {
    "color1": "#333333",
    "color2": "#FFFFFF"
  }
}

// 2. Test daltonismo completo
{
  "name": "simulate_color_blindness",
  "arguments": {
    "colors": ["#007bff", "#28a745", "#dc3545"],
    "blindness_type": "protanopia"
  }
}

// 3. Alternative accessibili
{
  "name": "find_closest_named_color",
  "arguments": {
    "color": "#007bff",
    "color_system": "css"
  }
}
```

### Teoria del Colore Integrata

#### Ruota Cromatica
- **Primari**: Rosso, Blu, Giallo
- **Secondari**: Verde, Arancione, Viola
- **Terziari**: Combinazioni primari + secondari

#### Proprietà Colore
- **Hue (Tonalità)**: Posizione sulla ruota (0-360°)
- **Saturation (Saturazione)**: Intensità colore (0-100%)
- **Value/Lightness**: Luminosità (0-100%)

#### Armonie Cromatiche
- **Monocromatica**: Stesso hue, diversa saturazione/luminosità
- **Analoga**: Colori adiacenti (±30° sulla ruota)
- **Complementare**: Colori opposti (180°)
- **Triadica**: 3 colori equidistanti (120°)
- **Tetradica**: 4 colori in quadrato/rettangolo

### Accessibilità Web (WCAG)

#### Livelli di Conformità
- **A**: Livello minimo accessibilità
- **AA**: Standard raccomandato (4.5:1 normale, 3:1 grande)
- **AAA**: Livello superiore (7:1 normale, 4.5:1 grande)

#### Best Practices
1. **Testa sempre** il contrasto con strumenti
2. **Non affidarti solo** al colore per informazioni
3. **Considera daltonismo** (8% uomini, 0.5% donne)
4. **Usa pattern** aggiuntivi per differenziazione
5. **Testa con utenti reali** quando possibile

## 🔒 Security Tools

Strumenti avanzati per sicurezza informatica, audit e protezione:

### Main Features

- **Password Security**: Generazione e analisi forza password
- **Crittografia**: Encryption/decryption con algoritmi sicuri
- **Token Generation**: Creazione token sicuri per vari usi
- **Vulnerability Scanning**: Scanner vulnerabilità automatizzato
- **Security Audit**: Audit completo di sicurezza sistemi/web
- **SSL/TLS Analysis**: Controllo certificati e configurazione
- **Security Headers**: Analisi header di sicurezza HTTP
- **Security Reporting**: Generazione report sicurezza dettagliati

### Available Tools

#### `generate_secure_password(length?: int, include_symbols?: bool, exclude_ambiguous?: bool)`
Generazione password sicure:
- Lunghezza configurabile (8-128 caratteri)
- Inclusione/esclusione simboli e caratteri ambigui
- Calcolo entropia e forza password
- Classificazione automatica sicurezza

#### `password_strength_check(password: string)`
Analisi dettagliata forza password:
- Controllo caratteri (maiuscole, minuscole, numeri, simboli)
- Rilevamento pattern comuni e sequenze
- Punteggio forza con suggerimenti miglioramento
- Classificazione da "Molto Debole" a "Molto Forte"

#### `generate_api_key(length?: int, format_type?: string)`
Generazione chiavi API sicure:
- Formati: hex, base64, alphanumeric
- Calcolo entropia bit
- Lunghezza personalizzabile
- Standard industry best practices

#### `generate_secure_tokens(token_type: string, count?: int, options?: string)`
Generazione token specializzati:
- Tipi: session, csrf, api, uuid, otp
- Opzioni personalizzazione per tipo
- Raccomandazioni sicurezza specifiche
- Batch generation fino a 100 token

#### `comprehensive_security_audit(target: string, scan_type?: string)`
Audit sicurezza completo:
- Tipi scan: basic, network, web, full
- Port scanning con analisi vulnerabilità
- Controllo SSL/TLS e certificati
- Risk scoring automatico
- Report findings e raccomandazioni

#### `vulnerability_scanner(target: string, scan_depth?: string)`
Scanner vulnerabilità avanzato:
- Profondità: surface, deep, aggressive
- Check porte aperte, SSL, DNS, HTTP headers
- Rilevamento service banners e credenziali default
- Test directory traversal e SQL injection
- Risk assessment con severity classification

#### `encrypt_decrypt_data(data: string, operation: string, key?: string, algorithm?: string)`
Crittografia/decrittografia sicura:
- Algoritmi: Fernet (AES), Base64 encoding
- Generazione chiavi automatica
- Operazioni encrypt/decrypt
- Note sicurezza e best practices

#### `security_headers_analyzer(url: string)`
Analisi header sicurezza HTTP:
- Check HSTS, CSP, X-Frame-Options, etc.
- Scoring sicurezza e grading (A-F)
- Identificazione header mancanti
- Raccomandazioni implementazione

#### `generate_security_report(data: string)`
Generazione report sicurezza completi:
- Aggregazione risultati multiple scan
- Executive summary con metriche chiave
- Risk assessment dettagliato
- Raccomandazioni prioritizzate
- Compliance status evaluation

#### `hash_file_content(content: string, algorithms?: string[])`
Hashing contenuti per integrità:
- Algoritmi: MD5, SHA1, SHA256, SHA512
- Multiple hash simultanei
- Verifica integrità file
- Forensic analysis support

#### `jwt_decode_header(jwt_token: string)`
Decodifica JWT token (senza verifica):
- Estrazione header e payload
- Analisi struttura token
- Warning sicurezza appropriati
- Debug e troubleshooting

#### `check_common_ports(host: string)`
Scanning porte comuni:
- Check servizi standard (FTP, SSH, HTTP, etc.)
- Identificazione servizi esposti
- Warning sicurezza automatici
- Risk level assessment

#### `ssl_certificate_check(domain: string, port?: int)`
Controllo certificati SSL/TLS:
- Validità e scadenza certificati
- Analisi issuer e subject
- Warning pre-scadenza
- Serial number e dettagli tecnici

### Esempi di Utilizzo

```javascript
// Audit sicurezza completo
const audit = await comprehensive_security_audit("example.com", "full");
console.log(`Risk Level: ${audit.audit_result.risk_level}`);

// Scan vulnerabilità approfondito
const vulnScan = await vulnerability_scanner("192.168.1.1", "deep");
console.log(`Vulnerabilities: ${vulnScan.vulnerability_report.total_vulnerabilities}`);

// Generazione password sicura
const password = await generate_secure_password(16, true, true);
console.log(`Password: ${password.password} (${password.strength})`);

// Analisi header sicurezza
const headers = await security_headers_analyzer("https://example.com");
console.log(`Security Grade: ${headers.analysis.security_grade}`);

// Crittografia dati
const encrypted = await encrypt_decrypt_data("sensitive data", "encrypt", null, "fernet");
const decrypted = await encrypt_decrypt_data(encrypted.encrypted_data, "decrypt", encrypted.key, "fernet");

// Generazione token sicuri
const tokens = await generate_secure_tokens("api", 5, JSON.stringify({prefix: "myapp"}));

// Report sicurezza completo
const scanData = JSON.stringify({
  port_scan: audit.audit_result.port_scan,
  ssl_analysis: audit.audit_result.ssl_analysis
});
const report = await generate_security_report(scanData);
```

### Security Standards & Compliance

**Password Security:**
- NIST SP 800-63B guidelines
- Minimum 12 caratteri raccomandati
- Entropy calculation algorithm
- Pattern detection avanzato

**Encryption Standards:**
- Fernet (AES 128 in CBC mode with HMAC)
- Cryptographically secure random generation
- Key derivation best practices
- Forward secrecy support

**Token Security:**
- Cryptographically secure random sources
- Industry-standard token formats
- Appropriate entropy levels
- Usage-specific recommendations

**Vulnerability Assessment:**
- OWASP Top 10 coverage
- CVE database integration potential
- Risk scoring methodology
- Severity classification standards

### Security Best Practices

**Password Management:**
- Use strong, unique passwords
- Implement 2FA/MFA where possible
- Regular password rotation policies
- Secure password storage (hashing)

**API Security:**
- Rotate API keys regularly
- Use HTTPS only
- Implement rate limiting
- Monitor API usage patterns

**Web Security:**
- Implement all security headers
- Use HTTPS everywhere
- Regular security assessments
- Keep software updated

**Network Security:**
- Minimize exposed services
- Use VPNs for sensitive access
- Implement network segmentation
- Regular port scans and monitoring

### Limitazioni e Considerazioni

**Scan Limitations:**
- Network scans may trigger security alerts
- Some checks require network access
- Rate limiting may affect deep scans
- False positives possible in automated scans

**Encryption Notes:**
- Keys must be stored securely
- Fernet requires cryptography library
- Base64 is encoding, not encryption
- Key rotation policies recommended

**Compliance Considerations:**
- Results may vary by implementation
- Professional security audit recommended
- Regular updates to threat intelligence
- Local regulations may apply

# 📜 Text Analysis Tools

Advanced tools for text analysis, information extraction, and computational linguistics.

## Main Features

- **Sentiment Analysis**: Sentiment evaluation (positive, negative, neutral)
- **Entity Extraction**: Named entity recognition (people, organizations, places)
- **Language Recognition**: Text language identification
- **Tokenization**: Text division into words, sentences, paragraphs
- **Lemmatization**: Word reduction to root form (lemma)
- **Frequency Analysis**: Counting and analysis of most frequent words
- **N-grams**: Extraction and analysis of n-grams (sequences of n words)
- **Stop Words**: Removal of common and uninformative words

## Available Tools

### `sentiment_analysis(text: string)`
Sentiment analysis of a text.

**Example:**
```json
{
  "name": "sentiment_analysis",
  "arguments": {
    "text": "The product is fantastic and exceeded my expectations!"
  }
}
```

**Output**: `{"sentiment": "positivo", "score": 0.95}`

### `entity_extraction(text: string)`
Estrazione delle entità nominate da un testo.

**Example:**
```json
{
  "name": "entity_extraction",
  "arguments": {
    "text": "Apple sta sviluppando un nuovo iPhone a San Francisco."
  }
}
```

**Output**: `{"entities": [{"type": "ORG", "value": "Apple"}, {"type": "PRODUCT", "value": "iPhone"}, {"type": "LOCATION", "value": "San Francisco"}]}`

### `language_detection(text: string)`
Riconoscimento della lingua di un testo.

**Example:**
```json
{
  "name": "language_detection",
  "arguments": {
    "text": "Ciao, come posso aiutarti oggi?"
  }
}
```

**Output**: `{"language": "Italian", "confidence": 0.98}`

### `text_tokenization(text: string, mode: string)`
Tokenizzazione del testo in parole o frasi.

**Example:**
```json
{
  "name": "text_tokenization",
  "arguments": {
    "text": "Nexus è un server MCP avanzato.",
    "mode": "word"
  }
}
```

**Output**: `["Nexus", "è", "un", "server", "MCP", "avanzato"]`

### `lemmatization(text: string)`
Lemmatizzazione del testo.

**Example:**
```json
{
  "name": "lemmatization",
  "arguments": {
    "text": "correndo corse correrò"
  }
}
```

**Output**: `["correre", "correre", "correre"]`

### `frequency_analysis(text: string)`
Analisi della frequenza delle parole nel testo.

**Example:**
```json
{
  "name": "frequency_analysis",
  "arguments": {
    "text": "ciao ciao come va va va"
  }
}
```

**Output**: `{"words": {"ciao": 2, "come": 1, "va": 3}}`

### `ngrams_extraction(text: string, n: int)`
Estrazione di n-grams dal testo.

**Example:**
```json
{
  "name": "ngrams_extraction",
  "arguments": {
    "text": "Il gatto e il topo sono amici.",
    "n": 2
  }
}
```

**Output**: `["Il gatto", "gatto e", "e il", "il topo", "topo sono", "sono amici"]`

### `stopwords_removal(text: string)`
Rimozione delle stop words dal testo.

**Example:**
```json
{
  "name": "stopwords_removal",
  "arguments": {
    "text": "Il rapido castoro marrone salta sopra il pigro cane."
  }
}
```

**Output**: `["rapido", "castoro", "marrone", "salta", "sopra", "pigro", "cane"]`

### Esempi di Utilizzo

```javascript
// Analisi del sentimento
const sentiment = await sentiment_analysis("Questo è il miglior servizio che abbia mai usato!");
console.log(`Sentiment: ${sentiment.sentiment}, Score: ${sentiment.score}`);

// Estrazione delle entità
const entities = await entity_extraction("Barack Obama è nato a Honolulu, Hawaii.");
console.log(`Entità trovate: ${JSON.stringify(entities)}`);

// Riconoscimento della lingua
const language = await language_detection("Bonjour tout le monde");
console.log(`Lingua: ${language.language}, Confidenza: ${language.confidence}`);

// Tokenizzazione
const tokens = await text_tokenization("Nexus è un server MCP avanzato.", "word");
console.log(`Token: ${tokens.join(", ")}`);

// Lemmatizzazione
const lemmas = await lemmatization("correndo corse correrò");
console.log(`Lemmi: ${lemmas.join(", ")}`);

// Analisi della frequenza
const freq = await frequency_analysis("ciao ciao come va va va");
console.log(`Frequenza parole: ${JSON.stringify(freq.words)}`);

// Estrazione di n-grams
const ngrams = await ngrams_extraction("Il gatto e il topo sono amici.", 2);
console.log(`N-grams: ${ngrams.join(", ")}`);

// Rimozione delle stop words
const noStopwords = await stopwords_removal("Il rapido castoro marrone salta sopra il pigro cane.");
console.log(`Testo senza stop words: ${noStopwords.join(" ")}`);
```

### Metriche e Analisi

**Sentiment Analysis:**
- Algoritmo basato su modelli di linguaggio pre-addestrati
- Classificazione in positivo, negativo, neutro
- Punteggio di confidenza

**Entity Recognition:**
- Modelli CRF o BERT-based per riconoscimento entità
- Classificazione entità in categorie predefinite
- Supporto per entità sovrapposte

**Language Detection:**
- Modelli n-gram e statistici per rilevamento lingua
- Supporto per più di 100 lingue
- Affidabilità > 98% per lingue comuni

**Tokenization:**
- Tokenizzazione basata su spazi bianchi e punteggiatura
- Supporto per lingue con scrittura complessa
- Opzioni di tokenizzazione personalizzabili

**Lemmatization:**
- Basata su dizionari e regole morfologiche
- Supporto per lingue con flessione complessa
- Opzioni di personalizzazione per domini specifici

**Frequency Analysis:**
- Conteggio parole e caratteri
- Analisi distribuzione frequenze
- Report dettagliato su richiesta

**N-grams Extraction:**
- Estrazione sequenziale di n parole
- Supporto per n-grams da 1 a 5
- Opzioni di filtro per frequenza e lunghezza

**Stopwords Removal:**
- Liste personalizzabili di stop words
- Supporto per lingue multiple
- Opzioni di normalizzazione testo

### Linguistica Computazionale

#### Modelli di Linguaggio
- Basati su architetture Transformer
- Addestrati su grandi corpora testuali
- Capacità di comprensione e generazione testo

#### Reti Neurali
- Reti neurali profonde per estrazione caratteristiche
- Architetture CNN e RNN per compiti specifici

#### Algoritmi di Machine Learning
- Classificazione, regressione, clustering
- Modelli supervisionati e non supervisionati
- Tecniche di ensemble e boosting

#### Elaborazione del Linguaggio Naturale (NLP)
- Tokenizzazione, stemming, lemmatizzazione
- Riconoscimento entità, analisi sentimentale
- Traduzione automatica, generazione testo

#### Statistiche e Probabilità
- Modelli basati su frequenze e probabilità
- Analisi statistica dei testi
- Modelli di Markov per sequenze

## 📝 String Tools

Strumenti avanzati per manipolazione, analisi e trasformazione di stringhe:

### Main Features

- **Case Conversion**: Trasformazione maiuscole/minuscole con formati avanzati
- **Text Analysis**: Analisi dettagliata con metriche leggibilità e linguistiche
- **Encoding/Decoding**: Supporto Base64, URL, HTML, Hex encoding
- **Format Operations**: Indentazione, allineamento, padding avanzati
- **Validation**: Validazione email, URL, telefoni, carte credito, JSON
- **String Comparison**: Algoritmi similarità, diff, Levenshtein distance
- **Batch Processing**: Operazioni multiple simultanee su stringhe
- **Text Cleaning**: Normalizzazione e pulizia testo avanzata

### Available Tools

#### `string_case_convert(text: string, case_type: string)`
Conversioni case multiple:
- Tipi: upper, lower, title, sentence, camel, snake, kebab
- Gestione caratteri speciali e spazi
- Output formattato con etichette

#### `string_stats(text: string)`
Statistiche base testo:
- Conteggio caratteri, parole, frasi, linee
- Analisi lettere, numeri, spazi, caratteri speciali
- Metriche strutturali essenziali

#### `string_clean(text: string, operation: string)`
Pulizia e normalizzazione:
- Operations: trim, normalize_spaces, remove_special, letters_only, numbers_only
- Rimozione caratteri indesiderati
- Normalizzazione spaziatura

#### `string_wrap(text: string, width?: int, break_long_words?: bool)`
Text wrapping avanzato:
- Larghezza configurabile (10-200)
- Controllo rottura parole lunghe
- Preservazione formattazione

#### `string_find_replace(text: string, find: string, replace: string, case_sensitive?: bool)`
Ricerca e sostituzione:
- Case sensitive/insensitive
- Conteggio occorrenze
- Report dettagliato modifiche

#### `string_advanced_analysis(text: string)`
Analisi approfondita testo:
- Statistiche caratteri e parole dettagliate
- Frequenza caratteri e parole più comuni
- Metriche leggibilità (Flesch Reading Ease)
- Analisi linguistica con rilevamento script Unicode
- Stima tempo lettura
- Informazioni encoding e Unicode

#### `string_encoding_operations(text: string, operation: string, encoding?: string)`
Encoding/Decoding completo:
- Base64: encode/decode con encoding personalizzabile
- URL: encode/decode per sicurezza web
- HTML: escape/unescape entità HTML
- Hex: conversione esadecimale bidirezionale
- Supporto encoding multipli (UTF-8, ASCII, etc.)

#### `string_format_operations(text: string, operation: string, options?: string)`
Formattazione avanzata:
- **Indent/Dedent**: Controllo indentazione con caratteri personalizzabili
- **Alignment**: Center, ljust, rjust con riempimento custom
- **Padding**: Padding laterale configurabile
- **Truncate**: Troncamento con suffisso personalizzabile
- **Zero Fill**: Riempimento zeri per numeri
- Opzioni JSON per controllo fine

#### `string_validation(text: string, validation_type: string, options?: string)`
Validazione formati specializzata:
- **Email**: Pattern RFC-compliant
- **URL**: HTTP/HTTPS con parametri
- **Phone**: Formati internazionali (E.164, Italia, USA)
- **Credit Card**: Algoritmo Luhn per validazione
- **UUID**: Versioni 1-5 con analisi versione
- **IP Address**: IPv4/IPv6 con rilevamento versione
- **JSON**: Parsing con analisi struttura
- Report dettagliato errori e metadati

#### `string_comparison(text1: string, text2: string, comparison_type?: string)`
Confronto stringhe avanzato:
- **Similarity**: Ratio similarità con SequenceMatcher
- **Levenshtein**: Distanza edit con normalizzazione
- **Diff**: Unified diff con conteggio modifiche
- **Common Substrings**: Sottostringhe comuni con lunghezza minima
- Percentuali similarità e metriche dettagliate

#### `string_batch_operations(operations_json: string)`
Processing batch multiplo:
- Fino a 100 operazioni simultanee
- Supporto: case_convert, clean, stats, encoding, validation
- Statistiche successo/fallimento aggregate
- Report esecuzione dettagliato

### Esempi di Utilizzo

```javascript
// Analisi completa testo
const analysis = await string_advanced_analysis("Il gatto camminava sul tetto.");
console.log(`Leggibilità: ${analysis.analysis.readability.level}`);
console.log(`Tempo lettura: ${analysis.analysis.readability.estimated_reading_time_minutes} min`);

// Encoding multiplo
const base64 = await string_encoding_operations("Hello World!", "base64_encode");
const url = await string_encoding_operations("hello world!", "url_encode");

// Validazione dati
const email = await string_validation("user@example.com", "email");
const phone = await string_validation("+39 123 456 7890", "phone");
const json = await string_validation('{"name": "test"}', "json");

// Formattazione avanzata
const centered = await string_format_operations("Title", "center", 
  JSON.stringify({width: 20, fill_char: "="}));
const indented = await string_format_operations("Code\nBlock", "indent",
  JSON.stringify({size: 4, char: " "}));

// Confronto stringhe
const similarity = await string_comparison("hello world", "hallo world", "similarity");
const diff = await string_comparison("version 1", "version 2", "diff");

// Batch processing
const batchOps = JSON.stringify([
  {type: "case_convert", text: "Hello World", options: {case_type: "snake"}},
  {type: "validation", text: "test@example.com", options: {validation_type: "email"}},
  {type: "encoding", text: "encode me", options: {operation: "base64_encode"}}
]);
const batchResult = await string_batch_operations(batchOps);
```

### Metriche e Analisi

**Readability Scoring:**
- Algoritmo basato su Flesch Reading Ease
- Considerazione lunghezza frasi e sillabe
- Livelli: Molto Facile → Molto Difficile
- Stima tempo lettura (200 WPM)

**Language Detection:**
- Analisi script Unicode
- Rilevamento parole comuni (italiano, inglese, spagnolo)
- Categorizzazione caratteri Unicode
- Compatibilità ASCII e encoding

**String Similarity:**
- SequenceMatcher ratio (0-1)
- Levenshtein distance con normalizzazione
- Common substring analysis
- Diff unified format

**Validation Accuracy:**
- Email: Pattern RFC-compliant
- Credit Card: Algoritmo Luhn checksum
- Phone: Pattern internazionali multipli
- UUID: Validazione versione e formato
- IP: IPv4/IPv6 pattern matching