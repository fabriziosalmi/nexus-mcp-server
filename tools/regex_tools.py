# -*- coding: utf-8 -*-
# tools/regex_tools.py
import re
import logging

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