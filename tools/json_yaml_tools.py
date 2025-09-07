# -*- coding: utf-8 -*-
# tools/json_yaml_tools.py
import logging
import json
import yaml
import re
from typing import Dict, Any

def register_tools(mcp):
    """Registra i tool JSON/YAML con l'istanza del server MCP."""
    logging.info("📄 Registrazione tool-set: JSON/YAML Tools")

    @mcp.tool()
    def validate_json_advanced(json_string: str) -> str:
        """
        Valida e analizza un JSON con controlli avanzati.
        
        Args:
            json_string: Stringa JSON da validare
        """
        try:
            # Prova a parsare il JSON
            try:
                data = json.loads(json_string)
                is_valid = True
                error_msg = None
            except json.JSONDecodeError as e:
                is_valid = False
                error_msg = str(e)
                data = None
            
            if not is_valid:
                return f"""❌ JSON NON VALIDO
Errore: {error_msg}

Possibili cause:
- Virgole mancanti o extra
- Parentesi non bilanciate
- Stringhe non quotate correttamente
- Valori null scritti come NULL invece di null"""
            
            # Analisi struttura
            def analyze_structure(obj, path="root"):
                info = {"types": {}, "depth": 0, "items": 0}
                
                if isinstance(obj, dict):
                    info["types"]["object"] = info["types"].get("object", 0) + 1
                    info["items"] += len(obj)
                    max_depth = 0
                    for key, value in obj.items():
                        sub_info = analyze_structure(value, f"{path}.{key}")
                        max_depth = max(max_depth, sub_info["depth"])
                        for t, count in sub_info["types"].items():
                            info["types"][t] = info["types"].get(t, 0) + count
                        info["items"] += sub_info["items"]
                    info["depth"] = max_depth + 1
                    
                elif isinstance(obj, list):
                    info["types"]["array"] = info["types"].get("array", 0) + 1
                    info["items"] += len(obj)
                    max_depth = 0
                    for i, item in enumerate(obj):
                        sub_info = analyze_structure(item, f"{path}[{i}]")
                        max_depth = max(max_depth, sub_info["depth"])
                        for t, count in sub_info["types"].items():
                            info["types"][t] = info["types"].get(t, 0) + count
                        info["items"] += sub_info["items"]
                    info["depth"] = max_depth + 1
                    
                elif isinstance(obj, str):
                    info["types"]["string"] = info["types"].get("string", 0) + 1
                elif isinstance(obj, (int, float)):
                    info["types"]["number"] = info["types"].get("number", 0) + 1
                elif isinstance(obj, bool):
                    info["types"]["boolean"] = info["types"].get("boolean", 0) + 1
                elif obj is None:
                    info["types"]["null"] = info["types"].get("null", 0) + 1
                
                return info
            
            analysis = analyze_structure(data)
            
            # Calcola dimensioni
            json_size = len(json_string)
            formatted_size = len(json.dumps(data, indent=2))
            
            result = f"""✅ JSON VALIDO
Dimensioni: {json_size:,} caratteri
Dimensioni formattato: {formatted_size:,} caratteri
Compressione: {((formatted_size - json_size) / formatted_size * 100):+.1f}%

STRUTTURA:
Profondità massima: {analysis['depth']}
Elementi totali: {analysis['items']}

TIPI DI DATO:"""
            
            for data_type, count in sorted(analysis['types'].items()):
                result += f"\n- {data_type}: {count}"
            
            # Controlli qualità
            result += "\n\nCONTROLLI QUALITÀ:"
            
            quality_checks = []
            if analysis['depth'] > 10:
                quality_checks.append("⚠️ Struttura molto profonda (>10 livelli)")
            if json_size > 1000000:  # 1MB
                quality_checks.append("⚠️ File molto grande (>1MB)")
            if analysis['items'] > 10000:
                quality_checks.append("⚠️ Molti elementi (>10,000)")
            
            # Verifica chiavi duplicate (approssimativo)
            json_lower = json_string.lower()
            if json_lower.count('"id"') > 1:
                quality_checks.append("⚠️ Possibili chiavi 'id' duplicate")
            
            if not quality_checks:
                quality_checks.append("✅ Nessun problema di qualità rilevato")
            
            result += "\n" + "\n".join(quality_checks)
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def convert_json_yaml(data: str, source_format: str, target_format: str) -> str:
        """
        Converte tra JSON e YAML.
        
        Args:
            data: Dati da convertire
            source_format: Formato sorgente (json o yaml)
            target_format: Formato destinazione (json o yaml)
        """
        try:
            # Parse i dati di input
            if source_format.lower() == "json":
                try:
                    parsed_data = json.loads(data)
                except json.JSONDecodeError as e:
                    return f"ERRORE JSON: {str(e)}"
                    
            elif source_format.lower() == "yaml":
                try:
                    parsed_data = yaml.safe_load(data)
                except yaml.YAMLError as e:
                    return f"ERRORE YAML: {str(e)}"
            else:
                return "ERRORE: source_format deve essere 'json' o 'yaml'"
            
            # Converte nel formato target
            if target_format.lower() == "json":
                try:
                    result_data = json.dumps(parsed_data, indent=2, ensure_ascii=False)
                    format_name = "JSON"
                except Exception as e:
                    return f"ERRORE nella conversione a JSON: {str(e)}"
                    
            elif target_format.lower() == "yaml":
                try:
                    result_data = yaml.dump(parsed_data, default_flow_style=False, allow_unicode=True, indent=2)
                    format_name = "YAML"
                except Exception as e:
                    return f"ERRORE nella conversione a YAML: {str(e)}"
            else:
                return "ERRORE: target_format deve essere 'json' o 'yaml'"
            
            # Statistiche
            original_size = len(data)
            converted_size = len(result_data)
            
            return f"""🔄 CONVERSIONE {source_format.upper()} → {target_format.upper()}
Dimensioni originali: {original_size:,} caratteri
Dimensioni convertite: {converted_size:,} caratteri
Differenza: {((converted_size - original_size) / original_size * 100):+.1f}%

RISULTATO {format_name}:
{result_data}"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def json_diff_comparison(json1: str, json2: str) -> str:
        """
        Confronta due JSON e mostra le differenze.
        
        Args:
            json1: Primo JSON
            json2: Secondo JSON
        """
        try:
            # Parse entrambi i JSON
            try:
                data1 = json.loads(json1)
            except json.JSONDecodeError as e:
                return f"ERRORE JSON1: {str(e)}"
            
            try:
                data2 = json.loads(json2)
            except json.JSONDecodeError as e:
                return f"ERRORE JSON2: {str(e)}"
            
            def find_differences(obj1, obj2, path=""):
                differences = []
                
                if type(obj1) != type(obj2):
                    differences.append(f"{path}: TIPO DIVERSO - {type(obj1).__name__} vs {type(obj2).__name__}")
                    return differences
                
                if isinstance(obj1, dict):
                    # Chiavi solo in obj1
                    only_in_1 = set(obj1.keys()) - set(obj2.keys())
                    for key in only_in_1:
                        differences.append(f"{path}.{key}: PRESENTE SOLO IN JSON1")
                    
                    # Chiavi solo in obj2
                    only_in_2 = set(obj2.keys()) - set(obj1.keys())
                    for key in only_in_2:
                        differences.append(f"{path}.{key}: PRESENTE SOLO IN JSON2")
                    
                    # Chiavi comuni
                    common_keys = set(obj1.keys()) & set(obj2.keys())
                    for key in common_keys:
                        new_path = f"{path}.{key}" if path else key
                        differences.extend(find_differences(obj1[key], obj2[key], new_path))
                
                elif isinstance(obj1, list):
                    if len(obj1) != len(obj2):
                        differences.append(f"{path}: LUNGHEZZA DIVERSA - {len(obj1)} vs {len(obj2)}")
                    
                    max_len = max(len(obj1), len(obj2))
                    for i in range(max_len):
                        if i >= len(obj1):
                            differences.append(f"{path}[{i}]: PRESENTE SOLO IN JSON2")
                        elif i >= len(obj2):
                            differences.append(f"{path}[{i}]: PRESENTE SOLO IN JSON1")
                        else:
                            differences.extend(find_differences(obj1[i], obj2[i], f"{path}[{i}]"))
                
                else:
                    if obj1 != obj2:
                        differences.append(f"{path}: VALORE DIVERSO - '{obj1}' vs '{obj2}'")
                
                return differences
            
            differences = find_differences(data1, data2)
            
            if not differences:
                return "✅ I due JSON sono IDENTICI"
            
            result = f"""🔍 CONFRONTO JSON
