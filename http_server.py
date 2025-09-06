# -*- coding: utf-8 -*-
# http_server.py - HTTP wrapper per Nexus MCP Server
import json
import logging
import asyncio
import sys
import importlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from multi_server import load_configuration, dynamically_register_tools
from mcp.server.fastmcp import FastMCP

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)-8s] --- %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Modelli Pydantic per le richieste
class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str
    message: str
    available_tools: list

# Inizializza FastAPI
app = FastAPI(
    title="Nexus MCP Server HTTP API",
    description="HTTP wrapper per il server MCP Nexus con tutti i tool disponibili",
    version="2.0.0"
)

# Variabile globale per il server MCP
mcp_server = None
available_tools = []
tool_registry = {}

def get_tool_list_from_config(config):
    """Ottieni la lista dei tool disponibili dal config e dai moduli."""
    tools = {}
    enabled_modules = config.get("enabled_tools", [])
    
    # Mapping hardcoded dei tool disponibili per modulo
    tool_mapping = {
        "calculator": ["add", "multiply"],
        "filesystem_reader": ["read_safe_file"],
        "web_fetcher": ["fetch_url_content"], 
        "crypto_tools": ["generate_hash", "generate_hmac", "generate_random_token"],
        "encoding_tools": ["base64_encode", "base64_decode", "url_encode", "url_decode", "html_escape", "json_format"],
        "datetime_tools": ["current_timestamp", "unix_to_date", "date_to_unix", "date_math"],
        "uuid_tools": ["generate_uuid4", "generate_uuid1", "generate_multiple_uuids", "generate_short_id", "generate_nanoid", "uuid_info"],
        "string_tools": ["string_case_convert", "string_stats", "string_clean", "string_wrap", "string_find_replace"],
        "validator_tools": ["validate_email", "validate_url", "validate_ip_address", "validate_phone", "validate_credit_card"],
        "system_info": ["system_overview", "memory_usage", "cpu_info", "disk_usage", "network_info", "running_processes"]
    }
    
    for module_name in enabled_modules:
        if module_name in tool_mapping:
            for tool_name in tool_mapping[module_name]:
                tools[tool_name] = module_name
    
    return tools

@app.on_event("startup")
async def startup_event():
    """Inizializza il server MCP all'avvio."""
    global mcp_server, available_tools, tool_registry
    
    logging.info("🚀 Inizializzazione HTTP wrapper per Nexus MCP...")
    
    try:
        # Carica configurazione
        config = load_configuration()
        
        # Crea istanza FastMCP
        mcp_server = FastMCP("NexusServer-HTTP")
        
        # Carica tool dinamicamente
        dynamically_register_tools(mcp_server, config)
        
        # Ottieni lista tool disponibili dall'oggetto FastMCP
        # FastMCP espone i tool in un modo diverso, usiamo inspect o una lista manuale
        tool_registry = get_tool_list_from_config(config)
        available_tools = list(tool_registry.keys())
        
        logging.info(f"✅ Server HTTP pronto con {len(available_tools)} tool: {', '.join(available_tools)}")
        
    except Exception as e:
        logging.error(f"❌ Errore durante inizializzazione: {e}")
        sys.exit(1)

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Nexus MCP Server HTTP API is running",
        available_tools=available_tools
    )

@app.get("/tools")
async def list_tools():
    """Lista tutti i tool disponibili."""
    return {
        "available_tools": available_tools,
        "count": len(available_tools),
        "server_info": {
            "name": "NexusServer-HTTP",
            "version": "2.0.0"
        }
    }

@app.post("/execute")
async def execute_tool(request: ToolRequest):
    """Esegue un tool specificato."""
    global mcp_server, tool_registry
    
    if not mcp_server:
        raise HTTPException(status_code=500, detail="Server MCP non inizializzato")
    
    if request.tool_name not in available_tools:
        raise HTTPException(
            status_code=404, 
            detail=f"Tool '{request.tool_name}' non trovato. Tool disponibili: {', '.join(available_tools)}"
        )
    
    try:
        # Ottieni il modulo che contiene il tool
        module_name = tool_registry[request.tool_name]
        module_path = f"tools.{module_name}"
        
        # Importa il modulo dinamicamente
        tool_module = importlib.import_module(module_path)
        
        # Trova la funzione corrispondente al tool
        if hasattr(tool_module, request.tool_name):
            tool_function = getattr(tool_module, request.tool_name)
            
            # Esegui il tool
            if asyncio.iscoroutinefunction(tool_function):
                result = await tool_function(**request.arguments)
            else:
                result = tool_function(**request.arguments)
            
            return {
                "tool_name": request.tool_name,
                "arguments": request.arguments,
                "result": result,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Funzione '{request.tool_name}' non trovata nel modulo '{module_name}'")
        
    except TypeError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Argomenti non validi per il tool '{request.tool_name}': {str(e)}"
        )
    except Exception as e:
        logging.error(f"Errore durante esecuzione tool '{request.tool_name}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Errore durante esecuzione: {str(e)}"
        )

@app.get("/execute/{tool_name}")
async def execute_tool_get(tool_name: str):
    """Esegue un tool senza argomenti via GET."""
    request = ToolRequest(tool_name=tool_name)
    return await execute_tool(request)

if __name__ == "__main__":
    # Avvia server HTTP
    uvicorn.run(
        "http_server:app",
        host="0.0.0.0", 
        port=9999, 
        log_level="info"
    )