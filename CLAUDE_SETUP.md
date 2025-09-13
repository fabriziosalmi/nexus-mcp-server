# Nexus MCP Server - Claude Code Setup Guide

## Quick Setup

1. **Install the configuration:**
   ```bash
   cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Restart Claude Code**

3. **Verify it's working** - You should see the Nexus MCP server with 47 tool categories available.

## Alternative: Minimal Configuration (for testing)

If you want to test with fewer tools first:

```bash
cp claude_desktop_config_minimal.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

This provides 8 essential tools: Calculator, Crypto, DateTime, Encoding, String, System Info, UUID, and Validator tools.

## Troubleshooting

### Check if server starts manually:
```bash
# Test full server
./start_mcp_server.sh

# Test minimal server  
./start_mcp_server_minimal.sh
```

### Common Issues:

1. **"Module not found" errors**: Make sure the virtual environment is activated
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **"Config file not found"**: The wrapper scripts ensure correct working directory

3. **Permission denied**: Make sure scripts are executable
   ```bash
   chmod +x start_mcp_server.sh start_mcp_server_minimal.sh
   ```

### Logs

Claude Code logs can be found in the application. Look for `[nexus]` entries to see server status.

## Configuration Details

The current configuration uses wrapper scripts that:
- Set the correct working directory
- Use the virtual environment Python
- Handle all path dependencies automatically

This eliminates the working directory issues that were causing the original "config.json not found" error.