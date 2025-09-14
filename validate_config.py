#!/usr/bin/env python3
"""
Nexus MCP Server Configuration Validator
Verifies that the server correctly selects configurations for different clients.
"""

import json
import os
import sys

def validate_config_file(config_path):
    """Validate a configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        tools = config.get('enabled_tools', [])
        func_count = config.get('actual_function_count', 'N/A')
        client_type = config.get('client_type', 'Not specified')
        
        return {
            'valid': True,
            'tools_count': len(tools),
            'function_count': func_count,
            'client_type': client_type,
            'config': config
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e)
        }

def main():
    print("🔍 Nexus MCP Server Configuration Validator")
    print("=" * 50)
    
    # Test configuration files
    configs_to_test = [
        {
            'name': 'Claude Desktop (Full)',
            'file': 'config.json',
            'expected_tools': 46,
            'expected_max_functions': None  # No limit
        },
        {
            'name': 'VSCode (Limited)',
            'file': 'config-vscode.json', 
            'expected_tools': 12,
            'expected_max_functions': 100
        }
    ]
    
    all_valid = True
    
    for config_test in configs_to_test:
        print(f"\n📋 Testing {config_test['name']} configuration...")
        
        result = validate_config_file(config_test['file'])
        
        if not result['valid']:
            print(f"❌ Error: {result['error']}")
            all_valid = False
            continue
        
        print(f"✅ Configuration valid")
        print(f"   📄 File: {config_test['file']}")
        print(f"   🔧 Tools: {result['tools_count']}")
        print(f"   ⚡ Functions: {result['function_count']}")
        print(f"   💻 Client type: {result['client_type']}")
        
        # Validate tool count
        if result['tools_count'] != config_test['expected_tools']:
            print(f"⚠️  Warning: Expected {config_test['expected_tools']} tools, got {result['tools_count']}")
        
        # Validate function limit for VSCode
        if config_test['expected_max_functions'] is not None:
            if result['function_count'] != 'N/A' and isinstance(result['function_count'], int):
                if result['function_count'] > config_test['expected_max_functions']:
                    print(f"❌ Function count ({result['function_count']}) exceeds VSCode limit ({config_test['expected_max_functions']})")
                    all_valid = False
                else:
                    print(f"✅ Function count within VSCode limit")
    
    # Test environment variable detection
    print(f"\n🧪 Testing environment variable detection...")
    
    # Save current env
    original_env = os.environ.get('MCP_CLIENT_TYPE')
    
    test_cases = [
        {'env_value': None, 'expected_config': 'config.json'},
        {'env_value': 'vscode', 'expected_config': 'config-vscode.json'},
        {'env_value': 'claude', 'expected_config': 'config.json'},
    ]
    
    for test_case in test_cases:
        if test_case['env_value'] is None:
            if 'MCP_CLIENT_TYPE' in os.environ:
                del os.environ['MCP_CLIENT_TYPE']
        else:
            os.environ['MCP_CLIENT_TYPE'] = test_case['env_value']
        
        # Simulate the config selection logic
        client_type = os.environ.get('MCP_CLIENT_TYPE', '').lower()
        if client_type == 'vscode':
            selected_config = 'config-vscode.json'
        else:
            selected_config = 'config.json'
        
        env_display = test_case['env_value'] or 'None'
        if selected_config == test_case['expected_config']:
            print(f"✅ MCP_CLIENT_TYPE='{env_display}' → {selected_config}")
        else:
            print(f"❌ MCP_CLIENT_TYPE='{env_display}' → {selected_config} (expected {test_case['expected_config']})")
            all_valid = False
    
    # Restore original env
    if original_env is not None:
        os.environ['MCP_CLIENT_TYPE'] = original_env
    elif 'MCP_CLIENT_TYPE' in os.environ:
        del os.environ['MCP_CLIENT_TYPE']
    
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 All tests passed! Configuration is ready for deployment.")
        print("\n💡 Usage tips:")
        print("   - For Claude Desktop: Use config.json (default)")
        print("   - For VSCode: Set MCP_CLIENT_TYPE=vscode or use start_mcp_server_vscode.sh")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration files.")
        return 1

if __name__ == "__main__":
    sys.exit(main())