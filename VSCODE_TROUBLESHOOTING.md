# VS Code MCP Integration Troubleshooting Guide

## ✅ Status Check

Your Nexus MCP Server is **working correctly**! The server starts and loads tools successfully.

## 🔍 VS Code MCP Requirements

1. **Install VS Code MCP Extension**:
   - Go to VS Code Extensions
   - Search for "Model Context Protocol" or "MCP" 
   - Install the official MCP extension

2. **Verify Extension is Active**:
   - Check VS Code status bar for MCP indicators
   - Open Command Palette (`Cmd+Shift+P`) and search for "MCP"

## 🛠️ Current Configuration

Your `.vscode/settings.json` is configured with:
- **Server Name**: `nexus-mcp-local`
- **Command**: Uses workspace Python interpreter 
- **Args**: `["multi_server.py", "--config", "config-minimal-vscode.json"]`
- **Tools**: 10 stable tools (calculator, crypto, datetime, etc.)

## 🧪 Test Commands

### 1. Manual Server Test
```bash
cd /Users/fab/GitHub/nexus/nexus-mcp-server
source .venv/bin/activate
python multi_server.py --config config-minimal-vscode.json
```
Expected: Server starts and shows "Server Nexus pronto e configurato"

### 2. VS Code Integration Test
1. Open VS Code in this workspace
2. Open Command Palette (`Cmd+Shift+P`)
3. Search for "MCP: Restart Servers" and run it
4. Check for MCP status in the status bar

### 3. Check VS Code Output
1. Open Output panel (`Cmd+Shift+U`)
2. Select "Model Context Protocol" from dropdown
3. Look for connection messages

## 🔧 Troubleshooting Steps

### Step 1: Restart VS Code MCP
```
Cmd+Shift+P → "MCP: Restart Servers"
```

### Step 2: Check Python Interpreter
```
Cmd+Shift+P → "Python: Select Interpreter"
```
Should show: `/Users/fab/GitHub/nexus/nexus-mcp-server/.venv/bin/python`

### Step 3: Verify File Paths
Ensure these files exist:
- ✅ `multi_server.py`
- ✅ `config-minimal-vscode.json` 
- ✅ `.venv/bin/python`

### Step 4: Check VS Code Logs
1. Open `Help → Toggle Developer Tools`
2. Go to Console tab
3. Look for MCP-related errors

## 🎯 Expected VS Code Behavior

When working correctly, you should see:
- MCP status indicator in status bar
- Available tools in Command Palette
- Tool execution capabilities in chat/assistant

## 📋 Quick Fix Commands

```bash
# Reload VS Code window
Cmd+Shift+P → "Developer: Reload Window"

# Reset MCP configuration  
Cmd+Shift+P → "MCP: Reset All Servers"

# Check MCP server status
Cmd+Shift+P → "MCP: Show Server Status"
```

## 🚨 If Still Not Working

1. **Check VS Code version**: Ensure you have latest VS Code
2. **Check MCP extension version**: Update to latest
3. **Try absolute paths** in settings.json instead of variables
4. **Check permissions**: Ensure Python executable has proper permissions

## 📞 Next Steps

If VS Code MCP still shows errors:
1. Share the exact error message from VS Code Output → Model Context Protocol
2. Verify MCP extension is properly installed and enabled
3. Try restarting VS Code completely