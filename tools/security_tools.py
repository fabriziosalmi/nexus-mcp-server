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
import time
from datetime import datetime, timedelta
import socket
import ssl

def register_tools(mcp):
    """Registra i tool di sicurezza con l'istanza del server MCP."""
    logging.info("🔒 Registrazione tool-set: Security Tools")

    @mcp.tool()
    def generate_secure_password(
        length: int = 16, 
        include_symbols: bool = True, 
        exclude_ambiguous: bool = True,
        password_type: str = "random",
        min_digits: int = 1,
        min_uppercase: int = 1,
        min_lowercase: int = 1,
        min_symbols: int = 1,
        custom_symbols: Optional[str] = None,
        avoid_patterns: bool = True
    ) -> Dict[str, Any]:
        """
        Genera una password sicura con opzioni avanzate di personalizzazione.
        
        Args:
            length: Lunghezza della password (default: 16, min: 4, max: 128)
            include_symbols: Include simboli speciali (default: True)
            exclude_ambiguous: Esclude caratteri ambigui come 0, O, l, 1, | (default: True)
            password_type: Tipo di password (random, passphrase, pin, hex) (default: random)
            min_digits: Numero minimo di cifre (default: 1)
            min_uppercase: Numero minimo di lettere maiuscole (default: 1)
            min_lowercase: Numero minimo di lettere minuscole (default: 1)
            min_symbols: Numero minimo di simboli (default: 1, se include_symbols=True)
            custom_symbols: Simboli personalizzati da usare invece di quelli predefiniti
            avoid_patterns: Evita pattern comuni e sequenze (default: True)
        """
        try:
            # Validazione parametri
            if length < 4:
                return {"success": False, "error": "La lunghezza minima è 4 caratteri"}
            if length > 128:
                return {"success": False, "error": "La lunghezza massima è 128 caratteri"}
            
            valid_types = ["random", "passphrase", "pin", "hex"]
            if password_type not in valid_types:
                return {"success": False, "error": f"Tipo password non valido. Usa: {', '.join(valid_types)}"}
            
            # Gestione tipi speciali di password
            if password_type == "pin":
                return _generate_pin(length)
            elif password_type == "hex":
                return _generate_hex_password(length)
            elif password_type == "passphrase":
                return _generate_passphrase(length)
            
            # Generazione password random avanzata
            # Definizione character sets
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase
            digits = string.digits
            
            # Simboli predefiniti o personalizzati
            if custom_symbols:
                symbols = custom_symbols
            else:
                symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?~`"
            
            # Rimuovi caratteri ambigui se richiesto
            if exclude_ambiguous:
                # Caratteri ambigui comuni: 0/O, 1/l/I, |/l, ecc.
                ambiguous_chars = "0O1lI|`~"
                lowercase = ''.join(c for c in lowercase if c not in ambiguous_chars)
                uppercase = ''.join(c for c in uppercase if c not in ambiguous_chars)
                digits = ''.join(c for c in digits if c not in ambiguous_chars)
                symbols = ''.join(c for c in symbols if c not in ambiguous_chars)
            
            # Costruisci character sets attivi
            active_charsets = []
            charset_names = []
            
            if min_lowercase > 0:
                active_charsets.append(lowercase)
                charset_names.append("lowercase")
            if min_uppercase > 0:
                active_charsets.append(uppercase)
                charset_names.append("uppercase")
            if min_digits > 0:
                active_charsets.append(digits)
                charset_names.append("digits")
            if include_symbols and min_symbols > 0:
                active_charsets.append(symbols)
                charset_names.append("symbols")
            
            # Verifica che i requisiti minimi siano soddisfacibili
            total_min_chars = min_lowercase + min_uppercase + min_digits + (min_symbols if include_symbols else 0)
            if total_min_chars > length:
                return {
                    "success": False, 
                    "error": f"I requisiti minimi ({total_min_chars}) superano la lunghezza richiesta ({length})"
                }
            
            # Genera password garantendo i requisiti minimi
            password_chars = []
            
            # Aggiungi caratteri obbligatori
            if min_lowercase > 0:
                password_chars.extend(secrets.choice(lowercase) for _ in range(min_lowercase))
            if min_uppercase > 0:
                password_chars.extend(secrets.choice(uppercase) for _ in range(min_uppercase))
            if min_digits > 0:
                password_chars.extend(secrets.choice(digits) for _ in range(min_digits))
            if include_symbols and min_symbols > 0:
                password_chars.extend(secrets.choice(symbols) for _ in range(min_symbols))
            
            # Completa con caratteri casuali dal set completo
            all_chars = lowercase + uppercase + digits + (symbols if include_symbols else "")
            remaining_length = length - len(password_chars)
            
            for _ in range(remaining_length):
                password_chars.append(secrets.choice(all_chars))
            
            # Mescola la password per evitare pattern prevedibili
            secrets.SystemRandom().shuffle(password_chars)
            password = ''.join(password_chars)
            
            # Verifica ed evita pattern comuni se richiesto
            if avoid_patterns:
                max_attempts = 10
                attempts = 0
                while _has_common_patterns(password) and attempts < max_attempts:
                    secrets.SystemRandom().shuffle(password_chars)
                    password = ''.join(password_chars)
                    attempts += 1
            
            # Calcola entropia corretta
            entropy_bits = length * (len(all_chars).bit_length() - 1)
            entropy_traditional = length * (len(all_chars) ** (1/length))  # Formula originale
            
            # Valutazione forza migliorata
            strength_score = _calculate_password_strength_score(password, length, len(all_chars))
            strength_levels = {
                0: "Molto Debole",
                1: "Debole", 
                2: "Mediocre",
                3: "Media",
                4: "Buona",
                5: "Forte",
                6: "Molto Forte",
                7: "Eccellente"
            }
            strength = strength_levels.get(min(strength_score, 7), "Molto Debole")
            
            # Analisi composizione password
            composition = _analyze_password_composition(password)
            
            # Tempo stimato per crack (semplificato)
            crack_time = _estimate_crack_time(entropy_bits)
            
            return {
                "success": True,
                "password": password,
                "length": length,
                "charset_size": len(all_chars),
                "entropy_bits": round(entropy_bits, 2),
                "entropy_traditional": round(entropy_traditional, 2),
                "strength": strength,
                "strength_score": strength_score,
                "composition": composition,
                "estimated_crack_time": crack_time,
                "requirements_met": {
                    "min_length": length >= 8,
                    "has_lowercase": composition["lowercase"] >= min_lowercase,
                    "has_uppercase": composition["uppercase"] >= min_uppercase,
                    "has_digits": composition["digits"] >= min_digits,
                    "has_symbols": composition["symbols"] >= min_symbols if include_symbols else True
                },
                "generation_info": {
                    "includes_symbols": include_symbols,
                    "excludes_ambiguous": exclude_ambiguous,
                    "password_type": password_type,
                    "active_charsets": charset_names,
                    "patterns_avoided": avoid_patterns
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Errore nella generazione password: {str(e)}"
            }

def _generate_pin(length: int) -> Dict[str, Any]:
    """Genera un PIN numerico sicuro."""
    if length < 4:
        return {"success": False, "error": "PIN deve essere almeno 4 cifre"}
    
    # Evita PIN comuni come 0000, 1234, ecc.
    pin = ''.join(secrets.choice(string.digits) for _ in range(length))
    
    # Verifica pattern comuni
    common_pins = ["0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999"]
    sequential = ["0123", "1234", "2345", "3456", "4567", "5678", "6789", "9876", "8765", "7654", "6543", "5432", "4321", "3210"]
    
    max_attempts = 20
    attempts = 0
    while (pin in common_pins or pin in sequential or pin[:4] in sequential) and attempts < max_attempts:
        pin = ''.join(secrets.choice(string.digits) for _ in range(length))
        attempts += 1
    
    return {
        "success": True,
        "password": pin,
        "length": length,
        "password_type": "pin",
        "strength": "Media" if length >= 6 else "Debole",
        "security_note": "Evita PIN comuni e sequenziali"
    }

def _generate_hex_password(length: int) -> Dict[str, Any]:
    """Genera una password esadecimale sicura."""
    hex_chars = "0123456789ABCDEF"
    password = ''.join(secrets.choice(hex_chars) for _ in range(length))
    
    entropy_bits = length * 4  # 4 bit per carattere hex
    
    return {
        "success": True,
        "password": password,
        "length": length,
        "password_type": "hex",
        "charset_size": 16,
        "entropy_bits": entropy_bits,
        "strength": "Forte" if entropy_bits >= 128 else "Media" if entropy_bits >= 64 else "Debole"
    }

def _generate_passphrase(word_count: int) -> Dict[str, Any]:
    """Genera una passphrase usando parole comuni."""
    # Lista di parole comuni italiane per passphrase
    common_words = [
        "casa", "mare", "sole", "luna", "terra", "fuoco", "acqua", "aria", "vento", "nube",
        "fiore", "albero", "monte", "valle", "fiume", "strada", "ponte", "porto", "isola", "campo",
        "libro", "penna", "carta", "tavolo", "sedia", "finestra", "porta", "chiave", "tempo", "vita",
        "amore", "pace", "gioia", "speranza", "sogno", "stella", "cielo", "mondo", "natura", "musica",
        "colore", "rosso", "blue", "verde", "giallo", "nero", "bianco", "grigio", "rosa", "viola"
    ]
    
    if word_count < 3:
        word_count = 3
    if word_count > 10:
        word_count = 10
    
    # Seleziona parole casuali
    selected_words = []
    for _ in range(word_count):
        word = secrets.choice(common_words)
        # Capitalizza casualmente
        if secrets.randbelow(2):
            word = word.capitalize()
        selected_words.append(word)
    
    # Aggiungi separatori e numeri casuali
    separators = ["-", "_", ".", "+", "="]
    passphrase_parts = []
    
    for i, word in enumerate(selected_words):
        passphrase_parts.append(word)
        if i < len(selected_words) - 1:  # Non aggiungere separatore dopo l'ultima parola
            if secrets.randbelow(3):  # 33% di possibilità di aggiungere numero
                passphrase_parts.append(str(secrets.randbelow(100)))
            passphrase_parts.append(secrets.choice(separators))
    
    # Aggiungi numero finale
    if secrets.randbelow(2):
        passphrase_parts.append(str(secrets.randbelow(1000)))
    
    passphrase = ''.join(passphrase_parts)
    
    return {
        "success": True,
        "password": passphrase,
        "length": len(passphrase),
        "word_count": word_count,
        "password_type": "passphrase",
        "strength": "Forte" if word_count >= 5 else "Media",
        "security_note": "Le passphrase sono facili da ricordare ma difficili da indovinare"
    }

def _has_common_patterns(password: str) -> bool:
    """Verifica se la password contiene pattern comuni."""
    # Pattern sequenziali
    sequential_patterns = [
        "123", "234", "345", "456", "567", "678", "789", "890",
        "abc", "bcd", "cde", "def", "efg", "fgh", "ghi", "hij",
        "qwe", "wer", "ert", "rty", "tyu", "yui", "uio", "iop",
        "asd", "sdf", "dfg", "fgh", "ghj", "hjk", "jkl",
        "zxc", "xcv", "cvb", "vbn", "bnm"
    ]
    
    password_lower = password.lower()
    
    # Verifica sequenze
    for pattern in sequential_patterns:
        if pattern in password_lower:
            return True
    
    # Verifica ripetizioni
    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            return True
    
    # Verifica pattern comuni
    common_patterns = ["password", "admin", "user", "test", "demo", "guest"]
    for pattern in common_patterns:
        if pattern in password_lower:
            return True
    
    return False

def _calculate_password_strength_score(password: str, length: int, charset_size: int) -> int:
    """Calcola un punteggio di forza della password (0-7)."""
    score = 0
    
    # Lunghezza
    if length >= 8: score += 1
    if length >= 12: score += 1
    if length >= 16: score += 1
    
    # Diversità caratteri
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)
    
    if has_lower: score += 1
    if has_upper: score += 1
    if has_digit: score += 1
    if has_symbol: score += 1
    
    # Penalità per pattern comuni
    if _has_common_patterns(password):
        score = max(0, score - 2)
    
    return min(score, 7)

