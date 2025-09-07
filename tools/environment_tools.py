# -*- coding: utf-8 -*-
# tools/environment_tools.py
import os
import json
import tempfile
import shutil
import logging
from typing import Dict, List, Any, Optional
import configparser
import subprocess

def register_tools(mcp):
    """Registra i tool di gestione ambiente con l'istanza del server MCP."""
    logging.info("🌍 Registrazione tool-set: Environment Management Tools")

    @mcp.tool()
    def manage_environment_variables(action: str, variables: Dict[str, str] = {}, variable_name: str = "") -> Dict[str, Any]:
        """
        Gestisce le variabili d'ambiente in modo sicuro.
        
        Args:
            action: Azione da eseguire (list, get, set, unset, validate)
            variables: Dizionario di variabili da impostare (per action=set)
            variable_name: Nome della variabile (per action=get/unset)
        """
        try:
            if action == "list":
                # Lista tutte le variabili d'ambiente (filtrate per sicurezza)
                sensitive_patterns = [
                    "PASSWORD", "SECRET", "KEY", "TOKEN", "AUTH", "PRIVATE",
                    "CREDENTIAL", "PASS", "PWD", "API_KEY"
                ]
                
                env_vars = {}
                sensitive_vars = []
                
                for key, value in os.environ.items():
                    is_sensitive = any(pattern in key.upper() for pattern in sensitive_patterns)
                    if is_sensitive:
                        env_vars[key] = "[HIDDEN - SENSITIVE]"
                        sensitive_vars.append(key)
                    else:
                        env_vars[key] = value
                
                return {
                    "success": True,
                    "action": action,
                    "total_variables": len(os.environ),
                    "sensitive_variables_count": len(sensitive_vars),
                    "variables": env_vars,
                    "sensitive_variables": sensitive_vars
                }
            
            elif action == "get":
                if not variable_name:
                    return {
                        "success": False,
                        "error": "variable_name is required for get action"
                    }
                
                value = os.environ.get(variable_name)
                exists = value is not None
                
                # Controlla se è sensibile
                sensitive_patterns = ["PASSWORD", "SECRET", "KEY", "TOKEN", "AUTH", "PRIVATE"]
                is_sensitive = any(pattern in variable_name.upper() for pattern in sensitive_patterns)
                
                return {
                    "success": True,
                    "action": action,
                    "variable_name": variable_name,
                    "exists": exists,
                    "value": "[HIDDEN - SENSITIVE]" if is_sensitive and exists else value,
                    "is_sensitive": is_sensitive
                }
            
            elif action == "set":
                if not variables:
                    return {
                        "success": False,
                        "error": "variables dictionary is required for set action"
                    }
                
                set_variables = []
                errors = []
                
                for var_name, var_value in variables.items():
                    if not var_name or not isinstance(var_name, str):
                        errors.append(f"Invalid variable name: {var_name}")
                        continue
                    
                    try:
                        os.environ[var_name] = str(var_value)
                        set_variables.append(var_name)
                    except Exception as e:
                        errors.append(f"Failed to set {var_name}: {str(e)}")
                
                return {
                    "success": len(errors) == 0,
                    "action": action,
                    "variables_set": set_variables,
                    "variables_set_count": len(set_variables),
                    "errors": errors
                }
            
            elif action == "unset":
                if not variable_name:
                    return {
                        "success": False,
                        "error": "variable_name is required for unset action"
                    }
                
                existed = variable_name in os.environ
                if existed:
                    del os.environ[variable_name]
                
                return {
                    "success": True,
                    "action": action,
                    "variable_name": variable_name,
                    "existed": existed,
                    "unset": existed
                }
            
            elif action == "validate":
                # Valida configurazione ambiente comune
                required_vars = variables.get("required", []) if isinstance(variables.get("required"), list) else []
                optional_vars = variables.get("optional", []) if isinstance(variables.get("optional"), list) else []
                
                validation_results = []
                missing_required = []
                present_vars = []
                
                # Controlla variabili richieste
                for var in required_vars:
                    if var in os.environ:
                        present_vars.append(var)
                        validation_results.append({
                            "variable": var,
                            "status": "present",
                            "required": True
                        })
                    else:
                        missing_required.append(var)
                        validation_results.append({
                            "variable": var,
                            "status": "missing",
                            "required": True
                        })
                
                # Controlla variabili opzionali
                for var in optional_vars:
                    if var in os.environ:
                        present_vars.append(var)
                        validation_results.append({
                            "variable": var,
                            "status": "present",
                            "required": False
                        })
                    else:
                        validation_results.append({
                            "variable": var,
                            "status": "missing",
                            "required": False
                        })
                
                is_valid = len(missing_required) == 0
                
                return {
                    "success": True,
                    "action": action,
                    "validation_passed": is_valid,
                    "required_variables": len(required_vars),
                    "optional_variables": len(optional_vars),
                    "missing_required": missing_required,
                    "present_variables": present_vars,
                    "validation_results": validation_results
                }
            
            else:
                return {
                    "success": False,
                    "error": "Invalid action. Use: list, get, set, unset, validate"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def create_environment_file(env_type: str, variables: Dict[str, str], file_path: str = "") -> Dict[str, Any]:
        """
        Crea file di configurazione ambiente (.env, .ini, etc.).
        
        Args:
            env_type: Tipo di file (env, ini, json, yaml)
            variables: Variabili da includere nel file
            file_path: Percorso del file (opzionale, altrimenti usa temp)
        """
        try:
            if not variables:
                return {
                    "success": False,
                    "error": "Variables dictionary is required"
                }
            
            # Se non specificato, usa directory temporanea
            if not file_path:
                temp_dir = tempfile.mkdtemp(prefix="nexus_env_")
                file_extension = {
                    "env": ".env",
                    "ini": ".ini", 
                    "json": ".json",
                    "yaml": ".yml"
                }.get(env_type, ".txt")
                file_path = os.path.join(temp_dir, f"environment{file_extension}")
            
            content = ""
            
            if env_type.lower() == "env":
                content = "# Environment Variables\n"
                content += f"# Generated by Nexus MCP Server\n\n"
                for key, value in variables.items():
                    # Escape value se contiene spazi o caratteri speciali
                    if " " in str(value) or any(char in str(value) for char in ['$', '"', "'"]):
                        content += f'{key}="{value}"\n'
                    else:
                        content += f"{key}={value}\n"
            
            elif env_type.lower() == "ini":
                content = "; Environment Configuration\n"
                content += "; Generated by Nexus MCP Server\n\n"
                content += "[environment]\n"
                for key, value in variables.items():
                    content += f"{key} = {value}\n"
            
            elif env_type.lower() == "json":
                env_data = {
                    "_comment": "Environment Configuration - Generated by Nexus MCP Server",
                    "environment": variables
                }
                content = json.dumps(env_data, indent=2)
            
            elif env_type.lower() == "yaml":
                content = "# Environment Configuration\n"
                content += "# Generated by Nexus MCP Server\n\n"
                content += "environment:\n"
                for key, value in variables.items():
                    content += f"  {key}: {value}\n"
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported env_type. Use: env, ini, json, yaml"
                }
            
            # Scrivi file
            with open(file_path, 'w') as f:
                f.write(content)
            
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "env_type": env_type,
                "file_path": file_path,
                "variables_count": len(variables),
                "file_size_bytes": file_size,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_system_environment() -> Dict[str, Any]:
        """
        Analizza l'ambiente di sistema e fornisce informazioni diagnostiche.
        """
        try:
            # Informazioni di base del sistema
            system_info = {
                "os_name": os.name,
                "platform": os.uname().sysname if hasattr(os, 'uname') else "Unknown",
                "python_executable": os.sys.executable,
                "working_directory": os.getcwd(),
                "user": os.environ.get("USER", os.environ.get("USERNAME", "Unknown")),
                "home_directory": os.path.expanduser("~"),
                "temp_directory": tempfile.gettempdir()
            }
            
            # PATH analysis
            path_var = os.environ.get("PATH", "")
            path_entries = path_var.split(os.pathsep) if path_var else []
            
            # Controlla directory PATH esistenti
            valid_paths = []
            invalid_paths = []
            
            for path in path_entries:
                if os.path.exists(path):
                    valid_paths.append(path)
                else:
                    invalid_paths.append(path)
            
            # Controlla spazio disco nelle directory importanti
            disk_usage = {}
            important_dirs = [
                system_info["working_directory"],
                system_info["home_directory"],
                system_info["temp_directory"]
            ]
            
            for dir_path in important_dirs:
                try:
                    if os.path.exists(dir_path):
                        usage = shutil.disk_usage(dir_path)
                        disk_usage[dir_path] = {
                            "total_gb": round(usage.total / (1024**3), 2),
                            "used_gb": round(usage.used / (1024**3), 2),
                            "free_gb": round(usage.free / (1024**3), 2),
                            "used_percent": round((usage.used / usage.total) * 100, 1)
                        }
                except:
                    pass
            
            # Controlla variabili d'ambiente comuni
            common_env_vars = [
                "LANG", "LC_ALL", "TZ", "SHELL", "EDITOR",
                "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"
            ]
            
            env_status = {}
            for var in common_env_vars:
                env_status[var] = {
                    "set": var in os.environ,
                    "value": os.environ.get(var, None)
                }
            
            # Controlla strumenti di sviluppo comuni
            dev_tools = ["git", "python", "node", "npm", "docker", "curl", "wget"]
            tool_availability = {}
            
            for tool in dev_tools:
                try:
                    result = subprocess.run([tool, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    tool_availability[tool] = {
                        "available": result.returncode == 0,
                        "version": result.stdout.split('\n')[0] if result.returncode == 0 else None
                    }
                except:
                    tool_availability[tool] = {
                        "available": False,
                        "version": None
                    }
            
            # Analisi problemi comuni
            issues = []
            recommendations = []
            
            if len(invalid_paths) > 0:
                issues.append(f"{len(invalid_paths)} invalid PATH entries found")
                recommendations.append("Clean up PATH variable to remove non-existent directories")
            
            for dir_path, usage in disk_usage.items():
                if usage["used_percent"] > 90:
                    issues.append(f"Low disk space in {dir_path} ({usage['used_percent']}% full)")
                    recommendations.append(f"Free up space in {dir_path}")
            
            if not env_status.get("EDITOR", {}).get("set"):
                recommendations.append("Set EDITOR environment variable for better development experience")
            
            return {
                "success": True,
                "system_info": system_info,
                "path_analysis": {
                    "total_entries": len(path_entries),
                    "valid_paths": len(valid_paths),
                    "invalid_paths": len(invalid_paths),
                    "invalid_path_list": invalid_paths
                },
                "disk_usage": disk_usage,
                "common_env_vars": env_status,
                "development_tools": tool_availability,
                "issues": issues,
                "recommendations": recommendations,
                "environment_health": "Good" if len(issues) == 0 else "Issues Found"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def backup_restore_environment(action: str, backup_path: str = "", variables: List[str] = []) -> Dict[str, Any]:
        """
        Backup e ripristino di variabili d'ambiente.
        
        Args:
            action: Azione da eseguire (backup, restore, list_backups)
            backup_path: Percorso del file di backup (opzionale per backup)
            variables: Lista di variabili specifiche da fare backup (vuoto = tutte)
        """
        try:
            if action == "backup":
                # Determina variabili da fare backup
                if variables:
                    env_to_backup = {var: os.environ.get(var) for var in variables if var in os.environ}
                    missing_vars = [var for var in variables if var not in os.environ]
                else:
                    # Backup di tutte le variabili non sensibili
                    sensitive_patterns = [
                        "PASSWORD", "SECRET", "KEY", "TOKEN", "AUTH", "PRIVATE",
                        "CREDENTIAL", "PASS", "PWD", "API_KEY"
                    ]
                    
                    env_to_backup = {}
                    for key, value in os.environ.items():
                        is_sensitive = any(pattern in key.upper() for pattern in sensitive_patterns)
                        if not is_sensitive:
                            env_to_backup[key] = value
                    missing_vars = []
                
                # Crea backup file
                if not backup_path:
                    temp_dir = tempfile.mkdtemp(prefix="nexus_env_backup_")
                    backup_path = os.path.join(temp_dir, "environment_backup.json")
                
                backup_data = {
                    "timestamp": os.popen('date').read().strip(),
                    "backup_type": "selective" if variables else "full_non_sensitive",
                    "variables": env_to_backup,
                    "variable_count": len(env_to_backup),
                    "excluded_sensitive": not variables  # True se abbiamo escluso variabili sensibili
                }
                
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                
                return {
                    "success": True,
                    "action": action,
                    "backup_path": backup_path,
                    "variables_backed_up": len(env_to_backup),
                    "missing_variables": missing_vars,
                    "backup_size_bytes": os.path.getsize(backup_path)
                }
            
            elif action == "restore":
                if not backup_path or not os.path.exists(backup_path):
                    return {
                        "success": False,
                        "error": "Backup file not found"
                    }
                
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)
                
                if "variables" not in backup_data:
                    return {
                        "success": False,
                        "error": "Invalid backup file format"
                    }
                
                restored_vars = []
                errors = []
                
                for var_name, var_value in backup_data["variables"].items():
                    try:
                        os.environ[var_name] = str(var_value)
                        restored_vars.append(var_name)
                    except Exception as e:
                        errors.append(f"Failed to restore {var_name}: {str(e)}")
                
                return {
                    "success": len(errors) == 0,
                    "action": action,
                    "backup_path": backup_path,
                    "backup_timestamp": backup_data.get("timestamp", "Unknown"),
                    "variables_restored": len(restored_vars),
                    "restored_variables": restored_vars,
                    "errors": errors
                }
            
            elif action == "list_backups":
                # Se backup_path è una directory, lista i backup
                if backup_path and os.path.isdir(backup_path):
                    backup_files = []
                    for file in os.listdir(backup_path):
                        if file.endswith('.json'):
                            file_path = os.path.join(backup_path, file)
                            try:
                                with open(file_path, 'r') as f:
                                    backup_data = json.load(f)
                                
                                backup_files.append({
                                    "filename": file,
                                    "path": file_path,
                                    "timestamp": backup_data.get("timestamp", "Unknown"),
                                    "variable_count": backup_data.get("variable_count", 0),
                                    "backup_type": backup_data.get("backup_type", "unknown"),
                                    "size_bytes": os.path.getsize(file_path)
                                })
                            except:
                                pass
                    
                    return {
                        "success": True,
                        "action": action,
                        "backup_directory": backup_path,
                        "backup_files": backup_files,
                        "backup_count": len(backup_files)
                    }
                else:
                    return {
                        "success": False,
                        "error": "backup_path must be a valid directory for list_backups action"
                    }
            
            else:
                return {
                    "success": False,
                    "error": "Invalid action. Use: backup, restore, list_backups"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def validate_configuration_file(file_path: str, config_type: str = "auto") -> Dict[str, Any]:
        """
        Valida file di configurazione comuni.
        
        Args:
            file_path: Percorso del file di configurazione
            config_type: Tipo di configurazione (auto, json, ini, yaml, env)
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "Configuration file not found"
                }
            
            file_size = os.path.getsize(file_path)
            
            # Auto-detect tipo se non specificato
            if config_type == "auto":
                file_ext = os.path.splitext(file_path)[1].lower()
                config_type = {
                    ".json": "json",
                    ".ini": "ini", 
                    ".cfg": "ini",
                    ".conf": "ini",
                    ".yml": "yaml",
                    ".yaml": "yaml",
                    ".env": "env"
                }.get(file_ext, "unknown")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            validation_result = {
                "file_path": file_path,
                "config_type": config_type,
                "file_size_bytes": file_size,
                "line_count": len(content.split('\n')),
                "valid": False,
                "errors": [],
                "warnings": [],
                "structure": {}
            }
            
            if config_type == "json":
                try:
                    data = json.loads(content)
                    validation_result["valid"] = True
                    validation_result["structure"] = {
                        "type": "object" if isinstance(data, dict) else type(data).__name__,
                        "keys": list(data.keys()) if isinstance(data, dict) else None,
                        "key_count": len(data.keys()) if isinstance(data, dict) else None
                    }
                except json.JSONDecodeError as e:
                    validation_result["errors"].append(f"JSON syntax error: {str(e)}")
            
            elif config_type == "ini":
                try:
                    config = configparser.ConfigParser()
                    config.read_string(content)
                    validation_result["valid"] = True
                    validation_result["structure"] = {
                        "sections": list(config.sections()),
                        "section_count": len(config.sections())
                    }
                    
                    # Controlla sezioni duplicate
                    sections_found = []
                    for line in content.split('\n'):
                        if line.strip().startswith('[') and line.strip().endswith(']'):
                            section = line.strip()[1:-1]
                            if section in sections_found:
                                validation_result["warnings"].append(f"Duplicate section: {section}")
                            sections_found.append(section)
                    
                except configparser.Error as e:
                    validation_result["errors"].append(f"INI syntax error: {str(e)}")
            
            elif config_type == "env":
                lines = content.split('\n')
                valid_lines = 0
                invalid_lines = []
                variables = {}
                
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes from value if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        variables[key] = value
                        valid_lines += 1
                    else:
                        invalid_lines.append(f"Line {i}: Invalid format")
                
                validation_result["valid"] = len(invalid_lines) == 0
                validation_result["errors"] = invalid_lines
                validation_result["structure"] = {
                    "variables": variables,
                    "variable_count": len(variables),
                    "valid_lines": valid_lines
                }
            
            elif config_type == "yaml":
                # Validazione YAML di base (senza libreria yaml)
                lines = content.split('\n')
                indentation_errors = []
                
                for i, line in enumerate(lines, 1):
                    if line.strip() and not line.startswith('#'):
                        # Controlla indentazione (dovrebbe essere multiplo di 2)
                        leading_spaces = len(line) - len(line.lstrip())
                        if leading_spaces % 2 != 0:
                            indentation_errors.append(f"Line {i}: Invalid indentation")
                
                validation_result["valid"] = len(indentation_errors) == 0
                validation_result["errors"] = indentation_errors
                validation_result["structure"] = {
                    "line_count": len(lines),
                    "non_empty_lines": len([l for l in lines if l.strip()])
                }
            
            else:
                validation_result["errors"].append(f"Unsupported config type: {config_type}")
            
            return {
                "success": True,
                **validation_result
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }