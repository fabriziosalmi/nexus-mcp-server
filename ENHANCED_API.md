# Enhanced HTTP API Documentation

## Overview

The Nexus MCP Server now features an **Enhanced REST API** that dynamically exposes ALL available tools without requiring manual configuration. This enables language-agnostic access to Nexus functionality from any programming language that can make HTTP requests.

## Key Features

### 🔄 Dynamic Tool Discovery
- **Automatic detection**: All tools are automatically discovered from enabled modules
- **Zero configuration**: No need to manually map tools or modify individual tool files
- **Hot reload**: Adding new tool modules to config.json makes them immediately available
- **Metadata extraction**: Tool descriptions and schemas are automatically extracted

### 🌐 Language-Agnostic Access
- **REST API**: Standard HTTP/JSON interface
- **Any language**: Use from Python, JavaScript, Go, Rust, Java, C#, etc.
- **Simple integration**: Standard HTTP libraries work out of the box
- **No MCP dependency**: Clients don't need MCP protocol knowledge

### 📚 Comprehensive Documentation
- **OpenAPI/Swagger**: Interactive documentation at `/docs`
- **ReDoc**: Alternative docs at `/redoc`
- **Tool metadata**: Each tool exposes description and input schema
- **Error handling**: Detailed error responses with debugging information

## API Endpoints

### Health & Discovery

#### `GET /`
Health check endpoint
```json
{
  "status": "healthy",
  "message": "Nexus MCP Server Enhanced API is running",
  "tools_count": 39,
  "server_info": {
    "name": "NexusServer-Enhanced",
    "version": "3.0.0",
    "type": "HTTP-MCP Bridge"
  }
}
```

#### `GET /tools`
List all available tools with metadata
```json
{
  "tools": [
    {
      "name": "add",
      "description": "Calcola la somma di due numeri (a + b)...",
      "input_schema": {}
    }
  ],
  "count": 39,
  "server_info": {...}
}
```

#### `GET /tools/{tool_name}`
Get detailed information about a specific tool
```json
{
  "name": "add",
  "description": "Calcola la somma di due numeri (a + b)...",
  "input_schema": {}
}
```

### Tool Execution

#### `POST /tools/{tool_name}/execute`
Execute a specific tool with arguments
```bash
curl -X POST http://localhost:9999/tools/add/execute \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"a": 15, "b": 27}}'
```

Response:
```json
{
  "tool_name": "add",
  "arguments": {"a": 15, "b": 27},
  "result": {"result": 42.0},
  "status": "success",
  "execution_time": 0.0002
}
```

#### `GET /tools/{tool_name}/execute`
Execute a tool without arguments (convenience endpoint)
```bash
curl http://localhost:9999/tools/current_timestamp/execute
```

### Legacy Compatibility

#### `POST /execute`
Legacy endpoint for backward compatibility
```bash
curl -X POST http://localhost:9999/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "multiply", "arguments": {"a": 7, "b": 6}}'
```

### Monitoring

#### `GET /metrics`
Prometheus metrics for monitoring and observability
```
# HELP nexus_tool_calls_total Total number of tool calls
# TYPE nexus_tool_calls_total counter
nexus_tool_calls_total{tool="add",status="success"} 15
```

## Usage Examples

### Python
```python
import requests

# List available tools
response = requests.get("http://localhost:9999/tools")
tools = response.json()
print(f"Available tools: {tools['count']}")

# Execute a tool
response = requests.post("http://localhost:9999/tools/add/execute", 
                        json={"arguments": {"a": 10, "b": 20}})
result = response.json()
print(f"Result: {result['result']}")
```

### JavaScript/Node.js
```javascript
const fetch = require('node-fetch');

async function callTool(toolName, args) {
    const response = await fetch(`http://localhost:9999/tools/${toolName}/execute`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({arguments: args})
    });
    return await response.json();
}

// Usage
callTool('generate_uuid4', {}).then(result => {
    console.log('UUID:', result.result);
});
```

### Go
```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type ToolRequest struct {
    Arguments map[string]interface{} `json:"arguments"`
}

func callTool(toolName string, args map[string]interface{}) {
    reqBody := ToolRequest{Arguments: args}
    jsonData, _ := json.Marshal(reqBody)
    
    resp, err := http.Post(
        fmt.Sprintf("http://localhost:9999/tools/%s/execute", toolName),
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    fmt.Printf("Result: %v\n", result["result"])
}
```

### cURL/Bash
```bash
#!/bin/bash

# Get server health
curl -s http://localhost:9999/ | jq '.tools_count'

# Hash a string
curl -s -X POST http://localhost:9999/tools/generate_hash/execute \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"text": "Hello World", "algorithm": "sha256"}}' \
  | jq -r '.result.result'

# Validate an email
curl -s -X POST http://localhost:9999/tools/validate_email/execute \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"email": "test@example.com"}}' \
  | jq -r '.result.result'
```

## Configuration

The API automatically discovers tools based on the `config.json` file:

```json
{
  "comment": "Control panel for Nexus MCP Server tools",
  "enabled_tools": [
    "calculator",
    "crypto_tools", 
    "system_info",
    "encoding_tools",
    "datetime_tools",
    "uuid_tools",
    "validator_tools"
  ]
}
```

Adding or removing tools from this list automatically updates the available API endpoints without code changes.

## Error Handling

The API provides detailed error responses:

```json
{
  "error": "HTTP 404",
  "detail": "Tool 'nonexistent' not found. Available tools: ['add', 'multiply', ...]"
}
```

Common error scenarios:
- **404**: Tool not found
- **400**: Invalid arguments
- **500**: Tool execution error
- **503**: Server not initialized

## Performance & Monitoring

- **Execution timing**: Each response includes execution time
- **Prometheus metrics**: Built-in metrics for monitoring
- **Structured logging**: Detailed logs for debugging
- **Health checks**: Regular health endpoint monitoring

## Migration from Previous Version

The enhanced API is fully backward compatible:

### Old Format (still supported)
```bash
curl -X POST http://localhost:9999/execute \
  -d '{"tool_name": "add", "arguments": {"a": 5, "b": 3}}'
```

### New Format (recommended)
```bash
curl -X POST http://localhost:9999/tools/add/execute \
  -d '{"arguments": {"a": 5, "b": 3}}'
```

## Benefits

1. **No tool file modifications**: The enhancement is implemented "a monte" (upstream)
2. **Language independence**: Use Nexus from any programming language  
3. **Automatic scaling**: New tools are immediately API-accessible
4. **Production ready**: Comprehensive error handling and monitoring
5. **Standards compliant**: OpenAPI documentation and REST principles
6. **Developer friendly**: Interactive documentation and examples

This enhancement transforms Nexus from a Python/MCP-specific tool into a universal, language-agnostic service that can be integrated into any technology stack.