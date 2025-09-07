# Nexus MCP Server API Examples

This directory contains examples demonstrating how to use the Nexus MCP Server from different programming languages via the REST API.

## Prerequisites

Make sure the Nexus HTTP server is running:

```bash
cd /path/to/nexus-mcp-server
python http_server.py
```

The server will be available at `http://localhost:9999`

## Examples

### Python Example (`api_demo.py`)

Comprehensive demonstration of Nexus tools from Python:

```bash
python examples/api_demo.py
```

**Features demonstrated:**
- Mathematical operations (add, multiply)
- Cryptographic functions (hashing, token generation)
- Encoding/decoding (Base64, URL encoding)
- UUID generation
- Data validation (email, URL)
- System information
- Tool discovery
- Performance measurement

### JavaScript/Node.js Example (`api_demo.js`)

Shows the same functionality from JavaScript:

```bash
node examples/api_demo.js
```

**Key points:**
- Uses only Node.js built-in modules (no external dependencies)
- Demonstrates HTTP client implementation
- Shows async/await patterns
- Language-agnostic approach

## Creating Your Own Integration

### Basic Pattern

```javascript
// 1. List available tools
GET http://localhost:9999/tools

// 2. Get tool information
GET http://localhost:9999/tools/{tool_name}

// 3. Execute a tool
POST http://localhost:9999/tools/{tool_name}/execute
Content-Type: application/json

{
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### Response Format

```json
{
  "tool_name": "add",
  "arguments": {"a": 5, "b": 3},
  "result": {"result": 8.0},
  "status": "success",
  "execution_time": 0.0001
}
```

## Language-Specific Examples

### Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

func callNexusTool(tool string, args map[string]interface{}) {
    data := map[string]interface{}{"arguments": args}
    jsonData, _ := json.Marshal(data)
    
    resp, err := http.Post(
        fmt.Sprintf("http://localhost:9999/tools/%s/execute", tool),
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    // Handle response...
}
```

### Rust

```rust
use reqwest;
use serde_json::{json, Value};

async fn call_nexus_tool(tool: &str, args: Value) -> Result<Value, reqwest::Error> {
    let client = reqwest::Client::new();
    let url = format!("http://localhost:9999/tools/{}/execute", tool);
    let payload = json!({"arguments": args});
    
    let response = client.post(&url)
        .json(&payload)
        .send()
        .await?;
    
    response.json().await
}
```

### cURL/Bash

```bash
#!/bin/bash

# Add two numbers
curl -s -X POST http://localhost:9999/tools/add/execute \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"a": 10, "b": 20}}' \
  | jq '.result.result'

# Generate UUID
curl -s http://localhost:9999/tools/generate_uuid4/execute \
  | jq -r '.result.result'

# Hash a string
curl -s -X POST http://localhost:9999/tools/generate_hash/execute \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"text": "Hello", "algorithm": "sha256"}}' \
  | jq -r '.result.result'
```

### PowerShell

```powershell
# PowerShell example
function Invoke-NexusTool {
    param(
        [string]$ToolName,
        [hashtable]$Arguments = @{}
    )
    
    $body = @{ arguments = $Arguments } | ConvertTo-Json
    $uri = "http://localhost:9999/tools/$ToolName/execute"
    
    Invoke-RestMethod -Uri $uri -Method POST -Body $body -ContentType "application/json"
}

# Usage
Invoke-NexusTool -ToolName "add" -Arguments @{ a = 15; b = 25 }
```

## Advanced Usage

### Error Handling

```python
import requests

def safe_call_tool(tool_name, args):
    try:
        response = requests.post(f"http://localhost:9999/tools/{tool_name}/execute", 
                               json={"arguments": args})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to Nexus server")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

### Batch Operations

```python
def batch_operations():
    operations = [
        ("add", {"a": 1, "b": 2}),
        ("multiply", {"a": 3, "b": 4}),
        ("generate_uuid4", {}),
        ("current_timestamp", {})
    ]
    
    results = []
    for tool_name, args in operations:
        result = call_tool(tool_name, args)
        results.append(result)
    
    return results
```

### Async Operations (JavaScript)

```javascript
async function parallelOperations() {
    const operations = [
        callTool('generate_uuid4'),
        callTool('current_timestamp'),
        callTool('add', {a: 10, b: 20}),
        callTool('system_overview')
    ];
    
    const results = await Promise.all(operations);
    return results;
}
```

## Benefits

1. **Language Independence**: Use any language that can make HTTP requests
2. **No Dependencies**: No need to install MCP libraries or Python dependencies
3. **Scalability**: HTTP APIs can be load balanced and cached
4. **Integration**: Easy to integrate into existing microservices
5. **Testing**: Standard HTTP testing tools work out of the box
6. **Documentation**: Self-documenting with OpenAPI/Swagger at `/docs`

## Next Steps

- Visit `http://localhost:9999/docs` for interactive API documentation
- Explore all available tools at `http://localhost:9999/tools`
- Check the main documentation in `ENHANCED_API.md`
- Try the monitoring endpoint at `http://localhost:9999/metrics`