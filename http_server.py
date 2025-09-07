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
        "system_info": ["system_overview", "memory_usage", "cpu_info", "disk_usage", "network_info", "running_processes"],
        "network_tools": ["ping_host", "dns_lookup", "port_scan", "traceroute", "whois_lookup", "check_website_status", "get_public_ip"],
        "security_tools": ["generate_secure_password", "password_strength_check", "generate_api_key", "hash_file_content", "jwt_decode_header", "check_common_ports", "ssl_certificate_check"],
        "performance_tools": ["benchmark_function_performance", "monitor_system_performance", "analyze_memory_usage", "disk_performance_test", "network_latency_test", "cpu_stress_test"],
        "data_analysis": ["analyze_csv_data", "analyze_json_structure", "statistical_analysis", "text_analysis", "correlation_analysis"],
        "image_processing": ["analyze_image_metadata", "resize_image", "convert_image_format", "apply_image_filters", "create_thumbnail", "extract_dominant_colors"],
        "audio_processing": ["analyze_audio_metadata", "generate_sine_wave", "analyze_audio_spectrum", "adjust_audio_volume", "convert_audio_format", "extract_audio_features"],
        "video_processing": ["analyze_video_metadata", "create_video_thumbnail_placeholder", "analyze_video_structure", "estimate_video_properties", "create_video_info_summary"]
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
        # Approccio semplificato: chiamiamo il tool direttamente dai moduli
        # Ricreiamo le funzioni localmente
        if request.tool_name == "add":
            result = request.arguments["a"] + request.arguments["b"]
        elif request.tool_name == "multiply":
            result = request.arguments["a"] * request.arguments["b"]
        elif request.tool_name == "generate_uuid4":
            import uuid
            result = str(uuid.uuid4())
        elif request.tool_name == "current_timestamp":
            from datetime import datetime
            result = {
                "iso": datetime.utcnow().isoformat() + "Z",
                "unix": int(datetime.utcnow().timestamp()),
                "human_readable": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        elif request.tool_name == "base64_encode":
            import base64
            result = base64.b64encode(request.arguments["text"].encode()).decode()
        elif request.tool_name == "system_overview":
            import psutil, platform
            result = {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "hostname": platform.node()
            }
        elif request.tool_name == "generate_secure_password":
            import secrets, string
            length = request.arguments.get("length", 16)
            include_symbols = request.arguments.get("include_symbols", True)
            
            charset = string.ascii_letters + string.digits
            if include_symbols:
                charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            password = ''.join(secrets.choice(charset) for _ in range(length))
            result = {
                "password": password,
                "length": len(password),
                "charset_size": len(charset)
            }
        elif request.tool_name == "get_public_ip":
            import requests
            try:
                response = requests.get('https://api.ipify.org?format=json', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "success": True,
                        "public_ip": data["ip"],
                        "service": "ipify.org"
                    }
                else:
                    result = {"success": False, "error": "Servizio non disponibile"}
            except:
                result = {"success": False, "error": "Errore connessione"}
        elif request.tool_name == "dns_lookup":
            import socket
            hostname = request.arguments.get("hostname", "")
            try:
                ip = socket.gethostbyname(hostname)
                result = {
                    "hostname": hostname,
                    "success": True,
                    "results": [ip],
                    "record_type": "A"
                }
            except socket.gaierror as e:
                result = {
                    "hostname": hostname,
                    "success": False,
                    "error": str(e)
                }
        elif request.tool_name == "check_website_status":
            import requests
            url = request.arguments.get("url", "")
            timeout = request.arguments.get("timeout", 10)
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            try:
                response = requests.get(url, timeout=timeout, allow_redirects=True)
                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "success": response.status_code < 400,
                    "response_time": response.elapsed.total_seconds(),
                    "content_length": len(response.content)
                }
            except Exception as e:
                result = {
                    "url": url,
                    "success": False,
                    "error": str(e)
                }
        else:
            # Per tool più complessi, cerca nel registro dei moduli
            module_name = tool_registry.get(request.tool_name)
            if module_name:
                # Importa e ricostruisci la logica del tool
                module_path = f"tools.{module_name}"
                tool_module = importlib.import_module(module_path)
                
                # Per ora restituiamo un messaggio
                result = f"Tool '{request.tool_name}' dal modulo '{module_name}' - implementazione in corso"
            else:
                raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' non supportato")
        
        return {
            "tool_name": request.tool_name,
            "arguments": request.arguments,
            "result": result,
            "status": "success"
        }
        
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