# -*- coding: utf-8 -*-
# tools/security_tools.py
import secrets
import string
import hashlib
import hmac
import base64
import logging
import subprocess
import json
from typing import Dict, List, Optional, Any
import re

def register_tools(mcp):
    """Registra i tool di sicurezza con l'istanza del server MCP."""
    logging.info("🔒 Registrazione tool-set: Security Tools")

    @mcp.tool()
    def generate_secure_password(length: int = 16, include_symbols: bool = True, exclude_ambiguous: bool = True) -> Dict[str, Any]:
        """
        Genera una password sicura.
        
        Args:
            length: Lunghezza della password (default: 16)
            include_symbols: Include simboli speciali (default: True)
            exclude_ambiguous: Esclude caratteri ambigui come 0, O, l, 1 (default: True)
        """
        try:
            # Caratteri base
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase
            digits = string.digits
            symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            # Rimuovi caratteri ambigui se richiesto
            if exclude_ambiguous:
                lowercase = lowercase.replace('l', '').replace('o', '')
                uppercase = uppercase.replace('I', '').replace('O', '')
                digits = digits.replace('0', '').replace('1', '')
                symbols = symbols.replace('|', '').replace('l', '')
            
            # Costruisci il set di caratteri
            charset = lowercase + uppercase + digits
            if include_symbols:
                charset += symbols
            
            # Genera password
            password = ''.join(secrets.choice(charset) for _ in range(length))
            
            # Calcola forza password
            entropy = length * (len(charset) ** (1/length))
            strength = "Debole"
            if entropy > 50:
                strength = "Media"
            if entropy > 70:
                strength = "Forte"
            if entropy > 100:
                strength = "Molto Forte"
            
            return {
                "password": password,
                "length": length,
                "charset_size": len(charset),
                "entropy": round(entropy, 2),
                "strength": strength,
                "includes_symbols": include_symbols,
                "excludes_ambiguous": exclude_ambiguous
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def password_strength_check(password: str) -> Dict[str, Any]:
        """
        Analizza la forza di una password.
        
        Args:
            password: La password da analizzare
        """
        try:
            length = len(password)
            
            # Controlli caratteri
            has_lower = bool(re.search(r'[a-z]', password))
            has_upper = bool(re.search(r'[A-Z]', password))
            has_digit = bool(re.search(r'\d', password))
            has_symbol = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
            
            # Patterns comuni
            common_patterns = [
                r'123', r'abc', r'qwerty', r'password', r'admin',
                r'(.)\1{2,}',  # caratteri ripetuti
                r'(01|12|23|34|45|56|67|78|89|90)',  # sequenze numeriche
            ]
            
            pattern_matches = []
            for pattern in common_patterns:
                if re.search(pattern, password.lower()):
                    pattern_matches.append(pattern)
            
            # Calcola punteggio
            score = 0
            if length >= 8: score += 1
            if length >= 12: score += 1
            if length >= 16: score += 1
            if has_lower: score += 1
            if has_upper: score += 1
            if has_digit: score += 1
            if has_symbol: score += 1
            if not pattern_matches: score += 1
            
            strength_levels = {
                0: "Molto Debole",
                1: "Molto Debole", 
                2: "Debole",
                3: "Debole",
                4: "Media",
                5: "Media",
                6: "Forte",
                7: "Forte",
                8: "Molto Forte"
            }
            
            strength = strength_levels.get(score, "Molto Debole")
            
            suggestions = []
            if length < 12:
                suggestions.append("Usa almeno 12 caratteri")
            if not has_lower:
                suggestions.append("Aggiungi lettere minuscole")
            if not has_upper:
                suggestions.append("Aggiungi lettere maiuscole")
            if not has_digit:
                suggestions.append("Aggiungi numeri")
            if not has_symbol:
                suggestions.append("Aggiungi simboli speciali")
            if pattern_matches:
                suggestions.append("Evita pattern comuni e sequenze")
            
            return {
                "length": length,
                "strength": strength,
                "score": score,
                "max_score": 8,
                "has_lowercase": has_lower,
                "has_uppercase": has_upper,
                "has_digits": has_digit,
                "has_symbols": has_symbol,
                "common_patterns_found": len(pattern_matches),
                "suggestions": suggestions
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_api_key(length: int = 32, format_type: str = "hex") -> Dict[str, Any]:
        """
        Genera una chiave API sicura.
        
        Args:
            length: Lunghezza della chiave (default: 32)
            format_type: Formato (hex, base64, alphanumeric)
        """
        try:
            if format_type == "hex":
                key = secrets.token_hex(length // 2)
            elif format_type == "base64":
                key = base64.urlsafe_b64encode(secrets.token_bytes(length)).decode()[:length]
            elif format_type == "alphanumeric":
                charset = string.ascii_letters + string.digits
                key = ''.join(secrets.choice(charset) for _ in range(length))
            else:
                return {
                    "success": False,
                    "error": "Formato non supportato. Usa: hex, base64, alphanumeric"
                }
            
            return {
                "api_key": key,
                "length": len(key),
                "format": format_type,
                "entropy_bits": length * 4 if format_type == "hex" else length * 6
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def hash_file_content(content: str, algorithms: List[str] = ["sha256"]) -> Dict[str, Any]:
        """
        Calcola hash di contenuto per verifica integrità.
        
        Args:
            content: Il contenuto da hashare
            algorithms: Lista di algoritmi (md5, sha1, sha256, sha512)
        """
        try:
            supported_algos = ["md5", "sha1", "sha256", "sha512"]
            results = {}
            
            for algo in algorithms:
                if algo.lower() not in supported_algos:
                    continue
                
                hasher = hashlib.new(algo.lower())
                hasher.update(content.encode('utf-8'))
                results[algo] = hasher.hexdigest()
            
            return {
                "content_length": len(content),
                "hashes": results,
                "algorithms_used": list(results.keys())
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def jwt_decode_header(jwt_token: str) -> Dict[str, Any]:
        """
        Decodifica l'header di un token JWT (senza verifica).
        
        Args:
            jwt_token: Il token JWT da decodificare
        """
        try:
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return {
                    "success": False,
                    "error": "Formato JWT non valido"
                }
            
            # Decodifica header
            header_b64 = parts[0]
            # Aggiungi padding se necessario
            header_b64 += '=' * (4 - len(header_b64) % 4)
            
            header_json = base64.urlsafe_b64decode(header_b64).decode('utf-8')
            header = json.loads(header_json)
            
            # Decodifica payload (senza verifica)
            payload_b64 = parts[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            
            payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
            payload = json.loads(payload_json)
            
            return {
                "success": True,
                "header": header,
                "payload": payload,
                "signature_present": bool(parts[2]),
                "warning": "Token NON verificato - solo decodifica"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def check_common_ports(host: str) -> Dict[str, Any]:
        """
        Controlla porte comuni su un host per valutazione sicurezza.
        
        Args:
            host: L'hostname o IP da controllare
        """
        try:
            import socket
            
            common_ports = {
                21: "FTP",
                22: "SSH", 
                23: "Telnet",
                25: "SMTP",
                53: "DNS",
                80: "HTTP",
                110: "POP3",
                443: "HTTPS",
                993: "IMAPS",
                995: "POP3S",
                3389: "RDP",
                5432: "PostgreSQL",
                3306: "MySQL"
            }
            
            open_ports = {}
            security_warnings = []
            
            for port, service in common_ports.items():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                
                try:
                    result = sock.connect_ex((host, port))
                    if result == 0:
                        open_ports[port] = service
                        
                        # Avvisi di sicurezza
                        if port == 21:
                            security_warnings.append("FTP aperto - considera SFTP")
                        elif port == 23:
                            security_warnings.append("Telnet aperto - usa SSH invece")
                        elif port == 3389:
                            security_warnings.append("RDP esposto - verifica sicurezza")
                            
                except Exception:
                    pass
                finally:
                    sock.close()
            
            return {
                "host": host,
                "open_ports": open_ports,
                "total_open": len(open_ports),
                "security_warnings": security_warnings,
                "risk_level": "Alto" if security_warnings else "Basso"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def ssl_certificate_check(domain: str, port: int = 443) -> Dict[str, Any]:
        """
        Controlla informazioni certificato SSL.
        
        Args:
            domain: Il dominio da controllare
            port: La porta SSL (default: 443)
        """
        try:
            import ssl
            import socket
            from datetime import datetime
            
            context = ssl.create_default_context()
            
            with socket.create_connection((domain, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
            
            # Analizza certificato
            subject = dict(x[0] for x in cert['subject'])
            issuer = dict(x[0] for x in cert['issuer'])
            
            # Date
            not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            now = datetime.now()
            
            days_until_expiry = (not_after - now).days
            
            # Status
            status = "Valido"
            warnings = []
            
            if days_until_expiry < 30:
                warnings.append("Certificato scade entro 30 giorni")
                status = "In scadenza"
            if days_until_expiry < 0:
                warnings.append("Certificato scaduto")
                status = "Scaduto"
            
            return {
                "domain": domain,
                "port": port,
                "status": status,
                "subject": subject.get('commonName', 'N/A'),
                "issuer": issuer.get('organizationName', 'N/A'),
                "valid_from": not_before.isoformat(),
                "valid_until": not_after.isoformat(),
                "days_until_expiry": days_until_expiry,
                "warnings": warnings,
                "serial_number": cert.get('serialNumber', 'N/A')
            }
        except Exception as e:
            return {
                "domain": domain,
                "port": port,
                "success": False,
                "error": str(e)
            }