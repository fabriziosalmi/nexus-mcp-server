# -*- coding: utf-8 -*-
# tools/crypto_tools.py
import hashlib
import hmac
import secrets
import base64
import logging

def register_tools(mcp):
    """Registra i tool crittografici con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Crypto Tools")

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