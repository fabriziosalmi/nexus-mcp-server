# Nexus MCP Server - Claude Code Configuration

This file configures Nexus MCP Server for use with Claude Code.

## Server Configuration

```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["multi_server.py"],
      "env": {
        "PYTHONPATH": ".",
        "MCP_SERVER_NAME": "NexusServer",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Available Tools

For a complete list of all available tools and their documentation, see [TOOLS.md](TOOLS.md).

The Nexus MCP server provides 120+ tools across 17 categories including mathematical operations, cryptographic tools, encoding/decoding, validation, system information, code analysis, Docker management, and more.

## Docker Integration

Use Docker for isolated, secure execution:

```bash
docker build -t nexus-mcp-server .
docker run --rm -i nexus-mcp-server
```

Or with docker-compose:

```bash
docker-compose up nexus-mcp
```