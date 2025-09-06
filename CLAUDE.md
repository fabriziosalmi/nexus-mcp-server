# Nexus MCP Server - Claude Code Configuration

This file configures Nexus MCP Server for use with Claude Code.

## Server Configuration

```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["multi_server.py"],
      "env": {
        "PYTHONPATH": ".",
        "MCP_SERVER_NAME": "NexusServer",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Available Tools

The Nexus MCP server provides the following tool categories:

### 🧮 Mathematical Operations
- `add(a, b)` - Addition
- `multiply(a, b)` - Multiplication

### 🔐 Cryptographic Tools  
- `generate_hash(text, algorithm)` - Generate hash (SHA256, SHA1, MD5, SHA512)
- `generate_hmac(message, secret_key, algorithm)` - Generate HMAC
- `generate_random_token(length, encoding)` - Generate secure tokens

### 🔤 Encoding/Decoding
- `base64_encode(text)` / `base64_decode(encoded_text)` - Base64 operations
- `url_encode(text)` / `url_decode(encoded_text)` - URL encoding
- `html_escape(text)` - HTML character escaping
- `json_format(json_string, indent)` - JSON formatting and validation

### 📅 Date/Time Operations
- `current_timestamp()` - Get current timestamp in various formats
- `unix_to_date(timestamp)` - Convert Unix timestamp to readable date
- `date_to_unix(date_string)` - Convert date to Unix timestamp
- `date_math(start_date, operation, amount, unit)` - Date arithmetic

### 🆔 ID Generation
- `generate_uuid4()` / `generate_uuid1()` - Generate UUIDs
- `generate_multiple_uuids(count, version)` - Generate multiple UUIDs
- `generate_short_id(length, use_uppercase)` - Generate short IDs
- `generate_nanoid(length, alphabet)` - Generate Nano IDs
- `uuid_info(uuid_string)` - Analyze UUID information

### 📝 String Manipulation
- `string_case_convert(text, case_type)` - Convert case (camel, snake, kebab, etc.)
- `string_stats(text)` - Get detailed string statistics
- `string_clean(text, operation)` - Clean and normalize strings
- `string_wrap(text, width, break_long_words)` - Text wrapping
- `string_find_replace(text, find, replace, case_sensitive)` - Find and replace

### ✅ Data Validation
- `validate_email(email)` - Validate email addresses
- `validate_url(url)` - Validate and analyze URLs
- `validate_ip_address(ip)` - Validate IP addresses (IPv4/IPv6)
- `validate_phone(phone, country_code)` - Validate phone numbers
- `validate_credit_card(card_number)` - Validate credit cards (Luhn algorithm)

### 💻 System Information
- `system_overview()` - Get system overview
- `memory_usage()` - Get memory usage information
- `cpu_info()` - Get CPU information and usage
- `disk_usage(path)` - Get disk usage for path
- `network_info()` - Get network interfaces information
- `running_processes(limit)` - Get top processes by CPU usage

### 📁 Secure File Access
- `read_safe_file(filename)` - Read files from secure sandbox directory

### 🌐 Web Content Fetching
- `fetch_url_content(url)` - Fetch content from URLs

## Security Features

- **Sandbox File Access**: File operations restricted to `safe_files/` directory
- **Path Traversal Protection**: Prevents access outside sandbox
- **Input Validation**: All parameters are validated
- **Secure Token Generation**: Cryptographically secure random generation
- **Timeout Protection**: Network requests have timeouts
- **Resource Limits**: Container resource limits when using Docker

## Docker Integration

Use Docker for isolated, secure execution:

```bash
docker build -t nexus-mcp-server .
docker run --rm -i nexus-mcp-server
```

Or with docker-compose:

```bash
docker-compose up nexus-mcp
```