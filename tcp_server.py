# -*- coding: utf-8 -*-
# tcp_server.py
import asyncio
import json
import logging
import sys
import argparse
from multi_server import load_configuration, dynamically_register_tools
from mcp.server.fastmcp import FastMCP
from monitoring import get_monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)-8s] --- %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def handle_client(reader, writer):
    """Handle a single client connection."""
    addr = writer.get_extra_info('peername')
    logging.info(f"Client connected from {addr}")
    
    try:
        # Initialize monitoring and track session
        monitoring = get_monitoring()
        config = load_configuration()
        
        server_instance = FastMCP("NexusServer")
        dynamically_register_tools(server_instance, config)
        
        # Create a transport that reads from the client and writes responses back
        class TCPTransport:
            def __init__(self, reader, writer):
                self.reader = reader
                self.writer = writer
                
            async def read_message(self):
                try:
                    # Read length-prefixed message
                    length_bytes = await self.reader.readexactly(4)
                    length = int.from_bytes(length_bytes, 'big')
                    message_bytes = await self.reader.readexactly(length)
                    return message_bytes.decode('utf-8')
                except Exception as e:
                    logging.error(f"Error reading message: {e}")
                    return None
                    
            async def write_message(self, message):
                try:
                    message_bytes = message.encode('utf-8')
                    length_bytes = len(message_bytes).to_bytes(4, 'big')
                    self.writer.write(length_bytes + message_bytes)
                    await self.writer.drain()
                except Exception as e:
                    logging.error(f"Error writing message: {e}")
        
        transport = TCPTransport(reader, writer)
        
        # Handle client messages
        while True:
            try:
                message = await transport.read_message()
                if message is None:
                    break
                    
                # Parse JSON-RPC message
                request = json.loads(message)
                logging.info(f"Received request: {request.get('method', 'unknown')}")
                
                # Process the request through FastMCP (this is simplified)
                # In a real implementation, you'd need to integrate more deeply with FastMCP
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"status": "received", "method": request.get("method")}
                }
                
                await transport.write_message(json.dumps(response))
                
            except json.JSONDecodeError:
                logging.error("Invalid JSON received")
                break
            except Exception as e:
                logging.error(f"Error handling client: {e}")
                break
                
    except Exception as e:
        logging.error(f"Client connection error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        logging.info(f"Client {addr} disconnected")

async def start_tcp_server(host='localhost', port=3000):
    """Start the TCP server."""
    logging.info(f"Starting TCP server on {host}:{port}")
    
    server = await asyncio.start_server(
        handle_client, host, port
    )
    
    addr = server.sockets[0].getsockname()
    logging.info(f"Serving on {addr}")
    
    async with server:
        await server.serve_forever()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Nexus MCP TCP Server')
    parser.add_argument('--host', default='localhost',
                       help='Host address (default: localhost)')
    parser.add_argument('--port', type=int, default=3000,
                       help='Port number (default: 3000)')
    
    args = parser.parse_args()
    
    logging.info("==============================================")
    logging.info("Avvio del Server MCP Nexus TCP in corso...")
    logging.info("==============================================")
    
    try:
        asyncio.run(start_tcp_server(args.host, args.port))
    except KeyboardInterrupt:
        logging.info("Server TCP arrestato dall'utente")
    except Exception as e:
        logging.error(f"Errore del server TCP: {e}")

if __name__ == "__main__":
    main()