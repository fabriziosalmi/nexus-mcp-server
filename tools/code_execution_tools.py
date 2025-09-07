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