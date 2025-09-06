# -*- coding: utf-8 -*-
# client.py
import asyncio
import sys
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_tool_from_cli():
    """
    Client a riga di comando per interagire con il server Nexus.
    Avvia il server, esegue un singolo tool e termina.
    """
    if len(sys.argv) < 2:
        print("Uso: python client.py <nome_tool> '[argomenti_json]'")
        print("Esempi:")
        print("  python client.py add '{\"a\": 10, \"b\": 5}'")
        print("  python client.py read_safe_file '{\"filename\": \"esempio.txt\"}'")
        print("  python client.py fetch_url_content '{\"url\": \"https://example.com\"}'")
        sys.exit(1)

    tool_name = sys.argv[1]
    args_json_str = sys.argv[2] if len(sys.argv) > 2 else '{}'

    try:
        args_dict = json.loads(args_json_str)
    except json.JSONDecodeError:
        print(f"Errore: L'argomento '{args_json_str}' non e' un JSON valido.")
        sys.exit(1)

    # Configura i parametri per lanciare il nostro server principale
    server_params = StdioServerParameters(command="python", args=["multi_server.py"])

    async with AsyncExitStack() as stack:
        # Avvia il server come sottoprocesso e stabilisce la comunicazione stdio
        read, write = await stack.enter_async_context(stdio_client(server_params))
        
        # Crea una sessione client MCP che gestisce la comunicazione
        async with ClientSession(read, write) as session:
            # Esegue l'handshake iniziale con il server
            await session.initialize()
            
            print(f"\nEsecuzione del tool '{tool_name}' con argomenti: {args_dict}...")
            
            # Esegue la chiamata al tool e attende il risultato
            result = await session.call_tool(tool_name, args_dict)
            
            print("\n" + "="*15 + " RISPOSTA DAL SERVER NEXUS " + "="*15)
            if result.content and hasattr(result.content[0], 'text'):
                print(result.content[0].text)
            else:
                print("(Nessun contenuto testuale ricevuto dal server)")
            print("="*54 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tool_from_cli())