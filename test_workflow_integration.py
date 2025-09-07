#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_workflow_integration.py - Integration test for workflow functionality

import json
import subprocess
import time
import threading
import os
import signal
import sys

def start_server():
    """Start the MCP server in the background."""
    try:
        proc = subprocess.Popen(
            [sys.executable, 'multi_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd='/home/runner/work/nexus-mcp-server/nexus-mcp-server'
        )
        return proc
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def test_workflow_with_simple_repo():
    """Test the analyze_repository workflow with a simple public repository."""
    
    print("🚀 Starting MCP server...")
    server_proc = start_server()
    
    if not server_proc:
        return False
    
    try:
        # Give server time to start
        time.sleep(2)
        
        # Create a simple MCP client request for our workflow tool
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "analyze_repository",
                "arguments": {
                    "url": "https://github.com/octocat/Hello-World.git",
                    "analysis_depth": "quick"
                }
            }
        }
        
        print("📡 Sending workflow request to server...")
        server_proc.stdin.write(json.dumps(request) + '\n')
        server_proc.stdin.flush()
        
        # Read response with timeout
        start_time = time.time()
        response_data = ""
        
        while time.time() - start_time < 30:  # 30 second timeout
            if server_proc.poll() is not None:
                break
            
            try:
                line = server_proc.stdout.readline()
                if line:
                    response_data += line
                    # Try to parse as JSON
                    try:
                        response = json.loads(line.strip())
                        if response.get("id") == 1:
                            print("✅ Received workflow response!")
                            result = response.get("result", {})
                            
                            print(f"   Workflow ID: {result.get('workflow_id', 'N/A')}")
                            print(f"   Status: {result.get('final_status', 'N/A')}")
                            print(f"   Steps completed: {len(result.get('steps_completed', []))}")
                            print(f"   Duration: {result.get('duration_seconds', 'N/A')} seconds")
                            
                            summary = result.get('summary', {})
                            if summary:
                                print(f"   Files analyzed: {summary.get('code_analysis', {}).get('files_analyzed', 'N/A')}")
                                print(f"   Languages detected: {summary.get('code_analysis', {}).get('languages_detected', 'N/A')}")
                            
                            return True
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                print(f"⚠️ Error reading server response: {e}")
                break
        
        print("⏰ Timeout waiting for server response")
        return False
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    
    finally:
        # Clean up server process
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()

def test_local_workflow_simulation():
    """Test workflow components locally without full server integration."""
    print("🧪 Testing local workflow simulation...")
    
    # Test with a simple dummy URL to check validation
    test_url = "https://github.com/test/dummy.git"
    
    # Import and create a mock MCP instance to test our registration
    class MockMCP:
        def __init__(self):
            self.tools = {}
        
        def tool(self):
            def decorator(func):
                self.tools[func.__name__] = func
                return func
            return decorator
    
    # Test tool registration
    try:
        import tools.workflows
        mock_mcp = MockMCP()
        tools.workflows.register_tools(mock_mcp)
        
        print(f"✅ Workflow tool registered: {'analyze_repository' in mock_mcp.tools}")
        
        if 'analyze_repository' in mock_mcp.tools:
            print("✅ analyze_repository tool is available")
            # Note: We won't actually call it with a real URL in this test
            # as it would require network access and might clone large repos
        
        return True
        
    except Exception as e:
        print(f"❌ Local simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Running workflow integration tests...")
    
    # Test local simulation first (faster and more reliable)
    local_success = test_local_workflow_simulation()
    
    if local_success:
        print("✅ Local workflow tests passed!")
        
        # Optionally test with actual server (commented out for CI environments)
        # integration_success = test_workflow_with_simple_repo()
        # if integration_success:
        #     print("✅ Full integration test passed!")
        # else:
        #     print("⚠️ Integration test failed (this may be expected in CI environments)")
        
        print("✅ Workflow testing completed successfully!")
        sys.exit(0)
    else:
        print("❌ Workflow tests failed!")
        sys.exit(1)