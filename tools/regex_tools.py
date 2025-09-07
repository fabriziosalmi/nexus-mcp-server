# -*- coding: utf-8 -*-
# tools/regex_tools.py
import re
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib

def register_tools(mcp):
    """Registra i tool per espressioni regolari con l'istanza del server MCP."""
    logging.info("🔍 Registrazione tool-set: Regex Tools")

    @mcp.tool()
    def regex_test(pattern: str, text: str, flags: str = "") -> str:
        """
        Testa se un pattern regex trova corrispondenze nel testo.

        Args:
            pattern: Il pattern regex da testare.
            text: Il testo su cui testare il pattern.
            flags: Flag opzionali (i=ignorecase, m=multiline, s=dotall, x=verbose).
        """
        try:
            # Converte i flag da stringa a flag regex
            regex_flags = 0
            if 'i' in flags.lower():
                regex_flags |= re.IGNORECASE
            if 'm' in flags.lower():
                regex_flags |= re.MULTILINE
            if 's' in flags.lower():
                regex_flags |= re.DOTALL
            if 'x' in flags.lower():
                regex_flags |= re.VERBOSE
            
            # Compila il pattern
            compiled_pattern = re.compile(pattern, regex_flags)
            
            # Cerca le corrispondenze
            matches = compiled_pattern.findall(text)
            
            result = "=== RISULTATO TEST REGEX ===\n"
            result += f"Pattern: {pattern}\n"
            result += f"Flag: {flags if flags else 'Nessuno'}\n"
            result += f"Testo testato: {text[:100]}{'...' if len(text) > 100 else ''}\n\n"
            
            if matches:
                result += f"✅ CORRISPONDENZE TROVATE: {len(matches)}\n"
                for i, match in enumerate(matches[:10], 1):  # Mostra max 10 risultati
                    result += f"  {i}. {match}\n"
                if len(matches) > 10:
                    result += f"  ... e altre {len(matches) - 10} corrispondenze\n"
            else:
                result += "❌ NESSUNA CORRISPONDENZA TROVATA\n"
            
            return result
            
        except re.error as e:
            return f"ERRORE REGEX: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_match_details(pattern: str, text: str, flags: str = "") -> str:
        """
        Fornisce dettagli completi sulle corrispondenze regex incluse posizioni.

        Args:
            pattern: Il pattern regex da testare.
            text: Il testo su cui cercare.
            flags: Flag opzionali (i=ignorecase, m=multiline, s=dotall, x=verbose).
        """
        try:
            # Converte i flag
            regex_flags = 0
            if 'i' in flags.lower():
                regex_flags |= re.IGNORECASE
            if 'm' in flags.lower():
                regex_flags |= re.MULTILINE
            if 's' in flags.lower():
                regex_flags |= re.DOTALL
            if 'x' in flags.lower():
                regex_flags |= re.VERBOSE
            
            compiled_pattern = re.compile(pattern, regex_flags)
            
            result = "=== DETTAGLI CORRISPONDENZE REGEX ===\n"
            result += f"Pattern: {pattern}\n"
            result += f"Flag: {flags if flags else 'Nessuno'}\n\n"
            
            matches = list(compiled_pattern.finditer(text))
            
            if matches:
                result += f"Corrispondenze trovate: {len(matches)}\n\n"
                for i, match in enumerate(matches[:10], 1):
                    result += f"Corrispondenza {i}:\n"
                    result += f"  Testo: '{match.group()}'\n"
                    result += f"  Posizione: {match.start()}-{match.end()}\n"
                    result += f"  Span: {match.span()}\n"
                    
                    # Mostra i gruppi se presenti
                    if match.groups():
                        result += f"  Gruppi: {match.groups()}\n"
                    
                    # Mostra i gruppi nominati se presenti
                    if match.groupdict():
                        result += f"  Gruppi nominati: {match.groupdict()}\n"
                    
                    result += "\n"
                
                if len(matches) > 10:
                    result += f"... e altre {len(matches) - 10} corrispondenze\n"
            else:
                result += "Nessuna corrispondenza trovata.\n"
            
            return result
            
        except re.error as e:
            return f"ERRORE REGEX: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_replace(pattern: str, text: str, replacement: str, flags: str = "", count: int = 0) -> str:
        """
        Sostituisce le corrispondenze del pattern con il testo di sostituzione.

        Args:
            pattern: Il pattern regex da cercare.
            text: Il testo originale.
            replacement: Il testo di sostituzione.
            flags: Flag opzionali (i, m, s, x).
            count: Numero massimo di sostituzioni (0 = tutte).
        """
        try:
            # Converte i flag
            regex_flags = 0
            if 'i' in flags.lower():
                regex_flags |= re.IGNORECASE
            if 'm' in flags.lower():
                regex_flags |= re.MULTILINE
            if 's' in flags.lower():
                regex_flags |= re.DOTALL
            if 'x' in flags.lower():
                regex_flags |= re.VERBOSE
            
            compiled_pattern = re.compile(pattern, regex_flags)
            
            # Conta le corrispondenze prima della sostituzione
            original_matches = len(compiled_pattern.findall(text))
            
            # Esegue la sostituzione
            new_text = compiled_pattern.sub(replacement, text, count=count)
            
            # Conta quante sostituzioni sono state effettuate
            remaining_matches = len(compiled_pattern.findall(new_text))
            replacements_made = original_matches - remaining_matches
            
            result = "=== RISULTATO SOSTITUZIONE REGEX ===\n"
            result += f"Pattern: {pattern}\n"
            result += f"Sostituzione: {replacement}\n"
            result += f"Flag: {flags if flags else 'Nessuno'}\n"
            result += f"Corrispondenze originali: {original_matches}\n"
            result += f"Sostituzioni effettuate: {replacements_made}\n"
            result += f"Corrispondenze rimanenti: {remaining_matches}\n\n"
            result += f"TESTO RISULTANTE:\n{new_text}"
            
            return result
            
        except re.error as e:
            return f"ERRORE REGEX: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_split(pattern: str, text: str, flags: str = "", maxsplit: int = 0) -> str:
        """
        Divide il testo usando il pattern regex come delimitatore.

        Args:
            pattern: Il pattern regex da usare come delimitatore.
            text: Il testo da dividere.
            flags: Flag opzionali (i, m, s, x).
            maxsplit: Numero massimo di divisioni (0 = illimitato).
        """
        try:
            # Converte i flag
            regex_flags = 0
            if 'i' in flags.lower():
                regex_flags |= re.IGNORECASE
            if 'm' in flags.lower():
                regex_flags |= re.MULTILINE
            if 's' in flags.lower():
                regex_flags |= re.DOTALL
            if 'x' in flags.lower():
                regex_flags |= re.VERBOSE
            
            compiled_pattern = re.compile(pattern, regex_flags)
            
            # Esegue la divisione
            parts = compiled_pattern.split(text, maxsplit=maxsplit)
            
            result = "=== RISULTATO DIVISIONE REGEX ===\n"
            result += f"Pattern delimitatore: {pattern}\n"
            result += f"Flag: {flags if flags else 'Nessuno'}\n"
            result += f"Massimo divisioni: {maxsplit if maxsplit > 0 else 'Illimitato'}\n"
            result += f"Parti risultanti: {len(parts)}\n\n"
            
            for i, part in enumerate(parts, 1):
                result += f"Parte {i}: '{part}'\n"
            
            return result
            
        except re.error as e:
            return f"ERRORE REGEX: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_validate_pattern(pattern: str) -> str:
        """
        Valida un pattern regex e fornisce informazioni su di esso.

        Args:
            pattern: Il pattern regex da validare.
        """
        try:
            # Tenta di compilare il pattern
            compiled = re.compile(pattern)
            
            result = "=== VALIDAZIONE PATTERN REGEX ===\n"
            result += f"Pattern: {pattern}\n"
            result += "✅ PATTERN VALIDO\n\n"
            
            # Analizza il pattern
            result += "ANALISI PATTERN:\n"
            
            # Controlla caratteri speciali
            special_chars = ['.', '^', '$', '*', '+', '?', '{', '}', '[', ']', '(', ')', '|', '\\']
            found_specials = [char for char in special_chars if char in pattern]
            if found_specials:
                result += f"Caratteri speciali usati: {', '.join(found_specials)}\n"
            
            # Controlla gruppi
            groups = compiled.groups
            if groups > 0:
                result += f"Numero di gruppi di cattura: {groups}\n"
            
            # Controlla gruppi nominati
            if compiled.groupindex:
                result += f"Gruppi nominati: {list(compiled.groupindex.keys())}\n"
            
            # Suggerimenti
            result += "\nSUGGERIMENTI:\n"
            if '.*' in pattern:
                result += "- Considera l'uso di '.+' invece di '.*' se vuoi almeno un carattere\n"
            if pattern.startswith('.*') or pattern.endswith('.*'):
                result += "- .* all'inizio/fine potrebbe essere ridondante\n"
            if '[0-9]' in pattern:
                result += "- Considera l'uso di \\d invece di [0-9]\n"
            if not (pattern.startswith('^') or pattern.endswith('$')):
                result += "- Aggiungi ^ e $ per match completo della stringa\n"
            
            return result
            
        except re.error as e:
            return f"❌ PATTERN NON VALIDO\nErrore: {str(e)}\n\nSuggerimenti:\n- Controlla parentesi e caratteri speciali\n- Usa \\\\ per caratteri letterali\n- Verifica la sintassi dei gruppi"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_common_patterns() -> str:
        """
        Fornisce una lista di pattern regex comuni e utili.
        """
        try:
            patterns = {
                "📧 Email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                "📱 Telefono IT": r'^(\+39)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4}$',
                "🌐 URL": r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
                "💳 Carta di Credito": r'^[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}$',
                "🆔 Codice Fiscale IT": r'^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$',
                "🏠 Indirizzo IP": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
                "🔢 Solo numeri": r'^[0-9]+$',
                "🔤 Solo lettere": r'^[a-zA-Z]+$',
                "📊 Numeri decimali": r'^[0-9]+(\.[0-9]+)?$',
                "📅 Data (DD/MM/YYYY)": r'^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/[0-9]{4}$',
                "🕐 Ora (HH:MM)": r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
                "🏷️ Tag HTML": r'<[^>]+>',
                "💬 Hashtag": r'#[a-zA-Z0-9_]+',
                "👤 Username": r'^[a-zA-Z0-9._-]{3,20}$',
                "🔐 Password forte": r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                "🏠 CAP Italia": r'^[0-9]{5}$'
            }
            
            result = "=== PATTERN REGEX COMUNI ===\n\n"
            
            for description, pattern in patterns.items():
                result += f"{description}:\n"
                result += f"Pattern: {pattern}\n"
                result += f"Esempio uso: regex_test('{pattern}', 'tuo_testo')\n\n"
            
            result += "=== CARATTERI SPECIALI COMUNI ===\n"
            result += "\\d - Cifra (0-9)\n"
            result += "\\w - Carattere alfanumerico (a-z, A-Z, 0-9, _)\n"
            result += "\\s - Spazio bianco\n"
            result += ". - Qualsiasi carattere\n"
            result += "* - Zero o più occorrenze\n"
            result += "+ - Una o più occorrenze\n"
            result += "? - Zero o una occorrenza\n"
            result += "^ - Inizio stringa\n"
            result += "$ - Fine stringa\n"
            result += "[] - Classe di caratteri\n"
            result += "() - Gruppo di cattura\n"
            result += "| - OR logico\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_extract_emails(text: str) -> str:
        """
        Estrae tutti gli indirizzi email da un testo.

        Args:
            text: Il testo da cui estrarre gli email.
        """
        try:
            email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            emails = re.findall(email_pattern, text, re.IGNORECASE)
            
            result = "=== ESTRAZIONE EMAIL ===\n"
            result += f"Testo analizzato: {len(text)} caratteri\n"
            
            if emails:
                # Rimuovi duplicati mantenendo l'ordine
                unique_emails = list(dict.fromkeys(emails))
                result += f"Email trovate: {len(emails)} ({len(unique_emails)} uniche)\n\n"
                
                for i, email in enumerate(unique_emails, 1):
                    result += f"{i}. {email}\n"
            else:
                result += "Nessun indirizzo email trovato.\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_extract_urls(text: str) -> str:
        """
        Estrae tutti gli URL da un testo.

        Args:
            text: Il testo da cui estrarre gli URL.
        """
        try:
            url_pattern = r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?'
            urls = re.findall(url_pattern, text, re.IGNORECASE)
            
            result = "=== ESTRAZIONE URL ===\n"
            result += f"Testo analizzato: {len(text)} caratteri\n"
            
            if urls:
                # Rimuovi duplicati mantenendo l'ordine
                unique_urls = list(dict.fromkeys(urls))
                result += f"URL trovati: {len(urls)} ({len(unique_urls)} unici)\n\n"
                
                for i, url in enumerate(unique_urls, 1):
                    result += f"{i}. {url}\n"
            else:
                result += "Nessun URL trovato.\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def regex_pattern_builder(pattern_type: str, options: str = "") -> Dict[str, Any]:
        """
        Costruisce pattern regex comuni con opzioni personalizzabili.
        
        Args:
            pattern_type: Tipo di pattern (email, phone, url, ip, date, time, etc.)
            options: Opzioni specifiche per il pattern (JSON string)
        """
        try:
            # Parse options
            opts = {}
            if options:
                try:
                    opts = json.loads(options)
                except json.JSONDecodeError:
                    opts = {}
            
            patterns = {
                "email": {
                    "basic": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    "strict": r'^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$',
                    "international": r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
                },
                "phone": {
                    "italy": r'^(\+39)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4}$',
                    "us": r'^(\+1)?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',
                    "international": r'^\+?[1-9]\d{1,14}$',
                    "mobile_italy": r'^(\+39)?[-.\s]?3[0-9]{2}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
                },
                "url": {
                    "http": r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
                    "strict": r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&=]*)$',
                    "with_port": r'^https?://[-a-zA-Z0-9@:%._\+~#=]{1,256}(?::[0-9]{1,5})?\b(?:[-a-zA-Z0-9()@:%_\+.~#?&=]*)$'
                },
                "ip": {
                    "ipv4": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
                    "ipv6": r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$',
                    "both": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
                },
                "date": {
                    "dd/mm/yyyy": r'^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/[0-9]{4}$',
                    "mm/dd/yyyy": r'^(0[1-9]|1[012])/(0[1-9]|[12][0-9]|3[01])/[0-9]{4}$',
                    "yyyy-mm-dd": r'^[0-9]{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$',
                    "flexible": r'^(?:[0-9]{1,2}[/-]){2}[0-9]{2,4}$'
                },
                "password": {
                    "strong": r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                    "medium": r'^(?=.*[a-zA-Z])(?=.*\d)[A-Za-z\d@$!%*?&]{6,}$',
                    "custom_length": f"^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{{{opts.get('min_length', 8)},}}$"
                },
                "credit_card": {
                    "visa": r'^4[0-9]{12}(?:[0-9]{3})?$',
                    "mastercard": r'^5[1-5][0-9]{14}$',
                    "amex": r'^3[47][0-9]{13}$',
                    "any": r'^[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}$'
                }
            }
            
            if pattern_type not in patterns:
                available_types = list(patterns.keys())
                return {
                    "success": False,
                    "error": f"Pattern type '{pattern_type}' not available",
                    "available_types": available_types
                }
            
            pattern_group = patterns[pattern_type]
            variant = opts.get('variant', 'basic')
            
            if variant not in pattern_group:
                # Usa il primo disponibile se variant non trovato
                variant = list(pattern_group.keys())[0]
            
            selected_pattern = pattern_group[variant]
            
            # Applica modificatori se richiesti
            if opts.get('case_insensitive', False):
                flags = "i"
            else:
                flags = ""
            
            if opts.get('multiline', False):
                flags += "m"
            
            # Test del pattern con esempi
            test_examples = get_test_examples(pattern_type, variant)
            test_results = []
            
            if test_examples:
                for example in test_examples:
                    try:
                        match = re.match(selected_pattern, example['text'], 
                                       re.IGNORECASE if 'i' in flags else 0)
                        test_results.append({
                            "text": example['text'],
                            "expected": example['should_match'],
                            "actual": bool(match),
                            "correct": bool(match) == example['should_match']
                        })
                    except:
                        test_results.append({
                            "text": example['text'],
                            "expected": example['should_match'],
                            "actual": False,
                            "correct": False,
                            "error": "Pattern test failed"
                        })
            
            return {
                "success": True,
                "pattern_type": pattern_type,
                "variant": variant,
                "pattern": selected_pattern,
                "flags": flags,
                "description": get_pattern_description(pattern_type, variant),
                "available_variants": list(pattern_group.keys()),
                "test_results": test_results,
                "usage_example": f"regex_test('{selected_pattern}', 'your_text', '{flags}')"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error building pattern: {str(e)}"
            }

    @mcp.tool()
    def regex_performance_test(pattern: str, text: str, iterations: int = 1000) -> Dict[str, Any]:
        """
        Testa le performance di un pattern regex.
        
        Args:
            pattern: Pattern regex da testare
            text: Testo di test
            iterations: Numero di iterazioni per il test (max 10000)
        """
        try:
            iterations = min(max(iterations, 1), 10000)
            
            # Compila il pattern
            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex pattern: {str(e)}"
                }
            
            # Test di compilazione
            compile_times = []
            for _ in range(min(100, iterations)):
                start_time = time.perf_counter()
                re.compile(pattern)
                compile_times.append(time.perf_counter() - start_time)
            
            avg_compile_time = sum(compile_times) / len(compile_times)
            
            # Test di matching
            match_times = []
            search_times = []
            findall_times = []
            
            for _ in range(iterations):
                # Test match()
                start_time = time.perf_counter()
                compiled_pattern.match(text)
                match_times.append(time.perf_counter() - start_time)
                
                # Test search()
                start_time = time.perf_counter()
                compiled_pattern.search(text)
                search_times.append(time.perf_counter() - start_time)
                
                # Test findall()
                start_time = time.perf_counter()
                compiled_pattern.findall(text)
                findall_times.append(time.perf_counter() - start_time)
            
            # Calcola statistiche
            def calc_stats(times):
                if not times:
                    return {"avg": 0, "min": 0, "max": 0, "total": 0}
                return {
                    "avg_microseconds": round(sum(times) / len(times) * 1000000, 3),
                    "min_microseconds": round(min(times) * 1000000, 3),
                    "max_microseconds": round(max(times) * 1000000, 3),
                    "total_seconds": round(sum(times), 6)
                }
            
            # Analizza complessità pattern
            complexity_score = analyze_pattern_complexity(pattern)
            
            return {
                "success": True,
                "pattern": pattern,
                "test_config": {
                    "iterations": iterations,
                    "text_length": len(text),
                    "pattern_length": len(pattern)
                },
                "performance_results": {
                    "compilation": calc_stats(compile_times),
                    "match": calc_stats(match_times),
                    "search": calc_stats(search_times),
                    "findall": calc_stats(findall_times)
                },
                "pattern_analysis": {
                    "complexity_score": complexity_score,
                    "complexity_level": get_complexity_level(complexity_score),
                    "optimization_tips": get_optimization_tips(pattern)
                },
                "recommendations": generate_performance_recommendations(
                    avg_compile_time, match_times, complexity_score
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Performance test failed: {str(e)}"
            }

    @mcp.tool()
    def regex_batch_operations(operations_json: str) -> Dict[str, Any]:
        """
        Esegue operazioni regex multiple in batch.
        
        Args:
            operations_json: JSON array con operazioni [{type, pattern, text, options}]
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
            
            if len(operations) > 50:
                return {
                    "success": False,
                    "error": "Maximum 50 operations per batch"
                }
            
            results = []
            successful_ops = 0
            failed_ops = 0
            total_matches = 0
            
            for i, op in enumerate(operations):
                if not isinstance(op, dict):
                    results.append({
                        "operation_index": i,
                        "success": False,
                        "error": "Operation must be an object"
                    })
                    failed_ops += 1
                    continue
                
                op_type = op.get('type', 'test')
                pattern = op.get('pattern', '')
                text = op.get('text', '')
                options = op.get('options', {})
                
                try:
                    if op_type == 'test':
                        matches = regex_test_batch(pattern, text, options)
                        total_matches += len(matches) if matches else 0
                        result = {
                            "operation_index": i,
                            "type": op_type,
                            "success": True,
                            "matches_count": len(matches) if matches else 0,
                            "matches": matches[:10] if matches else []  # Limit output
                        }
                    
                    elif op_type == 'replace':
                        replacement = op.get('replacement', '')
                        result_text, count = regex_replace_batch(pattern, text, replacement, options)
                        result = {
                            "operation_index": i,
                            "type": op_type,
                            "success": True,
                            "replacements_made": count,
                            "result_text": result_text[:500] + "..." if len(result_text) > 500 else result_text
                        }
                    
                    elif op_type == 'split':
                        parts = regex_split_batch(pattern, text, options)
                        result = {
                            "operation_index": i,
                            "type": op_type,
                            "success": True,
                            "parts_count": len(parts),
                            "parts": parts[:10]  # Limit output
                        }
                    
                    elif op_type == 'extract':
                        extracted = regex_extract_batch(pattern, text, options)
                        result = {
                            "operation_index": i,
                            "type": op_type,
                            "success": True,
                            "extracted_count": len(extracted),
                            "extracted": extracted[:20]  # Limit output
                        }
                    
                    else:
                        result = {
                            "operation_index": i,
                            "success": False,
                            "error": f"Unknown operation type: {op_type}"
                        }
                        failed_ops += 1
                        continue
                    
                    results.append(result)
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
                    "success_rate": round((successful_ops / len(operations)) * 100, 1) if operations else 0,
                    "total_matches_found": total_matches
                },
                "results": results,
                "execution_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Batch operation failed: {str(e)}"
            }

    @mcp.tool()
    def regex_advanced_validator(pattern: str) -> Dict[str, Any]:
        """
        Validazione avanzata di pattern regex con analisi dettagliata.
        
        Args:
            pattern: Pattern regex da validare
        """
        try:
            validation_result = {
                "pattern": pattern,
                "timestamp": datetime.now().isoformat()
            }
            
            # Test compilazione
            try:
                compiled = re.compile(pattern)
                validation_result["compilation"] = {
                    "success": True,
                    "groups": compiled.groups,
                    "named_groups": list(compiled.groupindex.keys()) if compiled.groupindex else []
                }
            except re.error as e:
                validation_result["compilation"] = {
                    "success": False,
                    "error": str(e),
                    "error_position": getattr(e, 'pos', None)
                }
                return {
                    "success": False,
                    "validation_result": validation_result
                }
            
            # Analisi strutturale
            structural_analysis = analyze_pattern_structure(pattern)
            validation_result["structural_analysis"] = structural_analysis
            
            # Test con esempi comuni
            common_tests = perform_common_tests(compiled)
            validation_result["common_tests"] = common_tests
            
            # Analisi performance potenziali
            performance_analysis = analyze_potential_performance(pattern)
            validation_result["performance_analysis"] = performance_analysis
            
            # Sicurezza e ReDOS
            security_analysis = analyze_regex_security(pattern)
            validation_result["security_analysis"] = security_analysis
            
            # Suggerimenti miglioramento
            improvement_suggestions = generate_improvement_suggestions(pattern, structural_analysis)
            validation_result["improvement_suggestions"] = improvement_suggestions
            
            # Punteggio qualità generale
            quality_score = calculate_pattern_quality_score(
                structural_analysis, performance_analysis, security_analysis
            )
            validation_result["quality_score"] = quality_score
            
            return {
                "success": True,
                "validation_result": validation_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Advanced validation failed: {str(e)}"
            }

    @mcp.tool()
    def regex_pattern_explainer(pattern: str) -> Dict[str, Any]:
        """
        Spiega un pattern regex in linguaggio naturale.
        
        Args:
            pattern: Pattern regex da spiegare
        """
        try:
            explanation = {
                "pattern": pattern,
                "breakdown": []
            }
            
            # Analizza il pattern carattere per carattere
            i = 0
            while i < len(pattern):
                char = pattern[i]
                
                if char == '\\' and i + 1 < len(pattern):
                    # Carattere escape
                    next_char = pattern[i + 1]
                    escape_explanation = explain_escape_sequence(f"\\{next_char}")
                    explanation["breakdown"].append({
                        "position": i,
                        "characters": f"\\{next_char}",
                        "type": "escape_sequence",
                        "explanation": escape_explanation
                    })
                    i += 2
                    
                elif char == '[':
                    # Character class
                    end_bracket = find_matching_bracket(pattern, i)
                    if end_bracket != -1:
                        char_class = pattern[i:end_bracket + 1]
                        explanation["breakdown"].append({
                            "position": i,
                            "characters": char_class,
                            "type": "character_class",
                            "explanation": explain_character_class(char_class)
                        })
                        i = end_bracket + 1
                    else:
                        explanation["breakdown"].append({
                            "position": i,
                            "characters": char,
                            "type": "literal",
                            "explanation": f"Literal character '{char}'"
                        })
                        i += 1
                        
                elif char == '(':
                    # Group
                    end_paren = find_matching_parenthesis(pattern, i)
                    if end_paren != -1:
                        group = pattern[i:end_paren + 1]
                        explanation["breakdown"].append({
                            "position": i,
                            "characters": group,
                            "type": "group",
                            "explanation": explain_group(group)
                        })
                        i = end_paren + 1
                    else:
                        explanation["breakdown"].append({
                            "position": i,
                            "characters": char,
                            "type": "literal",
                            "explanation": f"Literal character '{char}'"
                        })
                        i += 1
                        
                elif char in '.^$*+?{}|':
                    # Special characters
                    if char == '{' and i + 1 < len(pattern):
                        # Quantifier
                        end_brace = pattern.find('}', i)
                        if end_brace != -1:
                            quantifier = pattern[i:end_brace + 1]
                            explanation["breakdown"].append({
                                "position": i,
                                "characters": quantifier,
                                "type": "quantifier",
                                "explanation": explain_quantifier(quantifier)
                            })
                            i = end_brace + 1
                        else:
                            explanation["breakdown"].append({
                                "position": i,
                                "characters": char,
                                "type": "special",
                                "explanation": explain_special_character(char)
                            })
                            i += 1
                    else:
                        explanation["breakdown"].append({
                            "position": i,
                            "characters": char,
                            "type": "special",
                            "explanation": explain_special_character(char)
                        })
                        i += 1
                        
                else:
                    # Literal character
                    explanation["breakdown"].append({
                        "position": i,
                        "characters": char,
                        "type": "literal",
                        "explanation": f"Matches literal character '{char}'"
                    })
                    i += 1
            
            # Genera spiegazione in linguaggio naturale
            natural_explanation = generate_natural_explanation(explanation["breakdown"])
            explanation["natural_language"] = natural_explanation
            
            # Esempi di testo che dovrebbero fare match
            example_matches = generate_example_matches(pattern)
            explanation["example_matches"] = example_matches
            
            return {
                "success": True,
                "explanation": explanation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Pattern explanation failed: {str(e)}"
            }

# Helper functions for the new tools

def get_test_examples(pattern_type: str, variant: str) -> List[Dict]:
    """Restituisce esempi di test per un tipo di pattern."""
    examples = {
        "email": {
            "basic": [
                {"text": "test@example.com", "should_match": True},
                {"text": "user.name@domain.co.uk", "should_match": True},
                {"text": "invalid-email", "should_match": False},
                {"text": "@domain.com", "should_match": False}
            ]
        },
        "phone": {
            "italy": [
                {"text": "+39 123 456 7890", "should_match": True},
                {"text": "123.456.7890", "should_match": True},
                {"text": "123456", "should_match": False}
            ]
        }
    }
    return examples.get(pattern_type, {}).get(variant, [])

def get_pattern_description(pattern_type: str, variant: str) -> str:
    """Restituisce la descrizione di un pattern."""
    descriptions = {
        "email": {
            "basic": "Basic email validation pattern",
            "strict": "Strict email validation with RFC compliance",
            "international": "International email format support"
        },
        "phone": {
            "italy": "Italian phone number format",
            "us": "US phone number format",
            "international": "International phone number format"
        }
    }
    return descriptions.get(pattern_type, {}).get(variant, f"{pattern_type} pattern ({variant})")

def analyze_pattern_complexity(pattern: str) -> int:
    """Analizza la complessità di un pattern regex."""
    complexity = 0
    
    # Fattori di complessità
    complexity += pattern.count('*') * 3  # Quantificatori greedy
    complexity += pattern.count('+') * 2
    complexity += pattern.count('?') * 1
    complexity += pattern.count('.*') * 5  # Molto costoso
    complexity += pattern.count('.+') * 3
    complexity += pattern.count('(') * 2  # Gruppi
    complexity += pattern.count('[') * 1  # Character classes
    complexity += pattern.count('|') * 2  # Alternation
    complexity += len(re.findall(r'\\[dwsWDS]', pattern)) * 1  # Character classes
    
    # Nesting penalty
    if '((' in pattern or '[[' in pattern:
        complexity += 5
    
    return complexity

def get_complexity_level(score: int) -> str:
    """Determina il livello di complessità."""
    if score <= 5:
        return "Low"
    elif score <= 15:
        return "Medium"
    elif score <= 30:
        return "High"
    else:
        return "Very High"

def get_optimization_tips(pattern: str) -> List[str]:
    """Genera suggerimenti di ottimizzazione."""
    tips = []
    
    if '.*' in pattern:
        tips.append("Consider using '.+' instead of '.*' if you need at least one character")
    
    if pattern.count('(') > 5:
        tips.append("Consider using non-capturing groups (?:...) where possible")
    
    if '|' in pattern and len(pattern.split('|')) > 3:
        tips.append("Multiple alternations can be slow - consider character classes")
    
    if pattern.startswith('.*') or pattern.endswith('.*'):
        tips.append("Leading/trailing .* might be redundant")
    
    return tips

def regex_test_batch(pattern: str, text: str, options: Dict) -> List[str]:
    """Esegue test regex per batch operations."""
    flags = 0
    if options.get('ignorecase', False):
        flags |= re.IGNORECASE
    if options.get('multiline', False):
        flags |= re.MULTILINE
    
    compiled = re.compile(pattern, flags)
    return compiled.findall(text)

def regex_replace_batch(pattern: str, text: str, replacement: str, options: Dict) -> Tuple[str, int]:
    """Esegue replace regex per batch operations."""
    flags = 0
    if options.get('ignorecase', False):
        flags |= re.IGNORECASE
    if options.get('multiline', False):
        flags |= re.MULTILINE
    
    compiled = re.compile(pattern, flags)
    count = options.get('count', 0)
    
    original_matches = len(compiled.findall(text))
    result = compiled.sub(replacement, text, count=count)
    remaining_matches = len(compiled.findall(result))
    
    return result, original_matches - remaining_matches

def regex_split_batch(pattern: str, text: str, options: Dict) -> List[str]:
    """Esegue split regex per batch operations."""
    flags = 0
    if options.get('ignorecase', False):
        flags |= re.IGNORECASE
    if options.get('multiline', False):
        flags |= re.MULTILINE
    
    compiled = re.compile(pattern, flags)
    maxsplit = options.get('maxsplit', 0)
    
    return compiled.split(text, maxsplit=maxsplit)

def regex_extract_batch(pattern: str, text: str, options: Dict) -> List[str]:
    """Estrae tutti i match per batch operations."""
    flags = 0
    if options.get('ignorecase', False):
        flags |= re.IGNORECASE
    if options.get('multiline', False):
        flags |= re.MULTILINE
    
    compiled = re.compile(pattern, flags)
    return compiled.findall(text)

def analyze_pattern_structure(pattern: str) -> Dict[str, Any]:
    """Analizza la struttura di un pattern regex."""
    return {
        "length": len(pattern),
        "groups": pattern.count('('),
        "character_classes": pattern.count('['),
        "quantifiers": len(re.findall(r'[*+?{}]', pattern)),
        "anchors": pattern.startswith('^') or pattern.endswith('$'),
        "alternations": pattern.count('|'),
        "escaped_chars": len(re.findall(r'\\[^\\]', pattern))
    }

def perform_common_tests(compiled_pattern) -> Dict[str, Any]:
    """Esegue test comuni su un pattern."""
    test_strings = [
        "", "a", "123", "abc123", "ABC", "!@#$%", " \t\n",
        "test@example.com", "http://example.com", "123-456-7890"
    ]
    
    results = {}
    for test_str in test_strings:
        try:
            match = compiled_pattern.match(test_str)
            results[test_str] = bool(match)
        except:
            results[test_str] = "error"
    
    return results

def analyze_potential_performance(pattern: str) -> Dict[str, Any]:
    """Analizza potenziali problemi di performance."""
    issues = []
    
    # Backtracking catastrophico
    if re.search(r'\([^)]*\*[^)]*\)[*+]', pattern):
        issues.append("Potential catastrophic backtracking")
    
    # Quantificatori annidati
    if re.search(r'[*+]{2,}', pattern):
        issues.append("Nested quantifiers detected")
    
    # Alternazione con overlap
    if '|' in pattern and len(pattern.split('|')) > 2:
        issues.append("Multiple alternations may cause performance issues")
    
    return {
        "potential_issues": issues,
        "complexity_rating": get_complexity_level(analyze_pattern_complexity(pattern))
    }

def analyze_regex_security(pattern: str) -> Dict[str, Any]:
    """Analizza potenziali problemi di sicurezza."""
    vulnerabilities = []
    
    # ReDoS patterns
    redos_patterns = [
        r'\([^)]*\*[^)]*\)[*+]',  # Nested quantifiers
        r'\([^)]*\+[^)]*\)[*+]',  # Nested quantifiers with +
        r'[*+]{2,}',              # Multiple quantifiers
        r'\(.*\*.*\)\*'           # Nested star quantifiers
    ]
    
    for vuln_pattern in redos_patterns:
        if re.search(vuln_pattern, pattern):
            vulnerabilities.append("Potential ReDoS vulnerability")
            break
    
    # Overly permissive patterns
    if '.*' in pattern and len(pattern) < 10:
        vulnerabilities.append("Pattern may be overly permissive")
    
    return {
        "vulnerabilities": vulnerabilities,
        "security_rating": "Low" if not vulnerabilities else "High"
    }

def generate_improvement_suggestions(pattern: str, structural: Dict) -> List[str]:
    """Genera suggerimenti di miglioramento."""
    suggestions = []
    
    if structural["groups"] > 5:
        suggestions.append("Consider using non-capturing groups (?:...) to improve performance")
    
    if not structural["anchors"] and len(pattern) > 10:
        suggestions.append("Consider adding anchors (^ and $) for exact matching")
    
    if structural["alternations"] > 3:
        suggestions.append("Multiple alternations can be optimized with character classes")
    
    return suggestions

def calculate_pattern_quality_score(structural: Dict, performance: Dict, security: Dict) -> Dict[str, Any]:
    """Calcola un punteggio di qualità del pattern."""
    score = 100
    
    # Penalità per complessità
    if performance["complexity_rating"] == "Very High":
        score -= 30
    elif performance["complexity_rating"] == "High":
        score -= 20
    elif performance["complexity_rating"] == "Medium":
        score -= 10
    
    # Penalità per problemi di sicurezza
    if security["vulnerabilities"]:
        score -= 25
    
    # Penalità per struttura complessa
    if structural["groups"] > 10:
        score -= 15
    if structural["alternations"] > 5:
        score -= 10
    
    score = max(0, score)
    
    rating = "Excellent" if score >= 90 else "Good" if score >= 70 else "Fair" if score >= 50 else "Poor"
    
    return {
        "score": score,
        "rating": rating,
        "max_score": 100
    }

def generate_performance_recommendations(compile_time: float, match_times: List[float], complexity: int) -> List[str]:
    """Genera raccomandazioni per le performance."""
    recommendations = []
    
    avg_match_time = sum(match_times) / len(match_times) if match_times else 0
    
    if compile_time > 0.001:  # > 1ms
        recommendations.append("Pattern compilation is slow - consider simplifying")
    
    if avg_match_time > 0.0001:  # > 0.1ms
        recommendations.append("Pattern matching is slow - optimize quantifiers")
    
    if complexity > 30:
        recommendations.append("Pattern is very complex - break into smaller patterns")
    
    return recommendations

# Pattern explanation helpers
def explain_escape_sequence(seq: str) -> str:
    """Spiega una sequenza di escape."""
    explanations = {
        "\\d": "Matches any digit (0-9)",
        "\\w": "Matches any word character (a-z, A-Z, 0-9, _)",
        "\\s": "Matches any whitespace character",
        "\\D": "Matches any non-digit character",
        "\\W": "Matches any non-word character",
        "\\S": "Matches any non-whitespace character",
        "\\n": "Matches newline character",
        "\\t": "Matches tab character",
        "\\r": "Matches carriage return",
        "\\.": "Matches literal dot character",
        "\\^": "Matches literal caret character",
        "\\$": "Matches literal dollar character"
    }
    return explanations.get(seq, f"Escaped character: {seq}")

def explain_character_class(char_class: str) -> str:
    """Spiega una character class."""
    if char_class.startswith('[^'):
        return f"Matches any character NOT in the set: {char_class[2:-1]}"
    else:
        return f"Matches any character in the set: {char_class[1:-1]}"

def explain_group(group: str) -> str:
    """Spiega un gruppo."""
    if group.startswith('(?:'):
        return f"Non-capturing group: {group[3:-1]}"
    elif group.startswith('(?='):
        return f"Positive lookahead: {group[3:-1]}"
    elif group.startswith('(?!'):
        return f"Negative lookahead: {group[3:-1]}"
    else:
        return f"Capturing group: {group[1:-1]}"

def explain_quantifier(quant: str) -> str:
    """Spiega un quantificatore."""
    if quant == '*':
        return "Matches 0 or more of the preceding element"
    elif quant == '+':
        return "Matches 1 or more of the preceding element"
    elif quant == '?':
        return "Matches 0 or 1 of the preceding element"
    elif quant.startswith('{') and quant.endswith('}'):
        content = quant[1:-1]
        if ',' in content:
            parts = content.split(',')
            if len(parts[1]) == 0:
                return f"Matches {parts[0]} or more of the preceding element"
            else:
                return f"Matches between {parts[0]} and {parts[1]} of the preceding element"
        else:
            return f"Matches exactly {content} of the preceding element"
    return f"Quantifier: {quant}"

def explain_special_character(char: str) -> str:
    """Spiega un carattere speciale."""
    explanations = {
        '.': "Matches any character except newline",
        '^': "Matches start of string/line",
        '$': "Matches end of string/line",
        '|': "Alternation (OR operator)",
        '*': "Matches 0 or more of the preceding element",
        '+': "Matches 1 or more of the preceding element",
        '?': "Matches 0 or 1 of the preceding element"
    }
    return explanations.get(char, f"Special character: {char}")

def find_matching_bracket(pattern: str, start: int) -> int:
    """Trova la parentesi quadra chiusa corrispondente."""
    depth = 0
    for i in range(start, len(pattern)):
        if pattern[i] == '[':
            depth += 1
        elif pattern[i] == ']':
            depth -= 1
            if depth == 0:
                return i
    return -1

def find_matching_parenthesis(pattern: str, start: int) -> int:
    """Trova la parentesi tonda chiusa corrispondente."""
    depth = 0
    for i in range(start, len(pattern)):
        if pattern[i] == '(':
            depth += 1
        elif pattern[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    return -1

def generate_natural_explanation(breakdown: List[Dict]) -> str:
    """Genera una spiegazione in linguaggio naturale."""
    explanations = [item["explanation"] for item in breakdown]
    return "This pattern: " + " → ".join(explanations)

def generate_example_matches(pattern: str) -> List[str]:
    """Genera esempi di testo che dovrebbero fare match."""
    # Questa è una versione semplificata - in un'implementazione completa
    # si potrebbero usare librerie come hypothesis per generare esempi
    examples = []
    
    try:
        compiled = re.compile(pattern)
        
        # Test con stringhe comuni
        test_strings = [
            "test", "123", "abc123", "Test@Example.com", 
            "2023-12-25", "10:30", "+1-555-123-4567"
        ]
        
        for test_str in test_strings:
            if compiled.match(test_str):
                examples.append(test_str)
        
        if not examples:
            examples = ["(Pattern may be very specific - manual testing recommended)"]
        
    except:
        examples = ["(Unable to generate examples for this pattern)"]
    
    return examples[:5]  # Limit to 5 examples