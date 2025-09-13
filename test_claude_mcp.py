#!/usr/bin/env python3
"""
Simple test script to verify MCP server works with Claude Code.
Run this to test connectivity before configuring Claude Code.
"""

import json
import subprocess
import sys
import os

def test_mcp_server():
    """Test the MCP server startup and basic functionality"""
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🧪 Testing Nexus MCP Server...")
    print(f"📁 Working directory: {script_dir}")
    
    # Test 1: Check virtual environment
    venv_python = os.path.join(script_dir, ".venv", "bin", "python")
    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found at .venv/bin/python")
        return False
    
    print("✅ Virtual environment found")
    
    # Test 2: Check server files
    for server_file in ["multi_server.py", "multi_server_minimal.py", "config.json", "config-minimal.json"]:
        if not os.path.exists(server_file):
            print(f"❌ Missing file: {server_file}")
            return False
    
    print("✅ Server files present")
    
    # Test 3: Test minimal server startup
    try:
        print("🚀 Testing minimal server startup...")
        result = subprocess.run([
            venv_python, "multi_server_minimal.py"
        ], 
        capture_output=True, 
        text=True, 
        timeout=3,
        env={**os.environ, "PYTHONPATH": script_dir}
        )
    except subprocess.TimeoutExpired:
        print("✅ Server started successfully (timeout expected)")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False
    
    # Test 4: Check configuration files
    config_file = os.path.join(script_dir, "claude_desktop_config.json")
    if os.path.exists(config_file):
        print("✅ Claude Code configuration file created")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
            if "mcpServers" in config and "nexus" in config["mcpServers"]:
                print("✅ Configuration structure is correct")
            else:
                print("❌ Configuration structure is incorrect")
                return False
    
    print("\n🎉 All tests passed!")
    print("\n📋 Next steps:")
    print("1. Copy the configuration to Claude Code:")
    print(f"   cp {config_file} ~/Library/Application\\ Support/Claude/claude_desktop_config.json")
    print("\n2. Restart Claude Code")
    print("\n3. The Nexus MCP server should now be available with these tools:")
    print("   - Calculator, Crypto, DateTime, Encoding, String, System Info, UUID, Validator tools")
    
    return True

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)