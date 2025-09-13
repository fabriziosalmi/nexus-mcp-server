#!/bin/bash
# start_https_server.sh - Start Nexus MCP Server with HTTPS support via Caddy

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Nexus MCP Server with HTTPS support${NC}"
echo "================================================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv .venv${NC}"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    if [ ! -z "$MCP_PID" ]; then
        kill $MCP_PID 2>/dev/null
        echo -e "${GREEN}✅ MCP Server stopped${NC}"
    fi
    if [ ! -z "$CADDY_PID" ]; then
        kill $CADDY_PID 2>/dev/null
        echo -e "${GREEN}✅ Caddy server stopped${NC}"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start MCP server in background
echo -e "${YELLOW}📡 Starting MCP Server on localhost:3001...${NC}"
./.venv/bin/python tcp_server.py --port 3001 &
MCP_PID=$!

# Wait a moment for MCP server to start
sleep 2

# Check if MCP server started successfully
if ! kill -0 $MCP_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start MCP Server${NC}"
    exit 1
fi

echo -e "${GREEN}✅ MCP Server started (PID: $MCP_PID)${NC}"

# Start Caddy with HTTPS
echo -e "${YELLOW}🔒 Starting Caddy HTTPS proxy on localhost:443...${NC}"
caddy run --config Caddyfile &
CADDY_PID=$!

# Wait a moment for Caddy to start
sleep 3

# Check if Caddy started successfully
if ! kill -0 $CADDY_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start Caddy server${NC}"
    kill $MCP_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ Caddy HTTPS proxy started (PID: $CADDY_PID)${NC}"
echo "================================================================"
echo -e "${GREEN}🎉 Servers are running!${NC}"
echo ""
echo -e "${YELLOW}📋 Access URLs:${NC}"
echo "  • HTTP MCP Server:  http://localhost:3001"
echo "  • HTTPS via Caddy:  https://localhost"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo "  • Caddy logs: /tmp/caddy-nexus-mcp.log"
echo ""
echo -e "${RED}Press Ctrl+C to stop all servers${NC}"

# Wait for background processes
wait $MCP_PID $CADDY_PID