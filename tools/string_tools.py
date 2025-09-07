# -*- coding: utf-8 -*-
# tools/string_tools.py
import re
import textwrap
import logging
import json
import base64
import urllib.parse
import html
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import unicodedata
import difflib

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

    @mcp.tool()
    def string_advanced_analysis(text: str) -> Dict[str, Any]:
        """
        Analisi avanzata di una stringa con metriche dettagliate.

        Args:
            text: La stringa da analizzare
        """
        try:
            if not text:
                return {
                    "success": False,
                    "error": "Testo vuoto"
                }
            
            # Analisi base
            total_chars = len(text)
            chars_no_spaces = len(text.replace(' ', ''))
            words = text.split()
            lines = text.splitlines()
            
            # Analisi caratteri
            letters = sum(1 for c in text if c.isalpha())
            digits = sum(1 for c in text if c.isdigit())
            spaces = text.count(' ')
            punctuation = sum(1 for c in text if c in '.,;:!?"\'()[]{}')
            special_chars = total_chars - letters - digits - spaces
            
            # Analisi parole
            unique_words = set(word.lower().strip('.,;:!?"\'()[]{}') for word in words)
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            longest_word = max(words, key=len) if words else ""
            shortest_word = min(words, key=len) if words else ""
            
            # Analisi frasi
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            
            # Analisi frequenza caratteri
            char_frequency = {}
            for char in text.lower():
                if char.isalpha():
                    char_frequency[char] = char_frequency.get(char, 0) + 1
            
            most_common_chars = sorted(char_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Analisi frequenza parole
            word_frequency = {}
            for word in words:
                clean_word = word.lower().strip('.,;:!?"\'()[]{}')
                if clean_word and len(clean_word) > 2:  # Ignora parole troppo corte
                    word_frequency[clean_word] = word_frequency.get(clean_word, 0) + 1
            
            most_common_words = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Metriche di leggibilità (approssimate)
            readability_score = calculate_readability_score(text, words, sentences)
            
            # Analisi linguistica
            language_hints = detect_language_hints(text)
            
            # Encoding analysis
            encoding_info = analyze_text_encoding(text)
            
            return {
                "success": True,
                "analysis": {
                    "basic_stats": {
                        "total_characters": total_chars,
                        "characters_no_spaces": chars_no_spaces,
                        "words": len(words),
                        "unique_words": len(unique_words),
                        "sentences": len(sentences),
                        "lines": len(lines),
                        "paragraphs": len([p for p in text.split('\n\n') if p.strip()])
                    },
                    "character_breakdown": {
                        "letters": letters,
                        "digits": digits,
                        "spaces": spaces,
                        "punctuation": punctuation,
                        "special_characters": special_chars,
                        "letters_percentage": round((letters / total_chars) * 100, 2),
                        "digits_percentage": round((digits / total_chars) * 100, 2)
                    },
                    "word_analysis": {
                        "average_word_length": round(avg_word_length, 2),
                        "longest_word": longest_word,
                        "shortest_word": shortest_word,
                        "vocabulary_richness": round(len(unique_words) / len(words), 2) if words else 0,
                        "most_common_words": most_common_words
                    },
                    "sentence_analysis": {
                        "average_sentence_length": round(avg_sentence_length, 2),
                        "longest_sentence": max(sentences, key=lambda s: len(s.split())) if sentences else "",
                        "shortest_sentence": min(sentences, key=lambda s: len(s.split())) if sentences else ""
                    },
                    "frequency_analysis": {
                        "most_common_characters": most_common_chars,
                        "character_diversity": len(char_frequency),
                        "word_repetition": len(words) - len(unique_words)
                    },
                    "readability": {
                        "score": readability_score,
                        "level": get_readability_level(readability_score),
                        "estimated_reading_time_minutes": round(len(words) / 200, 1)  # 200 wpm average
                    },
                    "language_analysis": language_hints,
                    "encoding_info": encoding_info
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Analisi fallita: {str(e)}"
            }

    @mcp.tool()
    def string_encoding_operations(text: str, operation: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Operazioni di encoding/decoding su stringhe.

        Args:
            text: Testo da processare
            operation: Operazione (base64_encode, base64_decode, url_encode, url_decode, html_encode, html_decode, hex_encode, hex_decode)
            encoding: Encoding per operazioni che lo richiedono
        """
        try:
            if not text:
                return {
                    "success": False,
                    "error": "Testo vuoto"
                }
            
            result = {}
            
            if operation == "base64_encode":
                encoded = base64.b64encode(text.encode(encoding)).decode('ascii')
                result = {
                    "original": text,
                    "encoded": encoded,
                    "operation": "Base64 Encode",
                    "encoding_used": encoding
                }
            
            elif operation == "base64_decode":
                try:
                    decoded = base64.b64decode(text).decode(encoding)
                    result = {
                        "original": text,
                        "decoded": decoded,
                        "operation": "Base64 Decode",
                        "encoding_used": encoding
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Decodifica Base64 fallita: {str(e)}"
                    }
            
            elif operation == "url_encode":
                encoded = urllib.parse.quote(text, safe='')
                result = {
                    "original": text,
                    "encoded": encoded,
                    "operation": "URL Encode"
                }
            
            elif operation == "url_decode":
                try:
                    decoded = urllib.parse.unquote(text)
                    result = {
                        "original": text,
                        "decoded": decoded,
                        "operation": "URL Decode"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Decodifica URL fallita: {str(e)}"
                    }
            
            elif operation == "html_encode":
                encoded = html.escape(text)
                result = {
                    "original": text,
                    "encoded": encoded,
                    "operation": "HTML Encode"
                }
            
            elif operation == "html_decode":
                decoded = html.unescape(text)
                result = {
                    "original": text,
                    "decoded": decoded,
                    "operation": "HTML Decode"
                }
            
            elif operation == "hex_encode":
                encoded = text.encode(encoding).hex()
                result = {
                    "original": text,
                    "encoded": encoded,
                    "operation": "Hex Encode",
                    "encoding_used": encoding
                }
            
            elif operation == "hex_decode":
                try:
                    decoded = bytes.fromhex(text).decode(encoding)
                    result = {
                        "original": text,
                        "decoded": decoded,
                        "operation": "Hex Decode",
                        "encoding_used": encoding
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Decodifica Hex fallita: {str(e)}"
                    }
            
            else:
                return {
                    "success": False,
                    "error": "Operazione non supportata. Usa: base64_encode, base64_decode, url_encode, url_decode, html_encode, html_decode, hex_encode, hex_decode"
                }
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Operazione encoding fallita: {str(e)}"
            }

    @mcp.tool()
    def string_format_operations(text: str, operation: str, options: Optional[str] = None) -> Dict[str, Any]:
        """
        Operazioni avanzate di formattazione testo.

        Args:
            text: Testo da formattare
            operation: Operazione (indent, dedent, center, ljust, rjust, zfill, truncate, pad)
            options: Opzioni aggiuntive (JSON string)
        """
        try:
            if not text:
                return {
                    "success": False,
                    "error": "Testo vuoto"
                }
            
            # Parse options
            opts = {}
            if options:
                try:
                    opts = json.loads(options)
                except json.JSONDecodeError:
                    opts = {}
            
            result = {}
            
            if operation == "indent":
                indent_size = opts.get("size", 4)
                indent_char = opts.get("char", " ")
                lines = text.split('\n')
                indented_lines = [indent_char * indent_size + line for line in lines]
                formatted = '\n'.join(indented_lines)
                
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Indent",
                    "indent_size": indent_size,
                    "indent_char": repr(indent_char)
                }
            
            elif operation == "dedent":
                formatted = textwrap.dedent(text)
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Dedent"
                }
            
            elif operation == "center":
                width = opts.get("width", 80)
                fill_char = opts.get("fill_char", " ")
                lines = text.split('\n')
                centered_lines = [line.center(width, fill_char) for line in lines]
                formatted = '\n'.join(centered_lines)
                
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Center",
                    "width": width,
                    "fill_char": repr(fill_char)
                }
            
            elif operation == "ljust":
                width = opts.get("width", 80)
                fill_char = opts.get("fill_char", " ")
                formatted = text.ljust(width, fill_char)
                
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Left Justify",
                    "width": width,
                    "fill_char": repr(fill_char)
                }
            
            elif operation == "rjust":
                width = opts.get("width", 80)
                fill_char = opts.get("fill_char", " ")
                formatted = text.rjust(width, fill_char)
                
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Right Justify",
                    "width": width,
                    "fill_char": repr(fill_char)
                }
            
            elif operation == "zfill":
                width = opts.get("width", 10)
                formatted = text.zfill(width)
                
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Zero Fill",
                    "width": width
                }
            
            elif operation == "truncate":
                max_length = opts.get("max_length", 50)
                suffix = opts.get("suffix", "...")
                
                if len(text) <= max_length:
                    formatted = text
                else:
                    formatted = text[:max_length - len(suffix)] + suffix
                
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Truncate",
                    "max_length": max_length,
                    "suffix": suffix,
                    "was_truncated": len(text) > max_length
                }
            
            elif operation == "pad":
                total_width = opts.get("width", 80)
                pad_char = opts.get("char", " ")
                side = opts.get("side", "both")  # left, right, both
                
                if side == "left":
                    formatted = text.rjust(total_width, pad_char)
                elif side == "right":
                    formatted = text.ljust(total_width, pad_char)
                else:  # both
                    formatted = text.center(total_width, pad_char)
                
                result = {
                    "original": text,
                    "formatted": formatted,
                    "operation": "Pad",
                    "width": total_width,
                    "pad_char": repr(pad_char),
                    "side": side
                }
            
            else:
                return {
                    "success": False,
                    "error": "Operazione non supportata. Usa: indent, dedent, center, ljust, rjust, zfill, truncate, pad"
                }
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Formattazione fallita: {str(e)}"
            }

    @mcp.tool()
    def string_validation(text: str, validation_type: str, options: Optional[str] = None) -> Dict[str, Any]:
        """
        Validazione stringhe con vari criteri.

        Args:
            text: Testo da validare
            validation_type: Tipo validazione (email, url, phone, credit_card, isbn, uuid, ip, json, xml)
            options: Opzioni aggiuntive (JSON string)
        """
        try:
            if not text:
                return {
                    "success": False,
                    "error": "Testo vuoto"
                }
            
            # Parse options
            opts = {}
            if options:
                try:
                    opts = json.loads(options)
                except json.JSONDecodeError:
                    opts = {}
            
            validation_result = {
                "text": text,
                "validation_type": validation_type,
                "is_valid": False,
                "errors": [],
                "details": {}
            }
            
            if validation_type == "email":
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                validation_result["is_valid"] = bool(re.match(email_pattern, text))
                if not validation_result["is_valid"]:
                    validation_result["errors"].append("Formato email non valido")
                validation_result["details"]["pattern_used"] = email_pattern
            
            elif validation_type == "url":
                url_pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
                validation_result["is_valid"] = bool(re.match(url_pattern, text))
                if not validation_result["is_valid"]:
                    validation_result["errors"].append("Formato URL non valido")
                validation_result["details"]["pattern_used"] = url_pattern
            
            elif validation_type == "phone":
                # Supporta vari formati internazionali
                phone_patterns = [
                    r'^\+?[1-9]\d{1,14}$',  # E.164
                    r'^(\+39)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4}$',  # Italia
                    r'^(\+1)?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'  # USA
                ]
                
                for pattern in phone_patterns:
                    if re.match(pattern, text):
                        validation_result["is_valid"] = True
                        validation_result["details"]["matched_pattern"] = pattern
                        break
                
                if not validation_result["is_valid"]:
                    validation_result["errors"].append("Formato telefono non riconosciuto")
            
            elif validation_type == "credit_card":
                # Rimuovi spazi e trattini
                clean_number = re.sub(r'[\s-]', '', text)
                
                # Check Luhn algorithm
                def luhn_check(card_num):
                    def digits_of(n):
                        return [int(d) for d in str(n)]
                    digits = digits_of(card_num)
                    odd_digits = digits[-1::-2]
                    even_digits = digits[-2::-2]
                    checksum = sum(odd_digits)
                    for d in even_digits:
                        checksum += sum(digits_of(d*2))
                    return checksum % 10 == 0
                
                if clean_number.isdigit() and len(clean_number) in [13, 14, 15, 16, 17, 18, 19]:
                    validation_result["is_valid"] = luhn_check(clean_number)
                    validation_result["details"]["cleaned_number"] = clean_number
                    validation_result["details"]["length"] = len(clean_number)
                else:
                    validation_result["errors"].append("Formato carta di credito non valido")
            
            elif validation_type == "json":
                try:
                    parsed = json.loads(text)
                    validation_result["is_valid"] = True
                    validation_result["details"]["parsed_type"] = type(parsed).__name__
                    if isinstance(parsed, dict):
                        validation_result["details"]["keys_count"] = len(parsed.keys())
                    elif isinstance(parsed, list):
                        validation_result["details"]["items_count"] = len(parsed)
                except json.JSONDecodeError as e:
                    validation_result["errors"].append(f"JSON non valido: {str(e)}")
            
            elif validation_type == "uuid":
                uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
                validation_result["is_valid"] = bool(re.match(uuid_pattern, text))
                if validation_result["is_valid"]:
                    version = int(text[14])
                    validation_result["details"]["uuid_version"] = version
                else:
                    validation_result["errors"].append("Formato UUID non valido")
            
            elif validation_type == "ip":
                # IPv4
                ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
                # IPv6 (semplificato)
                ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
                
                if re.match(ipv4_pattern, text):
                    validation_result["is_valid"] = True
                    validation_result["details"]["ip_version"] = 4
                elif re.match(ipv6_pattern, text):
                    validation_result["is_valid"] = True
                    validation_result["details"]["ip_version"] = 6
                else:
                    validation_result["errors"].append("Formato IP non valido")
            
            else:
                return {
                    "success": False,
                    "error": f"Tipo di validazione non supportato: {validation_type}"
                }
            
            return {
                "success": True,
                "validation": validation_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Validazione fallita: {str(e)}"
            }

    @mcp.tool()
    def string_comparison(text1: str, text2: str, comparison_type: str = "similarity") -> Dict[str, Any]:
        """
        Confronta due stringhe con vari algoritmi.

        Args:
            text1: Prima stringa
            text2: Seconda stringa
            comparison_type: Tipo confronto (similarity, levenshtein, diff, common_substrings)
        """
        try:
            if not text1 or not text2:
                return {
                    "success": False,
                    "error": "Entrambe le stringhe devono essere fornite"
                }
            
            comparison_result = {
                "text1": text1,
                "text2": text2,
                "comparison_type": comparison_type
            }
            
            if comparison_type == "similarity":
                # Usa SequenceMatcher di difflib
                similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
                comparison_result.update({
                    "similarity_ratio": round(similarity, 4),
                    "similarity_percentage": round(similarity * 100, 2),
                    "are_similar": similarity > 0.8
                })
            
            elif comparison_type == "levenshtein":
                # Calcola distanza di Levenshtein
                distance = levenshtein_distance(text1, text2)
                max_len = max(len(text1), len(text2))
                similarity = 1 - (distance / max_len) if max_len > 0 else 1
                
                comparison_result.update({
                    "levenshtein_distance": distance,
                    "similarity_ratio": round(similarity, 4),
                    "similarity_percentage": round(similarity * 100, 2)
                })
            
            elif comparison_type == "diff":
                # Genera diff dettagliato
                differ = difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile='text1',
                    tofile='text2'
                )
                diff_lines = list(differ)
                
                comparison_result.update({
                    "diff_lines": diff_lines,
                    "has_differences": len(diff_lines) > 0,
                    "diff_summary": f"{len([l for l in diff_lines if l.startswith('+')])} additions, {len([l for l in diff_lines if l.startswith('-')])} deletions"
                })
            
            elif comparison_type == "common_substrings":
                # Trova sottostringhe comuni
                common_substrings = find_common_substrings(text1, text2)
                longest_common = max(common_substrings, key=len) if common_substrings else ""
                
                comparison_result.update({
                    "common_substrings": common_substrings[:10],  # Limita output
                    "longest_common_substring": longest_common,
                    "common_substrings_count": len(common_substrings)
                })
            
            else:
                return {
                    "success": False,
                    "error": "Tipo confronto non supportato. Usa: similarity, levenshtein, diff, common_substrings"
                }
            
            return {
                "success": True,
                "comparison": comparison_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Confronto fallito: {str(e)}"
            }

    @mcp.tool()
    def string_batch_operations(operations_json: str) -> Dict[str, Any]:
        """
        Esegue operazioni multiple su stringhe in batch.

        Args:
            operations_json: JSON array con operazioni [{type, text, options}]
        """
        try:
            # Parse operations
            try:
                operations = json.loads(operations_json)
                if not isinstance(operations, list):
                    return {
                        "success": False,
                        "error": "Operations must be a JSON array"
                    }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON: {str(e)}"
                }
            
            if len(operations) > 100:
                return {
                    "success": False,
                    "error": "Maximum 100 operations per batch"
                }
            
            results = []
            successful_ops = 0
            failed_ops = 0
            
            for i, op in enumerate(operations):
                if not isinstance(op, dict):
                    results.append({
                        "operation_index": i,
                        "success": False,
                        "error": "Operation must be an object"
                    })
                    failed_ops += 1
                    continue
                
                op_type = op.get('type', '')
                text = op.get('text', '')
                options = op.get('options', {})
                
                try:
                    if op_type == 'case_convert':
                        case_type = options.get('case_type', 'lower')
                        result = string_case_convert(text, case_type)
                        
                    elif op_type == 'clean':
                        operation = options.get('operation', 'trim')
                        result = string_clean(text, operation)
                        
                    elif op_type == 'stats':
                        result = string_stats(text)
                        
                    elif op_type == 'encoding':
                        operation = options.get('operation', 'base64_encode')
                        encoding = options.get('encoding', 'utf-8')
                        encoding_result = string_encoding_operations(text, operation, encoding)
                        result = encoding_result.get('result', {}) if encoding_result.get('success') else encoding_result.get('error', '')
                        
                    elif op_type == 'validation':
                        validation_type = options.get('validation_type', 'email')
                        validation_result = string_validation(text, validation_type)
                        result = validation_result.get('validation', {}) if validation_result.get('success') else validation_result.get('error', '')
                        
                    else:
                        result = f"Unknown operation type: {op_type}"
                        failed_ops += 1
                        results.append({
                            "operation_index": i,
                            "type": op_type,
                            "success": False,
                            "error": result
                        })
                        continue
                    
                    results.append({
                        "operation_index": i,
                        "type": op_type,
                        "success": True,
                        "result": result
                    })
                    successful_ops += 1
                    
                except Exception as e:
                    results.append({
                        "operation_index": i,
                        "type": op_type,
                        "success": False,
                        "error": str(e)
                    })
                    failed_ops += 1
            
            return {
                "success": True,
                "batch_summary": {
                    "total_operations": len(operations),
                    "successful": successful_ops,
                    "failed": failed_ops,
                    "success_rate": round((successful_ops / len(operations)) * 100, 1) if operations else 0
                },
                "results": results,
                "execution_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Batch operation failed: {str(e)}"
            }

# Helper functions for the new string tools

def calculate_readability_score(text: str, words: List[str], sentences: List[str]) -> float:
    """Calcola un punteggio di leggibilità approssimativo."""
    try:
        if not words or not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables = sum(count_syllables(word) for word in words) / len(words)
        
        # Formula semplificata ispirata a Flesch Reading Ease
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
        return max(0, min(100, score))
    except:
        return 0.0

def count_syllables(word: str) -> int:
    """Conta le sillabe in una parola (approssimativo)."""
    word = word.lower()
    vowels = "aeiouy"
    syllable_count = 0
    prev_was_vowel = False
    
    for char in word:
        if char in vowels:
            if not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = True
        else:
            prev_was_vowel = False
    
    # Se la parola finisce con 'e', rimuovi una sillaba
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1
    
    return max(1, syllable_count)

def get_readability_level(score: float) -> str:
    """Determina il livello di leggibilità."""
    if score >= 90:
        return "Molto Facile"
    elif score >= 80:
        return "Facile"
    elif score >= 70:
        return "Abbastanza Facile"
    elif score >= 60:
        return "Standard"
    elif score >= 50:
        return "Abbastanza Difficile"
    elif score >= 30:
        return "Difficile"
    else:
        return "Molto Difficile"

def detect_language_hints(text: str) -> Dict[str, Any]:
    """Rileva indizi sulla lingua del testo."""
    hints = {
        "detected_scripts": [],
        "common_words": {},
        "character_patterns": {}
    }
    
    # Analisi script Unicode
    scripts = set()
    for char in text:
        if char.isalpha():
            script = unicodedata.name(char, '').split()[0] if unicodedata.name(char, '') else 'UNKNOWN'
            scripts.add(script)
    
    hints["detected_scripts"] = list(scripts)[:5]  # Limita output
    
    # Parole comuni per lingue specifiche
    italian_words = ['il', 'la', 'di', 'che', 'e', 'a', 'un', 'per', 'con', 'non']
    english_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that']
    spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se']
    
    words = text.lower().split()
    
    italian_count = sum(1 for word in words if word in italian_words)
    english_count = sum(1 for word in words if word in english_words)
    spanish_count = sum(1 for word in words if word in spanish_words)
    
    hints["common_words"] = {
        "italian_indicators": italian_count,
        "english_indicators": english_count,
        "spanish_indicators": spanish_count
    }
    
    return hints

def analyze_text_encoding(text: str) -> Dict[str, Any]:
    """Analizza informazioni sull'encoding del testo."""
    info = {
        "contains_unicode": any(ord(char) > 127 for char in text),
        "ascii_compatible": all(ord(char) < 128 for char in text),
        "max_codepoint": max(ord(char) for char in text) if text else 0,
        "unicode_categories": {}
    }
    
    # Analisi categorie Unicode
    categories = {}
    for char in text:
        category = unicodedata.category(char)
        categories[category] = categories.get(category, 0) + 1
    
    info["unicode_categories"] = dict(list(categories.items())[:10])  # Top 10 categorie
    
    return info

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calcola la distanza di Levenshtein tra due stringhe."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def find_common_substrings(s1: str, s2: str, min_length: int = 3) -> List[str]:
    """Trova sottostringhe comuni tra due stringhe."""
    common = []
    len1, len2 = len(s1), len(s2)
    
    for i in range(len1):
        for j in range(len2):
            k = 0
            while (i + k < len1 and j + k < len2 and 
                   s1[i + k] == s2[j + k]):
                k += 1
            
            if k >= min_length:
                substring = s1[i:i + k]
                if substring not in common:
                    common.append(substring)
    
    return sorted(common, key=len, reverse=True)