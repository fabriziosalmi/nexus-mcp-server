#!/usr/bin/env python3
"""
Example demonstrating language-agnostic access to Nexus MCP tools via REST API.
This script showcases how to use Nexus tools from any language that can make HTTP requests.
"""

import requests
import json
import time

# Base URL for the Nexus API
BASE_URL = "http://localhost:9999"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def call_tool(tool_name, arguments=None):
    """Call a Nexus tool via REST API."""
    if arguments is None:
        arguments = {}
    
    url = f"{BASE_URL}/tools/{tool_name}/execute"
    payload = {"arguments": arguments}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    """Demonstrate various Nexus tools via REST API."""
    
    print_section("Nexus MCP Server - Language-Agnostic API Demo")
    
    # Check server health
    print("Checking server health...")
    health = requests.get(f"{BASE_URL}/").json()
    print(f"✅ Server is {health['status']} with {health['tools_count']} tools available")
    
    print_section("Mathematical Operations")
    
    # Addition
    result = call_tool("add", {"a": 42, "b": 58})
    if "result" in result:
        print(f"42 + 58 = {result['result']['result']}")
    
    # Multiplication  
    result = call_tool("multiply", {"a": 7, "b": 9})
    if "result" in result:
        print(f"7 × 9 = {result['result']['result']}")
    
    print_section("Cryptographic Operations")
    
    # Generate hash
    result = call_tool("generate_hash", {"text": "Hello Nexus API!", "algorithm": "sha256"})
    if "result" in result:
        print(f"SHA256 hash: {result['result']['result']}")
    
    # Generate secure token
    result = call_tool("generate_random_token", {"length": 16, "encoding": "hex"})
    if "result" in result:
        print(f"Random token: {result['result']['result']}")
    
    print_section("Encoding/Decoding")
    
    # Base64 encoding
    message = "This is a test message"
    result = call_tool("base64_encode", {"text": message})
    if "result" in result:
        encoded = result['result']['result'].split(": ")[1]  # Extract the encoded part
        print(f"Original: {message}")
        print(f"Base64: {encoded}")
        
        # Base64 decoding
        result = call_tool("base64_decode", {"encoded_text": encoded})
        if "result" in result:
            decoded = result['result']['result'].split(": ")[1]  # Extract the decoded part
            print(f"Decoded: {decoded}")
    
    print_section("UUID Generation")
    
    # Generate different types of UUIDs
    result = call_tool("generate_uuid4")
    if "result" in result:
        print(f"UUID4: {result['result']['result']}")
    
    result = call_tool("generate_short_id", {"length": 8, "use_uppercase": True})
    if "result" in result:
        print(f"Short ID: {result['result']['result']}")
    
    print_section("Data Validation")
    
    # Email validation
    emails = ["valid@example.com", "invalid-email", "test@nexus.dev"]
    for email in emails:
        result = call_tool("validate_email", {"email": email})
        if "result" in result:
            status = "✅ VALID" if "✅ SI" in result['result']['result'] else "❌ INVALID"
            print(f"{email}: {status}")
    
    # URL validation
    urls = ["https://github.com", "invalid-url", "http://nexus.local"]
    for url in urls:
        result = call_tool("validate_url", {"url": url})
        if "result" in result:
            status = "✅ VALID" if "✅ VALIDA" in result['result']['result'] else "❌ INVALID"
            print(f"{url}: {status}")
    
    print_section("System Information")
    
    # Get current timestamp
    result = call_tool("current_timestamp")
    if "result" in result:
        print("Current timestamp:")
        print(result['result']['result'])
    
    # Get system overview
    result = call_tool("system_overview")
    if "result" in result:
        print("\nSystem Overview:")
        print(result['result']['result'][:200] + "...")  # First 200 chars
    
    print_section("Available Tools Discovery")
    
    # List all available tools
    tools_response = requests.get(f"{BASE_URL}/tools")
    if tools_response.status_code == 200:
        tools_data = tools_response.json()
        print(f"Total tools available: {tools_data['count']}")
        print("\nTool categories found:")
        
        categories = {}
        for tool in tools_data['tools']:
            # Categorize by common prefixes
            if tool['name'].startswith('generate_'):
                categories.setdefault('Generation', []).append(tool['name'])
            elif tool['name'].startswith('validate_'):
                categories.setdefault('Validation', []).append(tool['name'])
            elif tool['name'] in ['add', 'multiply']:
                categories.setdefault('Math', []).append(tool['name'])
            elif 'base64' in tool['name'] or 'url_' in tool['name'] or 'html' in tool['name']:
                categories.setdefault('Encoding', []).append(tool['name'])
            elif 'system' in tool['name'] or 'cpu' in tool['name'] or 'memory' in tool['name']:
                categories.setdefault('System', []).append(tool['name'])
            else:
                categories.setdefault('Other', []).append(tool['name'])
        
        for category, tool_names in categories.items():
            print(f"  {category}: {len(tool_names)} tools")
    
    print_section("Performance Information")
    
    # Measure execution time for a few operations
    operations = [
        ("add", {"a": 1, "b": 1}),
        ("generate_uuid4", {}),
        ("current_timestamp", {}),
        ("base64_encode", {"text": "performance test"})
    ]
    
    for tool_name, args in operations:
        start_time = time.time()
        result = call_tool(tool_name, args)
        end_time = time.time()
        
        if "result" in result:
            server_time = result.get('execution_time', 0)
            total_time = end_time - start_time
            print(f"{tool_name}: {server_time:.4f}s (server) / {total_time:.4f}s (total)")
    
    print(f"\n{'='*50}")
    print("🎉 Demo completed successfully!")
    print("This demonstrates how Nexus tools can be accessed from ANY programming language")
    print("that can make HTTP requests - Python, JavaScript, Go, Rust, Java, C#, etc.")
    print(f"{'='*50}")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Nexus server.")
        print("Make sure the server is running on http://localhost:9999")
        print("Start it with: python http_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")