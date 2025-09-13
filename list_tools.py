#!/usr/bin/env python3
"""
List all available tools from the MCP server
"""
import json
import subprocess
import sys

def list_mcp_tools():
    """List all available tools from the MCP server"""
    
    cmd = [
        '/Users/fab/GitHub/nexus/nexus-mcp-server/.venv/bin/python',
        'multi_server.py'
    ]
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd='/Users/fab/GitHub/nexus/nexus-mcp-server'
    )
    
    try:
        # Initialize first
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        init_response = process.stdout.readline()
        
        # List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + '\n')
        process.stdin.flush()
        
        tools_response = process.stdout.readline()
        print(f"Tools response: {tools_response.strip()}")
        
        if tools_response:
            response_data = json.loads(tools_response)
            if "result" in response_data and "tools" in response_data["result"]:
                tools = response_data["result"]["tools"]
                print(f"\n✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
                return True
            else:
                print("❌ No tools found in response")
                return False
        else:
            print("❌ No response for tools list")
            return False
            
    except Exception as e:
        print(f"❌ Error listing tools: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("Listing MCP Tools...")
    list_mcp_tools()
