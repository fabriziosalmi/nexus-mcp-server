# -*- coding: utf-8 -*-
# ui_server.py - Dynamic Configuration Web UI for Nexus MCP Server
import json
import logging
import asyncio
import sys
import os
import signal
import glob
import importlib
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from multi_server import load_configuration, dynamically_register_tools
from mcp.server.fastmcp import FastMCP
from monitoring import get_monitoring

# Configurazione logging per catturare i log
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)-8s] --- %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Custom log handler per catturare i log in memoria
log_buffer = []
MAX_LOG_ENTRIES = 1000

class WebUILogHandler(logging.Handler):
    def emit(self, record):
        global log_buffer
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": self.format(record),
            "module": record.module
        }
        log_buffer.append(log_entry)
        # Mantieni solo le ultime MAX_LOG_ENTRIES righe
        if len(log_buffer) > MAX_LOG_ENTRIES:
            log_buffer = log_buffer[-MAX_LOG_ENTRIES:]

# Aggiungi handler personalizzato al logger root
web_handler = WebUILogHandler()
web_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)-8s] --- %(message)s'))
logging.getLogger().addHandler(web_handler)

# Modelli Pydantic
class ToolConfigUpdate(BaseModel):
    enabled_tools: List[str]

class ToolInfo(BaseModel):
    name: str
    file_path: str
    enabled: bool
    description: str

# Inizializza FastAPI
app = FastAPI(
    title="Nexus MCP Server - Configuration UI",
    description="Dynamic Configuration Interface for Nexus MCP Server",
    version="1.0.0"
)

# Variabili globali
mcp_server = None
current_config = {}
available_tool_files = []

def scan_available_tools() -> List[Dict[str, Any]]:
    """Scansiona la cartella tools per trovare tutti i file .py disponibili."""
    tools_dir = Path(__file__).parent / "tools"
    tool_files = []
    
    for py_file in tools_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        tool_name = py_file.stem
        description = "Tool per Nexus MCP Server"
        
        # Prova a leggere la descrizione dal file
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Cerca commenti con descrizione
                for line in content.split('\n')[:20]:  # Prime 20 righe
                    if 'Registrazione tool-set:' in line:
                        description = line.split('Registrazione tool-set:')[-1].strip(' "\'')
                        break
        except:
            pass
        
        tool_files.append({
            "name": tool_name,
            "file_path": str(py_file),
            "description": description,
            "enabled": tool_name in current_config.get("enabled_tools", [])
        })
    
    return sorted(tool_files, key=lambda x: x["name"])

