# Nexus MCP Server - Available Tools

The Nexus MCP server provides the following tool categories:

## 🧮 Mathematical Operations
- `add(a, b)` - Addition
- `multiply(a, b)` - Multiplication

## 🔐 Cryptographic Tools
- `generate_hash(text, algorithm)` - Generate hash (SHA256, SHA1, MD5, SHA512)
- `generate_hmac(message, secret_key, algorithm)` - Generate HMAC
- `generate_random_token(length, encoding)` - Generate secure tokens

## 🔤 Encoding/Decoding
- `base64_encode(text)` / `base64_decode(encoded_text)` - Base64 operations
- `url_encode(text)` / `url_decode(encoded_text)` - URL encoding
- `html_escape(text)` - HTML character escaping
- `json_format(json_string, indent)` - JSON formatting and validation

## 📅 Date/Time Operations
- `current_timestamp()` - Get current timestamp in various formats
- `unix_to_date(timestamp)` - Convert Unix timestamp to readable date
- `date_to_unix(date_string)` - Convert date to Unix timestamp
- `date_math(start_date, operation, amount, unit)` - Date arithmetic

## 🆔 ID Generation
- `generate_uuid4()` / `generate_uuid1()` - Generate UUIDs
- `generate_multiple_uuids(count, version)` - Generate multiple UUIDs
- `generate_short_id(length, use_uppercase)` - Generate short IDs
- `generate_nanoid(length, alphabet)` - Generate Nano IDs
- `uuid_info(uuid_string)` - Analyze UUID information

## 📝 String Manipulation
- `string_case_convert(text, case_type)` - Convert case (camel, snake, kebab, etc.)
- `string_stats(text)` - Get detailed string statistics
- `string_clean(text, operation)` - Clean and normalize strings
- `string_wrap(text, width, break_long_words)` - Text wrapping
- `string_find_replace(text, find, replace, case_sensitive)` - Find and replace

## ✅ Data Validation
- `validate_email(email)` - Validate email addresses
- `validate_url(url)` - Validate and analyze URLs
- `validate_ip_address(ip)` - Validate IP addresses (IPv4/IPv6)
- `validate_phone(phone, country_code)` - Validate phone numbers
- `validate_credit_card(card_number)` - Validate credit cards (Luhn algorithm)

## 💻 System Information
- `system_overview()` - Get system overview
- `memory_usage()` - Get memory usage information
- `cpu_info()` - Get CPU information and usage
- `disk_usage(path)` - Get disk usage for path
- `network_info()` - Get network interfaces information
- `running_processes(limit)` - Get top processes by CPU usage

## 📁 Secure File Access
- `read_safe_file(filename)` - Read files from secure sandbox directory

## 🌐 Web Content Fetching
- `fetch_url_content(url)` - Fetch content from URLs

## 🔍 Code Analysis & Quality
- `analyze_python_syntax(code)` - Analyze Python syntax and metrics
- `check_code_style(code, language)` - Check code style and provide suggestions
- `detect_code_patterns(code)` - Detect patterns and anti-patterns in code
- `estimate_code_complexity(code)` - Estimate code complexity using various metrics

## 🐳 Docker Management
- `check_docker_status()` - Check Docker installation and daemon status
- `list_docker_containers(status)` - List Docker containers with filtering
- `list_docker_images()` - List available Docker images
- `validate_dockerfile(dockerfile_content)` - Validate and analyze Dockerfile
- `generate_docker_compose(services)` - Generate docker-compose.yml files
- `docker_security_scan(image_name)` - Basic security scan of Docker images

## 📋 Git Repository Tools
- `analyze_git_repository(repo_path)` - Analyze Git repository statistics
- `git_diff_analysis(file_path, staged)` - Analyze Git diffs and changes
- `git_commit_history(limit, author)` - Analyze commit history
- `git_branch_analysis()` - Analyze Git branches and sync status
- `generate_gitignore(language, additional_patterns)` - Generate .gitignore files

## ⚙️ Process Management
- `list_processes_by_criteria(criteria, limit)` - List and filter system processes
- `monitor_process(pid, duration)` - Monitor specific process performance
- `execute_with_limits(command, timeout, memory_limit_mb)` - Execute commands with resource limits
- `analyze_system_resources()` - Analyze system resource usage
- `kill_process_safe(pid, force)` - Safely terminate processes
- `create_sandbox_environment()` - Create isolated execution environments

## 🚀 Code Generation
- `generate_python_class(class_name, attributes, methods)` - Generate Python classes
- `generate_api_endpoints(resource_name, operations, framework)` - Generate REST API endpoints
- `generate_dockerfile_template(base_image, language, port)` - Generate Dockerfile templates
- `generate_test_template(test_type, class_name, methods, framework)` - Generate test code
- `generate_config_file(config_type, application_name, environment)` - Generate configuration files

