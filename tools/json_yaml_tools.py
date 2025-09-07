# -*- coding: utf-8 -*-
# tools/json_yaml_tools.py
import logging
import json
import yaml
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from collections import defaultdict
import copy

def register_tools(mcp):
    """Registra i tool JSON/YAML avanzati con l'istanza del server MCP."""
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

    @mcp.tool()
    def validate_yaml_advanced(yaml_string: str) -> Dict[str, Any]:
        """
        Valida e analizza un YAML con controlli avanzati.
        
        Args:
            yaml_string: Stringa YAML da validare
        """
        try:
            # Prova a parsare il YAML
            try:
                data = yaml.safe_load(yaml_string)
                is_valid = True
                error_msg = None
            except yaml.YAMLError as e:
                is_valid = False
                error_msg = str(e)
                data = None
            
            if not is_valid:
                return {
                    "success": False,
                    "valid": False,
                    "error": error_msg,
                    "suggestions": [
                        "Check indentation (use spaces, not tabs)",
                        "Verify colon placement after keys",
                        "Check for special characters that need quoting",
                        "Ensure consistent indentation levels"
                    ]
                }
            
            # Analisi struttura
            structure_analysis = _analyze_data_structure(data)
            
            # Analisi YAML specifica
            yaml_analysis = _analyze_yaml_syntax(yaml_string)
            
            # Calcola dimensioni
            yaml_size = len(yaml_string)
            json_equivalent = json.dumps(data, indent=2)
            json_size = len(json_equivalent)
            
            return {
                "success": True,
                "valid": True,
                "structure_analysis": structure_analysis,
                "yaml_analysis": yaml_analysis,
                "size_comparison": {
                    "yaml_size": yaml_size,
                    "json_equivalent_size": json_size,
                    "yaml_efficiency": round((1 - yaml_size / json_size) * 100, 2) if json_size > 0 else 0
                },
                "quality_score": _calculate_yaml_quality_score(yaml_analysis, structure_analysis)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def validate_json_schema(json_data: str, schema: str) -> Dict[str, Any]:
        """
        Valida JSON contro uno schema JSON Schema.
        
        Args:
            json_data: Dati JSON da validare
            schema: Schema JSON Schema
        """
        try:
            # Parse JSON data
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON data: {str(e)}"}
            
            # Parse schema
            try:
                schema_obj = json.loads(schema)
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON schema: {str(e)}"}
            
            # Basic schema validation (simplified implementation)
            validation_errors = []
            warnings = []
            
            def validate_against_schema(data, schema, path=""):
                errors = []
                
                # Type validation
                if "type" in schema:
                    expected_type = schema["type"]
                    actual_type = _get_json_type(data)
                    
                    if actual_type != expected_type:
                        errors.append(f"{path}: Expected type '{expected_type}', got '{actual_type}'")
                
                # Required properties
                if isinstance(data, dict) and "required" in schema:
                    for required_prop in schema["required"]:
                        if required_prop not in data:
                            errors.append(f"{path}: Missing required property '{required_prop}'")
                
                # Properties validation
                if isinstance(data, dict) and "properties" in schema:
                    for prop, value in data.items():
                        if prop in schema["properties"]:
                            prop_errors = validate_against_schema(
                                value, 
                                schema["properties"][prop], 
                                f"{path}.{prop}" if path else prop
                            )
                            errors.extend(prop_errors)
                        elif schema.get("additionalProperties") is False:
                            warnings.append(f"{path}: Additional property '{prop}' not allowed in schema")
                
                # Array validation
                if isinstance(data, list) and "items" in schema:
                    for i, item in enumerate(data):
                        item_errors = validate_against_schema(
                            item, 
                            schema["items"], 
                            f"{path}[{i}]"
                        )
                        errors.extend(item_errors)
                
                # String constraints
                if isinstance(data, str):
                    if "minLength" in schema and len(data) < schema["minLength"]:
                        errors.append(f"{path}: String too short (min: {schema['minLength']})")
                    if "maxLength" in schema and len(data) > schema["maxLength"]:
                        errors.append(f"{path}: String too long (max: {schema['maxLength']})")
                    if "pattern" in schema:
                        if not re.match(schema["pattern"], data):
                            errors.append(f"{path}: String doesn't match pattern '{schema['pattern']}'")
                
                # Number constraints
                if isinstance(data, (int, float)):
                    if "minimum" in schema and data < schema["minimum"]:
                        errors.append(f"{path}: Value too small (min: {schema['minimum']})")
                    if "maximum" in schema and data > schema["maximum"]:
                        errors.append(f"{path}: Value too large (max: {schema['maximum']})")
                
                return errors
            
            validation_errors = validate_against_schema(data, schema_obj)
            
            is_valid = len(validation_errors) == 0
            
            return {
                "success": True,
                "valid": is_valid,
                "errors": validation_errors,
                "warnings": warnings,
                "schema_info": {
                    "schema_type": schema_obj.get("type", "unknown"),
                    "has_required": "required" in schema_obj,
                    "has_properties": "properties" in schema_obj
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def transform_data(data: str, source_format: str, transformations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applica trasformazioni ai dati JSON/YAML.
        
        Args:
            data: Dati da trasformare
            source_format: Formato sorgente (json o yaml)
            transformations: Lista di trasformazioni da applicare
        """
        try:
            # Parse data
            if source_format.lower() == "json":
                parsed_data = json.loads(data)
            elif source_format.lower() == "yaml":
                parsed_data = yaml.safe_load(data)
            else:
                return {"success": False, "error": "Invalid source_format. Use 'json' or 'yaml'"}
            
            # Create working copy
            result_data = copy.deepcopy(parsed_data)
            applied_transformations = []
            
            for transformation in transformations:
                transform_type = transformation.get("type")
                
                if transform_type == "filter":
                    # Filter data based on condition
                    condition = transformation.get("condition", {})
                    result_data = _apply_filter(result_data, condition)
                    applied_transformations.append("filter")
                
                elif transform_type == "map":
                    # Map/rename fields
                    mapping = transformation.get("mapping", {})
                    result_data = _apply_mapping(result_data, mapping)
                    applied_transformations.append("map")
                
                elif transform_type == "sort":
                    # Sort arrays by key
                    sort_key = transformation.get("key")
                    reverse = transformation.get("reverse", False)
                    if isinstance(result_data, list):
                        result_data = _sort_data(result_data, sort_key, reverse)
                        applied_transformations.append("sort")
                
                elif transform_type == "group":
                    # Group data by key
                    group_key = transformation.get("key")
                    if isinstance(result_data, list):
                        result_data = _group_data(result_data, group_key)
                        applied_transformations.append("group")
                
                elif transform_type == "flatten":
                    # Flatten nested structure
                    separator = transformation.get("separator", ".")
                    result_data = _flatten_data(result_data, separator)
                    applied_transformations.append("flatten")
                
                elif transform_type == "extract":
                    # Extract specific fields
                    fields = transformation.get("fields", [])
                    result_data = _extract_fields(result_data, fields)
                    applied_transformations.append("extract")
            
            return {
                "success": True,
                "original_data": parsed_data,
                "transformed_data": result_data,
                "applied_transformations": applied_transformations,
                "transformation_summary": {
                    "original_type": type(parsed_data).__name__,
                    "result_type": type(result_data).__name__,
                    "transformations_count": len(applied_transformations)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def merge_data_structures(data_list: List[str], format_type: str = "json", 
                            merge_strategy: str = "deep") -> Dict[str, Any]:
        """
        Unisce multiple strutture dati JSON/YAML.
        
        Args:
            data_list: Lista di stringhe JSON/YAML da unire
            format_type: Formato dei dati (json o yaml)
            merge_strategy: Strategia di merge (deep, shallow, array_concat)
        """
        try:
            if len(data_list) < 2:
                return {"success": False, "error": "At least 2 data structures required for merge"}
            
            parsed_data_list = []
            
            # Parse all data structures
            for i, data_str in enumerate(data_list):
                try:
                    if format_type.lower() == "json":
                        parsed = json.loads(data_str)
                    elif format_type.lower() == "yaml":
                        parsed = yaml.safe_load(data_str)
                    else:
                        return {"success": False, "error": "Invalid format_type. Use 'json' or 'yaml'"}
                    
                    parsed_data_list.append(parsed)
                except Exception as e:
                    return {"success": False, "error": f"Error parsing data structure {i+1}: {str(e)}"}
            
            # Merge data structures
            if merge_strategy == "deep":
                result = _deep_merge(parsed_data_list)
            elif merge_strategy == "shallow":
                result = _shallow_merge(parsed_data_list)
            elif merge_strategy == "array_concat":
                result = _array_concat_merge(parsed_data_list)
            else:
                return {"success": False, "error": "Invalid merge_strategy. Use 'deep', 'shallow', or 'array_concat'"}
            
            # Generate output in requested format
            if format_type.lower() == "json":
                output_data = json.dumps(result, indent=2, ensure_ascii=False)
            else:
                output_data = yaml.dump(result, default_flow_style=False, allow_unicode=True)
            
            return {
                "success": True,
                "merged_data": result,
                "output_format": output_data,
                "merge_info": {
                    "input_count": len(data_list),
                    "merge_strategy": merge_strategy,
                    "format_type": format_type,
                    "result_type": type(result).__name__
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def query_data(data: str, format_type: str, query: str, query_type: str = "jpath") -> Dict[str, Any]:
        """
        Esegue query sui dati JSON/YAML.
        
        Args:
            data: Dati da interrogare
            format_type: Formato dei dati (json o yaml)
            query: Query da eseguire
            query_type: Tipo di query (jpath, filter, search)
        """
        try:
            # Parse data
            if format_type.lower() == "json":
                parsed_data = json.loads(data)
            elif format_type.lower() == "yaml":
                parsed_data = yaml.safe_load(data)
            else:
                return {"success": False, "error": "Invalid format_type. Use 'json' or 'yaml'"}
            
            results = []
            
            if query_type == "jpath":
                # JSONPath-like query
                results = _execute_jpath_query(parsed_data, query)
            
            elif query_type == "filter":
                # Filter query
                filter_condition = json.loads(query) if query.startswith('{') else {"key": query}
                results = _execute_filter_query(parsed_data, filter_condition)
            
            elif query_type == "search":
                # Text search in values
                results = _execute_search_query(parsed_data, query)
            
            else:
                return {"success": False, "error": "Invalid query_type. Use 'jpath', 'filter', or 'search'"}
            
            return {
                "success": True,
                "query": query,
                "query_type": query_type,
                "results": results,
                "result_count": len(results),
                "data_type": type(parsed_data).__name__
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_json_schema(json_data: str, schema_title: str = "Generated Schema") -> Dict[str, Any]:
        """
        Genera uno schema JSON Schema da dati JSON esistenti.
        
        Args:
            json_data: Dati JSON da cui generare lo schema
            schema_title: Titolo per lo schema generato
        """
        try:
            # Parse JSON data
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON data: {str(e)}"}
            
            def generate_schema_for_value(value, required_fields=None):
                """Generate schema for a given value"""
                if value is None:
                    return {"type": "null"}
                
                elif isinstance(value, bool):
                    return {"type": "boolean"}
                
                elif isinstance(value, int):
                    return {"type": "integer"}
                
                elif isinstance(value, float):
                    return {"type": "number"}
                
                elif isinstance(value, str):
                    schema = {"type": "string"}
                    if len(value) > 0:
                        schema["minLength"] = 1
                    return schema
                
                elif isinstance(value, list):
                    schema = {"type": "array"}
                    if value:  # Non-empty array
                        # Analyze first few items to determine item schema
                        item_schemas = []
                        for item in value[:5]:  # Sample first 5 items
                            item_schemas.append(generate_schema_for_value(item))
                        
                        # If all items have same type, use that schema
                        if all(s.get("type") == item_schemas[0].get("type") for s in item_schemas):
                            schema["items"] = item_schemas[0]
                        else:
                            # Mixed types, use anyOf
                            unique_schemas = []
                            for s in item_schemas:
                                if s not in unique_schemas:
                                    unique_schemas.append(s)
                            schema["items"] = {"anyOf": unique_schemas} if len(unique_schemas) > 1 else unique_schemas[0]
                    
                    return schema
                
                elif isinstance(value, dict):
                    schema = {
                        "type": "object",
                        "properties": {}
                    }
                    
                    required = []
                    for key, val in value.items():
                        schema["properties"][key] = generate_schema_for_value(val)
                        # Consider non-null values as required
                        if val is not None:
                            required.append(key)
                    
                    if required:
                        schema["required"] = required
                    
                    return schema
                
                else:
                    return {"type": "string"}  # fallback
            
            # Generate main schema
            main_schema = generate_schema_for_value(data)
            
            # Add metadata
            full_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": schema_title,
                "description": f"Schema generated from JSON data on {datetime.now().isoformat()}",
                **main_schema
            }
            
            # Schema statistics
            stats = _analyze_schema_complexity(full_schema)
            
            return {
                "success": True,
                "schema": full_schema,
                "schema_json": json.dumps(full_schema, indent=2),
                "statistics": stats,
                "validation_ready": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def batch_validate_files(file_data_list: List[Dict[str, str]], 
                           validation_type: str = "syntax") -> Dict[str, Any]:
        """
        Valida multiple file JSON/YAML in batch.
        
        Args:
            file_data_list: Lista di dict con 'name', 'content', 'format'
            validation_type: Tipo validazione (syntax, schema, custom)
        """
        try:
            if len(file_data_list) > 50:  # Limit for performance
                return {"success": False, "error": "Too many files (max 50)"}
            
            results = []
            summary = {
                "total_files": len(file_data_list),
                "valid_files": 0,
                "invalid_files": 0,
                "errors": [],
                "warnings": []
            }
            
            for file_info in file_data_list:
                file_name = file_info.get("name", "unnamed")
                content = file_info.get("content", "")
                file_format = file_info.get("format", "json").lower()
                
                file_result = {
                    "name": file_name,
                    "format": file_format,
                    "valid": False,
                    "errors": [],
                    "warnings": [],
                    "size": len(content)
                }
                
                try:
                    # Parse based on format
                    if file_format == "json":
                        data = json.loads(content)
                        
                        # Additional JSON validations
                        if validation_type == "syntax":
                            file_result["valid"] = True
                        elif validation_type == "custom":
                            # Custom validation rules
                            validation_issues = _validate_json_custom_rules(data)
                            file_result["warnings"] = validation_issues
                            file_result["valid"] = len(validation_issues) == 0
                    
                    elif file_format == "yaml":
                        data = yaml.safe_load(content)
                        
                        if validation_type == "syntax":
                            file_result["valid"] = True
                        elif validation_type == "custom":
                            # Custom YAML validation
                            yaml_issues = _validate_yaml_custom_rules(content, data)
                            file_result["warnings"] = yaml_issues
                            file_result["valid"] = len(yaml_issues) == 0
                    
                    else:
                        file_result["errors"].append(f"Unsupported format: {file_format}")
                    
                    if file_result["valid"]:
                        summary["valid_files"] += 1
                    else:
                        summary["invalid_files"] += 1
                        summary["errors"].extend([f"{file_name}: {err}" for err in file_result["errors"]])
                
                except json.JSONDecodeError as e:
                    file_result["errors"].append(f"JSON syntax error: {str(e)}")
                    summary["invalid_files"] += 1
                except yaml.YAMLError as e:
                    file_result["errors"].append(f"YAML syntax error: {str(e)}")
                    summary["invalid_files"] += 1
                except Exception as e:
                    file_result["errors"].append(f"Validation error: {str(e)}")
                    summary["invalid_files"] += 1
                
                results.append(file_result)
            
            return {
                "success": True,
                "validation_type": validation_type,
                "summary": summary,
                "results": results,
                "success_rate": round((summary["valid_files"] / summary["total_files"]) * 100, 1) if summary["total_files"] > 0 else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions for enhanced functionality
    def _analyze_data_structure(data: Any) -> Dict[str, Any]:
        """Analyze data structure recursively."""
        def analyze_recursive(obj, depth=0):
            analysis = {
                "types": defaultdict(int),
                "max_depth": depth,
                "total_items": 0,
                "null_values": 0
            }
            
            if isinstance(obj, dict):
                analysis["types"]["object"] += 1
                analysis["total_items"] += len(obj)
                max_child_depth = depth
                
                for key, value in obj.items():
                    if value is None:
                        analysis["null_values"] += 1
                    
                    child_analysis = analyze_recursive(value, depth + 1)
                    max_child_depth = max(max_child_depth, child_analysis["max_depth"])
                    
                    for t, count in child_analysis["types"].items():
                        analysis["types"][t] += count
                    analysis["total_items"] += child_analysis["total_items"]
                    analysis["null_values"] += child_analysis["null_values"]
                
                analysis["max_depth"] = max_child_depth
                
            elif isinstance(obj, list):
                analysis["types"]["array"] += 1
                analysis["total_items"] += len(obj)
                max_child_depth = depth
                
                for item in obj:
                    if item is None:
                        analysis["null_values"] += 1
                    
                    child_analysis = analyze_recursive(item, depth + 1)
                    max_child_depth = max(max_child_depth, child_analysis["max_depth"])
                    
                    for t, count in child_analysis["types"].items():
                        analysis["types"][t] += count
                    analysis["total_items"] += child_analysis["total_items"]
                    analysis["null_values"] += child_analysis["null_values"]
                
                analysis["max_depth"] = max_child_depth
                
            else:
                if obj is None:
                    analysis["types"]["null"] += 1
                    analysis["null_values"] += 1
                elif isinstance(obj, bool):
                    analysis["types"]["boolean"] += 1
                elif isinstance(obj, int):
                    analysis["types"]["integer"] += 1
                elif isinstance(obj, float):
                    analysis["types"]["number"] += 1
                elif isinstance(obj, str):
                    analysis["types"]["string"] += 1
            
            return analysis
        
        return dict(analyze_recursive(data))

    def _analyze_yaml_syntax(yaml_string: str) -> Dict[str, Any]:
        """Analyze YAML-specific syntax patterns."""
        lines = yaml_string.split('\n')
        
        analysis = {
            "total_lines": len(lines),
            "empty_lines": 0,
            "comment_lines": 0,
            "indentation_levels": set(),
            "uses_tabs": False,
            "max_line_length": 0,
            "key_count": 0,
            "list_items": 0
        }
        
        for line in lines:
            if not line.strip():
                analysis["empty_lines"] += 1
                continue
            
            if line.strip().startswith('#'):
                analysis["comment_lines"] += 1
                continue
            
            # Check for tabs
            if '\t' in line:
                analysis["uses_tabs"] = True
            
            # Track indentation
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                analysis["indentation_levels"].add(indent)
            
            # Line length
            analysis["max_line_length"] = max(analysis["max_line_length"], len(line))
            
            # Count keys and list items
            if ':' in line and not line.strip().startswith('-'):
                analysis["key_count"] += 1
            elif line.strip().startswith('- '):
                analysis["list_items"] += 1
        
        analysis["indentation_levels"] = sorted(list(analysis["indentation_levels"]))
        
        return analysis

    def _calculate_yaml_quality_score(yaml_analysis: Dict, structure_analysis: Dict) -> Dict[str, Any]:
        """Calculate YAML quality score."""
        score = 100
        issues = []
        
        # Check indentation consistency
        if yaml_analysis["uses_tabs"]:
            score -= 20
            issues.append("Uses tabs instead of spaces")
        
        # Check indentation levels
        indents = yaml_analysis["indentation_levels"]
        if indents:
            # Check if indentation is consistent (multiples of 2)
            if not all(indent % 2 == 0 for indent in indents):
                score -= 10
                issues.append("Inconsistent indentation (not multiples of 2)")
        
        # Check line length
        if yaml_analysis["max_line_length"] > 120:
            score -= 5
            issues.append("Long lines (>120 characters)")
        
        # Check structure complexity
        if structure_analysis["max_depth"] > 8:
            score -= 10
            issues.append("Very deep nesting (>8 levels)")
        
        # Check null values ratio
        if structure_analysis["total_items"] > 0:
            null_ratio = structure_analysis["null_values"] / structure_analysis["total_items"]
            if null_ratio > 0.2:
                score -= 5
                issues.append("High ratio of null values")
        
        return {
            "score": max(0, score),
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D",
            "issues": issues
        }