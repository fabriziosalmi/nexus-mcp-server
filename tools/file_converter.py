# -*- coding: utf-8 -*-
# tools/file_converter.py
import json
import csv
import io
import re
import logging
from xml.etree import ElementTree as ET

def register_tools(mcp):
    """Registra i tool di conversione file con l'istanza del server MCP."""
    logging.info("🔄 Registrazione tool-set: File Converter Tools")

    @mcp.tool()
    def csv_to_json(csv_content: str, delimiter: str = ",", has_header: bool = True) -> str:
        """
        Converte contenuto CSV in formato JSON.

        Args:
            csv_content: Il contenuto CSV da convertire.
            delimiter: Il delimitatore CSV (default virgola).
            has_header: Se la prima riga contiene i nomi delle colonne.
        """
        try:
            if not csv_content.strip():
                return "ERRORE: Il contenuto CSV non può essere vuoto"
            
            # Parse CSV
            csv_reader = csv.reader(io.StringIO(csv_content), delimiter=delimiter)
            rows = list(csv_reader)
            
            if not rows:
                return "ERRORE: Nessuna riga trovata nel CSV"
            
            result_data = []
            
            if has_header:
                if len(rows) < 2:
                    return "ERRORE: CSV con header deve avere almeno 2 righe"
                
                headers = rows[0]
                for row in rows[1:]:
                    # Pad row se ha meno colonne degli header
                    while len(row) < len(headers):
                        row.append("")
                    
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header] = row[i] if i < len(row) else ""
                    result_data.append(row_dict)
            else:
                # Senza header, usa indici numerici
                for i, row in enumerate(rows):
                    row_dict = {}
                    for j, cell in enumerate(row):
                        row_dict[f"column_{j}"] = cell
                    result_data.append(row_dict)
            
            # Converti in JSON
            json_output = json.dumps(result_data, indent=2, ensure_ascii=False)
            
            result = "=== CONVERSIONE CSV → JSON ===\n"
            result += f"Righe processate: {len(rows)}\n"
            result += f"Record JSON: {len(result_data)}\n"
            result += f"Delimitatore: '{delimiter}'\n"
            result += f"Header: {'Sì' if has_header else 'No'}\n\n"
            result += "JSON RISULTANTE:\n"
            result += json_output
            
            return result
            
        except csv.Error as e:
            return f"ERRORE CSV: {str(e)}"
        except json.JSONDecodeError as e:
            return f"ERRORE JSON: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def json_to_csv(json_content: str, delimiter: str = ",", include_header: bool = True) -> str:
        """
        Converte contenuto JSON in formato CSV.

        Args:
            json_content: Il contenuto JSON da convertire (array di oggetti).
            delimiter: Il delimitatore per il CSV (default virgola).
            include_header: Se includere la riga header con i nomi delle colonne.
        """
        try:
            if not json_content.strip():
                return "ERRORE: Il contenuto JSON non può essere vuoto"
            
            # Parse JSON
            data = json.loads(json_content)
            
            if not isinstance(data, list):
                return "ERRORE: Il JSON deve essere un array di oggetti"
            
            if not data:
                return "ERRORE: L'array JSON è vuoto"
            
            if not all(isinstance(item, dict) for item in data):
                return "ERRORE: Tutti gli elementi dell'array devono essere oggetti"
            
            # Raccogli tutte le chiavi possibili
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())
            
            all_keys = sorted(list(all_keys))  # Ordina per consistenza
            
            # Crea CSV
            output = io.StringIO()
            csv_writer = csv.writer(output, delimiter=delimiter)
            
            # Scrivi header se richiesto
            if include_header:
                csv_writer.writerow(all_keys)
            
            # Scrivi dati
            for item in data:
                row = [str(item.get(key, "")) for key in all_keys]
                csv_writer.writerow(row)
            
            csv_output = output.getvalue()
            
            result = "=== CONVERSIONE JSON → CSV ===\n"
            result += f"Record processati: {len(data)}\n"
            result += f"Colonne: {len(all_keys)}\n"
            result += f"Delimitatore: '{delimiter}'\n"
            result += f"Header: {'Sì' if include_header else 'No'}\n\n"
            result += "CSV RISULTANTE:\n"
            result += csv_output
            
            return result
            
        except json.JSONDecodeError as e:
            return f"ERRORE JSON: {str(e)}"
        except csv.Error as e:
            return f"ERRORE CSV: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def json_to_xml(json_content: str, root_name: str = "root") -> str:
        """
        Converte contenuto JSON in formato XML.

        Args:
            json_content: Il contenuto JSON da convertire.
            root_name: Nome dell'elemento radice XML.
        """
        try:
            if not json_content.strip():
                return "ERRORE: Il contenuto JSON non può essere vuoto"
            
            # Parse JSON
            data = json.loads(json_content)
            
            def json_to_xml_element(obj, parent_name="item"):
                """Converte ricorsivamente JSON in elementi XML."""
                if isinstance(obj, dict):
                    element = ET.Element(parent_name)
                    for key, value in obj.items():
                        # Sanitize key per XML
                        safe_key = re.sub(r'[^a-zA-Z0-9_-]', '_', str(key))
                        if safe_key[0].isdigit():
                            safe_key = f"item_{safe_key}"
                        
                        child = json_to_xml_element(value, safe_key)
                        element.append(child)
                    return element
                    
                elif isinstance(obj, list):
                    element = ET.Element(parent_name)
                    for i, item in enumerate(obj):
                        child = json_to_xml_element(item, f"item_{i}")
                        element.append(child)
                    return element
                    
                else:
                    element = ET.Element(parent_name)
                    element.text = str(obj) if obj is not None else ""
                    return element
            
            # Crea l'elemento radice
            root = json_to_xml_element(data, root_name)
            
            # Converti in stringa XML
            xml_string = ET.tostring(root, encoding='unicode', method='xml')
            
            # Formatta per leggibilità (basic formatting)
            formatted_xml = xml_string.replace('><', '>\n<')
            
            result = "=== CONVERSIONE JSON → XML ===\n"
            result += f"Elemento radice: {root_name}\n"
            result += f"Tipo JSON: {type(data).__name__}\n\n"
            result += "XML RISULTANTE:\n"
            result += '<?xml version="1.0" encoding="UTF-8"?>\n'
            result += formatted_xml
            
            return result
            
        except json.JSONDecodeError as e:
            return f"ERRORE JSON: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def xml_to_json(xml_content: str) -> str:
        """
        Converte contenuto XML in formato JSON.

        Args:
            xml_content: Il contenuto XML da convertire.
        """
        try:
            if not xml_content.strip():
                return "ERRORE: Il contenuto XML non può essere vuoto"
            
            def xml_to_dict(element):
                """Converte ricorsivamente elementi XML in dizionario."""
                result = {}
                
                # Attributi dell'elemento
                if element.attrib:
                    result['@attributes'] = element.attrib
                
                # Testo dell'elemento
                if element.text and element.text.strip():
                    if len(element) == 0:  # Nessun figlio
                        return element.text.strip()
                    else:
                        result['@text'] = element.text.strip()
                
                # Elementi figli
                children = {}
                for child in element:
                    child_data = xml_to_dict(child)
                    if child.tag in children:
                        # Se già esiste, crea una lista
                        if not isinstance(children[child.tag], list):
                            children[child.tag] = [children[child.tag]]
                        children[child.tag].append(child_data)
                    else:
                        children[child.tag] = child_data
                
                result.update(children)
                
                # Se result ha solo un elemento che non è attributi, restituisci direttamente
                if len(result) == 1 and '@attributes' not in result and '@text' not in result:
                    return list(result.values())[0]
                    
                return result if result else None
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Converti in dizionario
            data = {root.tag: xml_to_dict(root)}
            
            # Converti in JSON
            json_output = json.dumps(data, indent=2, ensure_ascii=False)
            
            result = "=== CONVERSIONE XML → JSON ===\n"
            result += f"Elemento radice: {root.tag}\n"
            result += f"Numero di figli diretti: {len(root)}\n\n"
            result += "JSON RISULTANTE:\n"
            result += json_output
            
            return result
            
        except ET.ParseError as e:
            return f"ERRORE XML: {str(e)}"
        except json.JSONDecodeError as e:
            return f"ERRORE JSON: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def txt_to_json_lines(text_content: str, line_key: str = "line") -> str:
        """
        Converte un file di testo in JSON con ogni riga come elemento di array.

        Args:
            text_content: Il contenuto del file di testo.
            line_key: Nome della chiave per ogni riga nel JSON.
        """
        try:
            if not text_content:
                return "ERRORE: Il contenuto del testo non può essere vuoto"
            
            lines = text_content.split('\n')
            
            # Rimuovi righe vuote se richiesto
            non_empty_lines = [line for line in lines if line.strip()]
            
            # Crea struttura JSON
            data = []
            for i, line in enumerate(lines, 1):
                data.append({
                    "line_number": i,
                    line_key: line,
                    "is_empty": not line.strip(),
                    "length": len(line)
                })
            
            json_output = json.dumps(data, indent=2, ensure_ascii=False)
            
            result = "=== CONVERSIONE TXT → JSON ===\n"
            result += f"Righe totali: {len(lines)}\n"
            result += f"Righe non vuote: {len(non_empty_lines)}\n"
            result += f"Caratteri totali: {len(text_content)}\n\n"
            result += "JSON RISULTANTE:\n"
            result += json_output
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def json_lines_to_txt(json_content: str, line_field: str = "line") -> str:
        """
        Converte JSON lines in formato testo.

        Args:
            json_content: Il contenuto JSON (array di oggetti).
            line_field: Campo che contiene il testo della riga.
        """
        try:
            if not json_content.strip():
                return "ERRORE: Il contenuto JSON non può essere vuoto"
            
            data = json.loads(json_content)
            
            if not isinstance(data, list):
                return "ERRORE: Il JSON deve essere un array"
            
            lines = []
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    if line_field in item:
                        lines.append(str(item[line_field]))
                    else:
                        # Se non c'è il campo specifico, usa il primo campo stringa trovato
                        for key, value in item.items():
                            if isinstance(value, str):
                                lines.append(value)
                                break
                        else:
                            lines.append(f"[Oggetto {i+1}: {json.dumps(item)}]")
                else:
                    lines.append(str(item))
            
            text_output = '\n'.join(lines)
            
            result = "=== CONVERSIONE JSON → TXT ===\n"
            result += f"Oggetti processati: {len(data)}\n"
            result += f"Righe generate: {len(lines)}\n"
            result += f"Campo usato: {line_field}\n\n"
            result += "TESTO RISULTANTE:\n"
            result += text_output
            
            return result
            
        except json.JSONDecodeError as e:
            return f"ERRORE JSON: {str(e)}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def detect_file_format(content: str) -> str:
        """
        Tenta di rilevare automaticamente il formato di un file dal suo contenuto.

        Args:
            content: Il contenuto del file da analizzare.
        """
        try:
            if not content.strip():
                return "ERRORE: Il contenuto non può essere vuoto"
            
            content_sample = content[:1000]  # Analizza i primi 1000 caratteri
            
            result = "=== RILEVAMENTO FORMATO FILE ===\n"
            result += f"Dimensione contenuto: {len(content)} caratteri\n"
            result += f"Sample analizzato: {len(content_sample)} caratteri\n\n"
            
            # Test JSON
            try:
                json.loads(content)
                result += "✅ FORMATO RILEVATO: JSON\n"
                result += "Contenuto valido JSON\n"
                return result
            except:
                pass
            
            # Test XML
            try:
                ET.fromstring(content)
                result += "✅ FORMATO RILEVATO: XML\n"
                result += "Contenuto valido XML\n"
                return result
            except:
                pass
            
            # Test CSV
            try:
                # Prova diversi delimitatori
                for delimiter in [',', ';', '\t', '|']:
                    csv_reader = csv.reader(io.StringIO(content_sample), delimiter=delimiter)
                    rows = list(csv_reader)
                    if len(rows) > 1 and len(rows[0]) > 1:
                        # Se abbiamo più righe e più colonne, probabilmente è CSV
                        consistent_columns = all(len(row) == len(rows[0]) for row in rows[:5])
                        if consistent_columns:
                            result += f"✅ FORMATO RILEVATO: CSV\n"
                            result += f"Delimitatore probabile: '{delimiter}'\n"
                            result += f"Colonne rilevate: {len(rows[0])}\n"
                            result += f"Righe campione: {len(rows)}\n"
                            return result
            except:
                pass
            
            # Test file di testo con pattern
            lines = content.split('\n')
            
            # Controlla se sembra un file di log
            log_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # Date
                r'\d{2}:\d{2}:\d{2}',  # Time
                r'\[.*\]',             # Brackets
                r'ERROR|INFO|DEBUG|WARN'  # Log levels
            ]
            
            log_score = 0
            for line in lines[:10]:  # Analizza prime 10 righe
                for pattern in log_patterns:
                    if re.search(pattern, line):
                        log_score += 1
            
            if log_score > 3:
                result += "✅ FORMATO RILEVATO: LOG FILE\n"
                result += f"Pattern di log rilevati: {log_score}\n"
                return result
            
            # Default: testo semplice
            result += "✅ FORMATO RILEVATO: TESTO SEMPLICE\n"
            result += f"Righe: {len(lines)}\n"
            result += f"Riga più lunga: {max(len(line) for line in lines) if lines else 0} caratteri\n"
            
            # Statistiche aggiuntive
            if lines:
                non_empty = [line for line in lines if line.strip()]
                result += f"Righe non vuote: {len(non_empty)}\n"
                
                # Cerca pattern comuni
                if any('@' in line and '.' in line for line in lines):
                    result += "Possibili email rilevate\n"
                
                if any(line.startswith('http') for line in lines):
                    result += "Possibili URL rilevati\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def conversion_help() -> str:
        """
        Fornisce informazioni sui formati supportati e le conversioni disponibili.
        """
        try:
            help_text = """=== GUIDA CONVERSIONI FILE ===

📋 FORMATI SUPPORTATI:
• JSON (JavaScript Object Notation)
• CSV (Comma-Separated Values)
• XML (eXtensible Markup Language)
• TXT (Testo semplice)

🔄 CONVERSIONI DISPONIBILI:

1. CSV → JSON
   - Converte tabelle CSV in formato JSON
   - Supporta header personalizzati
   - Delimitatori configurabili

2. JSON → CSV
   - Converte array di oggetti JSON in CSV
   - Include header automatici
   - Gestisce oggetti con campi diversi

3. JSON → XML
   - Converte strutture JSON in XML
   - Elemento radice configurabile
   - Gestione array e oggetti annidati

4. XML → JSON
   - Converte documenti XML in JSON
   - Preserva attributi e struttura
   - Gestisce elementi multipli

5. TXT → JSON
   - Converte file di testo in JSON linea per linea
   - Include metadati riga (numero, lunghezza)
   - Gestisce righe vuote

6. JSON → TXT
   - Estrae testo da strutture JSON
   - Campo testo configurabile
   - Formato linea per linea

⚙️ PARAMETRI COMUNI:

CSV:
- delimiter: Delimitatore (default: virgola)
- has_header/include_header: Gestione header
- quote_char: Carattere di quotazione

JSON:
- indent: Indentazione per formattazione
- ensure_ascii: Encoding caratteri speciali

XML:
- root_name: Nome elemento radice
- formatting: Formattazione output

💡 SUGGERIMENTI:

1. Usa detect_file_format() per identificare il formato
2. Per CSV con delimitatori diversi, specifica il parametro
3. I file XML devono essere ben formati
4. JSON deve contenere array di oggetti per CSV
5. Testa su campioni piccoli prima di file grandi

🚨 LIMITAZIONI:

- Dimensione massima file: dipende dalla memoria
- XML: solo elementi, non DTD/Schema
- CSV: supporto base, non tutte le varianti
- Encoding: UTF-8 raccomandato"""

            return help_text
            
        except Exception as e:
            return f"ERRORE: {str(e)}"