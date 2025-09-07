# -*- coding: utf-8 -*-
# tools/code_execution_tools.py
import subprocess
import tempfile
import os
import sys
import resource
import signal
import time
import json
import logging
from typing import Dict, List, Any, Optional
import ast
import re
import uuid
import shutil

def register_tools(mcp):
    """Registra i tool di esecuzione codice con l'istanza del server MCP."""
    logging.info("🚀 Registrazione tool-set: Code Execution Tools")

    @mcp.tool()
    def execute_python_code(code: str, timeout: int = 30, memory_limit_mb: int = 50) -> Dict[str, Any]:
        """
        Esegue codice Python in un ambiente sandbox sicuro.
        
        Args:
            code: Codice Python da eseguire
            timeout: Timeout in secondi (5-300)
            memory_limit_mb: Limite memoria in MB (10-500)
        """
        try:
            if not code or not code.strip():
                return {
                    "success": False,
                    "error": "No code provided"
                }
            
            if timeout < 5 or timeout > 300:
                return {
                    "success": False,
                    "error": "Timeout must be between 5 and 300 seconds"
                }
            
            if memory_limit_mb < 10 or memory_limit_mb > 500:
                return {
                    "success": False,
                    "error": "Memory limit must be between 10 and 500 MB"
                }
            
            # Controlli di sicurezza
            security_check = _check_python_code_security(code)
            if not security_check["safe"]:
                return {
                    "success": False,
                    "error": f"Code contains potentially dangerous operations: {', '.join(security_check['violations'])}"
                }
            
            # Crea file temporaneo
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Prepara ambiente limitato
                env = os.environ.copy()
                env['PYTHONPATH'] = ''  # Limita import
                
                start_time = time.time()
                
                # Esegui con limiti
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                    preexec_fn=lambda: _set_execution_limits(memory_limit_mb) if os.name != 'nt' else None
                )
                
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "code": code,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time_seconds": round(execution_time, 3),
                    "memory_limit_mb": memory_limit_mb,
                    "timeout_seconds": timeout,
                    "security_check": security_check
                }
            
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Code execution timed out after {timeout} seconds",
                    "timeout": True
                }
            
            finally:
                # Cleanup
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def validate_python_syntax(code: str, strict_mode: bool = True) -> Dict[str, Any]:
        """
        Valida la sintassi del codice Python senza eseguirlo.
        
        Args:
            code: Codice Python da validare
            strict_mode: Se applicare controlli di stile aggiuntivi
        """
        try:
            if not code or not code.strip():
                return {
                    "success": False,
                    "error": "No code provided"
                }
            
            validation_result = {
                "code": code,
                "syntax_valid": False,
                "errors": [],
                "warnings": [],
                "style_issues": [],
                "complexity_analysis": {}
            }
            
            # Controllo sintassi base
            try:
                tree = ast.parse(code)
                validation_result["syntax_valid"] = True
                
                # Analisi AST
                complexity_analysis = _analyze_ast_complexity(tree)
                validation_result["complexity_analysis"] = complexity_analysis
                
            except SyntaxError as e:
                validation_result["errors"].append({
                    "type": "SyntaxError",
                    "message": str(e.msg),
                    "line": e.lineno,
                    "column": e.offset,
                    "text": e.text.strip() if e.text else ""
                })
            except Exception as e:
                validation_result["errors"].append({
                    "type": "ParseError",
                    "message": str(e)
                })
            
            # Controlli di stile se in strict mode
            if strict_mode and validation_result["syntax_valid"]:
                style_issues = _check_python_style(code)
                validation_result["style_issues"] = style_issues
            
            # Controlli di sicurezza
            security_check = _check_python_code_security(code)
            if not security_check["safe"]:
                validation_result["warnings"].extend([
                    {"type": "Security", "message": f"Potentially dangerous: {violation}"}
                    for violation in security_check["violations"]
                ])
            
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
    def execute_shell_command(command: str, working_directory: str = "", timeout: int = 30) -> Dict[str, Any]:
        """
        Esegue un comando shell in modo sicuro e limitato.
        
        Args:
            command: Comando da eseguire
            working_directory: Directory di lavoro (opzionale)
            timeout: Timeout in secondi (5-180)
        """
        try:
            if not command or not command.strip():
                return {
                    "success": False,
                    "error": "No command provided"
                }
            
            if timeout < 5 or timeout > 180:
                return {
                    "success": False,
                    "error": "Timeout must be between 5 and 180 seconds"
                }
            
            # Controlli di sicurezza
            security_check = _check_shell_command_security(command)
            if not security_check["safe"]:
                return {
                    "success": False,
                    "error": f"Command contains potentially dangerous operations: {', '.join(security_check['violations'])}"
                }
            
            # Prepara directory di lavoro
            if working_directory and not os.path.exists(working_directory):
                return {
                    "success": False,
                    "error": "Working directory does not exist"
                }
            
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=working_directory if working_directory else None,
                    preexec_fn=lambda: _set_execution_limits(100) if os.name != 'nt' else None  # 100MB limit
                )
                
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "command": command,
                    "working_directory": working_directory or os.getcwd(),
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time_seconds": round(execution_time, 3),
                    "timeout_seconds": timeout,
                    "security_check": security_check
                }
            
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "timeout": True
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def create_python_sandbox(sandbox_id: str = "", allowed_modules: List[str] = []) -> Dict[str, Any]:
        """
        Crea un ambiente sandbox Python isolato.
        
        Args:
            sandbox_id: ID del sandbox (opzionale, generato automaticamente se vuoto)
            allowed_modules: Lista dei moduli Python permessi
        """
        try:
            if not sandbox_id:
                sandbox_id = f"sandbox_{int(time.time())}"
            
            # Crea directory sandbox
            sandbox_dir = tempfile.mkdtemp(prefix=f"nexus_python_sandbox_{sandbox_id}_")
            
            # Lista moduli di base permessi
            default_allowed_modules = [
                "math", "random", "datetime", "json", "re", "string",
                "collections", "itertools", "functools", "operator"
            ]
            
            all_allowed_modules = list(set(default_allowed_modules + allowed_modules))
            
            # Crea script di configurazione sandbox
            sandbox_config = {
                "sandbox_id": sandbox_id,
                "created_at": time.time(),
                "sandbox_directory": sandbox_dir,
                "allowed_modules": all_allowed_modules,
                "restricted_modules": [
                    "os", "sys", "subprocess", "shutil", "glob", "socket",
                    "urllib", "http", "ftplib", "smtplib", "ssl", "tempfile"
                ],
                "max_execution_time": 30,
                "max_memory_mb": 50,
                "max_file_size_mb": 1
            }
            
            # Salva configurazione
            config_file = os.path.join(sandbox_dir, "sandbox_config.json")
            with open(config_file, 'w') as f:
                json.dump(sandbox_config, f, indent=2)
            
            # Crea script di esecuzione sicura
            safe_exec_script = f'''
import sys
import builtins
import ast
import types

# Moduli permessi
ALLOWED_MODULES = {all_allowed_modules}

# Override import
original_import = builtins.__import__

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name not in ALLOWED_MODULES:
        raise ImportError(f"Module '{{name}}' is not allowed in this sandbox")
    return original_import(name, globals, locals, fromlist, level)

builtins.__import__ = safe_import

# Funzione per eseguire codice sicuro
def execute_safe(code_string):
    try:
        # Parse del codice
        tree = ast.parse(code_string)
        
        # Compila ed esegui
        code_obj = compile(tree, '<sandbox>', 'exec')
        
        # Namespace limitato
        sandbox_globals = {{
            '__builtins__': {{
                'print': print,
                'len': len,
                'range': range,
                'list': list,
                'dict': dict,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'type': type,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'max': max,
                'min': min,
                'sum': sum,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'any': any,
                'all': all
            }}
        }}
        
        exec(code_obj, sandbox_globals)
        return {{"success": True, "output": "Code executed successfully"}}
        
    except Exception as e:
        return {{"success": False, "error": str(e), "type": type(e).__name__}}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            code = f.read()
        result = execute_safe(code)
        print(result)
'''
            
            exec_script_file = os.path.join(sandbox_dir, "safe_executor.py")
            with open(exec_script_file, 'w') as f:
                f.write(safe_exec_script)
            
            return {
                "success": True,
                "sandbox_id": sandbox_id,
                "sandbox_directory": sandbox_dir,
                "config_file": config_file,
                "executor_script": exec_script_file,
                "allowed_modules": all_allowed_modules,
                "configuration": sandbox_config,
                "usage_instructions": [
                    f"Use sandbox directory: {sandbox_dir}",
                    f"Execute Python code via: python {exec_script_file} <code_file>",
                    f"Allowed modules: {', '.join(all_allowed_modules)}",
                    "Write code to temporary files before execution",
                    "All operations are sandboxed and monitored"
                ]
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def execute_code_in_sandbox(sandbox_id: str, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Esegue codice in un sandbox esistente.
        
        Args:
            sandbox_id: ID del sandbox da utilizzare
            code: Codice da eseguire
            language: Linguaggio di programmazione (python, shell)
        """
        try:
            if not code or not code.strip():
                return {
                    "success": False,
                    "error": "No code provided"
                }
            
            # Trova sandbox directory
            temp_base = tempfile.gettempdir()
            sandbox_dirs = [d for d in os.listdir(temp_base) if d.startswith(f"nexus_python_sandbox_{sandbox_id}_")]
            
            if not sandbox_dirs:
                return {
                    "success": False,
                    "error": f"Sandbox {sandbox_id} not found"
                }
            
            sandbox_dir = os.path.join(temp_base, sandbox_dirs[0])
            config_file = os.path.join(sandbox_dir, "sandbox_config.json")
            
            if not os.path.exists(config_file):
                return {
                    "success": False,
                    "error": "Sandbox configuration not found"
                }
            
            # Carica configurazione
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if language.lower() == "python":
                # Crea file temporaneo per il codice
                code_file = os.path.join(sandbox_dir, f"code_{int(time.time())}.py")
                with open(code_file, 'w') as f:
                    f.write(code)
                
                # Esegui tramite safe executor
                executor_script = os.path.join(sandbox_dir, "safe_executor.py")
                
                start_time = time.time()
                result = subprocess.run(
                    [sys.executable, executor_script, code_file],
                    capture_output=True,
                    text=True,
                    timeout=config.get("max_execution_time", 30),
                    cwd=sandbox_dir
                )
                execution_time = time.time() - start_time
                
                # Cleanup
                if os.path.exists(code_file):
                    os.unlink(code_file)
                
                return {
                    "success": True,
                    "sandbox_id": sandbox_id,
                    "language": language,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time_seconds": round(execution_time, 3),
                    "sandbox_config": config
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Language {language} not supported in sandbox"
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Code execution timed out in sandbox",
                "timeout": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def create_and_run_tool(python_code: str, timeout: int = 60, memory_limit_mb: int = 128) -> Dict[str, Any]:
        """
        Crea ed esegue dinamicamente un tool one-time personalizzato in un ambiente Docker completamente isolato.
        
        Questa è la funzionalità più avanzata per permettere agli LLM di creare strumenti al volo 
        per risolvere problemi "long-tail" non previsti, come conversioni di formati proprietari.
        
        Args:
            python_code: Codice Python del tool personalizzato da creare ed eseguire
            timeout: Timeout di esecuzione in secondi (10-300)
            memory_limit_mb: Limite di memoria in MB (32-512)
        """
        try:
            if not python_code or not python_code.strip():
                return {
                    "success": False,
                    "error": "No Python code provided for the dynamic tool"
                }
            
            # Validazione parametri
            if timeout < 10 or timeout > 300:
                return {
                    "success": False,
                    "error": "Timeout must be between 10 and 300 seconds"
                }
            
            if memory_limit_mb < 32 or memory_limit_mb > 512:
                return {
                    "success": False,
                    "error": "Memory limit must be between 32 and 512 MB"
                }
            
            # Controlli di sicurezza avanzati per il codice dinamico
            security_check = _check_dynamic_tool_security(python_code)
            if not security_check["safe"]:
                return {
                    "success": False,
                    "error": f"Dynamic tool code contains dangerous operations: {', '.join(security_check['violations'])}",
                    "security_violations": security_check["violations"]
                }
            
            # Genera ID univoco per il tool
            tool_id = str(uuid.uuid4())[:8]
            
            # Crea directory temporanea per il tool
            with tempfile.TemporaryDirectory(prefix=f"nexus_dynamic_tool_{tool_id}_") as temp_dir:
                
                # Prepara il wrapper del tool dinamico
                tool_wrapper = _create_dynamic_tool_wrapper(python_code, tool_id)
                
                # Crea Dockerfile per l'isolamento completo
                dockerfile_content = _create_secure_dockerfile(memory_limit_mb)
                
                # Scrive i file necessari
                code_file = os.path.join(temp_dir, "dynamic_tool.py")
                dockerfile_path = os.path.join(temp_dir, "Dockerfile")
                requirements_path = os.path.join(temp_dir, "requirements.txt")
                
                with open(code_file, 'w') as f:
                    f.write(tool_wrapper)
                
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                with open(requirements_path, 'w') as f:
                    f.write("# Minimal requirements for dynamic tools\n")
                
                # Verifica che Docker sia disponibile
                docker_check = _check_docker_availability()
                if not docker_check["available"]:
                    # Fallback a esecuzione locale con restrizioni extra
                    logging.warning("Docker non disponibile, usando fallback locale con restrizioni")
                    return _execute_dynamic_tool_fallback(python_code, tool_id, timeout, memory_limit_mb)
                
                # Costruisce l'immagine Docker temporanea
                image_name = f"nexus-dynamic-tool-{tool_id}"
                build_result = _build_docker_image(temp_dir, image_name)
                
                if not build_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to build Docker image: {build_result['error']}",
                        "build_output": build_result.get("output", "")
                    }
                
                try:
                    # Esegue il tool nell'ambiente Docker isolato
                    execution_result = _run_dynamic_tool_in_docker(
                        image_name, tool_id, timeout, memory_limit_mb
                    )
                    
                    return {
                        "success": True,
                        "tool_id": tool_id,
                        "execution_mode": "docker_isolated",
                        "timeout_seconds": timeout,
                        "memory_limit_mb": memory_limit_mb,
                        "security_check": security_check,
                        "docker_image": image_name,
                        **execution_result
                    }
                
                finally:
                    # Cleanup dell'immagine Docker temporanea
                    _cleanup_docker_image(image_name)
        
        except Exception as e:
            logging.error(f"Errore nell'esecuzione del tool dinamico: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error in dynamic tool execution: {str(e)}"
            }

    @mcp.tool()
    def analyze_code_performance(code: str, language: str = "python", iterations: int = 3) -> Dict[str, Any]:
        """
        Analizza le performance del codice eseguendolo più volte.
        
        Args:
            code: Codice da analizzare
            language: Linguaggio di programmazione
            iterations: Numero di iterazioni per il test (1-10)
        """
        try:
            if not code or not code.strip():
                return {
                    "success": False,
                    "error": "No code provided"
                }
            
            if iterations < 1 or iterations > 10:
                return {
                    "success": False,
                    "error": "Iterations must be between 1 and 10"
                }
            
            if language.lower() != "python":
                return {
                    "success": False,
                    "error": "Only Python performance analysis is currently supported"
                }
            
            # Controlli di sicurezza
            security_check = _check_python_code_security(code)
            if not security_check["safe"]:
                return {
                    "success": False,
                    "error": f"Code contains potentially dangerous operations: {', '.join(security_check['violations'])}"
                }
            
            execution_times = []
            memory_usage = []
            outputs = []
            
            for i in range(iterations):
                # Crea wrapper per misurare performance
                performance_code = f"""
import time
import sys
import tracemalloc

# Start memory tracing
tracemalloc.start()
start_time = time.perf_counter()

try:
    # User code
{chr(10).join('    ' + line for line in code.split(chr(10)))}
    
    execution_success = True
    error_message = None
except Exception as e:
    execution_success = False
    error_message = str(e)

end_time = time.perf_counter()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

execution_time = end_time - start_time
peak_memory_mb = peak / 1024 / 1024

print(f"PERFORMANCE_RESULT:{{execution_time:.6f}}:{{peak_memory_mb:.2f}}:{{execution_success}}:{{error_message}}")
"""
                
                # Esegui con wrapper
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(performance_code)
                    temp_file = f.name
                
                try:
                    result = subprocess.run(
                        [sys.executable, temp_file],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        preexec_fn=lambda: _set_execution_limits(100) if os.name != 'nt' else None
                    )
                    
                    # Parse performance result
                    output_lines = result.stdout.split('\n')
                    performance_line = None
                    
                    for line in output_lines:
                        if line.startswith("PERFORMANCE_RESULT:"):
                            performance_line = line
                            break
                    
                    if performance_line:
                        parts = performance_line.split(':')
                        if len(parts) >= 4:
                            exec_time = float(parts[1])
                            memory_mb = float(parts[2])
                            success = parts[3] == "True"
                            error_msg = parts[4] if len(parts) > 4 else None
                            
                            execution_times.append(exec_time)
                            memory_usage.append(memory_mb)
                            outputs.append({
                                "iteration": i + 1,
                                "success": success,
                                "error": error_msg,
                                "stdout": '\n'.join([line for line in output_lines if not line.startswith("PERFORMANCE_RESULT:")])
                            })
                    
                finally:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
            
            if not execution_times:
                return {
                    "success": False,
                    "error": "Could not measure performance"
                }
            
            # Calcola statistiche
            avg_time = sum(execution_times) / len(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            
            avg_memory = sum(memory_usage) / len(memory_usage)
            max_memory = max(memory_usage)
            
            return {
                "success": True,
                "language": language,
                "iterations": iterations,
                "performance_metrics": {
                    "average_execution_time_seconds": round(avg_time, 6),
                    "min_execution_time_seconds": round(min_time, 6),
                    "max_execution_time_seconds": round(max_time, 6),
                    "average_memory_usage_mb": round(avg_memory, 2),
                    "peak_memory_usage_mb": round(max_memory, 2),
                    "time_consistency": round((max_time - min_time) / avg_time * 100, 2) if avg_time > 0 else 0
                },
                "raw_measurements": {
                    "execution_times": execution_times,
                    "memory_usage": memory_usage
                },
                "execution_outputs": outputs,
                "performance_rating": _rate_performance(avg_time, max_memory)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Helper functions
def _set_execution_limits(memory_limit_mb):
    """Imposta limiti di risorse per l'esecuzione."""
    try:
        # Limite memoria
        memory_bytes = memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        
        # Limite CPU (30 secondi)
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        
        # Limite file aperti
        resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    except:
        pass  # Ignora errori su sistemi che non supportano setrlimit

def _check_python_code_security(code):
    """Controlla la sicurezza del codice Python."""
    dangerous_patterns = [
        r'\bopen\s*\(',
        r'\bfile\s*\(',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\b__import__\s*\(',
        r'\bsubprocess\b',
        r'\bos\.',
        r'\bsys\.',
        r'\bshutil\b',
        r'\bglob\b',
        r'\bsocket\b',
        r'\btempfile\b',
        r'\bdel\s+',
        r'\brmdir\b',
        r'\bunlink\b',
        r'\bremove\b'
    ]
    
    violations = []
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            violations.append(pattern.replace('\\b', '').replace('\\s*\\(', '').replace('\\', ''))
    
    return {
        "safe": len(violations) == 0,
        "violations": violations
    }

def _check_shell_command_security(command):
    """Controlla la sicurezza di un comando shell."""
    dangerous_commands = [
        'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs',
        'dd', 'shred', 'sudo', 'su', 'chmod', 'chown',
        'passwd', 'useradd', 'userdel', 'mount', 'umount',
        'kill', 'killall', 'pkill', 'systemctl', 'service',
        'iptables', 'netstat', 'ss', 'nmap', 'wget', 'curl',
        'ssh', 'scp', 'rsync', 'nc', 'netcat'
    ]
    
    violations = []
    command_lower = command.lower()
    
    for dangerous in dangerous_commands:
        if dangerous in command_lower:
            violations.append(dangerous)
    
    # Controlla pipe e redirection sospetti
    if any(char in command for char in ['>', '>>', '|', '&', ';']):
        if any(dangerous in command_lower for dangerous in ['dev', 'proc', 'sys', 'etc']):
            violations.append("suspicious_redirection")
    
    return {
        "safe": len(violations) == 0,
        "violations": violations
    }

def _analyze_ast_complexity(tree):
    """Analizza la complessità del codice tramite AST."""
    complexity = {
        "functions": 0,
        "classes": 0,
        "loops": 0,
        "conditionals": 0,
        "try_blocks": 0,
        "imports": 0,
        "max_nesting_level": 0
    }
    
    def analyze_node(node, depth=0):
        complexity["max_nesting_level"] = max(complexity["max_nesting_level"], depth)
        
        if isinstance(node, ast.FunctionDef):
            complexity["functions"] += 1
        elif isinstance(node, ast.ClassDef):
            complexity["classes"] += 1
        elif isinstance(node, (ast.For, ast.While)):
            complexity["loops"] += 1
        elif isinstance(node, ast.If):
            complexity["conditionals"] += 1
        elif isinstance(node, ast.Try):
            complexity["try_blocks"] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            complexity["imports"] += 1
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.ClassDef, ast.For, ast.While, ast.If, ast.Try)):
                analyze_node(child, depth + 1)
            else:
                analyze_node(child, depth)
    
    analyze_node(tree)
    return complexity

def _check_python_style(code):
    """Controlla lo stile del codice Python."""
    issues = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Linee troppo lunghe
        if len(line) > 88:
            issues.append({
                "line": i,
                "type": "line_length",
                "message": f"Line too long ({len(line)} > 88 characters)"
            })
        
        # Spazi trailing
        if line.rstrip() != line:
            issues.append({
                "line": i,
                "type": "trailing_whitespace",
                "message": "Trailing whitespace"
            })
        
        # Import multipli
        if line.strip().startswith('import ') and ',' in line:
            issues.append({
                "line": i,
                "type": "multiple_imports",
                "message": "Multiple imports on one line"
            })
    
    return issues

def _rate_performance(avg_time, max_memory):
    """Valuta le performance del codice."""
    if avg_time < 0.001 and max_memory < 1:
        return "Excellent"
    elif avg_time < 0.01 and max_memory < 5:
        return "Good"
    elif avg_time < 0.1 and max_memory < 25:
        return "Fair"
    else:
        return "Poor"

# Helper functions for dynamic tool creation
def _check_dynamic_tool_security(code):
    """Controlli di sicurezza avanzati per tool dinamici."""
    dangerous_patterns = [
        r'\bopen\s*\(',
        r'\bfile\s*\(',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\b__import__\s*\(',
        r'\bsubprocess\b',
        r'\bos\.',
        r'\bsys\.',
        r'\bshutil\b',
        r'\bglob\b',
        r'\bsocket\b',
        r'\btempfile\b',
        r'\bdel\s+',
        r'\brmdir\b',
        r'\bunlink\b',
        r'\bremove\b',
        r'\bimport\s+os\b',
        r'\bfrom\s+os\s+import\b',
        r'\bimport\s+sys\b',
        r'\bfrom\s+sys\s+import\b',
        r'\bimport\s+subprocess\b',
        r'\bfrom\s+subprocess\s+import\b',
        r'\bimport\s+shutil\b',
        r'\b__file__\b',
        r'\b__name__\b',
        r'\bglobals\s*\(\s*\)',
        r'\blocals\s*\(\s*\)',
        r'\bvars\s*\(\s*\)',
        r'\bdir\s*\(\s*\)',
        r'\bgetattr\s*\(',
        r'\bsetattr\s*\(',
        r'\bdelattr\s*\(',
        r'\bhasattr\s*\(',
        r'\bcompile\s*\(',
        r'\bbytearray\s*\(',
        r'\bmemoryview\s*\(',
        r'\bexit\s*\(\s*\)',
        r'\bquit\s*\(\s*\)',
        r'0o[0-7]+',  # Octal numbers
        r'0x[0-9a-fA-F]+',  # Hex numbers that might be addresses
    ]
    
    violations = []
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            violations.append(pattern.replace('\\b', '').replace('\\s*\\(', '').replace('\\', ''))
    
    # Controlla import sospetti più specificamente
    import_lines = [line.strip() for line in code.split('\n') if 'import' in line]
    for line in import_lines:
        for dangerous_module in ['os', 'sys', 'subprocess', 'shutil', 'glob', 'socket', 'urllib', 'http', 'ftplib', 'smtplib', 'ssl', 'tempfile', 'pickle', 'marshal', 'ctypes', 'multiprocessing', 'threading']:
            if f'import {dangerous_module}' in line or f'from {dangerous_module}' in line:
                violations.append(f"dangerous_import_{dangerous_module}")
    
    return {
        "safe": len(violations) == 0,
        "violations": violations
    }

def _create_dynamic_tool_wrapper(user_code, tool_id):
    """Crea un wrapper sicuro per il tool dinamico."""
    wrapper_template = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nexus Dynamic Tool - ID: {tool_id}
Automatically generated secure wrapper for user-defined tool.
"""

import sys
import time
import json
import traceback
import signal
import gc
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Dynamic tool execution timed out")

# Signal handler for graceful shutdown
signal.signal(signal.SIGALRM, timeout_handler)

# Restricted builtins for security
SAFE_BUILTINS = {{
    'abs': abs,
    'all': all,
    'any': any,
    'ascii': ascii,
    'bin': bin,
    'bool': bool,
    'chr': chr,
    'dict': dict,
    'divmod': divmod,
    'enumerate': enumerate,
    'filter': filter,
    'float': float,
    'format': format,
    'frozenset': frozenset,
    'hex': hex,
    'int': int,
    'isinstance': isinstance,
    'issubclass': issubclass,
    'iter': iter,
    'len': len,
    'list': list,
    'map': map,
    'max': max,
    'min': min,
    'next': next,
    'oct': oct,
    'ord': ord,
    'pow': pow,
    'print': print,
    'range': range,
    'repr': repr,
    'reversed': reversed,
    'round': round,
    'set': set,
    'slice': slice,
    'sorted': sorted,
    'str': str,
    'sum': sum,
    'tuple': tuple,
    'type': type,
    'zip': zip,
}}

# Safe modules allowed for import
ALLOWED_MODULES = {{
    'math', 'random', 'datetime', 'json', 're', 'string',
    'collections', 'itertools', 'functools', 'operator',
    'decimal', 'fractions', 'statistics', 'uuid', 'hashlib',
    'base64', 'binascii', 'calendar', 'time', 'urllib.parse'
}}

# Custom import function
import builtins
original_import = builtins.__import__

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split('.')[0] not in ALLOWED_MODULES:
        raise ImportError(f"Module '{{name}}' is not allowed in dynamic tools")
    return original_import(name, globals, locals, fromlist, level)

# Override dangerous builtins
safe_globals = {{
    '__builtins__': SAFE_BUILTINS,
    '__import__': safe_import,
    '__name__': '__main__',
    '__doc__': 'Nexus Dynamic Tool Execution Environment',
}}

def execute_user_code():
    """Esegue il codice utente in ambiente sicuro."""
    try:
        # Capture stdout and stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Set execution timeout
            signal.alarm(55)  # 5 seconds less than container timeout
            
            start_time = time.time()
            
            # Execute user code in safe environment
            user_code = """
{user_code}
"""
            
            # Compile and execute
            compiled_code = compile(user_code, '<dynamic_tool>', 'exec')
            exec(compiled_code, safe_globals)
            
            end_time = time.time()
            
            # Disable alarm
            signal.alarm(0)
            
            execution_time = end_time - start_time
            
            return {{
                "success": True,
                "tool_id": "{tool_id}",
                "execution_time_seconds": round(execution_time, 6),
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "message": "Dynamic tool executed successfully"
            }}
    
    except TimeoutError:
        return {{
            "success": False,
            "error": "Dynamic tool execution timed out",
            "tool_id": "{tool_id}",
            "timeout": True
        }}
    except Exception as e:
        return {{
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "tool_id": "{tool_id}",
            "traceback": traceback.format_exc(),
            "stdout": stdout_capture.getvalue() if 'stdout_capture' in locals() else "",
            "stderr": stderr_capture.getvalue() if 'stderr_capture' in locals() else ""
        }}
    finally:
        # Force garbage collection
        gc.collect()

if __name__ == "__main__":
    result = execute_user_code()
    print(json.dumps(result, indent=2))
'''
    
    return wrapper_template

def _create_secure_dockerfile(memory_limit_mb):
    """Crea un Dockerfile sicuro per l'esecuzione del tool dinamico."""
    dockerfile_content = f"""# Nexus Dynamic Tool - Secure Execution Environment
FROM python:3.12-alpine

# Set security-focused environment variables
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONHASHSEED=random \\
    PIP_NO_CACHE_DIR=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN addgroup -g 1000 nexus && \\
    adduser -D -s /bin/sh -u 1000 -G nexus nexus

# Set working directory
WORKDIR /app

# Copy tool files
COPY dynamic_tool.py /app/
COPY requirements.txt /app/

# Install minimal Python requirements if any
RUN pip install --no-cache-dir -r requirements.txt

# Set strict permissions
RUN chown -R nexus:nexus /app && \\
    chmod 755 /app && \\
    chmod 644 /app/dynamic_tool.py

# Switch to non-root user
USER nexus

# Set resource limits at runtime
# Memory limit: {memory_limit_mb}MB
# CPU limit: 0.5 cores
# Network: none (isolated)
# Filesystem: read-only except /tmp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=1 \\
    CMD python -c "print('healthy')" || exit 1

# Entry point
ENTRYPOINT ["python", "/app/dynamic_tool.py"]
"""
    return dockerfile_content

def _check_docker_availability():
    """Controlla se Docker è disponibile e funzionante."""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return {"available": False, "error": "Docker not accessible"}
        
        # Test daemon
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
        daemon_running = result.returncode == 0
        
        return {"available": daemon_running, "version": result.stdout.strip() if daemon_running else None}
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        return {"available": False, "error": str(e)}

def _build_docker_image(build_context, image_name):
    """Costruisce l'immagine Docker per il tool dinamico."""
    try:
        start_time = time.time()
        
        result = subprocess.run([
            'docker', 'build', 
            '-t', image_name,
            '--no-cache',  # Ensure fresh build
            '--pull',      # Pull latest base image
            build_context
        ], capture_output=True, text=True, timeout=120)
        
        build_time = time.time() - start_time
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Docker build failed",
                "build_output": result.stderr,
                "build_time_seconds": round(build_time, 2)
            }
        
        return {
            "success": True,
            "image_name": image_name,
            "build_time_seconds": round(build_time, 2),
            "build_output": result.stdout
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Docker build timed out after 120 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Docker build error: {str(e)}"
        }

def _run_dynamic_tool_in_docker(image_name, tool_id, timeout, memory_limit_mb):
    """Esegue il tool dinamico nell'ambiente Docker isolato."""
    try:
        start_time = time.time()
        
        # Container security configuration
        container_name = f"nexus-dynamic-tool-{tool_id}"
        
        docker_cmd = [
            'docker', 'run',
            '--name', container_name,
            '--rm',  # Auto-remove after execution
            '--memory', f"{memory_limit_mb}m",  # Memory limit
            '--cpus', "0.5",  # CPU limit
            '--network', 'none',  # No network access
            '--read-only',  # Read-only filesystem
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=10m',  # Writable /tmp with limits
            '--security-opt', 'no-new-privileges',  # Security
            '--cap-drop', 'ALL',  # Drop all capabilities
            '--user', '1000:1000',  # Non-root user
            image_name
        ]
        
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        # Parse JSON output from the tool
        try:
            if result.stdout.strip():
                tool_result = json.loads(result.stdout.strip())
            else:
                tool_result = {"success": False, "error": "No output from dynamic tool"}
        except json.JSONDecodeError:
            tool_result = {
                "success": False,
                "error": "Invalid JSON output from dynamic tool",
                "raw_output": result.stdout
            }
        
        return {
            "container_name": container_name,
            "container_execution_time_seconds": round(execution_time, 3),
            "container_return_code": result.returncode,
            "container_stderr": result.stderr,
            "tool_result": tool_result
        }
    
    except subprocess.TimeoutExpired:
        # Try to kill the container if it's still running
        try:
            subprocess.run(['docker', 'kill', container_name], capture_output=True, timeout=10)
        except:
            pass
        
        return {
            "success": False,
            "error": f"Dynamic tool execution timed out after {timeout} seconds",
            "timeout": True,
            "tool_id": tool_id
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Docker execution error: {str(e)}",
            "tool_id": tool_id
        }

def _cleanup_docker_image(image_name):
    """Rimuove l'immagine Docker temporanea."""
    try:
        subprocess.run(['docker', 'rmi', '-f', image_name], capture_output=True, timeout=30)
    except:
        pass  # Ignore cleanup errors

def _execute_dynamic_tool_fallback(python_code, tool_id, timeout, memory_limit_mb):
    """Fallback per esecuzione locale quando Docker non è disponibile."""
    try:
        # Create more restricted local execution
        wrapper_code = f'''
import sys
import time
import json
import traceback
import signal
import resource
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

def timeout_handler(signum, frame):
    raise TimeoutError("Dynamic tool execution timed out")

signal.signal(signal.SIGALRM, timeout_handler)

# Set resource limits
try:
    memory_bytes = {memory_limit_mb} * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    resource.setrlimit(resource.RLIMIT_CPU, ({timeout-5}, {timeout-5}))
except:
    pass

# Safe execution environment with proper import handling
allowed_modules = {{
    'math', 'random', 'datetime', 'json', 're', 'string',
    'collections', 'itertools', 'functools', 'operator',
    'decimal', 'fractions', 'statistics', 'uuid', 'hashlib',
    'base64', 'binascii', 'calendar', 'time'
}}

import builtins
original_import = builtins.__import__

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split('.')[0] not in allowed_modules:
        raise ImportError(f"Module '{{name}}' is not allowed in dynamic tools")
    return original_import(name, globals, locals, fromlist, level)

safe_globals = {{
    '__builtins__': {{
        'abs': abs, 'all': all, 'any': any, 'bool': bool, 'chr': chr,
        'dict': dict, 'enumerate': enumerate, 'filter': filter, 'float': float,
        'int': int, 'len': len, 'list': list, 'map': map, 'max': max,
        'min': min, 'print': print, 'range': range, 'round': round,
        'set': set, 'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple, 'type': type,
        'zip': zip, '__import__': safe_import
    }},
    '__name__': '__main__'
}}

try:
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        signal.alarm({timeout-5})
        start_time = time.time()
        
        user_code = """{python_code}"""
        compiled_code = compile(user_code, '<dynamic_tool>', 'exec')
        exec(compiled_code, safe_globals)
        
        end_time = time.time()
        signal.alarm(0)
        
        result = {{
            "success": True,
            "tool_id": "{tool_id}",
            "execution_time_seconds": round(end_time - start_time, 6),
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "execution_mode": "local_fallback"
        }}
        
except Exception as e:
    result = {{
        "success": False,
        "error": str(e),
        "error_type": type(e).__name__,
        "tool_id": "{tool_id}",
        "execution_mode": "local_fallback"
    }}

print(json.dumps(result))
'''
        
        # Execute in subprocess with limits
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapper_code)
            temp_file = f.name
        
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=lambda: _set_execution_limits(memory_limit_mb) if os.name != 'nt' else None
            )
            execution_time = time.time() - start_time
            
            if result.stdout.strip():
                # Try to find JSON output in stdout
                lines = result.stdout.strip().split('\n')
                json_line = None
                for line in reversed(lines):  # Look for JSON from the end
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        json_line = line.strip()
                        break
                
                if json_line:
                    try:
                        tool_result = json.loads(json_line)
                    except json.JSONDecodeError:
                        tool_result = {"success": False, "error": "Invalid JSON in output", "raw_output": result.stdout}
                else:
                    tool_result = {"success": True, "stdout": result.stdout, "message": "No JSON output, but execution completed"}
            else:
                tool_result = {"success": False, "error": "No output from fallback execution"}
            
            return {
                "success": True,
                "execution_mode": "local_fallback",
                "tool_id": tool_id,
                "fallback_execution_time_seconds": round(execution_time, 3),
                "fallback_return_code": result.returncode,
                "fallback_stdout": result.stdout,
                "fallback_stderr": result.stderr,
                "tool_result": tool_result,
                "warning": "Executed in local fallback mode - Docker recommended for better security"
            }
        
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Fallback execution failed: {str(e)}",
            "tool_id": tool_id,
            "execution_mode": "local_fallback"
        }