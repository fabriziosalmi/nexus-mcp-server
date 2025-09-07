# -*- coding: utf-8 -*-
# tools/crypto_tools.py
import hashlib
import hmac
import secrets
import base64
import logging
import os
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
import re

# Try to import additional crypto libraries
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("Cryptography library not available - some advanced features disabled")

def register_tools(mcp):
    """Registra i tool crittografici avanzati con l'istanza del server MCP."""
    logging.info("🔐 Registrazione tool-set: Crypto Tools")

    @mcp.tool()
    def generate_hash(text: str, algorithm: str = "sha256") -> str:
        """
        Genera l'hash di un testo usando l'algoritmo specificato.

        Args:
            text: Il testo da cui generare l'hash.
            algorithm: L'algoritmo di hash (sha256, sha1, md5, sha512).
        """
        try:
            if algorithm not in ["sha256", "sha1", "md5", "sha512"]:
                return f"ERRORE: Algoritmo '{algorithm}' non supportato. Usa: sha256, sha1, md5, sha512"
            
            hash_func = getattr(hashlib, algorithm)
            result = hash_func(text.encode('utf-8')).hexdigest()
            return f"Hash {algorithm.upper()}: {result}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_hmac(message: str, secret_key: str, algorithm: str = "sha256") -> str:
        """
        Genera un HMAC (Hash-based Message Authentication Code).

        Args:
            message: Il messaggio da autenticare.
            secret_key: La chiave segreta per l'HMAC.
            algorithm: L'algoritmo di hash (sha256, sha1, md5, sha512).
        """
        try:
            if algorithm not in ["sha256", "sha1", "md5", "sha512"]:
                return f"ERRORE: Algoritmo '{algorithm}' non supportato. Usa: sha256, sha1, md5, sha512"
            
            hash_func = getattr(hashlib, algorithm)
            result = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hash_func
            ).hexdigest()
            return f"HMAC-{algorithm.upper()}: {result}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_random_token(length: int = 32, encoding: str = "hex") -> str:
        """
        Genera un token crittograficamente sicuro.

        Args:
            length: La lunghezza del token in bytes (default 32).
            encoding: Il tipo di encoding (hex, base64, urlsafe).
        """
        try:
            if length < 8 or length > 128:
                return "ERRORE: La lunghezza deve essere tra 8 e 128 bytes"
            
            random_bytes = secrets.token_bytes(length)
            
            if encoding == "hex":
                result = random_bytes.hex()
            elif encoding == "base64":
                result = base64.b64encode(random_bytes).decode('utf-8')
            elif encoding == "urlsafe":
                result = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
            else:
                return "ERRORE: Encoding deve essere 'hex', 'base64' o 'urlsafe'"
            
            return f"Token sicuro ({encoding}): {result}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def encrypt_text(plaintext: str, password: str, algorithm: str = "fernet") -> Dict[str, Any]:
        """
        Cripta testo usando algoritmi di cifratura simmetrica sicura.
        
        Args:
            plaintext: Testo da cifrare
            password: Password per la cifratura
            algorithm: Algoritmo (fernet, aes256_gcm)
        """
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                return {
                    "success": False,
                    "error": "Libreria cryptography non disponibile - installa con: pip install cryptography"
                }
            
            if len(password) < 8:
                return {
                    "success": False,
                    "error": "Password deve essere almeno 8 caratteri per sicurezza"
                }
            
            if algorithm == "fernet":
                # Deriva chiave dalla password
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                
                # Cripta con Fernet
                fernet = Fernet(key)
                encrypted_data = fernet.encrypt(plaintext.encode())
                
                # Combina salt + encrypted data
                result = salt + encrypted_data
                encoded_result = base64.b64encode(result).decode()
                
                return {
                    "success": True,
                    "algorithm": "Fernet (AES 128 CBC + HMAC SHA256)",
                    "encrypted_data": encoded_result,
                    "key_derivation": "PBKDF2-HMAC-SHA256 (100,000 iterazioni)",
                    "salt_length": len(salt),
                    "security_notes": [
                        "Cifratura autenticata",
                        "Salt casuale per ogni operazione",
                        "Protezione contro timing attacks"
                    ]
                }
            
            elif algorithm == "aes256_gcm":
                # AES-256-GCM con chiave derivata
                salt = os.urandom(16)
                nonce = os.urandom(12)  # GCM nonce
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,  # 256 bit key
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(password.encode())
                
                # Cripta con AES-GCM
                cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
                
                # Combina tutti i componenti
                result = salt + nonce + encryptor.tag + ciphertext
                encoded_result = base64.b64encode(result).decode()
                
                return {
                    "success": True,
                    "algorithm": "AES-256-GCM",
                    "encrypted_data": encoded_result,
                    "key_derivation": "PBKDF2-HMAC-SHA256 (100,000 iterazioni)",
                    "authentication": "GCM built-in authentication",
                    "components": {
                        "salt_length": 16,
                        "nonce_length": 12,
                        "tag_length": 16
                    }
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Algoritmo '{algorithm}' non supportato. Usa: fernet, aes256_gcm"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def decrypt_text(encrypted_data: str, password: str, algorithm: str = "fernet") -> Dict[str, Any]:
        """
        Decripta testo cifrato.
        
        Args:
            encrypted_data: Dati cifrati in base64
            password: Password per la decifratura
            algorithm: Algoritmo usato per cifrare
        """
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                return {
                    "success": False,
                    "error": "Libreria cryptography non disponibile"
                }
            
            # Decodifica base64
            try:
                encrypted_bytes = base64.b64decode(encrypted_data)
            except Exception:
                return {
                    "success": False,
                    "error": "Dati cifrati non validi (base64 malformato)"
                }
            
            if algorithm == "fernet":
                if len(encrypted_bytes) < 16:
                    return {
                        "success": False,
                        "error": "Dati cifrati troppo corti"
                    }
                
                # Estrae salt e dati cifrati
                salt = encrypted_bytes[:16]
                encrypted_payload = encrypted_bytes[16:]
                
                # Deriva la stessa chiave
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                
                # Decripta
                fernet = Fernet(key)
                decrypted_data = fernet.decrypt(encrypted_payload)
                
                return {
                    "success": True,
                    "decrypted_text": decrypted_data.decode(),
                    "algorithm": "Fernet"
                }
            
            elif algorithm == "aes256_gcm":
                if len(encrypted_bytes) < 44:  # 16+12+16 = header minimo
                    return {
                        "success": False,
                        "error": "Dati cifrati troppo corti per AES-GCM"
                    }
                
                # Estrae componenti
                salt = encrypted_bytes[:16]
                nonce = encrypted_bytes[16:28]
                tag = encrypted_bytes[28:44]
                ciphertext = encrypted_bytes[44:]
                
                # Deriva chiave
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(password.encode())
                
                # Decripta
                cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
                decryptor = cipher.decryptor()
                decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
                
                return {
                    "success": True,
                    "decrypted_text": decrypted_data.decode(),
                    "algorithm": "AES-256-GCM"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Algoritmo '{algorithm}' non supportato"
                }
        
        except Exception as e:
            # Non rivelare troppi dettagli per sicurezza
            return {
                "success": False,
                "error": "Decifratura fallita - password errata o dati corrotti"
            }

    @mcp.tool()
    def generate_keypair(key_type: str = "rsa", key_size: int = 2048) -> Dict[str, Any]:
        """
        Genera coppia di chiavi pubbliche/private.
        
        Args:
            key_type: Tipo di chiave (rsa)
            key_size: Dimensione chiave in bit (2048, 3072, 4096)
        """
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                return {
                    "success": False,
                    "error": "Libreria cryptography non disponibile"
                }
            
            if key_type.lower() != "rsa":
                return {
                    "success": False,
                    "error": "Solo chiavi RSA supportate attualmente"
                }
            
            if key_size not in [2048, 3072, 4096]:
                return {
                    "success": False,
                    "error": "Dimensioni supportate: 2048, 3072, 4096 bit"
                }
            
            # Genera chiave privata RSA
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
            )
            
            # Serializza chiave privata
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Ottieni chiave pubblica
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Calcola fingerprint
            public_der = public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            fingerprint = hashlib.sha256(public_der).hexdigest()
            
            return {
                "success": True,
                "key_type": f"RSA-{key_size}",
                "private_key": private_pem.decode(),
                "public_key": public_pem.decode(),
                "fingerprint": fingerprint,
                "key_info": {
                    "algorithm": "RSA",
                    "key_size": key_size,
                    "public_exponent": 65537,
                    "format": "PEM/PKCS8"
                },
                "security_warning": "Mantieni la chiave privata sicura e non condividerla mai"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def hash_password(password: str, algorithm: str = "pbkdf2", 
                     salt_length: int = 16, iterations: int = 100000) -> Dict[str, Any]:
        """
        Genera hash sicuro per password con salt.
        
        Args:
            password: Password da hashare
            algorithm: Algoritmo (pbkdf2, scrypt)
            salt_length: Lunghezza salt in byte
            iterations: Numero iterazioni (PBKDF2) o parametri (scrypt)
        """
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                return {
                    "success": False,
                    "error": "Libreria cryptography non disponibile"
                }
            
            if len(password) < 8:
                return {
                    "success": False,
                    "error": "Password deve essere almeno 8 caratteri"
                }
            
            if not 8 <= salt_length <= 32:
                return {
                    "success": False,
                    "error": "Salt length deve essere tra 8 e 32 byte"
                }
            
            salt = os.urandom(salt_length)
            
            if algorithm == "pbkdf2":
                if iterations < 10000:
                    return {
                        "success": False,
                        "error": "Iterazioni PBKDF2 devono essere almeno 10,000"
                    }
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=iterations,
                )
                password_hash = kdf.derive(password.encode())
                
                # Combina algoritmo + iterazioni + salt + hash
                stored_hash = f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(password_hash).decode()}"
                
                return {
                    "success": True,
                    "algorithm": "PBKDF2-HMAC-SHA256",
                    "password_hash": stored_hash,
                    "salt": base64.b64encode(salt).decode(),
                    "iterations": iterations,
                    "hash_length": len(password_hash),
                    "verification_info": "Usa verify_password per controllare"
                }
            
            elif algorithm == "scrypt":
                # Parametri scrypt sicuri
                n = 16384  # CPU/Memory cost
                r = 8      # Block size
                p = 1      # Parallelization
                
                kdf = Scrypt(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    n=n, r=r, p=p,
                )
                password_hash = kdf.derive(password.encode())
                
                stored_hash = f"scrypt${n}${r}${p}${base64.b64encode(salt).decode()}${base64.b64encode(password_hash).decode()}"
                
                return {
                    "success": True,
                    "algorithm": "scrypt",
                    "password_hash": stored_hash,
                    "salt": base64.b64encode(salt).decode(),
                    "parameters": {"n": n, "r": r, "p": p},
                    "security_level": "Alta resistenza a attacchi GPU/ASIC"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Algoritmo '{algorithm}' non supportato. Usa: pbkdf2, scrypt"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def verify_password(password: str, stored_hash: str) -> Dict[str, Any]:
        """
        Verifica password contro hash memorizzato.
        
        Args:
            password: Password da verificare
            stored_hash: Hash memorizzato (formato: algorithm$params$salt$hash)
        """
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                return {
                    "success": False,
                    "error": "Libreria cryptography non disponibile"
                }
            
            # Parse stored hash
            parts = stored_hash.split('$')
            if len(parts) < 4:
                return {
                    "success": False,
                    "error": "Formato hash non valido"
                }
            
            algorithm = parts[0]
            
            if algorithm == "pbkdf2_sha256":
                if len(parts) != 4:
                    return {"success": False, "error": "Formato PBKDF2 non valido"}
                
                iterations = int(parts[1])
                salt = base64.b64decode(parts[2])
                expected_hash = base64.b64decode(parts[3])
                
                # Deriva hash dalla password fornita
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=len(expected_hash),
                    salt=salt,
                    iterations=iterations,
                )
                derived_hash = kdf.derive(password.encode())
                
                # Confronto timing-safe
                is_valid = hmac.compare_digest(derived_hash, expected_hash)
                
                return {
                    "success": True,
                    "password_valid": is_valid,
                    "algorithm": "PBKDF2-HMAC-SHA256",
                    "iterations": iterations
                }
            
            elif algorithm == "scrypt":
                if len(parts) != 6:
                    return {"success": False, "error": "Formato scrypt non valido"}
                
                n = int(parts[1])
                r = int(parts[2])
                p = int(parts[3])
                salt = base64.b64decode(parts[4])
                expected_hash = base64.b64decode(parts[5])
                
                kdf = Scrypt(
                    algorithm=hashes.SHA256(),
                    length=len(expected_hash),
                    salt=salt,
                    n=n, r=r, p=p,
                )
                derived_hash = kdf.derive(password.encode())
                
                is_valid = hmac.compare_digest(derived_hash, expected_hash)
                
                return {
                    "success": True,
                    "password_valid": is_valid,
                    "algorithm": "scrypt",
                    "parameters": {"n": n, "r": r, "p": p}
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Algoritmo '{algorithm}' non supportato"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": "Verifica fallita - hash corrotto o formato non valido"
            }

    @mcp.tool()
    def analyze_entropy(data: str, analysis_type: str = "basic") -> Dict[str, Any]:
        """
        Analizza l'entropia e casualità di dati.
        
        Args:
            data: Dati da analizzare
            analysis_type: Tipo analisi (basic, detailed)
        """
        try:
            if not data:
                return {"success": False, "error": "Dati vuoti"}
            
            # Converte in byte se necessario
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Calcolo entropia Shannon
            entropy = _calculate_shannon_entropy(data_bytes)
            
            # Analisi caratteri
            char_analysis = _analyze_character_distribution(data)
            
            # Analisi pattern
            pattern_analysis = _analyze_patterns(data)
            
            result = {
                "success": True,
                "data_length": len(data),
                "shannon_entropy": round(entropy, 4),
                "max_entropy": 8.0,  # Per byte
                "entropy_percentage": round((entropy / 8.0) * 100, 2),
                "character_analysis": char_analysis,
                "randomness_quality": _classify_randomness(entropy, len(data))
            }
            
            if analysis_type == "detailed":
                result.update({
                    "pattern_analysis": pattern_analysis,
                    "compression_estimate": _estimate_compressibility(data),
                    "security_assessment": _assess_security_strength(data, entropy)
                })
            
            return result
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_secure_password(length: int = 16, include_symbols: bool = True,
                                exclude_ambiguous: bool = True) -> Dict[str, Any]:
        """
        Genera password crittograficamente sicura.
        
        Args:
            length: Lunghezza password (8-128)
            include_symbols: Include simboli speciali
            exclude_ambiguous: Esclude caratteri ambigui (0, O, l, 1, etc.)
        """
        try:
            if not 8 <= length <= 128:
                return {
                    "success": False,
                    "error": "Lunghezza deve essere tra 8 e 128 caratteri"
                }
            
            # Set di caratteri
            lowercase = "abcdefghijklmnopqrstuvwxyz"
            uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            digits = "0123456789"
            symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            # Rimuovi caratteri ambigui se richiesto
            if exclude_ambiguous:
                ambiguous = "0O1lI|"
                lowercase = lowercase.replace('l', '')
                uppercase = uppercase.replace('O', '').replace('I', '')
                digits = digits.replace('0', '').replace('1', '')
                symbols = symbols.replace('|', '')
            
            # Costruisci charset
            charset = lowercase + uppercase + digits
            if include_symbols:
                charset += symbols
            
            # Genera password con almeno un carattere da ogni categoria
            password_chars = []
            
            # Garantisci diversità
            password_chars.append(secrets.choice(lowercase))
            password_chars.append(secrets.choice(uppercase))
            password_chars.append(secrets.choice(digits.replace('0', '').replace('1', '') if exclude_ambiguous else digits))
            
            if include_symbols:
                symbol_set = symbols.replace('|', '') if exclude_ambiguous else symbols
                password_chars.append(secrets.choice(symbol_set))
            
            # Riempi con caratteri casuali
            remaining_length = length - len(password_chars)
            for _ in range(remaining_length):
                password_chars.append(secrets.choice(charset))
            
            # Mescola i caratteri
            for i in range(len(password_chars)):
                j = secrets.randbelow(len(password_chars))
                password_chars[i], password_chars[j] = password_chars[j], password_chars[i]
            
            password = ''.join(password_chars)
            
            # Analizza forza password
            strength_analysis = _analyze_password_strength(password)
            
            return {
                "success": True,
                "password": password,
                "length": len(password),
                "charset_size": len(charset),
                "entropy_bits": round(length * math.log2(len(charset)), 2),
                "strength_analysis": strength_analysis,
                "generation_params": {
                    "include_symbols": include_symbols,
                    "exclude_ambiguous": exclude_ambiguous,
                    "charset_categories": _get_charset_categories(password)
                }
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool() 
    def timing_safe_compare(value1: str, value2: str) -> Dict[str, Any]:
        """
        Confronto timing-safe di due valori per prevenire timing attacks.
        
        Args:
            value1: Primo valore
            value2: Secondo valore
        """
        try:
            # Usa compare_digest per confronto timing-safe
            are_equal = hmac.compare_digest(value1.encode(), value2.encode())
            
            return {
                "success": True,
                "values_equal": are_equal,
                "comparison_method": "HMAC timing-safe comparison",
                "security_note": "Protegge contro timing attacks"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions
    def _calculate_shannon_entropy(data: bytes) -> float:
        """Calcola entropia Shannon."""
        if not data:
            return 0
        
        # Conta frequenze
        frequency = {}
        for byte in data:
            frequency[byte] = frequency.get(byte, 0) + 1
        
        # Calcola entropia
        entropy = 0
        data_len = len(data)
        for count in frequency.values():
            probability = count / data_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy

    def _analyze_character_distribution(data: str) -> Dict[str, Any]:
        """Analizza distribuzione caratteri."""
        categories = {
            'lowercase': 0,
            'uppercase': 0, 
            'digits': 0,
            'symbols': 0,
            'whitespace': 0
        }
        
        for char in data:
            if char.islower():
                categories['lowercase'] += 1
            elif char.isupper():
                categories['uppercase'] += 1
            elif char.isdigit():
                categories['digits'] += 1
            elif char.isspace():
                categories['whitespace'] += 1
            else:
                categories['symbols'] += 1
        
        total = len(data)
        percentages = {k: round((v/total)*100, 2) if total > 0 else 0 
                      for k, v in categories.items()}
        
        return {
            "counts": categories,
            "percentages": percentages,
            "unique_chars": len(set(data)),
            "total_chars": total
        }

    def _classify_randomness(entropy: float, length: int) -> str:
        """Classifica qualità casualità."""
        entropy_ratio = entropy / 8.0  # Normalizza su 8 bit max
        
        if entropy_ratio > 0.95:
            return "Eccellente"
        elif entropy_ratio > 0.8:
            return "Buona"
        elif entropy_ratio > 0.6:
            return "Media"
        else:
            return "Scarsa"

    def _analyze_password_strength(password: str) -> Dict[str, Any]:
        """Analizza forza password."""
        score = 0
        feedback = []
        
        # Lunghezza
        if len(password) >= 12:
            score += 25
        elif len(password) >= 8:
            score += 15
        else:
            feedback.append("Password troppo corta")
        
        # Diversità caratteri
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)
        
        diversity_score = sum([has_lower, has_upper, has_digit, has_symbol])
        score += diversity_score * 15
        
        if diversity_score < 3:
            feedback.append("Usa mix di maiuscole, minuscole, numeri e simboli")
        
        # Pattern comuni
        if re.search(r'(.)\1{2,}', password):
            score -= 10
            feedback.append("Evita caratteri ripetuti")
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            score -= 15
            feedback.append("Evita sequenze numeriche")
        
        # Classifica forza
        if score >= 85:
            strength = "Molto forte"
        elif score >= 70:
            strength = "Forte"
        elif score >= 50:
            strength = "Media"
        elif score >= 30:
            strength = "Debole"
        else:
            strength = "Molto debole"
        
        return {
            "score": max(0, min(100, score)),
            "strength": strength,
            "feedback": feedback,
            "character_diversity": diversity_score
        }