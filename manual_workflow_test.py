#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# manual_workflow_test.py - Manual test of the analyze_repository workflow

import json
import tempfile
import os
import sys

# Add the current directory to the Python path to import our modules
sys.path.insert(0, '/home/runner/work/nexus-mcp-server/nexus-mcp-server')

def manual_test_workflow():
    """Manually test the workflow by calling the functions directly."""
    
    print("🧪 Manual Workflow Test")
    print("======================")
    
    # Create a mock MCP instance
    class MockMCP:
        def tool(self):
            def decorator(func):
                return func
            return decorator
    
    # Import and register our workflow
    import tools.workflows
    mock_mcp = MockMCP()
    
    # Since the functions are defined inside register_tools, 
    # we need to capture them during registration
    captured_tools = {}
    
    original_tool = mock_mcp.tool
    def capturing_tool():
        def decorator(func):
            captured_tools[func.__name__] = func
            return func
        return decorator
    
    mock_mcp.tool = capturing_tool
    tools.workflows.register_tools(mock_mcp)
    
    # Now we have access to the analyze_repository function
    analyze_repository = captured_tools.get('analyze_repository')
    
    if not analyze_repository:
        print("❌ Failed to capture analyze_repository function")
        return False
    
    print("✅ Successfully captured workflow function")
    
    # Test with a simple, small repository (Hello World from GitHub)
    test_url = "https://github.com/octocat/Hello-World.git"
    
    print(f"🔍 Testing workflow with repository: {test_url}")
    print("   This may take a moment as it clones and analyzes the repository...")
    
    try:
        # Call our workflow function
        result = analyze_repository(test_url, "quick")
        
        print("\n📊 Workflow Results:")
        print(f"   Workflow ID: {result.get('workflow_id', 'N/A')}")
        print(f"   Repository URL: {result.get('repository_url', 'N/A')}")
        print(f"   Final Status: {result.get('final_status', 'N/A')}")
        print(f"   Duration: {result.get('duration_seconds', 'N/A')} seconds")
        
        steps_completed = result.get('steps_completed', [])
        steps_failed = result.get('steps_failed', [])
        
        print(f"   Steps Completed: {len(steps_completed)} - {', '.join(steps_completed)}")
        if steps_failed:
            print(f"   Steps Failed: {len(steps_failed)} - {', '.join(steps_failed)}")
        
        # Show summary if available
        summary = result.get('summary', {})
        if summary:
            print("\n📈 Summary:")
            if 'code_analysis' in summary:
                ca = summary['code_analysis']
                print(f"   Files Analyzed: {ca.get('files_analyzed', 0)}")
                print(f"   Total Lines: {ca.get('total_lines', 0)}")
                print(f"   Languages: {ca.get('languages_detected', 0)}")
            
            if 'security_analysis' in summary:
                sa = summary['security_analysis']
                print(f"   Security Scan - Files: {sa.get('files_scanned', 0)}")
                print(f"   Security Scan - Secrets Found: {sa.get('secrets_found', 0)}")
                print(f"   Security Risk Level: {sa.get('risk_level', 'UNKNOWN')}")
        
        # Show detailed reports (abbreviated)
        reports = result.get('reports', {})
        if reports:
            print("\n📋 Detailed Reports:")
            
            if 'clone_info' in reports:
                clone = reports['clone_info']
                print(f"   Clone - Success: {clone.get('success', False)}")
                print(f"   Clone - Files: {clone.get('file_count', 0)}")
                print(f"   Clone - Branch: {clone.get('current_branch', 'N/A')}")
            
            if 'complexity_analysis' in reports:
                comp = reports['complexity_analysis']
                languages = comp.get('languages', {})
                print(f"   Code Analysis - Languages: {list(languages.keys())}")
                for lang, info in languages.items():
                    print(f"     {lang}: {info.get('files', 0)} files, {info.get('lines', 0)} lines")
            
            if 'repository_structure' in reports:
                struct = reports['repository_structure']
                print(f"   Structure - Total Files: {struct.get('total_files', 0)}")
                print(f"   Structure - Total Directories: {struct.get('total_directories', 0)}")
                common_files = struct.get('has_common_files', {})
                found_files = [name for name, exists in common_files.items() if exists]
                if found_files:
                    print(f"   Common Files Found: {', '.join(found_files)}")
        
        if result.get('final_status') == 'completed':
            print("\n✅ Workflow completed successfully!")
            return True
        else:
            print(f"\n⚠️ Workflow ended with status: {result.get('final_status')}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            return False
            
    except Exception as e:
        print(f"\n❌ Workflow test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = manual_test_workflow()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Manual workflow test {'passed' if success else 'failed'}")
    sys.exit(0 if success else 1)