# -*- coding: utf-8 -*-
# tools/network_tools.py
import subprocess
import socket
import requests
import json
import logging
from typing import Dict, List, Optional, Any

def register_tools(mcp):
    """Registra i tool di rete con l'istanza del server MCP."""
    logging.info("🌐 Registrazione tool-set: Network Tools")

    @mcp.tool()
    def ping_host(host: str, count: int = 4) -> Dict[str, Any]:
        """
        Esegue un ping verso un host specificato.
        
        Args:
            host: L'hostname o IP da pingare
            count: Numero di ping da inviare (default: 4)
        """
        try:
            result = subprocess.run(
                ['ping', '-c', str(count), host], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return {
                "host": host,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "packets_sent": count
            }
        except subprocess.TimeoutExpired:
            return {
                "host": host,
                "success": False,
                "error": "Timeout durante ping",
                "packets_sent": count
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e),
                "packets_sent": count
            }

    @mcp.tool()
    def dns_lookup(hostname: str, record_type: str = "A") -> Dict[str, Any]:
        """
        Esegue una lookup DNS per un hostname.
        
        Args:
            hostname: Il nome dell'host da risolvere
            record_type: Tipo di record DNS (A, AAAA, MX, NS, TXT)
        """
        try:
            import dns.resolver
            
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(hostname, record_type)
            
            results = []
            for answer in answers:
                results.append(str(answer))
            
            return {
                "hostname": hostname,
                "record_type": record_type,
                "success": True,
                "results": results,
                "count": len(results)
            }
        except ImportError:
            # Fallback usando socket per record A
            if record_type == "A":
                try:
                    ip = socket.gethostbyname(hostname)
                    return {
                        "hostname": hostname,
                        "record_type": record_type,
                        "success": True,
                        "results": [ip],
                        "count": 1
                    }
                except socket.gaierror as e:
                    return {
                        "hostname": hostname,
                        "record_type": record_type,
                        "success": False,
                        "error": str(e)
                    }
            else:
                return {
                    "hostname": hostname,
                    "record_type": record_type,
                    "success": False,
                    "error": "dnspython non installato - solo record A supportati"
                }
        except Exception as e:
            return {
                "hostname": hostname,
                "record_type": record_type,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def port_scan(host: str, ports: List[int]) -> Dict[str, Any]:
        """
        Scansiona porte specifiche su un host.
        
        Args:
            host: L'hostname o IP da scansionare
            ports: Lista delle porte da controllare
        """
        try:
            open_ports = []
            closed_ports = []
            
            for port in ports[:20]:  # Limita a 20 porte per sicurezza
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                
                try:
                    result = sock.connect_ex((host, port))
                    if result == 0:
                        open_ports.append(port)
                    else:
                        closed_ports.append(port)
                except Exception:
                    closed_ports.append(port)
                finally:
                    sock.close()
            
            return {
                "host": host,
                "scanned_ports": ports[:20],
                "open_ports": open_ports,
                "closed_ports": closed_ports,
                "total_open": len(open_ports),
                "total_scanned": len(ports[:20])
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def traceroute(host: str, max_hops: int = 15) -> Dict[str, Any]:
        """
        Esegue un traceroute verso un host.
        
        Args:
            host: L'hostname o IP di destinazione
            max_hops: Numero massimo di hop (default: 15)
        """
        try:
            result = subprocess.run(
                ['traceroute', '-m', str(max_hops), host], 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            return {
                "host": host,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "max_hops": max_hops
            }
        except subprocess.TimeoutExpired:
            return {
                "host": host,
                "success": False,
                "error": "Timeout durante traceroute",
                "max_hops": max_hops
            }
        except FileNotFoundError:
            return {
                "host": host,
                "success": False,
                "error": "Comando traceroute non disponibile",
                "max_hops": max_hops
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e),
                "max_hops": max_hops
            }

    @mcp.tool()
    def whois_lookup(domain: str) -> Dict[str, Any]:
        """
        Esegue una lookup whois per un dominio.
        
        Args:
            domain: Il dominio da controllare
        """
        try:
            result = subprocess.run(
                ['whois', domain], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return {
                "domain": domain,
                "success": result.returncode == 0,
                "whois_data": result.stdout,
                "error": result.stderr if result.stderr else None
            }
        except subprocess.TimeoutExpired:
            return {
                "domain": domain,
                "success": False,
                "error": "Timeout durante whois lookup"
            }
        except FileNotFoundError:
            return {
                "domain": domain,
                "success": False,
                "error": "Comando whois non disponibile"
            }
        except Exception as e:
            return {
                "domain": domain,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def check_website_status(url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Controlla lo status di un sito web.
        
        Args:
            url: URL del sito da controllare
            timeout: Timeout in secondi (default: 10)
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content),
                "headers": dict(response.headers),
                "final_url": response.url if response.url != url else None
            }
        except requests.exceptions.Timeout:
            return {
                "url": url,
                "success": False,
                "error": "Timeout durante connessione",
                "timeout": timeout
            }
        except requests.exceptions.ConnectionError:
            return {
                "url": url,
                "success": False,
                "error": "Impossibile connettersi al server"
            }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def get_public_ip() -> Dict[str, Any]:
        """
        Ottiene l'indirizzo IP pubblico corrente.
        """
        try:
            # Prova diversi servizi
            services = [
                'https://api.ipify.org?format=json',
                'https://httpbin.org/ip',
                'https://api.ip.sb/ip'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        if 'ipify' in service:
                            data = response.json()
                            return {
                                "success": True,
                                "public_ip": data["ip"],
                                "service": service
                            }
                        elif 'httpbin' in service:
                            data = response.json()
                            return {
                                "success": True,
                                "public_ip": data["origin"],
                                "service": service
                            }
                        elif 'ip.sb' in service:
                            return {
                                "success": True,
                                "public_ip": response.text.strip(),
                                "service": service
                            }
                except:
                    continue
            
            return {
                "success": False,
                "error": "Nessun servizio IP disponibile"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }