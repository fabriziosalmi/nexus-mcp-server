#!/bin/bash
# Wrapper script to start Nexus MCP Server with correct working directory

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Start the server with the virtual environment Python
exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/multi_server.py"