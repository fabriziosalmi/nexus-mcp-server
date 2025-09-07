# -*- coding: utf-8 -*-
# tools/environment_tools.py
import os
import json
import tempfile
import shutil
import logging
import configparser
import subprocess
import platform
import sys
import time
import psutil
import socket
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
import re

def register_tools(mcp):
    """Registra i tool di gestione ambiente avanzati con l'istanza del server MCP."""
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

    @mcp.tool()
    def monitor_system_resources(duration: int = 10, interval: int = 1) -> Dict[str, Any]:
        """
        Monitora risorse di sistema in tempo reale.
        
        Args:
            duration: Durata monitoraggio in secondi (max 60)
            interval: Intervallo campionamento in secondi
        """
        try:
            if duration > 60:
                duration = 60
            if interval < 1:
                interval = 1
                
            samples = []
            start_time = time.time()
            
            for i in range(min(duration // interval, 60)):
                sample_time = time.time()
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                
                # Memory usage
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                # Disk usage
                disk_usage = psutil.disk_usage('/')
                disk_io = psutil.disk_io_counters()
                
                # Network usage
                network_io = psutil.net_io_counters()
                
                # Process count
                process_count = len(psutil.pids())
                
                sample = {
                    "timestamp": datetime.fromtimestamp(sample_time).isoformat(),
                    "cpu": {
                        "percent": round(cpu_percent, 2),
                        "count": cpu_count,
                        "frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None
                    },
                    "memory": {
                        "total_gb": round(memory.total / (1024**3), 2),
                        "used_gb": round(memory.used / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2),
                        "percent": memory.percent
                    },
                    "swap": {
                        "total_gb": round(swap.total / (1024**3), 2),
                        "used_gb": round(swap.used / (1024**3), 2),
                        "percent": swap.percent
                    },
                    "disk": {
                        "total_gb": round(disk_usage.total / (1024**3), 2),
                        "used_gb": round(disk_usage.used / (1024**3), 2),
                        "free_gb": round(disk_usage.free / (1024**3), 2),
                        "percent": round((disk_usage.used / disk_usage.total) * 100, 2),
                        "read_mb": round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
                        "write_mb": round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0
                    },
                    "network": {
                        "bytes_sent_mb": round(network_io.bytes_sent / (1024**2), 2),
                        "bytes_recv_mb": round(network_io.bytes_recv / (1024**2), 2),
                        "packets_sent": network_io.packets_sent,
                        "packets_recv": network_io.packets_recv
                    },
                    "processes": process_count
                }
                
                samples.append(sample)
                
                if i < duration // interval - 1:
                    time.sleep(interval)
            
            # Calcola statistiche aggregate
            if samples:
                cpu_values = [s["cpu"]["percent"] for s in samples]
                memory_values = [s["memory"]["percent"] for s in samples]
                
                aggregated_stats = {
                    "cpu_avg": round(sum(cpu_values) / len(cpu_values), 2),
                    "cpu_max": max(cpu_values),
                    "cpu_min": min(cpu_values),
                    "memory_avg": round(sum(memory_values) / len(memory_values), 2),
                    "memory_max": max(memory_values),
                    "memory_min": min(memory_values)
                }
            else:
                aggregated_stats = {}
            
            # Genera raccomandazioni
            recommendations = _generate_performance_recommendations(samples)
            
            return {
                "success": True,
                "monitoring_duration": duration,
                "sample_interval": interval,
                "samples_collected": len(samples),
                "samples": samples,
                "aggregated_stats": aggregated_stats,
                "recommendations": recommendations,
                "system_health": _assess_system_health(aggregated_stats)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def manage_processes(action: str, process_name: str = "", pid: int = 0, 
                        command: str = "") -> Dict[str, Any]:
        """
        Gestisce processi di sistema.
        
        Args:
            action: Azione (list, find, info, kill, start)
            process_name: Nome processo per ricerca
            pid: PID processo specifico
            command: Comando da eseguire per start
        """
        try:
            if action == "list":
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                    try:
                        pinfo = proc.info
                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "cpu_percent": round(pinfo['cpu_percent'] or 0, 2),
                            "memory_percent": round(pinfo['memory_percent'] or 0, 2),
                            "status": pinfo['status']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Ordina per CPU usage
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                
                return {
                    "success": True,
                    "action": action,
                    "total_processes": len(processes),
                    "processes": processes[:50],  # Top 50 per performance
                    "top_cpu_processes": processes[:10]
                }
            
            elif action == "find":
                if not process_name:
                    return {"success": False, "error": "process_name required for find action"}
                
                matching_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
                    try:
                        if process_name.lower() in proc.info['name'].lower():
                            matching_processes.append({
                                "pid": proc.info['pid'],
                                "name": proc.info['name'],
                                "cmdline": ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else '',
                                "status": proc.info['status']
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return {
                    "success": True,
                    "action": action,
                    "search_term": process_name,
                    "matches_found": len(matching_processes),
                    "matching_processes": matching_processes
                }
            
            elif action == "info":
                if not pid:
                    return {"success": False, "error": "pid required for info action"}
                
                try:
                    proc = psutil.Process(pid)
                    
                    # Raccoglie informazioni dettagliate
                    proc_info = {
                        "pid": proc.pid,
                        "name": proc.name(),
                        "status": proc.status(),
                        "create_time": datetime.fromtimestamp(proc.create_time()).isoformat(),
                        "cpu_percent": proc.cpu_percent(),
                        "memory_info": {
                            "rss_mb": round(proc.memory_info().rss / (1024**2), 2),
                            "vms_mb": round(proc.memory_info().vms / (1024**2), 2),
                            "percent": round(proc.memory_percent(), 2)
                        },
                        "cmdline": proc.cmdline(),
                        "cwd": proc.cwd(),
                        "exe": proc.exe(),
                        "num_threads": proc.num_threads(),
                        "open_files": len(proc.open_files()),
                        "connections": len(proc.connections())
                    }
                    
                    return {
                        "success": True,
                        "action": action,
                        "process_info": proc_info
                    }
                    
                except psutil.NoSuchProcess:
                    return {"success": False, "error": f"Process with PID {pid} not found"}
                except psutil.AccessDenied:
                    return {"success": False, "error": f"Access denied for process {pid}"}
            
            elif action == "kill":
                if not pid:
                    return {"success": False, "error": "pid required for kill action"}
                
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                    proc.terminate()
                    
                    # Aspetta che il processo termini
                    try:
                        proc.wait(timeout=5)
                        terminated = True
                    except psutil.TimeoutExpired:
                        proc.kill()  # Force kill se non termina
                        terminated = True
                    
                    return {
                        "success": True,
                        "action": action,
                        "pid": pid,
                        "process_name": proc_name,
                        "terminated": terminated
                    }
                    
                except psutil.NoSuchProcess:
                    return {"success": False, "error": f"Process with PID {pid} not found"}
                except psutil.AccessDenied:
                    return {"success": False, "error": f"Access denied for process {pid}"}
            
            elif action == "start":
                if not command:
                    return {"success": False, "error": "command required for start action"}
                
                try:
                    # Avvia processo in background
                    process = subprocess.Popen(command.split(), 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE)
                    
                    return {
                        "success": True,
                        "action": action,
                        "command": command,
                        "pid": process.pid,
                        "started": True
                    }
                    
                except Exception as e:
                    return {"success": False, "error": f"Failed to start process: {str(e)}"}
            
            else:
                return {"success": False, "error": "Invalid action. Use: list, find, info, kill, start"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_config_template(template_type: str, application: str, 
                                environment: str = "development") -> Dict[str, Any]:
        """
        Genera template di configurazione per applicazioni comuni.
        
        Args:
            template_type: Tipo template (docker, k8s, nginx, apache, database)
            application: Nome applicazione
            environment: Ambiente (development, staging, production)
        """
        try:
            templates = {
                "docker": _generate_docker_template,
                "k8s": _generate_k8s_template,
                "kubernetes": _generate_k8s_template,
                "nginx": _generate_nginx_template,
                "apache": _generate_apache_template,
                "database": _generate_database_template,
                "systemd": _generate_systemd_template
            }
            
            if template_type not in templates:
                return {
                    "success": False,
                    "error": f"Unsupported template type. Available: {', '.join(templates.keys())}"
                }
            
            # Genera template
            template_content = templates[template_type](application, environment)
            
            # Crea file temporaneo
            temp_dir = tempfile.mkdtemp(prefix="nexus_config_")
            template_file = os.path.join(temp_dir, f"{application}_{template_type}_config")
            
            with open(template_file, 'w') as f:
                f.write(template_content)
            
            return {
                "success": True,
                "template_type": template_type,
                "application": application,
                "environment": environment,
                "template_file": template_file,
                "template_content": template_content,
                "content_length": len(template_content),
                "lines": len(template_content.split('\n'))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def compare_environments(env1_data: Dict[str, str], env2_data: Dict[str, str],
                           env1_name: str = "Environment 1", env2_name: str = "Environment 2") -> Dict[str, Any]:
        """
        Confronta due configurazioni ambiente.
        
        Args:
            env1_data: Primo ambiente (dict di variabili)
            env2_data: Secondo ambiente (dict di variabili)
            env1_name: Nome primo ambiente
            env2_name: Nome secondo ambiente
        """
        try:
            # Trova differenze
            only_in_env1 = set(env1_data.keys()) - set(env2_data.keys())
            only_in_env2 = set(env2_data.keys()) - set(env1_data.keys())
            common_keys = set(env1_data.keys()) & set(env2_data.keys())
            
            # Trova valori diversi per chiavi comuni
            different_values = {}
            for key in common_keys:
                if env1_data[key] != env2_data[key]:
                    different_values[key] = {
                        env1_name: env1_data[key],
                        env2_name: env2_data[key]
                    }
            
            # Analizza pattern
            env1_patterns = _analyze_env_patterns(env1_data)
            env2_patterns = _analyze_env_patterns(env2_data)
            
            # Genera raccomandazioni
            recommendations = []
            
            if only_in_env1:
                recommendations.append(f"Variables only in {env1_name}: {', '.join(list(only_in_env1)[:5])}")
            
            if only_in_env2:
                recommendations.append(f"Variables only in {env2_name}: {', '.join(list(only_in_env2)[:5])}")
            
            if different_values:
                recommendations.append(f"{len(different_values)} variables have different values")
            
            # Calcola similarità
            total_unique_keys = len(set(env1_data.keys()) | set(env2_data.keys()))
            similarity_score = len(common_keys) / total_unique_keys * 100 if total_unique_keys > 0 else 0
            
            return {
                "success": True,
                "env1_name": env1_name,
                "env2_name": env2_name,
                "comparison_summary": {
                    "total_vars_env1": len(env1_data),
                    "total_vars_env2": len(env2_data),
                    "common_variables": len(common_keys),
                    "only_in_env1": len(only_in_env1),
                    "only_in_env2": len(only_in_env2),
                    "different_values": len(different_values),
                    "similarity_percentage": round(similarity_score, 2)
                },
                "differences": {
                    "only_in_env1": list(only_in_env1),
                    "only_in_env2": list(only_in_env2),
                    "different_values": different_values
                },
                "pattern_analysis": {
                    env1_name: env1_patterns,
                    env2_name: env2_patterns
                },
                "recommendations": recommendations,
                "compatibility": "High" if similarity_score > 80 else "Medium" if similarity_score > 60 else "Low"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def check_dependencies(dependencies: List[str], check_type: str = "command") -> Dict[str, Any]:
        """
        Verifica disponibilità di dipendenze di sistema.
        
        Args:
            dependencies: Lista dipendenze da verificare
            check_type: Tipo controllo (command, python_package, system_library)
        """
        try:
            if not dependencies:
                return {"success": False, "error": "Dependencies list cannot be empty"}
            
            dependency_status = {}
            available_count = 0
            missing_dependencies = []
            
            for dep in dependencies:
                status = {"available": False, "version": None, "location": None, "error": None}
                
                try:
                    if check_type == "command":
                        # Verifica comando disponibile
                        result = subprocess.run([dep, "--version"], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            status["available"] = True
                            status["version"] = result.stdout.split('\n')[0].strip()
                            status["location"] = shutil.which(dep)
                        else:
                            # Prova senza --version
                            result = subprocess.run([dep], 
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode == 0 or "not found" not in result.stderr.lower():
                                status["available"] = True
                                status["location"] = shutil.which(dep)
                    
                    elif check_type == "python_package":
                        # Verifica package Python
                        try:
                            import importlib
                            module = importlib.import_module(dep)
                            status["available"] = True
                            status["version"] = getattr(module, '__version__', 'Unknown')
                            status["location"] = getattr(module, '__file__', 'Unknown')
                        except ImportError as e:
                            status["error"] = str(e)
                    
                    elif check_type == "system_library":
                        # Verifica libreria di sistema (basic check)
                        if platform.system() == "Linux":
                            result = subprocess.run(["ldconfig", "-p"], 
                                                  capture_output=True, text=True, timeout=10)
                            if dep in result.stdout:
                                status["available"] = True
                        elif platform.system() == "Darwin":  # macOS
                            result = subprocess.run(["find", "/usr/lib", "-name", f"*{dep}*"], 
                                                  capture_output=True, text=True, timeout=10)
                            if result.stdout.strip():
                                status["available"] = True
                                status["location"] = result.stdout.split('\n')[0]
                    
                    if status["available"]:
                        available_count += 1
                    else:
                        missing_dependencies.append(dep)
                        
                except subprocess.TimeoutExpired:
                    status["error"] = "Check timed out"
                except Exception as e:
                    status["error"] = str(e)
                
                dependency_status[dep] = status
            
            # Genera raccomandazioni di installazione
            installation_hints = []
            if missing_dependencies:
                if check_type == "command":
                    if platform.system() == "Linux":
                        installation_hints.append(f"Try: sudo apt-get install {' '.join(missing_dependencies)}")
                    elif platform.system() == "Darwin":
                        installation_hints.append(f"Try: brew install {' '.join(missing_dependencies)}")
                elif check_type == "python_package":
                    installation_hints.append(f"Try: pip install {' '.join(missing_dependencies)}")
            
            return {
                "success": True,
                "check_type": check_type,
                "total_dependencies": len(dependencies),
                "available_dependencies": available_count,
                "missing_dependencies": len(missing_dependencies),
                "dependency_status": dependency_status,
                "missing_list": missing_dependencies,
                "installation_hints": installation_hints,
                "system_info": {
                    "platform": platform.system(),
                    "architecture": platform.machine(),
                    "python_version": platform.python_version()
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def setup_deployment_environment(deployment_type: str, application_name: str,
                                   config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Configura ambiente per deployment.
        
        Args:
            deployment_type: Tipo deployment (docker, systemd, nginx, basic)
            application_name: Nome applicazione
            config: Configurazione specifica
        """
        try:
            config = config or {}
            setup_results = []
            created_files = []
            
            # Directory base per deployment
            base_dir = config.get("base_dir", f"/tmp/nexus_deployment_{application_name}")
            os.makedirs(base_dir, exist_ok=True)
            
            if deployment_type == "docker":
                # Setup Docker deployment
                dockerfile_content = _generate_dockerfile(application_name, config)
                dockerfile_path = os.path.join(base_dir, "Dockerfile")
                
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                created_files.append(dockerfile_path)
                
                # Docker Compose se richiesto
                if config.get("create_compose", True):
                    compose_content = _generate_docker_compose(application_name, config)
                    compose_path = os.path.join(base_dir, "docker-compose.yml")
                    
                    with open(compose_path, 'w') as f:
                        f.write(compose_content)
                    created_files.append(compose_path)
                
                setup_results.append("Docker configuration created")
            
            elif deployment_type == "systemd":
                # Setup systemd service
                service_content = _generate_systemd_service(application_name, config)
                service_path = os.path.join(base_dir, f"{application_name}.service")
                
                with open(service_path, 'w') as f:
                    f.write(service_content)
                created_files.append(service_path)
                
                setup_results.append("Systemd service file created")
            
            elif deployment_type == "nginx":
                # Setup Nginx configuration
                nginx_content = _generate_nginx_config(application_name, config)
                nginx_path = os.path.join(base_dir, f"{application_name}.conf")
                
                with open(nginx_path, 'w') as f:
                    f.write(nginx_content)
                created_files.append(nginx_path)
                
                setup_results.append("Nginx configuration created")
            
            elif deployment_type == "basic":
                # Setup basic deployment structure
                directories = ["bin", "config", "logs", "data"]
                for dir_name in directories:
                    dir_path = os.path.join(base_dir, dir_name)
                    os.makedirs(dir_path, exist_ok=True)
                
                # Create basic startup script
                startup_script = os.path.join(base_dir, "bin", "start.sh")
                with open(startup_script, 'w') as f:
                    f.write(f"""#!/bin/bash
# Startup script for {application_name}
cd "$(dirname "$0")/.."
echo "Starting {application_name}..."
# Add your application startup command here
""")
                os.chmod(startup_script, 0o755)
                created_files.append(startup_script)
                
                setup_results.append("Basic deployment structure created")
            
            # Crea file environment
            env_file = os.path.join(base_dir, ".env")
            env_content = f"""# Environment configuration for {application_name}
APP_NAME={application_name}
APP_ENV={config.get('environment', 'production')}
APP_PORT={config.get('port', 8080)}
APP_HOST={config.get('host', '0.0.0.0')}
"""
            
            with open(env_file, 'w') as f:
                f.write(env_content)
            created_files.append(env_file)
            
            # Crea README con istruzioni
            readme_file = os.path.join(base_dir, "README.md")
            readme_content = _generate_deployment_readme(deployment_type, application_name, config)
            
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            created_files.append(readme_file)
            
            return {
                "success": True,
                "deployment_type": deployment_type,
                "application_name": application_name,
                "base_directory": base_dir,
                "setup_results": setup_results,
                "created_files": created_files,
                "file_count": len(created_files),
                "next_steps": _get_deployment_next_steps(deployment_type)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions for enhanced functionality
    def _generate_performance_recommendations(samples: List[Dict]) -> List[str]:
        """Genera raccomandazioni performance."""
        recommendations = []
        
        if samples:
            avg_cpu = sum(s["cpu"]["percent"] for s in samples) / len(samples)
            avg_memory = sum(s["memory"]["percent"] for s in samples) / len(samples)
            
            if avg_cpu > 80:
                recommendations.append("High CPU usage detected - consider optimizing applications or upgrading hardware")
            
            if avg_memory > 85:
                recommendations.append("High memory usage detected - check for memory leaks or increase RAM")
            
            # Check for swap usage
            if any(s["swap"]["percent"] > 10 for s in samples):
                recommendations.append("Swap usage detected - consider increasing RAM")
        
        return recommendations

    def _assess_system_health(stats: Dict) -> str:
        """Valuta salute sistema."""
        if not stats:
            return "Unknown"
        
        cpu_avg = stats.get("cpu_avg", 0)
        memory_avg = stats.get("memory_avg", 0)
        
        if cpu_avg > 90 or memory_avg > 95:
            return "Critical"
        elif cpu_avg > 75 or memory_avg > 85:
            return "Warning"
        elif cpu_avg > 50 or memory_avg > 70:
            return "Fair"
        else:
            return "Good"

    def _generate_docker_template(app_name: str, environment: str) -> str:
        """Genera template Dockerfile."""
        return f"""# Dockerfile for {app_name}
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:3000/health || exit 1

# Start application
CMD ["npm", "start"]
"""

    def _generate_k8s_template(app_name: str, environment: str) -> str:
        """Genera template Kubernetes."""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
    environment: {environment}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {app_name}:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "{environment}"
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service
spec:
  selector:
    app: {app_name}
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
  type: ClusterIP
"""

    def _analyze_env_patterns(env_data: Dict[str, str]) -> Dict[str, Any]:
        """Analizza pattern nelle variabili ambiente."""
        patterns = {
            "database_vars": [],
            "api_vars": [],
            "security_vars": [],
            "port_vars": [],
            "url_vars": []
        }
        
        for key, value in env_data.items():
            key_upper = key.upper()
            
            if any(db in key_upper for db in ["DB", "DATABASE", "MYSQL", "POSTGRES", "MONGO"]):
                patterns["database_vars"].append(key)
            
            if any(api in key_upper for api in ["API", "TOKEN", "KEY"]):
                patterns["api_vars"].append(key)
            
            if any(sec in key_upper for sec in ["SECRET", "PASSWORD", "PRIVATE", "CREDENTIAL"]):
                patterns["security_vars"].append(key)
            
            if "PORT" in key_upper or (value.isdigit() and 1000 <= int(value) <= 65535):
                patterns["port_vars"].append(key)
            
            if value.startswith(("http://", "https://", "ftp://", "ws://", "wss://")):
                patterns["url_vars"].append(key)
        
        return patterns