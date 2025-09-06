# -*- coding: utf-8 -*-
# tools/encoding_tools.py
import base64
import urllib.parse
import html
import json
import logging

def register_tools(mcp):
    """Registra i tool di codifica/decodifica con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Encoding Tools")

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