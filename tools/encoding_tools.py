# -*- coding: utf-8 -*-
# tools/encoding_tools.py
import base64
import urllib.parse
import html
import json
import logging
import hashlib
import hmac
import binascii
import gzip
import zlib
import quopri
import codecs
import csv
import io
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone

# Try to import additional libraries
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

def register_tools(mcp):
    """Registra i tool di codifica/decodifica avanzati con l'istanza del server MCP."""
    logging.info("🔧 Registrazione tool-set: Encoding Tools")

    @mcp.tool()
    def base64_encode(text: str) -> str:
        """
        Codifica un testo in Base64.

        Args:
            text: Il testo da codificare in Base64.
        """
        try:
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return f"Base64 codificato: {encoded}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def base64_decode(encoded_text: str) -> str:
        """
        Decodifica un testo da Base64.

        Args:
            encoded_text: Il testo codificato in Base64 da decodificare.
        """
        try:
            decoded = base64.b64decode(encoded_text.encode('utf-8')).decode('utf-8')
            return f"Base64 decodificato: {decoded}"
        except Exception as e:
            return f"ERRORE: Testo Base64 non valido - {str(e)}"

    @mcp.tool()
    def url_encode(text: str) -> str:
        """
        Codifica un testo per l'uso negli URL (percent encoding).

        Args:
            text: Il testo da codificare per URL.
        """
        try:
            encoded = urllib.parse.quote(text, safe='')
            return f"URL codificato: {encoded}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def url_decode(encoded_text: str) -> str:
        """
        Decodifica un testo da URL encoding.

        Args:
            encoded_text: Il testo codificato URL da decodificare.
        """
        try:
            decoded = urllib.parse.unquote(encoded_text)
            return f"URL decodificato: {decoded}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def html_escape(text: str) -> str:
        """
        Esegue l'escape dei caratteri HTML speciali.

        Args:
            text: Il testo di cui fare l'escape HTML.
        """
        try:
            escaped = html.escape(text, quote=True)
            return f"HTML escaped: {escaped}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def json_format(json_string: str, indent: int = 2) -> str:
        """
        Formatta e valida una stringa JSON.

        Args:
            json_string: La stringa JSON da formattare.
            indent: Il numero di spazi per l'indentazione (default 2).
        """
        try:
            parsed = json.loads(json_string)
            formatted = json.dumps(parsed, indent=indent, ensure_ascii=False, sort_keys=True)
            return f"JSON formattato:\n{formatted}"
        except json.JSONDecodeError as e:
            return f"ERRORE: JSON non valido - {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def hex_encode(text: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Codifica testo in formato esadecimale.
        
        Args:
            text: Testo da codificare
            encoding: Encoding del testo (utf-8, ascii, latin-1)
        """
        try:
            # Converte testo in bytes con encoding specificato
            text_bytes = text.encode(encoding)
            hex_encoded = text_bytes.hex()
            
            return {
                "success": True,
                "original_text": text,
                "hex_encoded": hex_encoded,
                "encoding_used": encoding,
                "byte_length": len(text_bytes),
                "hex_length": len(hex_encoded),
                "uppercase_hex": hex_encoded.upper(),
                "formatted_hex": " ".join(hex_encoded[i:i+2] for i in range(0, len(hex_encoded), 2))
            }
        except UnicodeEncodeError as e:
            return {"success": False, "error": f"Encoding error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def hex_decode(hex_string: str, target_encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Decodifica stringa esadecimale in testo.
        
        Args:
            hex_string: Stringa esadecimale da decodificare
            target_encoding: Encoding per il testo risultante
        """
        try:
            # Pulisce la stringa hex (rimuove spazi e caratteri non-hex)
            clean_hex = re.sub(r'[^0-9a-fA-F]', '', hex_string)
            
            if len(clean_hex) % 2 != 0:
                return {"success": False, "error": "Hex string length must be even"}
            
            # Converte hex in bytes
            hex_bytes = bytes.fromhex(clean_hex)
            
            # Decodifica in testo
            decoded_text = hex_bytes.decode(target_encoding)
            
            return {
                "success": True,
                "hex_input": hex_string,
                "cleaned_hex": clean_hex,
                "decoded_text": decoded_text,
                "target_encoding": target_encoding,
                "byte_length": len(hex_bytes),
                "text_length": len(decoded_text)
            }
        except ValueError as e:
            return {"success": False, "error": f"Invalid hex string: {str(e)}"}
        except UnicodeDecodeError as e:
            return {"success": False, "error": f"Decoding error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_hash(text: str, algorithm: str = "sha256", 
                     output_format: str = "hex") -> Dict[str, Any]:
        """
        Genera hash del testo usando vari algoritmi.
        
        Args:
            text: Testo da hashare
            algorithm: Algoritmo hash (md5, sha1, sha256, sha512, blake2b)
            output_format: Formato output (hex, base64, binary)
        """
        try:
            # Algoritmi supportati
            algorithms = {
                'md5': hashlib.md5,
                'sha1': hashlib.sha1,
                'sha256': hashlib.sha256,
                'sha512': hashlib.sha512,
                'sha224': hashlib.sha224,
                'sha384': hashlib.sha384,
                'blake2b': hashlib.blake2b,
                'blake2s': hashlib.blake2s
            }
            
            if algorithm not in algorithms:
                return {
                    "success": False,
                    "error": f"Unsupported algorithm. Available: {', '.join(algorithms.keys())}"
                }
            
            # Genera hash
            hash_obj = algorithms[algorithm]()
            hash_obj.update(text.encode('utf-8'))
            
            # Formatta output
            if output_format == "hex":
                hash_result = hash_obj.hexdigest()
            elif output_format == "base64":
                hash_result = base64.b64encode(hash_obj.digest()).decode('utf-8')
            elif output_format == "binary":
                hash_result = hash_obj.digest().hex()  # Hex representation of binary
            else:
                return {"success": False, "error": "Invalid output format. Use: hex, base64, binary"}
            
            return {
                "success": True,
                "original_text": text,
                "algorithm": algorithm,
                "output_format": output_format,
                "hash_result": hash_result,
                "hash_length": len(hash_result),
                "digest_size": hash_obj.digest_size,
                "is_secure": algorithm not in ['md5', 'sha1']  # Security advisory
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_hmac(message: str, secret_key: str, algorithm: str = "sha256") -> Dict[str, Any]:
        """
        Genera HMAC (Hash-based Message Authentication Code).
        
        Args:
            message: Messaggio da autenticare
            secret_key: Chiave segreta
            algorithm: Algoritmo hash per HMAC
        """
        try:
            # Algoritmi supportati per HMAC
            algorithms = {
                'md5': hashlib.md5,
                'sha1': hashlib.sha1,
                'sha256': hashlib.sha256,
                'sha512': hashlib.sha512,
                'sha224': hashlib.sha224,
                'sha384': hashlib.sha384
            }
            
            if algorithm not in algorithms:
                return {
                    "success": False,
                    "error": f"Unsupported HMAC algorithm. Available: {', '.join(algorithms.keys())}"
                }
            
            # Genera HMAC
            hmac_obj = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                algorithms[algorithm]
            )
            
            hmac_hex = hmac_obj.hexdigest()
            hmac_base64 = base64.b64encode(hmac_obj.digest()).decode('utf-8')
            
            return {
                "success": True,
                "message": message,
                "algorithm": f"HMAC-{algorithm.upper()}",
                "hmac_hex": hmac_hex,
                "hmac_base64": hmac_base64,
                "digest_size": hmac_obj.digest_size,
                "security_note": "Keep secret key secure"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def compress_data(data: str, algorithm: str = "gzip", 
                     compression_level: int = 6) -> Dict[str, Any]:
        """
        Comprime dati usando vari algoritmi.
        
        Args:
            data: Dati da comprimere
            algorithm: Algoritmo compressione (gzip, zlib, deflate)
            compression_level: Livello compressione (1-9)
        """
        try:
            if not 1 <= compression_level <= 9:
                return {"success": False, "error": "Compression level must be between 1 and 9"}
            
            data_bytes = data.encode('utf-8')
            original_size = len(data_bytes)
            
            if algorithm == "gzip":
                compressed = gzip.compress(data_bytes, compresslevel=compression_level)
            elif algorithm == "zlib":
                compressed = zlib.compress(data_bytes, level=compression_level)
            elif algorithm == "deflate":
                compressed = zlib.compress(data_bytes, level=compression_level)[2:-4]  # Remove zlib header/trailer
            else:
                return {"success": False, "error": "Unsupported algorithm. Use: gzip, zlib, deflate"}
            
            compressed_size = len(compressed)
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            # Encode compressed data as base64 for safe transport
            compressed_b64 = base64.b64encode(compressed).decode('utf-8')
            
            return {
                "success": True,
                "algorithm": algorithm,
                "compression_level": compression_level,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": round(compression_ratio, 2),
                "size_reduction": original_size - compressed_size,
                "compressed_data_b64": compressed_b64,
                "efficiency": "Good" if compression_ratio > 50 else "Fair" if compression_ratio > 20 else "Poor"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def decompress_data(compressed_data_b64: str, algorithm: str = "gzip") -> Dict[str, Any]:
        """
        Decomprime dati compressi.
        
        Args:
            compressed_data_b64: Dati compressi in base64
            algorithm: Algoritmo usato per comprimere
        """
        try:
            # Decodifica base64
            compressed_bytes = base64.b64decode(compressed_data_b64)
            
            if algorithm == "gzip":
                decompressed = gzip.decompress(compressed_bytes)
            elif algorithm == "zlib":
                decompressed = zlib.decompress(compressed_bytes)
            elif algorithm == "deflate":
                decompressed = zlib.decompress(compressed_bytes, -zlib.MAX_WBITS)
            else:
                return {"success": False, "error": "Unsupported algorithm. Use: gzip, zlib, deflate"}
            
            # Decodifica in testo UTF-8
            decompressed_text = decompressed.decode('utf-8')
            
            return {
                "success": True,
                "algorithm": algorithm,
                "compressed_size": len(compressed_bytes),
                "decompressed_size": len(decompressed),
                "decompressed_text": decompressed_text,
                "expansion_ratio": round(len(decompressed) / len(compressed_bytes), 2)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def encode_jwt(payload: Dict[str, Any], secret_key: str, 
                  algorithm: str = "HS256", expires_in: int = 3600) -> Dict[str, Any]:
        """
        Codifica JWT token.
        
        Args:
            payload: Payload del JWT
            secret_key: Chiave segreta per firmare
            algorithm: Algoritmo firma (HS256, HS512)
            expires_in: Scadenza in secondi
        """
        try:
            if not JWT_AVAILABLE:
                return {
                    "success": False,
                    "error": "JWT library not available. Install with: pip install PyJWT"
                }
            
            # Aggiunge timestamp di scadenza
            if expires_in > 0:
                payload_copy = payload.copy()
                payload_copy['exp'] = datetime.now(timezone.utc).timestamp() + expires_in
                payload_copy['iat'] = datetime.now(timezone.utc).timestamp()
            else:
                payload_copy = payload
            
            # Genera JWT
            token = jwt.encode(payload_copy, secret_key, algorithm=algorithm)
            
            # Decodifica header per info
            header = jwt.get_unverified_header(token)
            
            return {
                "success": True,
                "jwt_token": token,
                "algorithm": algorithm,
                "header": header,
                "payload": payload_copy,
                "expires_in": expires_in,
                "token_length": len(token),
                "security_note": "Keep secret key secure and use HTTPS"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def decode_jwt(token: str, secret_key: str = "", verify: bool = True) -> Dict[str, Any]:
        """
        Decodifica JWT token.
        
        Args:
            token: JWT token da decodificare
            secret_key: Chiave segreta per verifica (vuota per skip verifica)
            verify: Se verificare la firma
        """
        try:
            if not JWT_AVAILABLE:
                return {
                    "success": False,
                    "error": "JWT library not available. Install with: pip install PyJWT"
                }
            
            # Estrae header senza verifica
            header = jwt.get_unverified_header(token)
            
            if verify and secret_key:
                # Decodifica con verifica
                payload = jwt.decode(token, secret_key, algorithms=[header.get('alg', 'HS256')])
                verified = True
            else:
                # Decodifica senza verifica (UNSAFE per produzione)
                payload = jwt.decode(token, options={"verify_signature": False})
                verified = False
            
            # Controlla scadenza
            is_expired = False
            if 'exp' in payload:
                exp_timestamp = payload['exp']
                current_timestamp = datetime.now(timezone.utc).timestamp()
                is_expired = current_timestamp > exp_timestamp
            
            return {
                "success": True,
                "header": header,
                "payload": payload,
                "verified": verified,
                "is_expired": is_expired,
                "algorithm": header.get('alg', 'Unknown'),
                "issued_at": payload.get('iat'),
                "expires_at": payload.get('exp'),
                "security_warning": "Token decoded without verification" if not verified else None
            }
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token has expired"}
        except jwt.InvalidTokenError as e:
            return {"success": False, "error": f"Invalid token: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def encode_quoted_printable(text: str) -> Dict[str, Any]:
        """
        Codifica testo in Quoted-Printable (RFC 2045).
        
        Args:
            text: Testo da codificare
        """
        try:
            encoded = quopri.encodestring(text.encode('utf-8')).decode('ascii')
            
            # Statistiche
            original_length = len(text.encode('utf-8'))
            encoded_length = len(encoded)
            overhead = ((encoded_length - original_length) / original_length * 100) if original_length > 0 else 0
            
            return {
                "success": True,
                "original_text": text,
                "quoted_printable": encoded,
                "original_length": original_length,
                "encoded_length": encoded_length,
                "overhead_percentage": round(overhead, 2),
                "is_efficient": overhead < 50
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def decode_quoted_printable(encoded_text: str) -> Dict[str, Any]:
        """
        Decodifica testo Quoted-Printable.
        
        Args:
            encoded_text: Testo Quoted-Printable da decodificare
        """
        try:
            decoded_bytes = quopri.decodestring(encoded_text.encode('ascii'))
            decoded_text = decoded_bytes.decode('utf-8')
            
            return {
                "success": True,
                "encoded_input": encoded_text,
                "decoded_text": decoded_text,
                "encoded_length": len(encoded_text),
                "decoded_length": len(decoded_text)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def convert_character_encoding(text: str, from_encoding: str, 
                                 to_encoding: str) -> Dict[str, Any]:
        """
        Converte testo tra diversi encoding di caratteri.
        
        Args:
            text: Testo da convertire
            from_encoding: Encoding sorgente
            to_encoding: Encoding destinazione
        """
        try:
            # Lista encoding supportati
            supported_encodings = [
                'utf-8', 'utf-16', 'utf-32', 'ascii', 'latin-1', 'iso-8859-1',
                'cp1252', 'cp1251', 'koi8-r', 'gb2312', 'big5', 'shift_jis'
            ]
            
            if from_encoding not in supported_encodings:
                return {
                    "success": False,
                    "error": f"Unsupported source encoding. Supported: {', '.join(supported_encodings)}"
                }
            
            if to_encoding not in supported_encodings:
                return {
                    "success": False,
                    "error": f"Unsupported target encoding. Supported: {', '.join(supported_encodings)}"
                }
            
            # Se input è già stringa, encode con from_encoding poi decode con to_encoding
            if from_encoding == 'utf-8':
                # Assumi che il testo sia già in UTF-8
                intermediate_bytes = text.encode('utf-8')
            else:
                # Prova a decodificare da from_encoding (assumendo input come bytes-like)
                intermediate_bytes = text.encode('latin-1').decode(from_encoding).encode('utf-8')
            
            # Converte a target encoding
            converted_text = intermediate_bytes.decode('utf-8').encode(to_encoding, errors='replace').decode(to_encoding)
            
            return {
                "success": True,
                "original_text": text,
                "from_encoding": from_encoding,
                "to_encoding": to_encoding,
                "converted_text": converted_text,
                "original_length": len(text),
                "converted_length": len(converted_text),
                "conversion_info": f"Converted from {from_encoding} to {to_encoding}"
            }
        except UnicodeError as e:
            return {"success": False, "error": f"Encoding conversion error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def format_csv_data(data: List[List[str]], delimiter: str = ",", 
                       quote_char: str = '"', escape_newlines: bool = True) -> Dict[str, Any]:
        """
        Formatta dati in CSV con escape appropriato.
        
        Args:
            data: Dati come lista di liste
            delimiter: Delimitatore CSV
            quote_char: Carattere quote
            escape_newlines: Se fare escape dei newline
        """
        try:
            if not data:
                return {"success": False, "error": "No data provided"}
            
            # Crea CSV in memoria
            output = io.StringIO()
            writer = csv.writer(output, delimiter=delimiter, quotechar=quote_char, 
                              quoting=csv.QUOTE_MINIMAL)
            
            processed_data = []
            for row in data:
                if escape_newlines:
                    processed_row = [str(cell).replace('\n', '\\n').replace('\r', '\\r') for cell in row]
                else:
                    processed_row = [str(cell) for cell in row]
                processed_data.append(processed_row)
                writer.writerow(processed_row)
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                "success": True,
                "csv_content": csv_content,
                "row_count": len(data),
                "column_count": len(data[0]) if data else 0,
                "delimiter": delimiter,
                "quote_char": quote_char,
                "total_characters": len(csv_content),
                "newlines_escaped": escape_newlines
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_encoding(data: str) -> Dict[str, Any]:
        """
        Analizza e rileva encoding di dati testuali.
        
        Args:
            data: Dati da analizzare
        """
        try:
            analysis = {
                "success": True,
                "data_length": len(data),
                "character_analysis": {},
                "encoding_detection": {},
                "recommendations": []
            }
            
            # Analisi caratteri
            ascii_count = sum(1 for c in data if ord(c) < 128)
            extended_ascii_count = sum(1 for c in data if 128 <= ord(c) < 256)
            unicode_count = sum(1 for c in data if ord(c) >= 256)
            
            analysis["character_analysis"] = {
                "ascii_chars": ascii_count,
                "extended_ascii_chars": extended_ascii_count,
                "unicode_chars": unicode_count,
                "ascii_percentage": round((ascii_count / len(data)) * 100, 2) if data else 0,
                "max_codepoint": max(ord(c) for c in data) if data else 0,
                "min_codepoint": min(ord(c) for c in data) if data else 0
            }
            
            # Rilevamento encoding probabile
            if unicode_count > 0:
                likely_encoding = "utf-8"
                confidence = "high"
            elif extended_ascii_count > 0:
                likely_encoding = "latin-1"
                confidence = "medium"
            else:
                likely_encoding = "ascii"
                confidence = "high"
            
            analysis["encoding_detection"] = {
                "likely_encoding": likely_encoding,
                "confidence": confidence,
                "requires_unicode": unicode_count > 0,
                "safe_for_ascii": unicode_count == 0 and extended_ascii_count == 0
            }
            
            # Raccomandazioni
            if unicode_count > 0:
                analysis["recommendations"].append("Use UTF-8 encoding for Unicode characters")
            
            if extended_ascii_count > len(data) * 0.1:
                analysis["recommendations"].append("Consider UTF-8 instead of extended ASCII")
            
            if len(data) > 10000:
                analysis["recommendations"].append("Consider compression for large text data")
            
            return analysis
        except Exception as e:
            return {"success": False, "error": str(e)}