def _analyze_password_composition(password: str) -> Dict[str, int]:
    """Analizza la composizione della password."""
    composition = {
        "lowercase": sum(1 for c in password if c.islower()),
        "uppercase": sum(1 for c in password if c.isupper()),
        "digits": sum(1 for c in password if c.isdigit()),
        "symbols": sum(1 for c in password if not c.isalnum()),
        "total": len(password)
    }
    return composition

def _estimate_crack_time(entropy_bits: float) -> str:
    """Stima il tempo per craccare la password."""
    # Ipotizza 1 miliardo di tentativi al secondo (GPU moderna)
    attempts_per_second = 1_000_000_000
    total_combinations = 2 ** entropy_bits
    
    # Tempo medio per craccare (metà delle combinazioni)
    seconds_to_crack = (total_combinations / 2) / attempts_per_second
    
    if seconds_to_crack < 60:
        return f"{seconds_to_crack:.1f} secondi"
    elif seconds_to_crack < 3600:
        return f"{seconds_to_crack/60:.1f} minuti"
    elif seconds_to_crack < 86400:
        return f"{seconds_to_crack/3600:.1f} ore"
    elif seconds_to_crack < 31536000:
        return f"{seconds_to_crack/86400:.1f} giorni"
    elif seconds_to_crack < 31536000000:
        return f"{seconds_to_crack/31536000:.1f} anni"
    else:
        return "Più di 1000 anni"

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

    @mcp.tool()
    def comprehensive_security_audit(target: str, scan_type: str = "basic") -> Dict[str, Any]:
        """
        Esegue un audit di sicurezza completo su un target.
        
        Args:
            target: Hostname/IP/URL da analizzare
            scan_type: Tipo di scan (basic, network, web, full)
        """
        try:
            audit_result = {
                "target": target,
                "scan_type": scan_type,
                "timestamp": datetime.now().isoformat(),
                "findings": [],
                "recommendations": [],
                "risk_score": 0
            }
            
            # Parse target
            if target.startswith(('http://', 'https://')):
                target_type = "web"
                domain = target.split('//')[1].split('/')[0].split(':')[0]
            elif '.' in target and not target.replace('.', '').isdigit():
                target_type = "domain"
                domain = target
            else:
                target_type = "ip"
                domain = target
            
            audit_result["target_type"] = target_type
            
            # Basic security checks
            if scan_type in ["basic", "full"]:
                # Port scan
                port_results = check_common_ports(domain)
                if port_results.get("open_ports"):
                    audit_result["port_scan"] = port_results
                    audit_result["risk_score"] += len(port_results["security_warnings"]) * 10
                
                # SSL check se applicabile
                if target_type == "web" and (target.startswith('https://') or ':443' in target):
                    ssl_results = ssl_certificate_check(domain)
                    if ssl_results.get("warnings"):
                        audit_result["ssl_analysis"] = ssl_results
                        audit_result["risk_score"] += len(ssl_results["warnings"]) * 15
            
            # Network security checks
            if scan_type in ["network", "full"]:
                network_analysis = analyze_network_security(domain)
                audit_result["network_analysis"] = network_analysis
                audit_result["risk_score"] += network_analysis.get("risk_points", 0)
            
            # Web security checks
            if scan_type in ["web", "full"] and target_type == "web":
                web_analysis = analyze_web_security(target)
                audit_result["web_analysis"] = web_analysis
                audit_result["risk_score"] += web_analysis.get("risk_points", 0)
            
            # Generate findings and recommendations
            audit_result["findings"] = generate_security_findings(audit_result)
            audit_result["recommendations"] = generate_security_recommendations(audit_result)
            
            # Risk level classification
            risk_level = "Low"
            if audit_result["risk_score"] > 50:
                risk_level = "Medium"
            if audit_result["risk_score"] > 100:
                risk_level = "High"
            if audit_result["risk_score"] > 200:
                risk_level = "Critical"
            
            audit_result["risk_level"] = risk_level
            
            return {
                "success": True,
                "audit_result": audit_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Security audit failed: {str(e)}"
            }

    @mcp.tool()
    def vulnerability_scanner(target: str, scan_depth: str = "surface") -> Dict[str, Any]:
        """
        Scanner vulnerabilità comuni.
        
        Args:
            target: Target da scansionare
            scan_depth: Profondità scan (surface, deep, aggressive)
        """
        try:
            vulnerabilities = {
                "target": target,
                "scan_depth": scan_depth,
                "vulnerabilities_found": [],
                "scan_timestamp": datetime.now().isoformat()
            }
            
            # Common vulnerability checks
            vuln_checks = [
                check_open_ports_vulnerability,
                check_ssl_vulnerabilities,
                check_dns_security,
                check_http_headers_security
            ]
            
            if scan_depth == "deep":
                vuln_checks.extend([
                    check_service_banners,
                    check_default_credentials
                ])
            
            if scan_depth == "aggressive":
                vuln_checks.extend([
                    check_directory_traversal,
                    check_sql_injection_indicators
                ])
            
            total_vulns = 0
            critical_vulns = 0
            
            for check_function in vuln_checks:
                try:
                    result = check_function(target)
                    if result.get("vulnerabilities"):
                        vulnerabilities["vulnerabilities_found"].extend(result["vulnerabilities"])
                        total_vulns += len(result["vulnerabilities"])
                        critical_vulns += len([v for v in result["vulnerabilities"] 
                                             if v.get("severity") == "Critical"])
                except Exception as e:
                    logging.warning(f"Vulnerability check failed: {str(e)}")
            
            # Risk assessment
            risk_score = total_vulns * 10 + critical_vulns * 25
            
            vulnerabilities.update({
                "total_vulnerabilities": total_vulns,
                "critical_vulnerabilities": critical_vulns,
                "risk_score": risk_score,
                "risk_level": "Critical" if critical_vulns > 0 else 
                             "High" if total_vulns > 5 else
                             "Medium" if total_vulns > 2 else "Low"
            })
            
            return {
                "success": True,
                "vulnerability_report": vulnerabilities
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Vulnerability scan failed: {str(e)}"
            }

    @mcp.tool()
    def encrypt_decrypt_data(data: str, operation: str, key: Optional[str] = None, algorithm: str = "aes") -> Dict[str, Any]:
        """
        Crittografia/decrittografia dati con algoritmi sicuri.
        
        Args:
            data: Dati da processare
            operation: 'encrypt' o 'decrypt'
            key: Chiave (se None, genera automaticamente)
            algorithm: Algoritmo (aes, fernet)
        """
        try:
            if algorithm == "fernet":
                from cryptography.fernet import Fernet
                
                if operation == "encrypt":
                    if not key:
                        key = Fernet.generate_key().decode()
                    else:
                        key = key.encode() if isinstance(key, str) else key
                    
                    f = Fernet(key)
                    encrypted_data = f.encrypt(data.encode()).decode()
                    
                    return {
                        "success": True,
                        "operation": "encrypt",
                        "algorithm": "fernet",
                        "encrypted_data": encrypted_data,
                        "key": key.decode() if isinstance(key, bytes) else key,
                        "note": "Store key securely - required for decryption"
                    }
                
                elif operation == "decrypt":
                    if not key:
                        return {
                            "success": False,
                            "error": "Key required for decryption"
                        }
                    
                    key = key.encode() if isinstance(key, str) else key
                    f = Fernet(key)
                    decrypted_data = f.decrypt(data.encode()).decode()
                    
                    return {
                        "success": True,
                        "operation": "decrypt",
                        "algorithm": "fernet",
                        "decrypted_data": decrypted_data
                    }
            
            elif algorithm == "base64":
                # Simple base64 encoding (not encryption)
                if operation == "encrypt":
                    encoded_data = base64.b64encode(data.encode()).decode()
                    return {
                        "success": True,
                        "operation": "encode",
                        "algorithm": "base64",
                        "encoded_data": encoded_data,
                        "note": "Base64 is encoding, not encryption"
                    }
                elif operation == "decrypt":
                    decoded_data = base64.b64decode(data.encode()).decode()
                    return {
                        "success": True,
                        "operation": "decode",
                        "algorithm": "base64",
                        "decoded_data": decoded_data
                    }
            
            return {
                "success": False,
                "error": f"Unsupported algorithm: {algorithm}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Encryption/decryption failed: {str(e)}"
            }

    @mcp.tool()
    def generate_secure_tokens(token_type: str, count: int = 1, options: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera vari tipi di token sicuri.
        
        Args:
            token_type: Tipo (session, csrf, api, uuid, otp)
            count: Numero di token da generare
            options: Opzioni aggiuntive (JSON string)
        """
        try:
            import uuid
            
            if count > 100:
                return {
                    "success": False,
                    "error": "Maximum 100 tokens per request"
                }
            
            # Parse options
            opts = {}
            if options:
                try:
                    opts = json.loads(options)
                except json.JSONDecodeError:
                    opts = {}
            
            tokens = []
            
            for _ in range(count):
                if token_type == "session":
                    token = secrets.token_urlsafe(32)
                    tokens.append({
                        "token": token,
                        "type": "session",
                        "length": len(token),
                        "expires_recommended": "30 minutes"
                    })
                
                elif token_type == "csrf":
                    token = secrets.token_hex(16)
                    tokens.append({
                        "token": token,
                        "type": "csrf",
                        "length": len(token),
                        "usage": "Include in forms and validate server-side"
                    })
                
                elif token_type == "api":
                    prefix = opts.get("prefix", "ak")
                    token = f"{prefix}_{secrets.token_urlsafe(24)}"
                    tokens.append({
                        "token": token,
                        "type": "api",
                        "prefix": prefix,
                        "security_note": "Store securely, rotate regularly"
                    })
                
                elif token_type == "uuid":
                    token = str(uuid.uuid4())
                    tokens.append({
                        "token": token,
                        "type": "uuid",
                        "version": 4,
                        "uniqueness": "Globally unique"
                    })
                
                elif token_type == "otp":
                    length = opts.get("length", 6)
                    if opts.get("numeric_only", True):
                        token = ''.join(secrets.choice(string.digits) for _ in range(length))
                    else:
                        charset = string.ascii_uppercase + string.digits
                        token = ''.join(secrets.choice(charset) for _ in range(length))
                    
                    tokens.append({
                        "token": token,
                        "type": "otp",
                        "length": length,
                        "expires_recommended": "5 minutes",
                        "single_use": True
                    })
                
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported token type: {token_type}"
                    }
            
            return {
                "success": True,
                "token_type": token_type,
                "count": count,
                "tokens": tokens,
                "generated_at": datetime.now().isoformat(),
                "security_recommendations": get_token_security_recommendations(token_type)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Token generation failed: {str(e)}"
            }

    @mcp.tool()
    def security_headers_analyzer(url: str) -> Dict[str, Any]:
        """
        Analizza gli header di sicurezza di un sito web.
        
        Args:
            url: URL da analizzare
        """
        try:
            import urllib.request
            import urllib.error
            
            # Prepare request
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Nexus-Security-Scanner/1.0')
            
            try:
                response = urllib.request.urlopen(req, timeout=10)
                headers = dict(response.headers)
                status_code = response.getcode()
            except urllib.error.HTTPError as e:
                headers = dict(e.headers)
                status_code = e.code
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to fetch headers: {str(e)}"
                }
            
            # Security headers to check
            security_headers = {
                'strict-transport-security': {
                    'name': 'HTTP Strict Transport Security (HSTS)',
                    'importance': 'High',
                    'description': 'Prevents protocol downgrade attacks'
                },
                'content-security-policy': {
                    'name': 'Content Security Policy (CSP)',
                    'importance': 'High',
                    'description': 'Prevents XSS and injection attacks'
                },
                'x-frame-options': {
                    'name': 'X-Frame-Options',
                    'importance': 'Medium',
                    'description': 'Prevents clickjacking attacks'
                },
                'x-content-type-options': {
                    'name': 'X-Content-Type-Options',
                    'importance': 'Medium',
                    'description': 'Prevents MIME type sniffing'
                },
                'referrer-policy': {
                    'name': 'Referrer Policy',
                    'importance': 'Medium',
                    'description': 'Controls referrer information'
                },
                'permissions-policy': {
                    'name': 'Permissions Policy',
                    'importance': 'Medium',
                    'description': 'Controls browser features'
                }
            }
            
            analysis = {
                "url": url,
                "status_code": status_code,
                "analysis_timestamp": datetime.now().isoformat(),
                "security_headers": {},
                "missing_headers": [],
                "security_score": 0
            }
            
            # Check each security header
            headers_lower = {k.lower(): v for k, v in headers.items()}
            
            for header_key, header_info in security_headers.items():
                if header_key in headers_lower:
                    analysis["security_headers"][header_key] = {
                        "present": True,
                        "value": headers_lower[header_key],
                        "name": header_info["name"],
                        "importance": header_info["importance"]
                    }
                    
                    # Score based on importance
                    if header_info["importance"] == "High":
                        analysis["security_score"] += 30
                    elif header_info["importance"] == "Medium":
                        analysis["security_score"] += 20
                else:
                    analysis["missing_headers"].append({
                        "header": header_key,
                        "name": header_info["name"],
                        "importance": header_info["importance"],
                        "description": header_info["description"]
                    })
            
            # Additional security checks
            security_issues = []
            
            # Check for information disclosure
            if 'server' in headers_lower:
                security_issues.append({
                    "issue": "Server header present",
                    "severity": "Low",
                    "description": "Server information disclosed"
                })
            
            if 'x-powered-by' in headers_lower:
                security_issues.append({
                    "issue": "X-Powered-By header present",
                    "severity": "Low", 
                    "description": "Technology stack disclosed"
                })
            
            # Check HTTPS
            if not url.startswith('https://'):
                security_issues.append({
                    "issue": "Non-HTTPS connection",
                    "severity": "High",
                    "description": "Unencrypted connection vulnerable to interception"
                })
                analysis["security_score"] -= 40
            
            analysis["security_issues"] = security_issues
            analysis["recommendations"] = generate_header_recommendations(analysis)
            
            # Security grade
            score = analysis["security_score"]
            if score >= 80:
                grade = "A"
            elif score >= 60:
                grade = "B"
            elif score >= 40:
                grade = "C"
            elif score >= 20:
                grade = "D"
            else:
                grade = "F"
            
            analysis["security_grade"] = grade
            analysis["max_score"] = 140
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Header analysis failed: {str(e)}"
            }

    @mcp.tool()
    def generate_security_report(data: str) -> Dict[str, Any]:
        """
        Genera un report di sicurezza completo basato sui dati forniti.
        
        Args:
            data: JSON string con risultati di vari scan di sicurezza
        """
        try:
            # Parse input data
            try:
                scan_data = json.loads(data)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON data provided"
                }
            
            report = {
                "report_id": secrets.token_hex(8),
                "generated_at": datetime.now().isoformat(),
                "executive_summary": {},
                "detailed_findings": [],
                "risk_assessment": {},
                "recommendations": []
            }
            
            # Analyze aggregated data
            total_issues = 0
            critical_issues = 0
            high_issues = 0
            medium_issues = 0
            low_issues = 0
            
            # Process different types of scan data
            for scan_type, scan_result in scan_data.items():
                if isinstance(scan_result, dict):
                    # Extract issues based on scan type
                    if scan_type == "port_scan":
                        issues = extract_port_scan_issues(scan_result)
                    elif scan_type == "ssl_analysis":
                        issues = extract_ssl_issues(scan_result)
                    elif scan_type == "vulnerability_scan":
                        issues = extract_vulnerability_issues(scan_result)
                    elif scan_type == "header_analysis":
                        issues = extract_header_issues(scan_result)
                    else:
                        issues = extract_generic_issues(scan_result)
                    
                    report["detailed_findings"].extend(issues)
                    
                    # Count by severity
                    for issue in issues:
                        severity = issue.get("severity", "Low")
                        total_issues += 1
                        if severity == "Critical":
                            critical_issues += 1
                        elif severity == "High":
                            high_issues += 1
                        elif severity == "Medium":
                            medium_issues += 1
                        else:
                            low_issues += 1
            
            # Executive summary
            report["executive_summary"] = {
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "medium_issues": medium_issues,
                "low_issues": low_issues,
                "overall_risk": calculate_overall_risk(critical_issues, high_issues, medium_issues, low_issues)
            }
            
            # Risk assessment
            risk_score = (critical_issues * 40) + (high_issues * 20) + (medium_issues * 10) + (low_issues * 5)
            
            report["risk_assessment"] = {
                "risk_score": risk_score,
                "risk_level": "Critical" if critical_issues > 0 else
                             "High" if high_issues > 2 else
                             "Medium" if medium_issues > 5 else "Low",
                "compliance_status": "Non-Compliant" if critical_issues > 0 or high_issues > 3 else "Compliant",
                "immediate_action_required": critical_issues > 0 or high_issues > 5
            }
            
            # Generate recommendations
            report["recommendations"] = generate_comprehensive_recommendations(report["detailed_findings"])
            
            return {
                "success": True,
                "security_report": report
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Report generation failed: {str(e)}"
            }

# Helper functions for the new security tools

def analyze_network_security(domain: str) -> Dict[str, Any]:
    """Analizza la sicurezza di rete."""
    try:
        analysis = {
            "domain": domain,
            "dns_analysis": {},
            "network_topology": {},
            "risk_points": 0
        }
        
        # DNS security checks
        try:
            import dns.resolver
            # Check for SPF, DMARC, DKIM records
            txt_records = dns.resolver.resolve(domain, 'TXT')
            has_spf = any('v=spf1' in str(record) for record in txt_records)
            has_dmarc = False
            
            try:
                dmarc_records = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
                has_dmarc = len(dmarc_records) > 0
            except:
                pass
            
            analysis["dns_analysis"] = {
                "spf_record": has_spf,
                "dmarc_record": has_dmarc
            }
            
            if not has_spf:
                analysis["risk_points"] += 10
            if not has_dmarc:
                analysis["risk_points"] += 15
                
        except:
            analysis["dns_analysis"] = {"error": "DNS analysis failed"}
        
        return analysis
        
    except Exception as e:
        return {"error": str(e), "risk_points": 0}

def analyze_web_security(url: str) -> Dict[str, Any]:
    """Analizza la sicurezza web."""
    try:
        analysis = {
            "url": url,
            "risk_points": 0
        }
        
        # Basic HTTP security checks
        if not url.startswith('https://'):
            analysis["http_security"] = {
                "https": False,
                "risk": "Unencrypted connection"
            }
            analysis["risk_points"] += 30
        else:
            analysis["http_security"] = {
                "https": True
            }
        
        return analysis
        
    except Exception as e:
        return {"error": str(e), "risk_points": 0}

def generate_security_findings(audit_result: Dict) -> List[Dict]:
    """Genera findings di sicurezza."""
    findings = []
    
    if "port_scan" in audit_result:
        for warning in audit_result["port_scan"].get("security_warnings", []):
            findings.append({
                "category": "Network Security",
                "severity": "Medium",
                "finding": warning,
                "impact": "Potential exposure of services"
            })
    
    if "ssl_analysis" in audit_result:
        for warning in audit_result["ssl_analysis"].get("warnings", []):
            findings.append({
                "category": "SSL/TLS Security",
                "severity": "High" if "scaduto" in warning.lower() else "Medium",
                "finding": warning,
                "impact": "Certificate issues affect trust"
            })
    
    return findings

def generate_security_recommendations(audit_result: Dict) -> List[str]:
    """Genera raccomandazioni di sicurezza."""
    recommendations = []
    
    if audit_result.get("risk_score", 0) > 50:
        recommendations.append("Implement immediate security measures")
    
    if "port_scan" in audit_result and audit_result["port_scan"].get("security_warnings"):
        recommendations.append("Review and secure exposed services")
    
    if "ssl_analysis" in audit_result and audit_result["ssl_analysis"].get("warnings"):
        recommendations.append("Update SSL certificates and configuration")
    
    recommendations.append("Conduct regular security assessments")
    recommendations.append("Implement monitoring and alerting")
    
    return recommendations

# Vulnerability check functions
def check_open_ports_vulnerability(target: str) -> Dict[str, Any]:
    """Check for vulnerable open ports."""
    try:
        result = check_common_ports(target)
        vulnerabilities = []
        
        for port, service in result.get("open_ports", {}).items():
            if port in [21, 23]:  # FTP, Telnet
                vulnerabilities.append({
                    "type": "Insecure Service",
                    "port": port,
                    "service": service,
                    "severity": "High",
                    "description": f"Insecure {service} service exposed"
                })
        
        return {"vulnerabilities": vulnerabilities}
    except:
        return {"vulnerabilities": []}

def check_ssl_vulnerabilities(target: str) -> Dict[str, Any]:
    """Check SSL/TLS vulnerabilities."""
    try:
        result = ssl_certificate_check(target)
        vulnerabilities = []
        
        if result.get("warnings"):
            for warning in result["warnings"]:
                vulnerabilities.append({
                    "type": "SSL/TLS Issue",
                    "severity": "High" if "scaduto" in warning.lower() else "Medium",
                    "description": warning
                })
        
        return {"vulnerabilities": vulnerabilities}
    except:
        return {"vulnerabilities": []}

def check_dns_security(target: str) -> Dict[str, Any]:
    """Check DNS security configuration."""
    return {"vulnerabilities": []}  # Placeholder

def check_http_headers_security(target: str) -> Dict[str, Any]:
    """Check HTTP security headers."""
    return {"vulnerabilities": []}  # Placeholder

def check_service_banners(target: str) -> Dict[str, Any]:
    """Check for information disclosure in service banners."""
    return {"vulnerabilities": []}  # Placeholder

def check_default_credentials(target: str) -> Dict[str, Any]:
    """Check for default credentials."""
    return {"vulnerabilities": []}  # Placeholder

def check_directory_traversal(target: str) -> Dict[str, Any]:
    """Check for directory traversal vulnerabilities."""
    return {"vulnerabilities": []}  # Placeholder

def check_sql_injection_indicators(target: str) -> Dict[str, Any]:
    """Check for SQL injection indicators."""
    return {"vulnerabilities": []}  # Placeholder

def get_token_security_recommendations(token_type: str) -> List[str]:
    """Get security recommendations for token types."""
    recommendations = {
        "session": [
            "Store in httpOnly, secure cookies",
            "Implement session timeout",
            "Regenerate on privilege changes"
        ],
        "csrf": [
            "Validate on all state-changing operations",
            "Use SameSite cookie attribute",
            "Implement double-submit pattern"
        ],
        "api": [
            "Use HTTPS only",
            "Implement rate limiting",
            "Rotate keys regularly"
        ],
        "otp": [
            "Implement attempt limiting",
            "Use secure delivery channel",
            "Set short expiration time"
        ]
    }
    
    return recommendations.get(token_type, ["Follow security best practices"])

def generate_header_recommendations(analysis: Dict) -> List[str]:
    """Generate recommendations for HTTP security headers."""
    recommendations = []
    
    for missing in analysis.get("missing_headers", []):
        if missing["importance"] == "High":
            recommendations.append(f"Implement {missing['name']} header - {missing['description']}")
    
    if analysis.get("security_score", 0) < 60:
        recommendations.append("Review and implement comprehensive security header policy")
    
    return recommendations

def extract_port_scan_issues(scan_result: Dict) -> List[Dict]:
    """Extract issues from port scan results."""
    issues = []
    
    for warning in scan_result.get("security_warnings", []):
        issues.append({
            "category": "Network Security",
            "severity": "Medium",
            "finding": warning,
            "source": "Port Scan"
        })
    
    return issues

def extract_ssl_issues(ssl_result: Dict) -> List[Dict]:
    """Extract issues from SSL analysis."""
    issues = []
    
    for warning in ssl_result.get("warnings", []):
        severity = "High" if "scaduto" in warning.lower() else "Medium"
        issues.append({
            "category": "SSL/TLS Security",
            "severity": severity,
            "finding": warning,
            "source": "SSL Analysis"
        })
    
    return issues

def extract_vulnerability_issues(vuln_result: Dict) -> List[Dict]:
    """Extract issues from vulnerability scan."""
    issues = []
    
    for vuln in vuln_result.get("vulnerabilities_found", []):
        issues.append({
            "category": "Vulnerability",
            "severity": vuln.get("severity", "Medium"),
            "finding": vuln.get("description", "Vulnerability detected"),
            "source": "Vulnerability Scan"
        })
    
    return issues

def extract_header_issues(header_result: Dict) -> List[Dict]:
    """Extract issues from header analysis."""
    issues = []
    
    for missing in header_result.get("analysis", {}).get("missing_headers", []):
        severity = "High" if missing["importance"] == "High" else "Medium"
        issues.append({
            "category": "Web Security",
            "severity": severity,
            "finding": f"Missing {missing['name']} header",
            "source": "Header Analysis"
        })
    
    return issues

def extract_generic_issues(scan_result: Dict) -> List[Dict]:
    """Extract issues from generic scan results."""
    issues = []
    
    # Generic extraction logic
    if isinstance(scan_result, dict):
        if scan_result.get("risk_level") in ["High", "Critical"]:
            issues.append({
                "category": "General Security",
                "severity": scan_result.get("risk_level", "Medium"),
                "finding": "High risk detected in scan",
                "source": "Generic Scan"
            })
    
    return issues

def calculate_overall_risk(critical: int, high: int, medium: int, low: int) -> str:
    """Calculate overall risk level."""
    if critical > 0:
        return "Critical"
    elif high > 2:
        return "High"
    elif high > 0 or medium > 5:
        return "Medium"
    else:
        return "Low"

def generate_comprehensive_recommendations(findings: List[Dict]) -> List[str]:
    """Generate comprehensive security recommendations."""
    recommendations = []
    
    # Category-based recommendations
    categories = set(finding.get("category", "") for finding in findings)
    
    if "Network Security" in categories:
        recommendations.append("Review and harden network security configuration")
    
    if "SSL/TLS Security" in categories:
        recommendations.append("Update SSL/TLS certificates and improve configuration")
    
    if "Web Security" in categories:
        recommendations.append("Implement proper HTTP security headers")
    
    if "Vulnerability" in categories:
        recommendations.append("Patch identified vulnerabilities immediately")
    
    # Severity-based recommendations
    critical_count = len([f for f in findings if f.get("severity") == "Critical"])
    high_count = len([f for f in findings if f.get("severity") == "High"])
    
    if critical_count > 0:
        recommendations.insert(0, "URGENT: Address critical security issues immediately")
    
    if high_count > 3:
        recommendations.append("Prioritize resolution of high-severity issues")
    
    recommendations.extend([
        "Implement regular security monitoring",
        "Conduct periodic security assessments",
        "Maintain security incident response plan"
    ])
    
    return recommendations