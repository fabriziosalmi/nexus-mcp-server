# 📋 Nexus MCP Server - Complete Tools Reference

This document provides comprehensive documentation for all available tools in the Nexus MCP Server, including detailed function descriptions, parameters, examples, and usage patterns.

## 📖 Quick Navigation

- [📊 Tools Overview](#-tools-overview)
- [📋 Complete Tools Table](#-complete-tools-table)
- [🧮 Mathematical Tools](#-mathematical-tools)
- [🔒 Security & Cryptography](#-security--cryptography)
- [💻 Development Tools](#-development-tools)
- [📁 File Operations](#-file-operations)
- [🖥️ System Tools](#️-system-tools)
- [🌐 Network Tools](#-network-tools)
- [📝 Data Processing](#-data-processing)
- [🔤 String Operations](#-string-operations)
- [🚀 Advanced Features](#-advanced-features)

## 📊 Tools Overview

🛠️ **Available Tools**: **120+**
⚙️ **Total Functions**: **500+**
🏗️ **Categories**: **17**

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

## 🧮 Mathematical Tools

### 🔧 Calculator (`calculator.py`)

### 🔧 Calculator (`calculator.py`)

Complete mathematical calculation system with advanced functions, number theory, statistics, and secure expression evaluation.

#### Main Features
- **Basic Operations**: Fundamental arithmetic with security controls
- **Advanced Functions**: Trigonometry, logarithms, roots, powers
- **Number Theory**: GCD, LCM, factorization, prime numbers
- **Statistics**: Mean, median, standard deviation, variance
- **Unit Conversions**: Length, weight, temperature, volume, time
- **Financial Calculations**: Simple and compound interest
- **Expression Evaluation**: Secure parser for complex expressions
- **Mathematical Constants**: Access to important constants

#### Available Functions

##### Basic Operations
- **`add(a, b)`** - Addition of two numbers
- **`subtract(a, b)`** - Subtraction with detailed results
- **`multiply(a, b)`** - Multiplication with overflow protection
- **`divide(a, b)`** - Division with remainder and validation

##### Advanced Operations
- **`power(base, exponent)`** - Power calculation with overflow protection
- **`square_root(number)`** - Square root calculation
- **`nth_root(number, n)`** - N-th root with support for odd roots of negative numbers
- **`factorial(n)`** - Factorial calculation with limits

##### Trigonometric Functions
- **`trigonometric_functions(angle, unit, functions)`** - Sin, cos, tan, cot, sec, csc
  - **Units**: `radians`, `degrees`
  - **Functions**: `sin`, `cos`, `tan`, `cot`, `sec`, `csc`

##### Statistics
- **`statistics_functions(numbers, operation)`** - Statistical calculations
  - **Operations**: `mean`, `median`, `mode`, `stdev`, `variance`, `range`, `all`

##### Unit Conversions
- **`unit_converter(value, from_unit, to_unit, unit_type)`**
  - **Length**: meter, kilometer, centimeter, foot, yard, mile
  - **Weight**: kilogram, gram, pound, ounce, ton
  - **Temperature**: celsius, fahrenheit, kelvin
  - **Volume**: liter, milliliter, gallon, quart, pint
  - **Time**: second, minute, hour, day, week, year

##### Expression Evaluation
- **`expression_evaluator(expression, variables)`** - Secure expression parsing
  - **Functions**: Arithmetic, trigonometric, logarithmic
  - **Constants**: pi, e, golden ratio
  - **Security**: Whitelist of allowed functions, injection prevention

#### Usage Examples

```bash
# Basic arithmetic
python client.py add '{"a": 42, "b": 8}'
python client.py divide '{"a": 15, "b": 4}'

# Advanced calculations
python client.py power '{"base": 2, "exponent": 10}'
python client.py trigonometric_functions '{"angle": 45, "unit": "degrees", "functions": ["sin", "cos", "tan"]}'

# Statistics
python client.py statistics_functions '{"numbers": [1, 2, 3, 4, 5], "operation": "all"}'

# Unit conversion
python client.py unit_converter '{"value": 100, "from_unit": "meter", "to_unit": "foot", "unit_type": "length"}'

# Expression evaluation
python client.py expression_evaluator '{"expression": "2 * pi * r", "variables": {"r": 5}}'
```

### 📊 Unit Converter (`unit_converter.py`)

Comprehensive unit conversion system supporting multiple measurement types.

#### Available Functions
- **`convert_length(value, from_unit, to_unit)`** - Length conversions
- **`convert_temperature(value, from_unit, to_unit)`** - Temperature conversions
- **`convert_weight(value, from_unit, to_unit)`** - Weight/mass conversions
- **`convert_volume(value, from_unit, to_unit)`** - Volume conversions
- **`convert_time(value, from_unit, to_unit)`** - Time conversions
- **`list_available_units()`** - List all supported units by category

#### Usage Examples

```bash
# Length conversion
python client.py convert_length '{"value": 100, "from_unit": "cm", "to_unit": "m"}'

# Temperature conversion
python client.py convert_temperature '{"value": 100, "from_unit": "C", "to_unit": "F"}'

# Weight conversion
python client.py convert_weight '{"value": 1000, "from_unit": "g", "to_unit": "kg"}'

# List available units
python client.py list_available_units '{}'
```

## 🔒 Security & Cryptography

### 🔐 Security Tools (`security_tools.py`)

Advanced tools for security, audit, and protection with comprehensive vulnerability scanning and encryption capabilities.

#### Main Features
- **Password Security**: Generation and strength analysis
- **Cryptography**: Encryption/decryption with secure algorithms
- **Token Generation**: Secure tokens for various uses
- **Vulnerability Scanning**: Automated security assessment
- **Security Audit**: Complete security evaluation
- **SSL/TLS Analysis**: Certificate and configuration checking
- **Security Headers**: HTTP security header analysis
- **Security Reporting**: Detailed security reports

#### Available Functions

##### Password & Token Security
- **`generate_secure_password(length, include_symbols, exclude_ambiguous)`** - Secure password generation
- **`password_strength_check(password)`** - Password strength analysis
- **`generate_api_key(length, format_type)`** - API key generation
- **`generate_secure_tokens(token_type, count, options)`** - Specialized token generation

##### Cryptography
- **`encrypt_decrypt_data(data, operation, key, algorithm)`** - Data encryption/decryption
- **`hash_file_content(content, algorithms)`** - File integrity hashing
- **`jwt_decode_header(jwt_token)`** - JWT token analysis

##### Security Assessment
- **`comprehensive_security_audit(target, scan_type)`** - Complete security audit
- **`vulnerability_scanner(target, scan_depth)`** - Advanced vulnerability scanning
- **`security_headers_analyzer(url)`** - HTTP security headers analysis
- **`ssl_certificate_check(domain, port)`** - SSL/TLS certificate validation

##### Network Security
- **`check_common_ports(host)`** - Port scanning for security assessment
- **`generate_security_report(data)`** - Comprehensive security reporting

#### Usage Examples

```bash
# Password generation and analysis
python client.py generate_secure_password '{"length": 16, "include_symbols": true}'
python client.py password_strength_check '{"password": "MyPassword123!"}'

# Cryptography
python client.py encrypt_decrypt_data '{"data": "sensitive data", "operation": "encrypt", "algorithm": "fernet"}'
python client.py hash_file_content '{"content": "file content", "algorithms": ["sha256", "md5"]}'

# Security scanning
python client.py comprehensive_security_audit '{"target": "example.com", "scan_type": "full"}'
python client.py vulnerability_scanner '{"target": "192.168.1.1", "scan_depth": "deep"}'

# SSL/TLS analysis
python client.py ssl_certificate_check '{"domain": "example.com", "port": 443}'
python client.py security_headers_analyzer '{"url": "https://example.com"}'
```

### 🔑 Crypto Tools (`crypto_tools.py`)

Cryptographic functions and hashing utilities for secure operations.

#### Available Functions
- **`generate_hash(text, algorithm)`** - Hash generation (MD5, SHA1, SHA256, SHA512)
- **`generate_random_token(length, encoding)`** - Cryptographically secure tokens
- **`encode_base64(text)`** / **`decode_base64(text)`** - Base64 encoding/decoding
- **`generate_uuid(version)`** - UUID generation (versions 1-5)
- **`password_hash(password, algorithm)`** - Password hashing with salt
- **`verify_password(password, hash)`** - Password verification
- **`encrypt_text(text, password)`** / **`decrypt_text(encrypted, password)`** - Text encryption
- **`generate_keypair()`** - RSA key pair generation
- **`sign_data(data, private_key)`** / **`verify_signature(data, signature, public_key)`** - Digital signatures

#### Usage Examples

```bash
# Hash generation
python client.py generate_hash '{"text": "Hello World", "algorithm": "sha256"}'

# Token generation
python client.py generate_random_token '{"length": 32, "encoding": "hex"}'

# Password operations
python client.py password_hash '{"password": "mypassword", "algorithm": "bcrypt"}'

# Encryption
python client.py encrypt_text '{"text": "secret message", "password": "encryption_key"}'
```

## 🚀 Advanced Features

### 🛠️ Dynamic Tool Creation (`code_execution_tools.py`)

The most advanced feature that allows LLMs to create custom tools on-the-fly for specific tasks.

#### `create_and_run_tool` Function

**Function Signature:**
```python
create_and_run_tool(python_code: str, timeout: int = 60, memory_limit_mb: int = 128) -> Dict[str, Any]
```

**Parameters:**
- `python_code`: The Python code for the custom tool
- `timeout`: Execution timeout in seconds (10-300, default: 60)
- `memory_limit_mb`: Memory limit in MB (32-512, default: 128)

#### Security Features
1. **Code Security Validation**: Checks for dangerous patterns before execution
2. **Docker Isolation**: Complete environment isolation using Docker containers
3. **Resource Limits**: CPU, memory, and time restrictions
4. **Network Isolation**: No network access during execution
5. **Filesystem Restrictions**: Read-only filesystem with limited temp space
6. **Non-root Execution**: Runs as unprivileged user

#### Use Cases
1. **Data Format Conversion**: Convert proprietary or legacy formats
2. **Mathematical Computations**: Complex calculations not covered by existing tools
3. **Text Processing**: Custom parsing and analysis
4. **Algorithm Implementation**: Specific algorithms for unique problems
5. **Long-tail Problems**: Any computational task not covered by existing tools

#### Usage Examples

```bash
# Custom date converter
python client.py create_and_run_tool '{
  "python_code": "from datetime import datetime\ncustom_date = \"20250907-143022\"\ndate_part, time_part = custom_date.split(\"-\")\ndt = datetime(int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8]), int(time_part[:2]), int(time_part[2:4]), int(time_part[4:6]))\nprint(f\"ISO: {dt.isoformat()}\")",
  "timeout": 30,
  "memory_limit_mb": 64
}'

# Data format converter
python client.py create_and_run_tool '{
  "python_code": "legacy_data = \"JOHN|25|NYC|50000\\nJANE|30|LA|75000\"\nrecords = []\nfor line in legacy_data.strip().split(\"\\n\"):\n    if line.strip():\n        name, age, city, salary = line.split(\"|\")\n        records.append({\"name\": name, \"age\": int(age), \"city\": city, \"salary\": int(salary)})\nimport json\nprint(json.dumps(records, indent=2))",
  "timeout": 45
}'
```
---

**Nexus MCP Server** - Your comprehensive toolkit for LLM integration with 500+ functions across 120+ tools. From simple calculations to complex code generation, security scanning, and dynamic tool creation - everything you need in one powerful, secure package.