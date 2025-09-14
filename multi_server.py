# -*- coding: utf-8 -*-
# multi_server.py
import json
import logging
import sys
import os
import importlib
from mcp.server.fastmcp import FastMCP
from monitoring import get_monitoring

# Configurazione avanzata del logging per una diagnostica chiara
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr, # Fondamentale per il trasporto stdio per non corrompere il JSON-RPC
    format='[%(asctime)s] [%(levelname)-8s] --- %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_configuration(config_path="config.json") -> dict:
    """Carica la configurazione da un file JSON, con gestione robusta degli errori."""
    try:
        with open(config_path, 'r', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.critical(f"FATALE: File di configurazione '{config_path}' non trovato. Il server non puo' avviarsi.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.critical(f"FATALE: Errore di sintassi nel file JSON '{config_path}': {e}. Il server non puo' avviarsi.")
        sys.exit(1)

def dynamically_register_tools(mcp: FastMCP, config: dict):
    """
    Scansiona la configurazione, importa dinamicamente i moduli dei tool specificati
    e invoca la loro funzione 'register_tools'.
    """
    enabled_modules = config.get("enabled_tools", [])
    if not enabled_modules:
        logging.warning("Nessun modulo tool abilitato nel file di configurazione. Il server si avviera' senza funzionalita'.")
        return

    logging.info(f"Inizio caricamento dinamico dei moduli tool: {', '.join(enabled_modules)}")
    for module_name in enabled_modules:
        try:
            module_path = f"tools.{module_name}"
            tool_module = importlib.import_module(module_path)
            
            if hasattr(tool_module, "register_tools") and callable(tool_module.register_tools):
                tool_module.register_tools(mcp)
                logging.info(f"Modulo '{module_name}' caricato e registrato con successo.")
            else:
                logging.warning(f"Modulo '{module_name}' non contiene una funzione 'register_tools' eseguibile. Ignorato.")
        except ImportError:
            logging.error(f"FALLITO: Impossibile importare il modulo tool '{module_name}'. Controllare che il file 'tools/{module_name}.py' esista.")
        except Exception as e:
            logging.error(f"FALLITO: Errore critico durante la registrazione del tool '{module_name}': {e}", exc_info=True)

def get_config_file() -> str:
    """
    Determina il file di configurazione da utilizzare basandosi su:
    1. Variabile d'ambiente MCP_CLIENT_TYPE
    2. Argomenti da riga di comando --config
    3. Default per Claude Desktop (config.json)
    """
    # Check command line arguments first
    if len(sys.argv) > 1:
        if sys.argv[1] == "--config" and len(sys.argv) > 2:
            return sys.argv[2]
    
    # Check environment variable for client type
    client_type = os.environ.get('MCP_CLIENT_TYPE', '').lower()
    
    if client_type == 'vscode':
        config_file = "config-vscode.json"
        logging.info(f"🔧 Rilevato client VSCode - utilizzando configurazione limitata: {config_file}")
    else:
        config_file = "config.json"  # Default for Claude Desktop
        if client_type:
            logging.info(f"🔧 Client rilevato: {client_type} - utilizzando configurazione completa: {config_file}")
        else:
            logging.info(f"🔧 Nessun client specificato - utilizzando configurazione completa per Claude Desktop: {config_file}")
    
    return config_file

def main():
    """Punto di ingresso principale dell'applicazione server."""
    logging.info("==============================================")
    logging.info("Avvio del Server MCP Nexus in corso...")
    logging.info("==============================================")
    
    # Initialize monitoring and track session
    monitoring = get_monitoring()
    
    # Determine configuration file based on client type or arguments
    config_file = get_config_file()
    
    config = load_configuration(config_file)
    
    # Log configuration details
    enabled_tools = config.get("enabled_tools", [])
    client_type = config.get("client_type", "unknown")
    actual_function_count = config.get("actual_function_count", "unknown")
    
    logging.info(f"📊 Configurazione caricata: {len(enabled_tools)} moduli tool abilitati")
    if actual_function_count != "unknown":
        logging.info(f"📊 Funzioni totali disponibili: {actual_function_count}")
    if client_type != "unknown":
        logging.info(f"📊 Configurazione ottimizzata per client: {client_type}")
    
    server_instance = FastMCP("NexusServer")
    
    dynamically_register_tools(server_instance, config)
    
    # Check if tools were loaded (we can't easily access the count with FastMCP)
    # but we know from logging if the registration was successful
    logging.info("----------------------------------------------")
    logging.info("Server Nexus pronto e configurato")
    logging.info("----------------------------------------------")
    logging.info("In ascolto di connessioni client su stdio...")
    
    # Track the session lifecycle
    with monitoring.track_session():
        # Avvia il ciclo di vita del server, che ascoltera' i messaggi dal client
        server_instance.run(transport='stdio')

if __name__ == "__main__":
    main()