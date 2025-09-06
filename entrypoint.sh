#!/bin/bash
# Nexus MCP Server - Docker Entrypoint Script
set -e

# Se non ci sono argomenti, avvia il server MCP
if [ $# -eq 0 ]; then
    echo "🚀 Avvio server MCP Nexus..."
    exec python multi_server.py
else
    # Altrimenti esegui il comando fornito
    exec "$@"
fi