Differenze trovate: {len(differences)}

DETTAGLI DIFFERENZE:
"""
            
            for i, diff in enumerate(differences[:20], 1):  # Limita a 20 differenze
                result += f"{i:2d}. {diff}\n"
            
            if len(differences) > 20:
                result += f"\n... e altre {len(differences) - 20} differenze"
            
            # Statistiche
            def count_elements(obj):
                if isinstance(obj, dict):
                    return sum(count_elements(v) for v in obj.values()) + len(obj)
                elif isinstance(obj, list):
                    return sum(count_elements(item) for item in obj) + len(obj)
                else:
                    return 1
            
            elements1 = count_elements(data1)
            elements2 = count_elements(data2)
            
            result += f"""
STATISTICHE:
Elementi JSON1: {elements1}
Elementi JSON2: {elements2}
Similitudine: {((max(elements1, elements2) - len(differences)) / max(elements1, elements2) * 100):.1f}%"""
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def json_path_extractor(json_string: str, json_path: str) -> str:
        """
        Estrae valori da un JSON usando un path semplice.
        
        Args:
            json_string: JSON da cui estrarre
            json_path: Path nel formato "key.subkey[0].value"
        """
        try:
            # Parse JSON
            try:
                data = json.loads(json_string)
            except json.JSONDecodeError as e:
                return f"ERRORE JSON: {str(e)}"
            
            # Parse del path
            current = data
            path_parts = []
            
            # Semplice parser per path come "a.b[0].c"
            parts = json_path.replace('[', '.').replace(']', '').split('.')
            parts = [p for p in parts if p]  # Rimuove parti vuote
            
            try:
                for part in parts:
                    path_parts.append(part)
                    
                    if part.isdigit():
                        # Indice array
                        index = int(part)
                        if not isinstance(current, list):
                            return f"ERRORE: '{'.'.join(path_parts[:-1])}' non è un array"
                        if index >= len(current):
                            return f"ERRORE: Indice {index} fuori range per array di {len(current)} elementi"
                        current = current[index]
                    else:
                        # Chiave oggetto
                        if not isinstance(current, dict):
                            return f"ERRORE: '{'.'.join(path_parts[:-1])}' non è un oggetto"
                        if part not in current:
                            available_keys = list(current.keys())[:10]  # Prime 10 chiavi
                            return f"ERRORE: Chiave '{part}' non trovata. Chiavi disponibili: {available_keys}"
                        current = current[part]
                
                # Formatta risultato
                if isinstance(current, (dict, list)):
                    result_json = json.dumps(current, indent=2, ensure_ascii=False)
                    type_name = "Oggetto" if isinstance(current, dict) else "Array"
                    size_info = f"({len(current)} elementi)"
                else:
                    result_json = json.dumps(current, ensure_ascii=False)
                    type_name = type(current).__name__
                    size_info = f"({len(str(current))} caratteri)" if isinstance(current, str) else ""
                
                return f"""🎯 ESTRAZIONE JSON PATH
