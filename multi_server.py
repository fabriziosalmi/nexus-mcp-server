# -*- coding: utf-8 -*-
# multi_server.py
import json
import logging
import sys
import importlib
from mcp.server.fastmcp import FastMCP

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

def main():
    """Punto di ingresso principale dell'applicazione server."""
    logging.info("==============================================")
    logging.info("Avvio del Server MCP Nexus in corso...")
    logging.info("==============================================")
    
    config = load_configuration()
    
    server_instance = FastMCP("NexusServer")
    
    dynamically_register_tools(server_instance, config)
    
    # Check if tools were loaded (we can't easily access the count with FastMCP)
    # but we know from logging if the registration was successful
    logging.info("----------------------------------------------")
    logging.info("Server Nexus pronto e configurato")
    logging.info("----------------------------------------------")
    logging.info("In ascolto di connessioni client su stdio...")
    
    # Avvia il ciclo di vita del server, che ascoltera' i messaggi dal client
    server_instance.run(transport='stdio')

if __name__ == "__main__":
    main()