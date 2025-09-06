# -*- coding: utf-8 -*-
# tools/uuid_tools.py
import uuid
import secrets
import string
import logging

def register_tools(mcp):
    """Registra i tool per la generazione di UUID e ID con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: UUID/ID Generation Tools")

    @mcp.tool()
    def generate_uuid4() -> str:
        """
        Genera un UUID versione 4 (random).
        """
        return f"UUID4: {str(uuid.uuid4())}"

    @mcp.tool()
    def generate_uuid1() -> str:
        """
        Genera un UUID versione 1 (basato su timestamp e MAC address).
        """
        return f"UUID1: {str(uuid.uuid1())}"

    @mcp.tool()
    def generate_multiple_uuids(count: int = 5, version: int = 4) -> str:
        """
        Genera multipli UUID.

        Args:
            count: Il numero di UUID da generare (max 50).
            version: La versione UUID da usare (1 o 4).
        """
        if count < 1 or count > 50:
            return "ERRORE: Il numero deve essere tra 1 e 50"
        
        if version not in [1, 4]:
            return "ERRORE: La versione deve essere 1 o 4"
        
        uuids = []
        for i in range(count):
            if version == 1:
                uuids.append(str(uuid.uuid1()))
            else:
                uuids.append(str(uuid.uuid4()))
        
        result = f"Lista di {count} UUID versione {version}:\n"
        for i, uid in enumerate(uuids, 1):
            result += f"{i:2d}. {uid}\n"
        
        return result.strip()

    @mcp.tool()
    def generate_short_id(length: int = 8, use_uppercase: bool = False) -> str:
        """
        Genera un ID breve alfanumerico.

        Args:
            length: La lunghezza dell'ID (4-32 caratteri).
            use_uppercase: Se includere lettere maiuscole.
        """
        if length < 4 or length > 32:
            return "ERRORE: La lunghezza deve essere tra 4 e 32 caratteri"
        
        alphabet = string.ascii_lowercase + string.digits
        if use_uppercase:
            alphabet += string.ascii_uppercase
        
        short_id = ''.join(secrets.choice(alphabet) for _ in range(length))
        return f"Short ID: {short_id}"

    @mcp.tool()
    def generate_nanoid(length: int = 21, alphabet: str = "default") -> str:
        """
        Genera un Nano ID (alternativa agli UUID).

        Args:
            length: La lunghezza dell'ID (4-64 caratteri).
            alphabet: L'alfabeto da usare ("default", "numbers", "lowercase", "uppercase").
        """
        if length < 4 or length > 64:
            return "ERRORE: La lunghezza deve essere tra 4 e 64 caratteri"
        
        if alphabet == "default":
            chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
        elif alphabet == "numbers":
            chars = "0123456789"
        elif alphabet == "lowercase":
            chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        elif alphabet == "uppercase":
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        else:
            return "ERRORE: Alfabeto deve essere 'default', 'numbers', 'lowercase' o 'uppercase'"
        
        nanoid = ''.join(secrets.choice(chars) for _ in range(length))
        return f"Nano ID ({alphabet}): {nanoid}"

    @mcp.tool()
    def uuid_info(uuid_string: str) -> str:
        """
        Analizza e fornisce informazioni su un UUID.

        Args:
            uuid_string: L'UUID da analizzare.
        """
        try:
            parsed_uuid = uuid.UUID(uuid_string)
            
            info = f"""Analisi UUID: {uuid_string}
- Versione: {parsed_uuid.version}
- Variante: {parsed_uuid.variant}
- Formato hex: {parsed_uuid.hex}
- Formato int: {parsed_uuid.int}"""
            
            if parsed_uuid.version == 1:
                timestamp = (parsed_uuid.time - 0x01b21dd213814000) / 10000000
                import datetime
                dt = datetime.datetime.fromtimestamp(timestamp)
                info += f"\n- Timestamp (v1): {dt.strftime('%Y-%m-%d %H:%M:%S')}"
                info += f"\n- Node (MAC): {hex(parsed_uuid.node)}"
            
            return info
        except ValueError:
            return "ERRORE: UUID non valido"