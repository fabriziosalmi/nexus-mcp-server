# -*- coding: utf-8 -*-
# tools/network_security_tools.py
import socket
import ssl
import requests
import subprocess
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import base64

def register_tools(mcp):
    """Registra i tool di sicurezza di rete con l'istanza del server MCP."""
    logging.info("🛡️ Registrazione tool-set: Network Security Tools")

    @mcp.tool()
    def ip_threat_intelligence(ip_address: str) -> Dict[str, Any]:
        """
        Controlla se un indirizzo IP è noto come minaccia usando servizi pubblici.
        
        Args:
            ip_address: L'indirizzo IP da controllare
        """
        try:
            # Validazione IP
            try:
                socket.inet_aton(ip_address)
            except socket.error:
                return {
                    "success": False,
                    "error": "Indirizzo IP non valido"
                }
            
            results = {
                "ip_address": ip_address,
                "threat_status": "Unknown",
                "details": {},
                "sources_checked": []
            }
            
            # Check 1: AbuseIPDB (senza API key, solo controllo base)
            try:
                # Controlla se l'IP è in range privati
                ip_parts = ip_address.split('.')
                if len(ip_parts) == 4:
                    first_octet = int(ip_parts[0])
                    second_octet = int(ip_parts[1])
                    
                    is_private = (
                        first_octet == 10 or
                        (first_octet == 172 and 16 <= second_octet <= 31) or
                        (first_octet == 192 and second_octet == 168) or
                        first_octet == 127
                    )
                    
                    if is_private:
                        results["threat_status"] = "Private/Local"
                        results["details"]["network_type"] = "Private IP address"
                        return results
                
                results["sources_checked"].append("IP Range Analysis")
            except:
                pass
            
            # Check 2: DNS Blacklist (alcune blacklist pubbliche)
            blacklists = [
                "zen.spamhaus.org",
                "dnsbl.sorbs.net", 
                "bl.spamcop.net"
            ]
            
            blacklist_hits = []
            for blacklist in blacklists:
                try:
                    # Reverse IP per DNS blacklist
                    reversed_ip = '.'.join(reversed(ip_address.split('.')))
                    query = f"{reversed_ip}.{blacklist}"
                    
                    socket.gethostbyname(query)
                    blacklist_hits.append(blacklist)
                except socket.gaierror:
                    # Non listato (normale)
                    pass
                except Exception:
                    # Errore nella query
                    pass
            
            if blacklist_hits:
                results["threat_status"] = "Suspicious"
                results["details"]["blacklist_hits"] = blacklist_hits
                results["sources_checked"].extend(blacklists)
            else:
                results["threat_status"] = "Clean"
                results["sources_checked"].extend(blacklists)
            
            # Check 3: Geolocation info (base)
            try:
                response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
                if response.status_code == 200:
                    geo_data = response.json()
                    if geo_data.get("status") == "success":
                        results["details"]["geolocation"] = {
                            "country": geo_data.get("country"),
                            "region": geo_data.get("regionName"),
                            "city": geo_data.get("city"),
                            "isp": geo_data.get("isp"),
                            "organization": geo_data.get("org")
                        }
                        results["sources_checked"].append("IP Geolocation")
            except:
                pass
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def scan_security_headers(url: str, follow_redirects: bool = True) -> Dict[str, Any]:
        """
        Analizza gli header di sicurezza HTTP di un sito web.
        
        Args:
            url: URL del sito web da analizzare
            follow_redirects: Segui i redirect (default: True)
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = requests.get(
                url, 
                timeout=10, 
                allow_redirects=follow_redirects,
                verify=False  # Allow self-signed certificates for testing
            )
            
            headers = response.headers
            
            # Header di sicurezza da controllare
            security_headers = {
                "Strict-Transport-Security": {
                    "present": "Strict-Transport-Security" in headers,
                    "value": headers.get("Strict-Transport-Security", ""),
                    "description": "Forza HTTPS per il dominio"
                },
                "Content-Security-Policy": {
                    "present": "Content-Security-Policy" in headers,
                    "value": headers.get("Content-Security-Policy", ""),
                    "description": "Previene attacchi XSS e injection"
                },
                "X-Frame-Options": {
                    "present": "X-Frame-Options" in headers,
                    "value": headers.get("X-Frame-Options", ""),
                    "description": "Previene clickjacking"
                },
                "X-Content-Type-Options": {
                    "present": "X-Content-Type-Options" in headers,
                    "value": headers.get("X-Content-Type-Options", ""),
                    "description": "Previene MIME type sniffing"
                },
                "Referrer-Policy": {
                    "present": "Referrer-Policy" in headers,
                    "value": headers.get("Referrer-Policy", ""),
                    "description": "Controlla informazioni referrer"
                },
                "Permissions-Policy": {
                    "present": "Permissions-Policy" in headers,
                    "value": headers.get("Permissions-Policy", ""),
                    "description": "Controlla permessi browser API"
                },
                "X-XSS-Protection": {
                    "present": "X-XSS-Protection" in headers,
                    "value": headers.get("X-XSS-Protection", ""),
                    "description": "Protezione XSS del browser (deprecato)"
                }
            }
            
            # Calcola punteggio sicurezza
            total_headers = len(security_headers)
            present_headers = sum(1 for h in security_headers.values() if h["present"])
            security_score = round((present_headers / total_headers) * 100, 2)
            
            # Raccomandazioni
            recommendations = []
            for header, info in security_headers.items():
                if not info["present"]:
                    recommendations.append(f"Aggiungi header {header}: {info['description']}")
            
            # Analisi specifiche
            warnings = []
            if "X-XSS-Protection" in headers:
                warnings.append("X-XSS-Protection è deprecato, usa Content-Security-Policy")
            
            if headers.get("Server"):
                warnings.append(f"Header Server espone informazioni: {headers['Server']}")
            
            return {
                "url": url,
                "final_url": response.url,
                "status_code": response.status_code,
                "security_headers": security_headers,
                "security_score": security_score,
                "headers_present": present_headers,
                "total_headers_checked": total_headers,
                "recommendations": recommendations,
                "warnings": warnings,
                "response_time": response.elapsed.total_seconds()
            }
            
        except requests.exceptions.SSLError as e:
            return {
                "url": url,
                "success": False,
                "error": f"Errore SSL: {str(e)}"
            }
        except requests.exceptions.Timeout:
            return {
                "url": url,
                "success": False,
                "error": "Timeout durante la connessione"
            }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def discover_subdomains(domain: str, wordlist_size: str = "small") -> Dict[str, Any]:
        """
        Scopre sottodomini di un dominio per analisi di sicurezza.
        
        Args:
            domain: Il dominio principale da analizzare
            wordlist_size: Dimensione wordlist (small, medium) - default: small
        """
        try:
            # Wordlist comuni per sottodomini
            if wordlist_size == "small":
                subdomains = [
                    "www", "mail", "ftp", "test", "dev", "staging", "admin", "api", 
                    "blog", "shop", "store", "support", "help", "docs", "cdn",
                    "img", "images", "static", "assets", "forum", "wiki"
                ]
            elif wordlist_size == "medium":
                subdomains = [
                    "www", "mail", "ftp", "test", "dev", "staging", "admin", "api", 
                    "blog", "shop", "store", "support", "help", "docs", "cdn",
                    "img", "images", "static", "assets", "forum", "wiki", "news",
                    "app", "mobile", "m", "beta", "demo", "preview", "portal",
                    "secure", "login", "account", "my", "user", "panel", "cp",
                    "webmail", "email", "mx", "ns1", "ns2", "ns3", "dns",
                    "db", "database", "sql", "backup", "files", "download"
                ]
            else:
                return {
                    "success": False,
                    "error": "wordlist_size deve essere 'small' o 'medium'"
                }
            
            found_subdomains = []
            failed_subdomains = []
            
            for subdomain in subdomains:
                full_domain = f"{subdomain}.{domain}"
                try:
                    # Prova risoluzione DNS
                    ip = socket.gethostbyname(full_domain)
                    
                    # Prova connessione HTTP/HTTPS
                    ports_to_check = [80, 443]
                    accessible_ports = []
                    
                    for port in ports_to_check:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        try:
                            result = sock.connect_ex((full_domain, port))
                            if result == 0:
                                accessible_ports.append(port)
                        except:
                            pass
                        finally:
                            sock.close()
                    
                    found_subdomains.append({
                        "subdomain": full_domain,
                        "ip_address": ip,
                        "accessible_ports": accessible_ports,
                        "has_web_service": bool(accessible_ports)
                    })
                    
                except socket.gaierror:
                    # Subdomain non esiste
                    failed_subdomains.append(full_domain)
                except Exception as e:
                    failed_subdomains.append(f"{full_domain} (error: {str(e)})")
                
                # Piccola pausa per non sovraccaricare
                time.sleep(0.1)
            
            return {
                "domain": domain,
                "wordlist_size": wordlist_size,
                "total_checked": len(subdomains),
                "found_subdomains": found_subdomains,
                "total_found": len(found_subdomains),
                "failed_subdomains": failed_subdomains[:10],  # Limita output
                "success_rate": round((len(found_subdomains) / len(subdomains)) * 100, 2)
            }
            
        except Exception as e:
            return {
                "domain": domain,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def grab_service_banner(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
        """
        Ottiene il banner di un servizio per identificazione di versione.
        
        Args:
            host: L'hostname o IP del target
            port: La porta del servizio
            timeout: Timeout in secondi (default: 5)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            try:
                sock.connect((host, port))
                
                # Servizi comuni e le loro richieste
                service_probes = {
                    21: b"",  # FTP - banner automatico
                    22: b"",  # SSH - banner automatico  
                    23: b"",  # Telnet - banner automatico
                    25: b"EHLO test\r\n",  # SMTP
                    53: b"",  # DNS - non TCP di solito
                    80: b"HEAD / HTTP/1.0\r\n\r\n",  # HTTP
                    110: b"",  # POP3 - banner automatico
                    143: b"",  # IMAP - banner automatico
                    443: b"",  # HTTPS - richiede SSL
                    993: b"",  # IMAPS - richiede SSL
                    995: b"",  # POP3S - richiede SSL
                    3389: b"",  # RDP
                    5432: b"",  # PostgreSQL
                    3306: b""  # MySQL
                }
                
                probe = service_probes.get(port, b"")
                
                # Invia probe se necessario
                if probe:
                    sock.send(probe)
                
                # Leggi risposta
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                
                # Analisi del banner
                service_info = {
                    "detected_service": "Unknown",
                    "version": "Unknown",
                    "details": {}
                }
                
                # Pattern per riconoscimento servizi
                if port == 21 and "FTP" in banner:
                    service_info["detected_service"] = "FTP"
                    ftp_match = re.search(r'(\w+)\s+([\d\.]+)', banner)
                    if ftp_match:
                        service_info["version"] = ftp_match.group(2)
                        service_info["details"]["software"] = ftp_match.group(1)
                
                elif port == 22 and "SSH" in banner:
                    service_info["detected_service"] = "SSH"
                    ssh_match = re.search(r'SSH-([^\s]+)\s+([^\s]+)', banner)
                    if ssh_match:
                        service_info["version"] = ssh_match.group(1)
                        service_info["details"]["software"] = ssh_match.group(2)
                
                elif port == 25 and ("SMTP" in banner or "ESMTP" in banner):
                    service_info["detected_service"] = "SMTP"
                    smtp_match = re.search(r'(\w+)\s+([\d\.]+)', banner)
                    if smtp_match:
                        service_info["details"]["software"] = smtp_match.group(1)
                
                elif port == 80 and "HTTP" in banner:
                    service_info["detected_service"] = "HTTP"
                    server_match = re.search(r'Server:\s*([^\r\n]+)', banner)
                    if server_match:
                        service_info["details"]["server"] = server_match.group(1)
                
                return {
                    "host": host,
                    "port": port,
                    "success": True,
                    "banner": banner,
                    "banner_length": len(banner),
                    "service_info": service_info,
                    "response_time": f"{timeout}s max"
                }
                
            except socket.timeout:
                return {
                    "host": host,
                    "port": port,
                    "success": False,
                    "error": "Timeout durante connessione"
                }
            except ConnectionRefusedError:
                return {
                    "host": host,
                    "port": port,
                    "success": False,
                    "error": "Connessione rifiutata"
                }
            finally:
                sock.close()
                
        except Exception as e:
            return {
                "host": host,
                "port": port,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_certificate_chain(domain: str, port: int = 443) -> Dict[str, Any]:
        """
        Analizza in dettaglio la catena di certificati SSL/TLS.
        
        Args:
            domain: Il dominio da analizzare
            port: La porta SSL (default: 443)
        """
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    # Ottieni informazioni SSL
                    ssl_info = {
                        "protocol": ssock.version(),
                        "cipher": ssock.cipher(),
                        "compression": ssock.compression()
                    }
                    
                    # Ottieni certificato
                    cert = ssock.getpeercert()
                    cert_der = ssock.getpeercert(binary_form=True)
            
            # Analizza certificato principale
            from datetime import datetime
            
            subject = dict(x[0] for x in cert.get('subject', []))
            issuer = dict(x[0] for x in cert.get('issuer', []))
            
            # Date di validità
            not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            now = datetime.now()
            
            days_until_expiry = (not_after - now).days
            days_since_issued = (now - not_before).days
            
            # Subject Alternative Names
            san_list = []
            for extension in cert.get('subjectAltName', []):
                if extension[0] == 'DNS':
                    san_list.append(extension[1])
            
            # Analisi sicurezza
            security_analysis = {
                "key_size": "Unknown",
                "signature_algorithm": cert.get('signatureAlgorithm', 'Unknown'),
                "version": cert.get('version', 'Unknown'),
                "serial_number": cert.get('serialNumber', 'Unknown')
            }
            
            # Warnings e raccomandazioni
            warnings = []
            recommendations = []
            
            if days_until_expiry < 30:
                warnings.append(f"Certificato scade tra {days_until_expiry} giorni")
            if days_until_expiry < 0:
                warnings.append("Certificato scaduto")
            
            if ssl_info["protocol"] in ["TLSv1", "TLSv1.1"]:
                warnings.append(f"Protocollo {ssl_info['protocol']} deprecato")
                recommendations.append("Aggiorna a TLS 1.2 o 1.3")
            
            # Controlla dominio nel certificato
            domain_match = False
            if subject.get('commonName') == domain:
                domain_match = True
            elif domain in san_list:
                domain_match = True
            
            if not domain_match:
                warnings.append("Nome dominio non corrisponde al certificato")
            
            return {
                "domain": domain,
                "port": port,
                "ssl_info": ssl_info,
                "certificate": {
                    "subject": subject,
                    "issuer": issuer,
                    "valid_from": not_before.isoformat(),
                    "valid_until": not_after.isoformat(),
                    "days_until_expiry": days_until_expiry,
                    "days_since_issued": days_since_issued,
                    "subject_alt_names": san_list,
                    "domain_match": domain_match
                },
                "security_analysis": security_analysis,
                "warnings": warnings,
                "recommendations": recommendations,
                "certificate_pem_length": len(cert_der) if cert_der else 0
            }
            
        except ssl.SSLError as e:
            return {
                "domain": domain,
                "port": port,
                "success": False,
                "error": f"Errore SSL: {str(e)}"
            }
        except socket.timeout:
            return {
                "domain": domain,
                "port": port,
                "success": False,
                "error": "Timeout durante connessione SSL"
            }
        except Exception as e:
            return {
                "domain": domain,
                "port": port,
                "success": False,
                "error": str(e)
            }