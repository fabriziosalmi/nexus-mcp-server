# Dynamic One-Time Tools

## Overview

The Nexus MCP Server now supports **Dynamic One-Time Tools** - the most advanced feature that allows LLMs to create custom tools on-the-fly for specific tasks that don't have existing solutions.

## The `create_and_run_tool` Function

### Function Signature
```python
create_and_run_tool(python_code: str, timeout: int = 60, memory_limit_mb: int = 128) -> Dict[str, Any]
```

### Parameters
- `python_code`: The Python code for the custom tool to create and execute
- `timeout`: Execution timeout in seconds (10-300, default: 60)
- `memory_limit_mb`: Memory limit in MB (32-512, default: 128)

### Security Features

The implementation includes multiple layers of security:

1. **Code Security Validation**: Checks for dangerous patterns before execution
2. **Docker Isolation**: Complete environment isolation using Docker containers
3. **Resource Limits**: CPU, memory, and time restrictions
4. **Network Isolation**: No network access during execution
5. **Filesystem Restrictions**: Read-only filesystem with limited temp space
6. **Non-root Execution**: Runs as unprivileged user

### Execution Modes

#### 1. Docker Mode (Recommended)
- **Maximum Security**: Complete isolation in Docker container
- **Resource Limits**: Memory (32-512MB), CPU (0.5 cores), Network (none)
- **Filesystem**: Read-only with limited /tmp access
- **User**: Non-root execution (nexus:1000)

#### 2. Fallback Mode
- **Local Execution**: When Docker is unavailable
- **Restricted Environment**: Limited builtins and imports
- **Resource Limits**: Memory and CPU limits via system calls
- **Security**: Code validation and import restrictions

### Example Usage

#### Example 1: Custom Date Converter
```python
# Dynamic tool for converting proprietary date format
code = """
from datetime import datetime

# Convert custom format YYYYMMDD-HHMMSS to ISO
custom_date = "20250907-143022"
date_part, time_part = custom_date.split('-')

year = int(date_part[:4])
month = int(date_part[4:6])
day = int(date_part[6:8])
hour = int(time_part[:2])
minute = int(time_part[2:4])
second = int(time_part[4:6])

dt = datetime(year, month, day, hour, minute, second)
print(f"ISO format: {dt.isoformat()}")
print(f"Readable: {dt.strftime('%B %d, %Y at %I:%M:%S %p')}")
"""

result = create_and_run_tool(code, timeout=30, memory_limit_mb=64)
```

#### Example 2: Data Format Converter
```python
# Convert legacy data format to JSON
code = """
# Parse legacy format: NAME|AGE|CITY|SALARY
legacy_data = '''
JOHN|25|NYC|50000
JANE|30|LA|75000
BOB|35|CHI|60000
'''

records = []
for line in legacy_data.strip().split('\\n'):
    if line.strip():
        name, age, city, salary = line.split('|')
        records.append({
            'name': name,
            'age': int(age),
            'city': city,
            'salary': int(salary),
            'tax_bracket': '20%' if int(salary) < 60000 else '25%'
        })

import json
print(json.dumps(records, indent=2))
"""

result = create_and_run_tool(code)
```

#### Example 3: Mathematical Calculator
```python
# Custom mathematical computations
code = """
import math

def calculate_compound_interest(principal, rate, time, n=12):
    return principal * (1 + rate/n)**(n*time)

# Calculate loan scenarios
scenarios = [
    {'principal': 100000, 'rate': 0.05, 'time': 30},
    {'principal': 100000, 'rate': 0.04, 'time': 30},
    {'principal': 100000, 'rate': 0.06, 'time': 20}
]

for i, scenario in enumerate(scenarios, 1):
    result = calculate_compound_interest(**scenario)
    print(f"Scenario {i}: ${result:,.2f}")
"""

result = create_and_run_tool(code, timeout=45)
```

### Response Format

```json
{
  "success": true,
  "tool_id": "abc12345",
  "execution_mode": "docker_isolated", // or "local_fallback"
  "timeout_seconds": 60,
  "memory_limit_mb": 128,
  "security_check": {
    "safe": true,
    "violations": []
  },
  "docker_image": "nexus-dynamic-tool-abc12345",
  "container_name": "nexus-dynamic-tool-abc12345",
  "container_execution_time_seconds": 1.234,
  "container_return_code": 0,
  "container_stderr": "",
  "tool_result": {
    "success": true,
    "tool_id": "abc12345",
    "execution_time_seconds": 0.123,
    "stdout": "Tool output here...",
    "stderr": "",
    "message": "Dynamic tool executed successfully"
  }
}
```

### Security Restrictions

#### Blocked Operations
- File system access (`open`, `file`, etc.)
- System commands (`os.system`, `subprocess`)
- Network operations (`socket`, `urllib`, `requests`)
- Process manipulation (`os.kill`, `signal`)
- Dangerous imports (`os`, `sys`, `subprocess`, etc.)
- Code execution (`eval`, `exec`)
- Module inspection (`globals`, `locals`, `vars`)

#### Allowed Modules
- `math`, `random`, `datetime`, `json`, `re`, `string`
- `collections`, `itertools`, `functools`, `operator`
- `decimal`, `fractions`, `statistics`, `uuid`, `hashlib`
- `base64`, `binascii`, `calendar`, `time`

### Use Cases

1. **Data Format Conversion**: Convert between proprietary formats
2. **Mathematical Computations**: Complex calculations not covered by existing tools
3. **Text Processing**: Custom parsing and analysis
4. **Data Validation**: Custom validation rules
5. **Algorithm Implementation**: Specific algorithms for unique problems
6. **Report Generation**: Custom formatted outputs
7. **Long-tail Problems**: Any specific task not covered by existing tools

### Performance Characteristics

- **Docker Startup**: ~2-5 seconds for container creation
- **Execution**: Typically < 1 second for simple tools
- **Memory Usage**: As configured (32-512MB limit)
- **Cleanup**: Automatic image and container removal

### Best Practices

1. **Keep Tools Simple**: Focus on single, specific tasks
2. **Avoid Heavy Computation**: Use timeouts appropriately
3. **Validate Input Data**: Include input validation in your code
4. **Handle Errors Gracefully**: Use try-catch blocks
5. **Minimize Dependencies**: Use only allowed modules
6. **Test Iteratively**: Start with simple versions

### Error Handling

Common error scenarios and solutions:

- **Security Violations**: Code contains dangerous patterns
- **Import Errors**: Module not in allowed list
- **Timeout Errors**: Execution exceeds time limit
- **Memory Errors**: Exceeds memory allocation
- **Syntax Errors**: Invalid Python syntax

### Workflow Integration

This feature enables the following workflow:

1. **LLM Identifies Gap**: Determines no existing tool can solve the problem
2. **Code Generation**: LLM writes Python code for the specific task
3. **Dynamic Execution**: `create_and_run_tool` executes the code safely
4. **Result Integration**: Output is returned for further processing

This represents the pinnacle of agentic capabilities, allowing true on-demand tool creation for any computational task within security constraints.