async def reload_server_configuration():
    """Ricarica la configurazione del server senza downtime."""
    global mcp_server, current_config
    
    try:
        # Ricarica configurazione
        current_config = load_configuration()
        
        # Crea nuova istanza del server MCP
        new_server = FastMCP("NexusServer-UI")
        dynamically_register_tools(new_server, current_config)
        
        # Sostituisci il server esistente
        old_server = mcp_server
        mcp_server = new_server
        
        logging.info(f"✅ Configurazione ricaricata con successo. Tool abilitati: {len(current_config.get('enabled_tools', []))}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Errore durante ricarica configurazione: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Inizializza il server all'avvio."""
    global mcp_server, current_config, available_tool_files
    
    logging.info("🚀 Inizializzazione UI Server per Nexus MCP...")
    
    try:
        # Carica configurazione
        current_config = load_configuration()
        
        # Scansiona tool disponibili
        available_tool_files = scan_available_tools()
        
        # Crea istanza FastMCP
        mcp_server = FastMCP("NexusServer-UI")
        dynamically_register_tools(mcp_server, current_config)
        
        logging.info(f"✅ UI Server pronto. Tool disponibili: {len(available_tool_files)}, Tool abilitati: {len(current_config.get('enabled_tools', []))}")
        
    except Exception as e:
        logging.error(f"❌ Errore durante inizializzazione: {e}")
        sys.exit(1)

# Endpoint per la UI principale
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Dashboard principale con interfaccia di configurazione."""
    html_content = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus MCP Server - Configuration Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #27ae60;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .panel {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .panel h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }
        
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .tool-item {
            display: flex;
            align-items: center;
            padding: 10px;
            border: 1px solid #ecf0f1;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .tool-item:hover {
            background: #f8f9fa;
            border-color: #3498db;
        }
        
        .tool-item input[type="checkbox"] {
            margin-right: 10px;
            transform: scale(1.2);
        }
        
        .tool-info {
            flex: 1;
        }
        
        .tool-name {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .tool-description {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 2px;
        }
        
        .log-container {
            height: 300px;
            overflow-y: auto;
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }
        
        .log-level-INFO { color: #3498db; }
        .log-level-WARNING { color: #f39c12; }
        .log-level-ERROR { color: #e74c3c; }
        .log-level-DEBUG { color: #95a5a6; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        
        .metric-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: #3498db;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2980b9;
        }
        
        .btn-success {
            background: #27ae60;
            color: white;
        }
        
        .btn-success:hover {
            background: #219a52;
        }
        
        .btn-warning {
            background: #f39c12;
            color: white;
        }
        
        .btn-warning:hover {
            background: #e67e22;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification.success {
            background: #27ae60;
        }
        
        .notification.error {
            background: #e74c3c;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            .tools-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="status-indicator"></span>Nexus MCP Server - Configuration Dashboard</h1>
            <p>Gestione dinamica dei tool e monitoraggio in tempo reale</p>
        </div>
        
        <div class="grid">
            <!-- Panel Configurazione Tool -->
            <div class="panel">
                <h2>🔧 Configurazione Tool</h2>
                <div id="tools-container" class="tools-grid">
                    <!-- I tool verranno caricati dinamicamente -->
                </div>
                <div class="action-buttons">
                    <button id="apply-config" class="btn btn-success">Applica Modifiche</button>
                    <button id="select-all" class="btn btn-primary">Seleziona Tutti</button>
                    <button id="deselect-all" class="btn btn-warning">Deseleziona Tutti</button>
                </div>
            </div>
            
            <!-- Panel Metriche -->
            <div class="panel">
                <h2>📊 Metriche del Server</h2>
                <div id="metrics-container" class="metrics-grid">
                    <!-- Le metriche verranno caricate dinamicamente -->
                </div>
            </div>
        </div>
        
        <!-- Panel Log -->
        <div class="panel">
            <h2>📋 Log del Server (Real-time)</h2>
            <div id="logs-container" class="log-container">
                <!-- I log verranno aggiornati in tempo reale -->
            </div>
        </div>
    </div>
    
    <!-- Notifica -->
    <div id="notification" class="notification"></div>
    
    <script>
        let tools = [];
        let logEventSource = null;
        let metricsEventSource = null;
        
        // Funzioni di utilità
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }
        
        // Carica configurazione tool
        async function loadToolsConfiguration() {
            try {
                const response = await fetch('/api/tools/available');
                tools = await response.json();
                renderTools();
            } catch (error) {
                console.error('Errore caricamento tool:', error);
                showNotification('Errore caricamento configurazione tool', 'error');
            }
        }
        
        // Renderizza lista tool
        function renderTools() {
            const container = document.getElementById('tools-container');
            container.innerHTML = '';
            
            tools.forEach(tool => {
                const toolItem = document.createElement('div');
                toolItem.className = 'tool-item';
                toolItem.innerHTML = `
                    <input type="checkbox" id="tool-${tool.name}" ${tool.enabled ? 'checked' : ''} 
                           onchange="toggleTool('${tool.name}', this.checked)">
                    <div class="tool-info">
                        <div class="tool-name">${tool.name}</div>
                        <div class="tool-description">${tool.description}</div>
                    </div>
                `;
                container.appendChild(toolItem);
            });
        }
        
        // Toggle stato tool
        function toggleTool(toolName, enabled) {
            const tool = tools.find(t => t.name === toolName);
            if (tool) {
                tool.enabled = enabled;
            }
        }
        
        // Applica configurazione
        async function applyConfiguration() {
            const enabledTools = tools.filter(t => t.enabled).map(t => t.name);
            
            try {
                const response = await fetch('/api/tools/configure', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ enabled_tools: enabledTools })
                });
                
                if (response.ok) {
                    showNotification('Configurazione applicata con successo! Server ricaricato.', 'success');
                    setTimeout(() => loadMetrics(), 1000); // Ricarica metriche dopo un secondo
                } else {
                    throw new Error('Errore durante applicazione configurazione');
                }
            } catch (error) {
                console.error('Errore:', error);
                showNotification('Errore durante applicazione configurazione', 'error');
            }
        }
        
        // Carica metriche
        async function loadMetrics() {
            try {
                const response = await fetch('/api/metrics/current');
                const metrics = await response.json();
                renderMetrics(metrics);
            } catch (error) {
                console.error('Errore caricamento metriche:', error);
            }
        }
        
        // Renderizza metriche
        function renderMetrics(metrics) {
            const container = document.getElementById('metrics-container');
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${metrics.enabled_tools}</div>
                    <div class="metric-label">Tool Abilitati</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.available_tools}</div>
                    <div class="metric-label">Tool Disponibili</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.active_sessions}</div>
                    <div class="metric-label">Sessioni Attive</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.total_calls}</div>
                    <div class="metric-label">Chiamate Totali</div>
                </div>
            `;
        }
        
        // Inizializza streaming log
        function initLogStreaming() {
            if (logEventSource) {
                logEventSource.close();
            }
            
            logEventSource = new EventSource('/api/logs/stream');
            
            logEventSource.onmessage = function(event) {
                const logEntry = JSON.parse(event.data);
                addLogEntry(logEntry);
            };
            
            logEventSource.onerror = function(event) {
                console.error('Errore streaming log:', event);
            };
        }
        
        // Aggiunge entry di log
        function addLogEntry(logEntry) {
            const container = document.getElementById('logs-container');
            const entry = document.createElement('div');
            entry.className = `log-entry log-level-${logEntry.level}`;
            entry.innerHTML = `<span class="timestamp">${logEntry.timestamp}</span> <span class="level">[${logEntry.level}]</span> ${logEntry.message}`;
            
            container.appendChild(entry);
            
            // Mantieni solo ultime 100 righe
            const entries = container.children;
            if (entries.length > 100) {
                container.removeChild(entries[0]);
            }
            
            // Auto-scroll
            container.scrollTop = container.scrollHeight;
        }
        
        // Event listeners
        document.getElementById('apply-config').addEventListener('click', applyConfiguration);
        
        document.getElementById('select-all').addEventListener('click', () => {
            tools.forEach(tool => tool.enabled = true);
            renderTools();
        });
        
        document.getElementById('deselect-all').addEventListener('click', () => {
            tools.forEach(tool => tool.enabled = false);
            renderTools();
        });
        
        // Inizializzazione
        document.addEventListener('DOMContentLoaded', () => {
            loadToolsConfiguration();
            loadMetrics();
            initLogStreaming();
            
            // Aggiorna metriche ogni 5 secondi
            setInterval(loadMetrics, 5000);
        });
        
        // Cleanup quando la pagina viene chiusa
        window.addEventListener('beforeunload', () => {
            if (logEventSource) {
                logEventSource.close();
            }
            if (metricsEventSource) {
                metricsEventSource.close();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

# API Endpoints
@app.get("/api/tools/available")
async def get_available_tools():
    """Restituisce la lista di tutti i tool disponibili con il loro stato."""
    global available_tool_files
    available_tool_files = scan_available_tools()  # Aggiorna la lista
    return available_tool_files

@app.post("/api/tools/configure")
async def configure_tools(config: ToolConfigUpdate):
    """Aggiorna la configurazione dei tool e ricarica il server."""
    global current_config
    
    try:
        # Aggiorna configurazione
        current_config["enabled_tools"] = config.enabled_tools
        
        # Salva configurazione su file
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=2, ensure_ascii=False)
        
        # Ricarica configurazione del server
        success = await reload_server_configuration()
        
        if success:
            # Aggiorna lista tool disponibili
            global available_tool_files
            available_tool_files = scan_available_tools()
            
            logging.info(f"🔄 Configurazione aggiornata: {len(config.enabled_tools)} tool abilitati")
            return {"status": "success", "message": "Configurazione applicata con successo", "enabled_tools": len(config.enabled_tools)}
        else:
            raise HTTPException(status_code=500, detail="Errore durante ricarica configurazione")
            
    except Exception as e:
        logging.error(f"Errore configurazione tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/current")
async def get_current_metrics():
    """Restituisce le metriche correnti del server."""
    monitoring = get_monitoring()
    
    return {
        "enabled_tools": len(current_config.get("enabled_tools", [])),
        "available_tools": len(available_tool_files),
        "active_sessions": monitoring.get_current_sessions(),
        "total_calls": "N/A",  # Le metriche Prometheus richiederebbero parsing
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/logs/stream")
async def stream_logs():
    """Stream dei log in tempo reale usando Server-Sent Events."""
    async def log_generator():
        last_sent = len(log_buffer)
        
        while True:
            # Invia nuovi log
            if len(log_buffer) > last_sent:
                for log_entry in log_buffer[last_sent:]:
                    yield f"data: {json.dumps(log_entry)}\n\n"
                last_sent = len(log_buffer)
            
            await asyncio.sleep(1)  # Controlla ogni secondo
    
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/logs/recent")
async def get_recent_logs(limit: int = 50):
    """Restituisce gli ultimi log entries."""
    return log_buffer[-limit:] if log_buffer else []

@app.get("/health")
async def health_check():
    """Health check per il server UI."""
    return {
        "status": "healthy",
        "message": "Nexus MCP Server UI is running",
        "tools_count": len(available_tool_files),
        "enabled_tools": len(current_config.get("enabled_tools", []))
    }

if __name__ == "__main__":
    # Avvia server UI
    uvicorn.run(
        "ui_server:app",
        host="0.0.0.0", 
        port=8888, 
        log_level="info",
        reload=False  # Disabilita reload per evitare conflitti
    )