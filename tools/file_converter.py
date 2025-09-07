# -*- coding: utf-8 -*-
# tools/file_converter.py
import json
import csv
import io
import re
import logging
import configparser
import base64
from xml.etree import ElementTree as ET
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import urllib.parse

# Try to import additional libraries
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

def register_tools(mcp):
    """Registra i tool di conversione file avanzati con l'istanza del server MCP."""
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

    @mcp.tool()
    def convert_yaml(content: str, source_format: str, target_format: str, 
                    options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Converte da/verso formato YAML.
        
        Args:
            content: Contenuto da convertire
            source_format: Formato sorgente (yaml, json, toml)
            target_format: Formato destinazione (yaml, json, toml)
            options: Opzioni conversione
        """
        try:
            if not YAML_AVAILABLE:
                return {
                    "success": False,
                    "error": "YAML library not available. Install with: pip install PyYAML"
                }
            
            options = options or {}
            
            # Parse contenuto sorgente
            if source_format.lower() == "yaml":
                try:
                    data = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    return {"success": False, "error": f"Invalid YAML: {str(e)}"}
            
            elif source_format.lower() == "json":
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"Invalid JSON: {str(e)}"}
            
            elif source_format.lower() == "toml" and TOML_AVAILABLE:
                try:
                    data = toml.loads(content)
                except Exception as e:
                    return {"success": False, "error": f"Invalid TOML: {str(e)}"}
            
            else:
                return {"success": False, "error": f"Unsupported source format: {source_format}"}
            
            # Converti al formato destinazione
            if target_format.lower() == "yaml":
                converted_content = yaml.dump(
                    data, 
                    default_flow_style=options.get("flow_style", False),
                    allow_unicode=options.get("unicode", True),
                    indent=options.get("indent", 2)
                )
            
            elif target_format.lower() == "json":
                converted_content = json.dumps(
                    data,
                    indent=options.get("indent", 2),
                    ensure_ascii=options.get("ensure_ascii", False),
                    sort_keys=options.get("sort_keys", False)
                )
            
            elif target_format.lower() == "toml" and TOML_AVAILABLE:
                converted_content = toml.dumps(data)
            
            else:
                return {"success": False, "error": f"Unsupported target format: {target_format}"}
            
            # Analizza struttura dati
            data_analysis = _analyze_data_structure(data)
            
            return {
                "success": True,
                "source_format": source_format,
                "target_format": target_format,
                "converted_content": converted_content,
                "content_length": len(converted_content),
                "original_length": len(content),
                "compression_ratio": round((1 - len(converted_content) / len(content)) * 100, 2) if len(content) > 0 else 0,
                "data_analysis": data_analysis
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def batch_convert_data(data_items: List[Dict[str, Any]], source_format: str, 
                          target_format: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Converte batch di dati tra formati.
        
        Args:
            data_items: Lista di item da convertire (ogni item ha 'content' e opzionale 'name')
            source_format: Formato sorgente
            target_format: Formato destinazione
            options: Opzioni conversione
        """
        try:
            if not data_items:
                return {"success": False, "error": "No data items provided"}
            
            if len(data_items) > 100:
                return {"success": False, "error": "Too many items (max 100)"}
            
            options = options or {}
            results = []
            successful_conversions = 0
            total_original_size = 0
            total_converted_size = 0
            
            for i, item in enumerate(data_items):
                item_name = item.get("name", f"item_{i+1}")
                content = item.get("content", "")
                
                if not content:
                    results.append({
                        "name": item_name,
                        "success": False,
                        "error": "Empty content"
                    })
                    continue
                
                # Converti singolo item
                conversion_result = _convert_single_item(content, source_format, target_format, options)
                
                result_item = {
                    "name": item_name,
                    "success": conversion_result["success"]
                }
                
                if conversion_result["success"]:
                    result_item.update({
                        "converted_content": conversion_result["converted_content"],
                        "original_size": len(content),
                        "converted_size": len(conversion_result["converted_content"])
                    })
                    successful_conversions += 1
                    total_original_size += len(content)
                    total_converted_size += len(conversion_result["converted_content"])
                else:
                    result_item["error"] = conversion_result["error"]
                
                results.append(result_item)
            
            return {
                "success": True,
                "source_format": source_format,
                "target_format": target_format,
                "total_items": len(data_items),
                "successful_conversions": successful_conversions,
                "failed_conversions": len(data_items) - successful_conversions,
                "total_original_size": total_original_size,
                "total_converted_size": total_converted_size,
                "overall_compression_ratio": round((1 - total_converted_size / total_original_size) * 100, 2) if total_original_size > 0 else 0,
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def validate_data_format(content: str, expected_format: str, 
                           strict_mode: bool = True) -> Dict[str, Any]:
        """
        Valida formato dati e fornisce analisi dettagliata.
        
        Args:
            content: Contenuto da validare
            expected_format: Formato atteso (json, xml, csv, yaml, toml)
            strict_mode: Se usare validazione rigorosa
        """
        try:
            validation_result = {
                "success": True,
                "format": expected_format,
                "is_valid": False,
                "errors": [],
                "warnings": [],
                "statistics": {},
                "suggestions": []
            }
            
            content_stats = {
                "length": len(content),
                "lines": len(content.split('\n')),
                "non_empty_lines": len([line for line in content.split('\n') if line.strip()]),
                "whitespace_ratio": (len(content) - len(content.replace(' ', '').replace('\t', '').replace('\n', ''))) / len(content) if content else 0
            }
            
            if expected_format.lower() == "json":
                try:
                    data = json.loads(content)
                    validation_result["is_valid"] = True
                    validation_result["statistics"] = {
                        **content_stats,
                        "data_type": type(data).__name__,
                        "object_depth": _calculate_object_depth(data),
                        "total_keys": _count_total_keys(data) if isinstance(data, dict) else 0,
                        "array_length": len(data) if isinstance(data, list) else 0
                    }
                    
                    # Controlli aggiuntivi
                    if isinstance(data, dict) and not data:
                        validation_result["warnings"].append("Empty JSON object")
                    
                    if _calculate_object_depth(data) > 10:
                        validation_result["warnings"].append("Very deep nesting (>10 levels)")
                    
                except json.JSONDecodeError as e:
                    validation_result["errors"].append(f"JSON syntax error: {str(e)}")
                    
                    if strict_mode:
                        # Analizza errori comuni
                        if "Expecting ',' delimiter" in str(e):
                            validation_result["suggestions"].append("Check for missing commas between JSON elements")
                        elif "Expecting property name" in str(e):
                            validation_result["suggestions"].append("Check for unquoted property names")
            
            elif expected_format.lower() == "xml":
                try:
                    root = ET.fromstring(content)
                    validation_result["is_valid"] = True
                    
                    # Analisi XML
                    all_elements = root.findall(".//*")
                    validation_result["statistics"] = {
                        **content_stats,
                        "root_element": root.tag,
                        "total_elements": len(all_elements) + 1,  # +1 per root
                        "max_depth": _calculate_xml_depth(root),
                        "has_attributes": any(elem.attrib for elem in all_elements + [root]),
                        "has_text_content": any(elem.text and elem.text.strip() for elem in all_elements + [root])
                    }
                    
                except ET.ParseError as e:
                    validation_result["errors"].append(f"XML parse error: {str(e)}")
                    
                    if strict_mode:
                        if "not well-formed" in str(e):
                            validation_result["suggestions"].append("Check for unclosed tags or invalid characters")
            
            elif expected_format.lower() == "csv":
                try:
                    # Prova diversi delimitatori
                    delimiters = [',', ';', '\t', '|']
                    best_delimiter = None
                    max_columns = 0
                    
                    for delimiter in delimiters:
                        try:
                            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
                            rows = list(reader)
                            if rows:
                                avg_columns = sum(len(row) for row in rows) / len(rows)
                                if avg_columns > max_columns:
                                    max_columns = avg_columns
                                    best_delimiter = delimiter
                        except:
                            continue
                    
                    if best_delimiter and max_columns > 1:
                        validation_result["is_valid"] = True
                        reader = csv.reader(io.StringIO(content), delimiter=best_delimiter)
                        rows = list(reader)
                        
                        validation_result["statistics"] = {
                            **content_stats,
                            "detected_delimiter": best_delimiter,
                            "total_rows": len(rows),
                            "average_columns": round(max_columns, 1),
                            "consistent_columns": len(set(len(row) for row in rows)) == 1,
                            "empty_cells": sum(1 for row in rows for cell in row if not cell.strip())
                        }
                        
                        if not validation_result["statistics"]["consistent_columns"]:
                            validation_result["warnings"].append("Inconsistent column count across rows")
                    
                    else:
                        validation_result["errors"].append("No valid CSV structure detected")
                        
                except Exception as e:
                    validation_result["errors"].append(f"CSV validation error: {str(e)}")
            
            elif expected_format.lower() == "yaml" and YAML_AVAILABLE:
                try:
                    data = yaml.safe_load(content)
                    validation_result["is_valid"] = True
                    validation_result["statistics"] = {
                        **content_stats,
                        "data_type": type(data).__name__,
                        "indentation_consistent": _check_yaml_indentation(content)
                    }
                    
                except yaml.YAMLError as e:
                    validation_result["errors"].append(f"YAML syntax error: {str(e)}")
            
            elif expected_format.lower() == "toml" and TOML_AVAILABLE:
                try:
                    data = toml.loads(content)
                    validation_result["is_valid"] = True
                    validation_result["statistics"] = {
                        **content_stats,
                        "sections": len([line for line in content.split('\n') if line.strip().startswith('[') and line.strip().endswith(']')])
                    }
                    
                except Exception as e:
                    validation_result["errors"].append(f"TOML syntax error: {str(e)}")
            
            else:
                validation_result["errors"].append(f"Unsupported format: {expected_format}")
            
            # Raccomandazioni generali
            if validation_result["is_valid"]:
                if content_stats["whitespace_ratio"] > 0.3:
                    validation_result["suggestions"].append("Consider minifying to reduce whitespace")
                
                if content_stats["length"] > 1000000:  # 1MB
                    validation_result["suggestions"].append("Large file size - consider compression or chunking")
            
            return validation_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def transform_data_structure(content: str, source_format: str, 
                               transformations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applica trasformazioni ai dati durante la conversione.
        
        Args:
            content: Contenuto da trasformare
            source_format: Formato sorgente
            transformations: Lista di trasformazioni da applicare
        """
        try:
            # Parse contenuto
            if source_format.lower() == "json":
                data = json.loads(content)
            elif source_format.lower() == "yaml" and YAML_AVAILABLE:
                data = yaml.safe_load(content)
            elif source_format.lower() == "xml":
                root = ET.fromstring(content)
                data = _xml_to_dict_advanced(root)
            else:
                return {"success": False, "error": f"Unsupported format for transformation: {source_format}"}
            
            original_data = data.copy() if isinstance(data, dict) else data[:]
            applied_transformations = []
            
            # Applica trasformazioni
            for transform in transformations:
                transform_type = transform.get("type")
                
                if transform_type == "filter":
                    # Filtra dati in base a condizioni
                    condition = transform.get("condition", {})
                    data = _apply_filter(data, condition)
                    applied_transformations.append("filter")
                
                elif transform_type == "map":
                    # Mappa campi
                    mapping = transform.get("mapping", {})
                    data = _apply_mapping(data, mapping)
                    applied_transformations.append("map")
                
                elif transform_type == "aggregate":
                    # Aggrega dati
                    group_by = transform.get("group_by")
                    agg_function = transform.get("function", "count")
                    data = _apply_aggregation(data, group_by, agg_function)
                    applied_transformations.append("aggregate")
                
                elif transform_type == "sort":
                    # Ordina dati
                    sort_key = transform.get("key")
                    reverse = transform.get("reverse", False)
                    data = _apply_sorting(data, sort_key, reverse)
                    applied_transformations.append("sort")
                
                elif transform_type == "flatten":
                    # Appiattisce strutture annidate
                    separator = transform.get("separator", ".")
                    data = _flatten_structure(data, separator)
                    applied_transformations.append("flatten")
            
            return {
                "success": True,
                "source_format": source_format,
                "transformations_applied": applied_transformations,
                "original_size": len(str(original_data)),
                "transformed_size": len(str(data)),
                "transformed_data": data,
                "transformation_summary": {
                    "original_type": type(original_data).__name__,
                    "transformed_type": type(data).__name__,
                    "original_length": len(original_data) if isinstance(original_data, (list, dict)) else 0,
                    "transformed_length": len(data) if isinstance(data, (list, dict)) else 0
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_conversion_template(source_format: str, target_format: str, 
                                   sample_data: str = "") -> Dict[str, Any]:
        """
        Genera template per conversioni specifiche.
        
        Args:
            source_format: Formato sorgente
            target_format: Formato destinazione
            sample_data: Dati campione per personalizzare template
        """
        try:
            template_info = {
                "success": True,
                "source_format": source_format,
                "target_format": target_format,
                "template": "",
                "options": {},
                "best_practices": [],
                "example_usage": ""
            }
            
            conversion_key = f"{source_format.lower()}_to_{target_format.lower()}"
            
            # Template specifici per conversione
            templates = {
                "csv_to_json": {
                    "template": '''import csv
import json

def convert_csv_to_json(csv_content, delimiter=",", has_header=True):
    reader = csv.DictReader(csv_content.splitlines(), delimiter=delimiter)
    return json.dumps(list(reader), indent=2)''',
                    "options": {"delimiter": ",", "has_header": True, "indent": 2},
                    "best_practices": [
                        "Validate CSV structure before conversion",
                        "Handle missing values appropriately",
                        "Use consistent field names"
                    ]
                },
                
                "json_to_xml": {
                    "template": '''import json
import xml.etree.ElementTree as ET

def convert_json_to_xml(json_content, root_name="root"):
    data = json.loads(json_content)
    root = ET.Element(root_name)
    # Add conversion logic here
    return ET.tostring(root, encoding='unicode')''',
                    "options": {"root_name": "root", "encoding": "unicode"},
                    "best_practices": [
                        "Sanitize JSON keys for XML compatibility",
                        "Handle arrays and nested objects properly",
                        "Include XML declaration"
                    ]
                },
                
                "yaml_to_json": {
                    "template": '''import yaml
import json

def convert_yaml_to_json(yaml_content, indent=2):
    data = yaml.safe_load(yaml_content)
    return json.dumps(data, indent=indent)''',
                    "options": {"indent": 2, "ensure_ascii": False},
                    "best_practices": [
                        "Use safe_load for security",
                        "Handle YAML-specific types",
                        "Preserve data structure"
                    ]
                }
            }
            
            if conversion_key in templates:
                template_data = templates[conversion_key]
                template_info.update(template_data)
            else:
                # Template generico
                template_info["template"] = f"""# Generic conversion template
# Source: {source_format.upper()}
# Target: {target_format.upper()}

def convert_data(content):
    # 1. Parse source format
    # 2. Transform data structure
    # 3. Generate target format
    pass"""
                
                template_info["best_practices"] = [
                    "Validate input format",
                    "Handle edge cases",
                    "Test with various data samples",
                    "Include error handling"
                ]
            
            # Analizza sample data se fornito
            if sample_data:
                sample_analysis = _analyze_sample_data(sample_data, source_format)
                template_info["sample_analysis"] = sample_analysis
                template_info["recommended_options"] = _get_recommended_options(sample_analysis, target_format)
            
            return template_info
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def optimize_conversion_output(content: str, target_format: str, 
                                 optimization_goals: List[str] = None) -> Dict[str, Any]:
        """
        Ottimizza output conversione per obiettivi specifici.
        
        Args:
            content: Contenuto da ottimizzare
            target_format: Formato di output
            optimization_goals: Obiettivi (size, readability, performance)
        """
        try:
            optimization_goals = optimization_goals or ["size"]
            
            optimized_versions = {}
            
            for goal in optimization_goals:
                if goal == "size":
                    # Ottimizza per dimensione
                    if target_format.lower() == "json":
                        data = json.loads(content)
                        optimized_content = json.dumps(data, separators=(',', ':'))
                    elif target_format.lower() == "xml":
                        # Rimuovi whitespace non necessario
                        optimized_content = re.sub(r'>\s+<', '><', content)
                    else:
                        optimized_content = content.strip()
                    
                    optimized_versions["size_optimized"] = {
                        "content": optimized_content,
                        "original_size": len(content),
                        "optimized_size": len(optimized_content),
                        "reduction_percent": round((1 - len(optimized_content) / len(content)) * 100, 2) if len(content) > 0 else 0
                    }
                
                elif goal == "readability":
                    # Ottimizza per leggibilità
                    if target_format.lower() == "json":
                        data = json.loads(content)
                        optimized_content = json.dumps(data, indent=4, sort_keys=True)
                    elif target_format.lower() == "xml":
                        # Formatta XML con indentazione
                        optimized_content = _format_xml_pretty(content)
                    else:
                        optimized_content = content
                    
                    optimized_versions["readability_optimized"] = {
                        "content": optimized_content,
                        "formatting": "enhanced",
                        "indentation": 4
                    }
                
                elif goal == "performance":
                    # Ottimizza per performance parsing
                    if target_format.lower() == "json":
                        data = json.loads(content)
                        # Converti a struttura più piatta se possibile
                        optimized_content = json.dumps(_flatten_for_performance(data))
                    else:
                        optimized_content = content
                    
                    optimized_versions["performance_optimized"] = {
                        "content": optimized_content,
                        "structure": "flattened"
                    }
            
            return {
                "success": True,
                "target_format": target_format,
                "optimization_goals": optimization_goals,
                "optimized_versions": optimized_versions,
                "recommendations": _get_optimization_recommendations(content, target_format)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Enhanced helper functions
    def _convert_single_item(content: str, source_format: str, target_format: str, options: Dict) -> Dict[str, Any]:
        """Converte singolo item tra formati."""
        try:
            # Parse source
            if source_format.lower() == "json":
                data = json.loads(content)
            elif source_format.lower() == "yaml" and YAML_AVAILABLE:
                data = yaml.safe_load(content)
            elif source_format.lower() == "xml":
                root = ET.fromstring(content)
                data = _xml_to_dict_advanced(root)
            else:
                return {"success": False, "error": f"Unsupported source format: {source_format}"}
            
            # Convert to target
            if target_format.lower() == "json":
                converted_content = json.dumps(data, indent=options.get("indent", 2))
            elif target_format.lower() == "yaml" and YAML_AVAILABLE:
                converted_content = yaml.dump(data, default_flow_style=False)
            elif target_format.lower() == "xml":
                root = _dict_to_xml_advanced(data, options.get("root_name", "root"))
                converted_content = ET.tostring(root, encoding='unicode')
            else:
                return {"success": False, "error": f"Unsupported target format: {target_format}"}
            
            return {
                "success": True,
                "converted_content": converted_content
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_data_structure(data: Any) -> Dict[str, Any]:
        """Analizza struttura dati."""
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": len(data),
                "depth": _calculate_object_depth(data),
                "has_arrays": any(isinstance(v, list) for v in data.values()),
                "has_nested_objects": any(isinstance(v, dict) for v in data.values())
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "item_types": list(set(type(item).__name__ for item in data[:10])),
                "uniform_structure": len(set(type(item).__name__ for item in data)) == 1
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:100] + "..." if len(str(data)) > 100 else str(data)
            }

    def _calculate_object_depth(obj: Any, current_depth: int = 0) -> int:
        """Calcola profondità oggetto."""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(_calculate_object_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(_calculate_object_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth

    def _count_total_keys(obj: Any) -> int:
        """Conta chiavi totali in oggetto."""
        if isinstance(obj, dict):
            return len(obj) + sum(_count_total_keys(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(_count_total_keys(item) for item in obj)
        else:
            return 0

    def _calculate_xml_depth(element: ET.Element, current_depth: int = 0) -> int:
        """Calcola profondità XML."""
        if not list(element):
            return current_depth
        return max(_calculate_xml_depth(child, current_depth + 1) for child in element)

    def _check_yaml_indentation(content: str) -> bool:
        """Verifica consistenza indentazione YAML."""
        lines = content.split('\n')
        indentations = []
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    indentations.append(indent)
        
        if not indentations:
            return True
        
        # Verifica che le indentazioni siano multiple di un valore base
        base_indent = min(indentations)
        return all(indent % base_indent == 0 for indent in indentations)

    def _apply_filter(data: Any, condition: Dict[str, Any]) -> Any:
        """Applica filtro ai dati in base a condizioni."""
        # Implementa logica filtro avanzata qui
        return data

    def _apply_mapping(data: Any, mapping: Dict[str, str]) -> Any:
        """Applica mappatura campi ai dati."""
        # Implementa logica mappatura avanzata qui
        return data

    def _apply_aggregation(data: Any, group_by: str, agg_function: str) -> Any:
        """Applica aggregazione ai dati."""
        # Implementa logica aggregazione avanzata qui
        return data

    def _apply_sorting(data: Any, sort_key: str, reverse: bool) -> Any:
        """Applica ordinamento ai dati."""
        # Implementa logica ordinamento avanzata qui
        return data

    def _flatten_structure(data: Any, separator: str) -> Any:
        """Appiattisce strutture dati annidate."""
        # Implementa logica appiattimento avanzata qui
        return data

    def _format_xml_pretty(xml_content: str) -> str:
        """Formatta XML con indentazione per leggibilità."""
        try:
            from xml.dom import minidom
            xml_dom = minidom.parseString(xml_content)
            return xml_dom.toprettyxml(indent="  ", newl="\n", encoding="UTF-8").decode("UTF-8")
        except Exception as e:
            return xml_content  # Restituisci originale in caso di errore

    def _flatten_for_performance(data: Any) -> Any:
        """Converte dati in una struttura più piatta per migliorare le performance di parsing."""
        # Implementa logica flattening per performance qui
        return data

    def _get_optimization_recommendations(content: str, target_format: str) -> List[str]:
        """Fornisce raccomandazioni per ottimizzare l'output della conversione."""
        recommendations = []
        
        if target_format.lower() == "json":
            # Raccomandazioni specifiche per JSON
            recommendations.append("Consider using compact JSON format (no spaces/tabs)")
            recommendations.append("Ensure all keys are strings")
        
        elif target_format.lower() == "xml":
            # Raccomandazioni specifiche per XML
            recommendations.append("Use attributes for metadata when possible")
            recommendations.append("Keep element names simple and consistent")
        
        return recommendations

    def _analyze_sample_data(sample_data: str, source_format: str) -> Dict[str, Any]:
        """Analizza i dati campione per fornire suggerimenti sulla conversione."""
        # Implementa logica analisi dati campione qui
        return {}

    def _get_recommended_options(sample_analysis: Dict[str, Any], target_format: str) -> Dict[str, Any]:
        """Fornisce opzioni raccomandate per la conversione basate sull'analisi dei dati campione."""
        recommended_options = {}
        
        # Esempio: se i dati campione hanno molte righe vuote, suggerisci di rimuoverle
        if sample_analysis.get("empty_lines", 0) > 0:
            recommended_options["remove_empty_lines"] = True
        
        return recommended_options