## 🗄️ Database Tools
- `create_sqlite_database(database_name, tables)` - Create SQLite databases with schema
- `validate_sql_query(query, database_type)` - Validate and analyze SQL queries
- `generate_database_schema(schema_name, entities, relationships)` - Generate database schemas
- `execute_safe_query(database_path, query, max_rows)` - Execute safe SELECT queries
- `analyze_database_structure(database_path)` - Analyze database structure and health

## 🌍 Environment Management
- `manage_environment_variables(action, variables, variable_name)` - Manage environment variables
- `create_environment_file(env_type, variables, file_path)` - Create environment configuration files
- `analyze_system_environment()` - Analyze system environment and configuration
- `backup_restore_environment(action, backup_path, variables)` - Backup/restore environment settings
- `validate_configuration_file(file_path, config_type)` - Validate configuration files

## 💾 Backup & Archive Tools
- `create_archive(source_path, archive_type, include_patterns, exclude_patterns)` - Create file archives
- `extract_archive(archive_path, destination_path, verify_integrity)` - Extract archives safely
- `create_backup_manifest(backup_path, source_paths, metadata)` - Create backup manifests
- `verify_backup_integrity(manifest_path, backup_base_path)` - Verify backup integrity
- `compress_files(file_paths, compression_level, algorithm)` - Compress individual files

## 📊 Log Analysis
- `parse_log_file(file_path, log_format, max_lines)` - Parse and analyze log files
- `analyze_log_patterns(log_data, pattern_type)` - Analyze specific patterns in logs
- `generate_log_report(log_data, report_type)` - Generate comprehensive log reports
- `filter_log_entries(log_data, filters)` - Filter log entries by criteria
- `export_log_analysis(analysis_data, export_format, file_path)` - Export analysis results

## 🚀 Code Execution (Sandboxed)
- `execute_python_code(code, timeout, memory_limit_mb)` - Execute Python code safely
- `validate_python_syntax(code, strict_mode)` - Validate Python syntax without execution
- `execute_shell_command(command, working_directory, timeout)` - Execute shell commands safely
- `create_python_sandbox(sandbox_id, allowed_modules)` - Create isolated Python environments
- `execute_code_in_sandbox(sandbox_id, code, language)` - Execute code in existing sandbox
- `analyze_code_performance(code, language, iterations)` - Analyze code performance metrics

## 🔄 Workflow Orchestration
- `analyze_repository(url, analysis_depth)` - **META-TOOL**: Complete repository analysis workflow
  - Chains multiple tools: clone → complexity analysis → security scan → structure analysis → archive → cleanup
  - Analysis depths: "quick", "standard", "deep"
  - Reduces LLM conversation rounds from 6+ individual tool calls to 1
  - Provides comprehensive reporting with workflow tracking and error handling
  - Automatic resource cleanup and temporary directory management

## Security Features

- **Sandbox File Access**: File operations restricted to `safe_files/` directory
- **Path Traversal Protection**: Prevents access outside sandbox
- **Input Validation**: All parameters are validated
- **Secure Token Generation**: Cryptographically secure random generation
- **Timeout Protection**: Network requests have timeouts
- **Resource Limits**: Container resource limits when using Docker

## Workflow Orchestration (NEW)

The new workflow system enables **advanced tool chaining** and **meta-tool orchestration**:

### Key Benefits
- **Reduced Complexity**: Single tool call replaces multiple individual operations
- **Rich Results**: Comprehensive analysis with aggregated reporting
- **Error Resilience**: Graceful failure handling with detailed error reporting
- **Resource Management**: Automatic cleanup prevents disk space issues
- **Flexible Analysis**: Configurable depth levels for different use cases

### Example Workflow
```python
# Instead of 6+ separate tool calls:
# 1. clone_repository(url)
# 2. analyze_code_complexity(path)
# 3. detect_secrets(path)
# 4. analyze_structure(path)
# 5. create_archive(path)
# 6. cleanup_directory(path)

# Now just one meta-tool call:
analyze_repository("https://github.com/user/repo.git", "standard")
```

### Workflow Output Structure
```json
{
  "workflow_id": "repo_analysis_20250907_094500",
  "repository_url": "https://github.com/example/repo.git",
  "final_status": "completed",
  "steps_completed": ["repository_clone", "code_complexity", "secret_detection", "structure_analysis", "cleanup"],
  "summary": {
    "code_analysis": {"files_analyzed": 25, "total_lines": 1500, "languages_detected": 3},
    "security_analysis": {"secrets_found": 0, "risk_level": "LOW"}
  },
  "duration_seconds": 2.45
}
```