Path: {json_path}
Tipo risultato: {type_name} {size_info}

VALORE ESTRATTO:
{result_json}"""
                
            except Exception as e:
                return f"ERRORE nel path '{json_path}': {str(e)}"
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def json_minify_beautify(json_string: str, operation: str = "beautify") -> str:
        """
        Minifica o beautifica un JSON.
        
        Args:
            json_string: JSON da processare
            operation: Operazione da eseguire (minify o beautify)
        """
        try:
            # Parse JSON
            try:
                data = json.loads(json_string)
            except json.JSONDecodeError as e:
                return f"ERRORE JSON: {str(e)}"
            
            original_size = len(json_string)
            
            if operation.lower() == "minify":
                result = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
                operation_name = "MINIFICATO"
            elif operation.lower() == "beautify":
                result = json.dumps(data, indent=2, ensure_ascii=False)
                operation_name = "BEAUTIFICATO"
            else:
                return "ERRORE: operation deve essere 'minify' o 'beautify'"
            
            new_size = len(result)
            size_change = ((new_size - original_size) / original_size * 100)
            
            return f"""🎨 JSON {operation_name}
Dimensioni originali: {original_size:,} caratteri
Dimensioni finali: {new_size:,} caratteri
Variazione: {size_change:+.1f}%

RISULTATO:
{result}"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"