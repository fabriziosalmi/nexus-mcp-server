# -*- coding: utf-8 -*-
# tools/string_tools.py
import re
import textwrap
import logging

def register_tools(mcp):
    """Registra i tool di manipolazione stringhe con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: String Manipulation Tools")

    @mcp.tool()
    def string_case_convert(text: str, case_type: str) -> str:
        """
        Converte una stringa in diversi formati di case.

        Args:
            text: La stringa da convertire.
            case_type: Il tipo di conversione (upper, lower, title, sentence, camel, snake, kebab).
        """
        if not text:
            return "ERRORE: Testo vuoto"
        
        if case_type == "upper":
            return f"MAIUSCOLO: {text.upper()}"
        elif case_type == "lower":
            return f"minuscolo: {text.lower()}"
        elif case_type == "title":
            return f"Title Case: {text.title()}"
        elif case_type == "sentence":
            return f"Sentence case: {text.capitalize()}"
        elif case_type == "camel":
            words = re.sub(r'[^\w\s]', ' ', text).split()
            camel = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
            return f"camelCase: {camel}"
        elif case_type == "snake":
            snake = re.sub(r'[^\w\s]', '', text).replace(' ', '_').lower()
            return f"snake_case: {snake}"
        elif case_type == "kebab":
            kebab = re.sub(r'[^\w\s]', '', text).replace(' ', '-').lower()
            return f"kebab-case: {kebab}"
        else:
            return "ERRORE: Tipo non supportato. Usa: upper, lower, title, sentence, camel, snake, kebab"

    @mcp.tool()
    def string_stats(text: str) -> str:
        """
        Fornisce statistiche dettagliate su una stringa.

        Args:
            text: La stringa da analizzare.
        """
        if not text:
            return "ERRORE: Testo vuoto"
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return f"""Statistiche stringa:
- Caratteri totali: {len(text)}
- Caratteri (no spazi): {len(text.replace(' ', ''))}
- Parole: {len(words)}
- Frasi: {len(sentences)}
- Linee: {len(text.splitlines())}
- Lettere: {sum(1 for c in text if c.isalpha())}
- Numeri: {sum(1 for c in text if c.isdigit())}
- Spazi: {text.count(' ')}
- Caratteri speciali: {sum(1 for c in text if not c.isalnum() and not c.isspace())}"""

    @mcp.tool()
    def string_clean(text: str, operation: str) -> str:
        """
        Pulisce e normalizza una stringa.

        Args:
            text: La stringa da pulire.
            operation: Il tipo di pulizia (trim, normalize_spaces, remove_special, letters_only, numbers_only).
        """
        if not text:
            return "ERRORE: Testo vuoto"
        
        if operation == "trim":
            result = text.strip()
            return f"Trimmed: '{result}'"
        elif operation == "normalize_spaces":
            result = re.sub(r'\s+', ' ', text.strip())
            return f"Spazi normalizzati: '{result}'"
        elif operation == "remove_special":
            result = re.sub(r'[^\w\s]', '', text)
            return f"Caratteri speciali rimossi: '{result}'"
        elif operation == "letters_only":
            result = re.sub(r'[^a-zA-Z\s]', '', text)
            return f"Solo lettere: '{result}'"
        elif operation == "numbers_only":
            result = re.sub(r'[^\d\s]', '', text)
            return f"Solo numeri: '{result}'"
        else:
            return "ERRORE: Operazione non supportata. Usa: trim, normalize_spaces, remove_special, letters_only, numbers_only"

    @mcp.tool()
    def string_wrap(text: str, width: int = 80, break_long_words: bool = True) -> str:
        """
        Avvolge il testo a una larghezza specificata.

        Args:
            text: Il testo da avvolgere.
            width: La larghezza massima delle linee (10-200).
            break_long_words: Se spezzare le parole lunghe.
        """
        if not text:
            return "ERRORE: Testo vuoto"
        
        if width < 10 or width > 200:
            return "ERRORE: La larghezza deve essere tra 10 e 200"
        
        wrapped = textwrap.fill(text, width=width, break_long_words=break_long_words)
        return f"Testo avvolto (larghezza {width}):\n{wrapped}"

    @mcp.tool()
    def string_find_replace(text: str, find: str, replace: str, case_sensitive: bool = True) -> str:
        """
        Trova e sostituisce testo in una stringa.

        Args:
            text: La stringa originale.
            find: Il testo da trovare.
            replace: Il testo sostitutivo.
            case_sensitive: Se la ricerca e' case-sensitive.
        """
        if not text or not find:
            return "ERRORE: Testo e pattern di ricerca non possono essere vuoti"
        
        flags = 0 if case_sensitive else re.IGNORECASE
        original_count = len(re.findall(re.escape(find), text, flags))
        
        if original_count == 0:
            return f"Nessuna occorrenza trovata di '{find}'"
        
        result = re.sub(re.escape(find), replace, text, flags=flags)
        
        return f"""Sostituzione completata:
- Occorrenze trovate: {original_count}
- Pattern: '{find}' -> '{replace}'
- Case sensitive: {case_sensitive}
- Risultato: '{result}'"""