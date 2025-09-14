#!/bin/bash
# VSCode-specific startup script for Nexus MCP Server
# This script sets the client type environment variable to ensure VSCode gets the limited tool configuration

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Set environment variable to indicate VSCode client
export MCP_CLIENT_TYPE=vscode

# Start the server with the virtual environment Python
exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/multi_server.py"