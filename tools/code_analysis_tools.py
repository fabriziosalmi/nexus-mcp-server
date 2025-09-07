# -*- coding: utf-8 -*-
# tools/code_analysis_tools.py
import ast
import re
import os
import subprocess
import tempfile
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import json
import hashlib
from collections import defaultdict, Counter
from datetime import datetime, timezone

def register_tools(mcp):
    """Registra i tool di analisi codice avanzata con l'istanza del server MCP."""
    logging.info("🔍 Registrazione tool-set: Code Analysis Tools")

    @mcp.tool()
    def analyze_python_syntax(code: str) -> Dict[str, Any]:
        """
        Analizza la sintassi del codice Python e fornisce metriche di base.
        
        Args:
            code: Il codice Python da analizzare
        """
        try:
            # Parse del codice
            tree = ast.parse(code)
            
            # Contatori
            functions = 0
            classes = 0
            imports = 0
            lines = len(code.split('\n'))
            
            # Analisi AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions += 1
                elif isinstance(node, ast.ClassDef):
                    classes += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports += 1
            
            # Calcola complessità ciclomatica di base
            complexity = 1  # Base complexity
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.Try):
                    complexity += len(node.handlers)
            
            return {
                "syntax_valid": True,
                "lines_of_code": lines,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "cyclomatic_complexity": complexity,
                "complexity_rating": "Low" if complexity <= 10 else "Medium" if complexity <= 20 else "High"
            }
        except SyntaxError as e:
            return {
                "syntax_valid": False,
                "error": f"Syntax Error: {e.msg}",
                "line": e.lineno,
                "column": e.offset
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def check_code_style(code: str, language: str = "python") -> Dict[str, Any]:
        """
        Controlla lo stile del codice e fornisce suggerimenti.
        
        Args:
            code: Il codice da analizzare
            language: Il linguaggio di programmazione (python, javascript, etc.)
        """
        try:
            issues = []
            suggestions = []
            
            if language.lower() == "python":
                lines = code.split('\n')
                
                # Controlli stile Python
                for i, line in enumerate(lines, 1):
                    # Linee troppo lunghe
                    if len(line) > 88:
                        issues.append(f"Line {i}: Line too long ({len(line)} > 88 characters)")
                    
                    # Spazi vs tabs
                    if '\t' in line and '    ' in line:
                        issues.append(f"Line {i}: Mixed tabs and spaces")
                    
                    # Spazi trailing
                    if line.endswith(' ') or line.endswith('\t'):
                        issues.append(f"Line {i}: Trailing whitespace")
                    
                    # Import style
                    if line.strip().startswith('import ') and ',' in line:
                        issues.append(f"Line {i}: Multiple imports on one line")
                
                # Controlli generali
                if not code.strip().startswith('# -*- coding: utf-8 -*-'):
                    suggestions.append("Consider adding encoding declaration at the top")
                
                if 'def ' in code and '"""' not in code and "'''" not in code:
                    suggestions.append("Consider adding docstrings to functions")
            
            elif language.lower() == "javascript":
                lines = code.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Semicolons
                    if re.search(r'[^;}]\s*$', line.strip()) and line.strip() and not line.strip().startswith('//'):
                        if any(keyword in line for keyword in ['var ', 'let ', 'const ', 'return ', 'throw ']):
                            issues.append(f"Line {i}: Missing semicolon")
                    
                    # var vs let/const
                    if 'var ' in line:
                        suggestions.append(f"Line {i}: Consider using 'let' or 'const' instead of 'var'")
            
            score = max(0, 100 - len(issues) * 5)
            rating = "Excellent" if score >= 90 else "Good" if score >= 70 else "Fair" if score >= 50 else "Poor"
            
            return {
                "language": language,
                "style_score": score,
                "rating": rating,
                "issues": issues,
                "suggestions": suggestions,
                "total_issues": len(issues)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def detect_code_patterns(code: str) -> Dict[str, Any]:
        """
        Rileva pattern comuni e anti-pattern nel codice.
        
        Args:
            code: Il codice da analizzare
        """
        try:
            patterns_found = []
            anti_patterns = []
            
            # Pattern comuni
            patterns = {
                "Design Patterns": {
                    "singleton": r"class\s+\w+.*def\s+__new__",
                    "factory": r"def\s+create_\w+|def\s+\w+_factory",
                    "decorator": r"@\w+|def\s+\w+\(.*\).*def\s+wrapper"
                },
                "Security Patterns": {
                    "sql_injection_risk": r"execute\(.*%.*\)|\.format\(.*\)",
                    "hardcoded_password": r"password\s*=\s*['\"][^'\"]*['\"]",
                    "eval_usage": r"eval\(|exec\("
                },
                "Performance Patterns": {
                    "list_comprehension": r"\[.*for.*in.*\]",
                    "generator_expression": r"\(.*for.*in.*\)",
                    "string_concatenation": r"\+.*['\"]"
                }
            }
            
            # Anti-pattern comuni
            anti_pattern_checks = {
                "Empty except blocks": r"except.*:\s*pass",
                "Bare except": r"except\s*:",
                "Global variables": r"global\s+\w+",
                "Long parameter lists": r"def\s+\w+\([^)]{50,}\)",
                "Nested loops": r"for.*:.*for.*:",
                "Deep nesting": None  # Verrà controllato separatamente
            }
            
            # Cerca pattern
            for category, category_patterns in patterns.items():
                for pattern_name, pattern_regex in category_patterns.items():
                    if re.search(pattern_regex, code, re.MULTILINE):
                        patterns_found.append({
                            "category": category,
                            "pattern": pattern_name,
                            "description": f"Found {pattern_name.replace('_', ' ')} pattern"
                        })
            
            # Cerca anti-pattern
            for anti_pattern, regex in anti_pattern_checks.items():
                if regex and re.search(regex, code, re.MULTILINE):
                    anti_patterns.append({
                        "type": anti_pattern,
                        "severity": "High" if "security" in anti_pattern.lower() else "Medium"
                    })
            
            # Controlla nesting profondo
            max_nesting = 0
            current_nesting = 0
            for line in code.split('\n'):
                stripped = line.lstrip()
                if stripped.startswith(('if ', 'for ', 'while ', 'with ', 'try:', 'def ', 'class ')):
                    current_nesting = len(line) - len(stripped)
                    max_nesting = max(max_nesting, current_nesting // 4)
            
            if max_nesting > 4:
                anti_patterns.append({
                    "type": "Deep nesting",
                    "severity": "Medium",
                    "details": f"Maximum nesting level: {max_nesting}"
                })
            
            return {
                "patterns_found": patterns_found,
                "anti_patterns": anti_patterns,
                "pattern_count": len(patterns_found),
                "anti_pattern_count": len(anti_patterns),
                "max_nesting_level": max_nesting,
                "code_quality": "Good" if len(anti_patterns) < 2 else "Fair" if len(anti_patterns) < 5 else "Poor"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def estimate_code_complexity(code: str) -> Dict[str, Any]:
        """
        Stima la complessità del codice usando varie metriche.
        
        Args:
            code: Il codice da analizzare
        """
        try:
            lines = code.split('\n')
            total_lines = len(lines)
            blank_lines = sum(1 for line in lines if not line.strip())
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            code_lines = total_lines - blank_lines - comment_lines
            
            # Conta operatori e operandi (Halstead metrics approximation)
            operators = len(re.findall(r'[+\-*/=<>!&|^%]|==|!=|<=|>=|and|or|not|in|is', code))
            operands = len(re.findall(r'\b\w+\b', code))
            
            # Complessità ciclomatica
            cyclomatic_complexity = 1
            decision_points = re.findall(r'\b(if|elif|while|for|except|and|or)\b', code)
            cyclomatic_complexity += len(decision_points)
            
            # Maintainability Index (simplified)
            halstead_volume = (operators + operands) * (operators + operands).bit_length() if operators + operands > 0 else 0
            maintainability_index = max(0, 171 - 5.2 * cyclomatic_complexity - 0.23 * halstead_volume - 16.2 * (code_lines).bit_length())
            
            # Classificazioni
            complexity_rating = (
                "Very Low" if cyclomatic_complexity <= 5 else
                "Low" if cyclomatic_complexity <= 10 else
                "Medium" if cyclomatic_complexity <= 20 else
                "High" if cyclomatic_complexity <= 50 else
                "Very High"
            )
            
            maintainability_rating = (
                "Excellent" if maintainability_index >= 85 else
                "Good" if maintainability_index >= 70 else
                "Fair" if maintainability_index >= 55 else
                "Poor"
            )
            
            return {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
                "comment_ratio": round(comment_lines / total_lines * 100, 2) if total_lines > 0 else 0,
                "cyclomatic_complexity": cyclomatic_complexity,
                "complexity_rating": complexity_rating,
                "operators": operators,
                "operands": operands,
                "halstead_volume": round(halstead_volume, 2),
                "maintainability_index": round(maintainability_index, 2),
                "maintainability_rating": maintainability_rating,
                "recommendations": [
                    "Add more comments" if comment_lines / total_lines < 0.1 else None,
                    "Reduce complexity" if cyclomatic_complexity > 20 else None,
                    "Break down large functions" if code_lines > 100 else None
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def security_vulnerability_scan(code: str, language: str = "python") -> Dict[str, Any]:
        """
        Scansiona il codice per vulnerabilità di sicurezza comuni.
        
        Args:
            code: Il codice da analizzare
            language: Il linguaggio di programmazione
        """
        try:
            vulnerabilities = []
            security_score = 100
            
            if language.lower() == "python":
                # Vulnerabilità Python specifiche
                python_vulns = {
                    "SQL Injection": {
                        "patterns": [
                            r"execute\s*\(\s*['\"].*%.*['\"]",
                            r"\.format\s*\(",
                            r"f['\"].*\{.*\}.*['\"].*execute",
                            r"cursor\.execute\s*\(\s*.*\+.*\)"
                        ],
                        "severity": "High",
                        "description": "Potential SQL injection vulnerability"
                    },
                    "Command Injection": {
                        "patterns": [
                            r"os\.system\s*\(",
                            r"subprocess\.call\s*\(.*shell\s*=\s*True",
                            r"subprocess\.run\s*\(.*shell\s*=\s*True",
                            r"eval\s*\(",
                            r"exec\s*\("
                        ],
                        "severity": "Critical",
                        "description": "Potential command injection vulnerability"
                    },
                    "Path Traversal": {
                        "patterns": [
                            r"open\s*\(\s*.*\+.*\)",
                            r"\.\.\/",
                            r"\.\.\\",
                            r"os\.path\.join\s*\(.*user"
                        ],
                        "severity": "Medium",
                        "description": "Potential path traversal vulnerability"
                    },
                    "Hardcoded Secrets": {
                        "patterns": [
                            r"password\s*=\s*['\"][^'\"]{8,}['\"]",
                            r"api_key\s*=\s*['\"][^'\"]{16,}['\"]",
                            r"secret\s*=\s*['\"][^'\"]{8,}['\"]",
                            r"token\s*=\s*['\"][^'\"]{16,}['\"]"
                        ],
                        "severity": "High",
                        "description": "Hardcoded credentials detected"
                    },
                    "Insecure Randomness": {
                        "patterns": [
                            r"random\.random\(",
                            r"random\.choice\(",
                            r"random\.randint\("
                        ],
                        "severity": "Medium",
                        "description": "Using insecure random number generator"
                    },
                    "Unsafe Deserialization": {
                        "patterns": [
                            r"pickle\.loads\(",
                            r"cPickle\.loads\(",
                            r"yaml\.load\(\s*[^,)]*\s*\)"
                        ],
                        "severity": "High",
                        "description": "Unsafe deserialization detected"
                    }
                }
                
                for vuln_type, vuln_info in python_vulns.items():
                    for pattern in vuln_info["patterns"]:
                        matches = list(re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE))
                        for match in matches:
                            line_num = code[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "type": vuln_type,
                                "severity": vuln_info["severity"],
                                "description": vuln_info["description"],
                                "line": line_num,
                                "code_snippet": code.split('\n')[line_num-1].strip(),
                                "recommendation": self._get_security_recommendation(vuln_type)
                            })
                            
                            # Deduct points based on severity
                            if vuln_info["severity"] == "Critical":
                                security_score -= 25
                            elif vuln_info["severity"] == "High":
                                security_score -= 15
                            elif vuln_info["severity"] == "Medium":
                                security_score -= 10
                            else:
                                security_score -= 5
            
            elif language.lower() == "javascript":
                js_vulns = {
                    "XSS": {
                        "patterns": [
                            r"innerHTML\s*=\s*.*\+",
                            r"document\.write\s*\(",
                            r"eval\s*\(",
                            r"\.html\s*\(\s*.*\+.*\)"
                        ],
                        "severity": "High",
                        "description": "Potential XSS vulnerability"
                    },
                    "Prototype Pollution": {
                        "patterns": [
                            r"__proto__",
                            r"constructor\.prototype",
                            r"Object\.prototype"
                        ],
                        "severity": "Medium",
                        "description": "Potential prototype pollution"
                    }
                }
                
                for vuln_type, vuln_info in js_vulns.items():
                    for pattern in vuln_info["patterns"]:
                        matches = list(re.finditer(pattern, code, re.MULTILINE))
                        for match in matches:
                            line_num = code[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "type": vuln_type,
                                "severity": vuln_info["severity"],
                                "description": vuln_info["description"],
                                "line": line_num,
                                "code_snippet": code.split('\n')[line_num-1].strip()
                            })
            
            security_score = max(0, security_score)
            security_rating = (
                "Excellent" if security_score >= 90 else
                "Good" if security_score >= 70 else
                "Fair" if security_score >= 50 else
                "Poor"
            )
            
            return {
                "language": language,
                "security_score": security_score,
                "security_rating": security_rating,
                "vulnerabilities": vulnerabilities,
                "vulnerability_count": len(vulnerabilities),
                "critical_issues": len([v for v in vulnerabilities if v["severity"] == "Critical"]),
                "high_issues": len([v for v in vulnerabilities if v["severity"] == "High"]),
                "medium_issues": len([v for v in vulnerabilities if v["severity"] == "Medium"]),
                "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                "recommendations": self._generate_security_recommendations(vulnerabilities)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_security_recommendation(self, vuln_type: str) -> str:
        """Fornisce raccomandazioni per correggere vulnerabilità specifiche."""
        recommendations = {
            "SQL Injection": "Use parameterized queries or ORM instead of string concatenation",
            "Command Injection": "Avoid shell=True, use subprocess with list arguments, validate inputs",
            "Path Traversal": "Validate and sanitize file paths, use os.path.abspath()",
            "Hardcoded Secrets": "Use environment variables or secure credential storage",
            "Insecure Randomness": "Use secrets module for cryptographic purposes",
            "Unsafe Deserialization": "Use safe serialization formats like JSON, validate inputs",
            "XSS": "Sanitize user inputs, use textContent instead of innerHTML",
            "Prototype Pollution": "Validate object properties, use Object.create(null)"
        }
        return recommendations.get(vuln_type, "Review code for security best practices")

    def _generate_security_recommendations(self, vulnerabilities: List[Dict]) -> List[str]:
        """Genera raccomandazioni di sicurezza generali."""
        recommendations = []
        
        if any(v["severity"] == "Critical" for v in vulnerabilities):
            recommendations.append("Critical vulnerabilities found - immediate action required")
        
        if len(vulnerabilities) > 5:
            recommendations.append("Consider implementing automated security testing")
        
        vuln_types = set(v["type"] for v in vulnerabilities)
        if "SQL Injection" in vuln_types or "Command Injection" in vuln_types:
            recommendations.append("Implement input validation and sanitization")
        
        if "Hardcoded Secrets" in vuln_types:
            recommendations.append("Implement secure credential management system")
        
        return recommendations

    @mcp.tool()
    def analyze_dependencies(code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analizza le dipendenze e gli import del codice.
        
        Args:
            code: Il codice da analizzare
            language: Il linguaggio di programmazione
        """
        try:
            dependencies = []
            import_analysis = {}
            
            if language.lower() == "python":
                # Analisi import Python
                try:
                    tree = ast.parse(code)
                    standard_libs = self._get_python_standard_libraries()
                    
                    imports = {
                        "standard": [],
                        "third_party": [],
                        "local": [],
                        "unused": [],
                        "star_imports": []
                    }
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                module_name = alias.name.split('.')[0]
                                if module_name in standard_libs:
                                    imports["standard"].append(alias.name)
                                elif module_name.startswith('.'):
                                    imports["local"].append(alias.name)
                                else:
                                    imports["third_party"].append(alias.name)
                        
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                module_name = node.module.split('.')[0]
                                if module_name in standard_libs:
                                    imports["standard"].append(node.module)
                                elif node.module.startswith('.'):
                                    imports["local"].append(node.module)
                                else:
                                    imports["third_party"].append(node.module)
                            
                            # Check for star imports
                            for alias in node.names:
                                if alias.name == '*':
                                    imports["star_imports"].append(node.module or "relative")
                    
                    # Rimuovi duplicati
                    for key in imports:
                        imports[key] = list(set(imports[key]))
                    
                    import_analysis = {
                        "total_imports": sum(len(v) for v in imports.values() if v != imports["star_imports"]),
                        "standard_library": imports["standard"],
                        "third_party": imports["third_party"],
                        "local_imports": imports["local"],
                        "star_imports": imports["star_imports"],
                        "import_complexity": len(imports["third_party"]) + len(imports["star_imports"]) * 2
                    }
                    
                except SyntaxError:
                    # Fallback a regex se AST fallisce
                    import_analysis = self._regex_import_analysis(code)
            
            elif language.lower() == "javascript":
                # Analisi import JavaScript/Node.js
                import_patterns = [
                    r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
                    r"const\s+.*\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]",
                    r"import\s*\(\s*['\"]([^'\"]+)['\"]"
                ]
                
                js_imports = {"external": [], "local": []}
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, code)
                    for match in matches:
                        if match.startswith('./') or match.startswith('../'):
                            js_imports["local"].append(match)
                        else:
                            js_imports["external"].append(match)
                
                import_analysis = {
                    "total_imports": len(js_imports["external"]) + len(js_imports["local"]),
                    "external_modules": list(set(js_imports["external"])),
                    "local_modules": list(set(js_imports["local"]))
                }
            
            # Analisi sicurezza dipendenze
            security_issues = []
            for dep in import_analysis.get("third_party", []):
                if dep in ["pickle", "cPickle", "marshal"]:
                    security_issues.append(f"Potentially unsafe module: {dep}")
            
            return {
                "language": language,
                "import_analysis": import_analysis,
                "security_issues": security_issues,
                "recommendations": self._generate_dependency_recommendations(import_analysis),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_python_standard_libraries(self) -> Set[str]:
        """Restituisce set di librerie standard Python."""
        return {
            'os', 'sys', 'json', 'datetime', 're', 'math', 'random', 'collections',
            'itertools', 'functools', 'operator', 'pathlib', 'typing', 'logging',
            'unittest', 'sqlite3', 'urllib', 'http', 'email', 'html', 'xml',
            'csv', 'configparser', 'argparse', 'tempfile', 'shutil', 'glob',
            'pickle', 'base64', 'hashlib', 'hmac', 'secrets', 'ssl', 'socket',
            'threading', 'multiprocessing', 'asyncio', 'concurrent', 'queue'
        }

    def _regex_import_analysis(self, code: str) -> Dict[str, Any]:
        """Analisi import usando regex come fallback."""
        import_patterns = [
            r"^import\s+([^\s]+)",
            r"^from\s+([^\s]+)\s+import"
        ]
        
        imports = []
        for pattern in import_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            imports.extend(matches)
        
        return {
            "total_imports": len(imports),
            "modules": list(set(imports)),
            "analysis_method": "regex_fallback"
        }

    def _generate_dependency_recommendations(self, import_analysis: Dict) -> List[str]:
        """Genera raccomandazioni per la gestione delle dipendenze."""
        recommendations = []
        
        if "star_imports" in import_analysis and import_analysis["star_imports"]:
            recommendations.append("Avoid star imports - they pollute namespace and hide dependencies")
        
        if import_analysis.get("import_complexity", 0) > 20:
            recommendations.append("High number of dependencies - consider modularization")
        
        if len(import_analysis.get("third_party", [])) > 10:
            recommendations.append("Many third-party dependencies - ensure they are necessary and maintained")
        
        return recommendations

    @mcp.tool()
    def analyze_code_documentation(code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analizza la qualità e completezza della documentazione del codice.
        
        Args:
            code: Il codice da analizzare
            language: Il linguaggio di programmazione
        """
        try:
            doc_analysis = {}
            
            if language.lower() == "python":
                try:
                    tree = ast.parse(code)
                    
                    functions = []
                    classes = []
                    documented_functions = 0
                    documented_classes = 0
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.append(node.name)
                            # Check for docstring
                            if (node.body and 
                                isinstance(node.body[0], ast.Expr) and 
                                isinstance(node.body[0].value, ast.Constant) and 
                                isinstance(node.body[0].value.value, str)):
                                documented_functions += 1
                        
                        elif isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                            # Check for docstring
                            if (node.body and 
                                isinstance(node.body[0], ast.Expr) and 
                                isinstance(node.body[0].value, ast.Constant) and 
                                isinstance(node.body[0].value.value, str)):
                                documented_classes += 1
                    
                    # Analisi commenti
                    lines = code.split('\n')
                    comment_lines = [line for line in lines if line.strip().startswith('#')]
                    docstring_lines = len(re.findall(r'""".*?"""', code, re.DOTALL))
                    
                    total_functions = len(functions)
                    total_classes = len(classes)
                    
                    doc_analysis = {
                        "total_functions": total_functions,
                        "documented_functions": documented_functions,
                        "function_doc_coverage": (documented_functions / total_functions * 100) if total_functions > 0 else 0,
                        "total_classes": total_classes,
                        "documented_classes": documented_classes,
                        "class_doc_coverage": (documented_classes / total_classes * 100) if total_classes > 0 else 0,
                        "comment_lines": len(comment_lines),
                        "docstring_blocks": docstring_lines,
                        "functions": functions,
                        "classes": classes
                    }
                    
                except SyntaxError:
                    doc_analysis = self._regex_documentation_analysis(code, language)
            
            elif language.lower() == "javascript":
                # Analisi documentazione JavaScript
                jsdoc_pattern = r'/\*\*[\s\S]*?\*/'
                single_comments = len(re.findall(r'//.*', code))
                block_comments = len(re.findall(r'/\*[\s\S]*?\*/', code))
                jsdoc_comments = len(re.findall(jsdoc_pattern, code))
                
                function_pattern = r'function\s+(\w+)|const\s+(\w+)\s*=\s*\(|(\w+)\s*:\s*function'
                functions = re.findall(function_pattern, code)
                total_functions = len([f for f in functions if any(f)])
                
                doc_analysis = {
                    "single_line_comments": single_comments,
                    "block_comments": block_comments,
                    "jsdoc_comments": jsdoc_comments,
                    "total_functions": total_functions,
                    "estimated_doc_coverage": (jsdoc_comments / total_functions * 100) if total_functions > 0 else 0
                }
            
            # Calcola punteggio documentazione
            if language.lower() == "python":
                doc_score = (
                    doc_analysis.get("function_doc_coverage", 0) * 0.4 +
                    doc_analysis.get("class_doc_coverage", 0) * 0.3 +
                    min(100, len(doc_analysis.get("comment_lines", [])) * 2) * 0.3
                )
            else:
                doc_score = doc_analysis.get("estimated_doc_coverage", 0)
            
            doc_rating = (
                "Excellent" if doc_score >= 80 else
                "Good" if doc_score >= 60 else
                "Fair" if doc_score >= 40 else
                "Poor"
            )
            
            recommendations = self._generate_documentation_recommendations(doc_analysis, language)
            
            return {
                "language": language,
                "documentation_score": round(doc_score, 2),
                "documentation_rating": doc_rating,
                "analysis": doc_analysis,
                "recommendations": recommendations,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _regex_documentation_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Analisi documentazione usando regex come fallback."""
        comment_lines = len(re.findall(r'#.*', code))
        docstrings = len(re.findall(r'"""[\s\S]*?"""', code))
        functions = len(re.findall(r'def\s+\w+', code))
        
        return {
            "comment_lines": comment_lines,
            "docstring_blocks": docstrings,
            "total_functions": functions,
            "analysis_method": "regex_fallback"
        }

    def _generate_documentation_recommendations(self, analysis: Dict, language: str) -> List[str]:
        """Genera raccomandazioni per migliorare la documentazione."""
        recommendations = []
        
        if language.lower() == "python":
            if analysis.get("function_doc_coverage", 0) < 50:
                recommendations.append("Add docstrings to functions explaining parameters and return values")
            
            if analysis.get("class_doc_coverage", 0) < 50:
                recommendations.append("Add docstrings to classes explaining their purpose and usage")
            
            if analysis.get("comment_lines", 0) < analysis.get("total_functions", 0):
                recommendations.append("Add more inline comments to explain complex logic")
        
        elif language.lower() == "javascript":
            if analysis.get("jsdoc_comments", 0) < analysis.get("total_functions", 0) * 0.5:
                recommendations.append("Add JSDoc comments to functions")
            
            if analysis.get("single_line_comments", 0) < 5:
                recommendations.append("Add more inline comments for clarity")
        
        return recommendations

    @mcp.tool()
    def suggest_code_improvements(code: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggerisce miglioramenti specifici per il codice.
        
        Args:
            code: Il codice da analizzare
            language: Il linguaggio di programmazione
        """
        try:
            improvements = []
            performance_suggestions = []
            maintainability_suggestions = []
            
            if language.lower() == "python":
                # Analisi performance Python
                performance_patterns = {
                    "List comprehension opportunity": r'for\s+\w+\s+in\s+.*:\s*\w+\.append\(',
                    "String concatenation in loop": r'for\s+.*:\s*.*\+=.*[\'"]',
                    "Inefficient dictionary lookup": r'if\s+\w+\s+in\s+\w+\.keys\(\)',
                    "Multiple list iterations": r'(for\s+\w+\s+in\s+\w+:.*){2,}',
                    "Nested loops": r'for\s+.*:\s*.*for\s+.*:'
                }
                
                for pattern_name, pattern in performance_patterns.items():
                    if re.search(pattern, code, re.MULTILINE):
                        performance_suggestions.append({
                            "type": pattern_name,
                            "suggestion": self._get_performance_suggestion(pattern_name),
                            "priority": "Medium"
                        })
                
                # Analisi maintainability
                maintainability_patterns = {
                    "Long functions": len(re.findall(r'def\s+\w+.*?(?=def|\Z)', code, re.DOTALL)),
                    "Magic numbers": len(re.findall(r'\b\d{2,}\b', code)),
                    "Deep nesting": self._calculate_max_nesting(code),
                    "Complex conditions": len(re.findall(r'if\s+.*and.*and', code))
                }
                
                if maintainability_patterns["Long functions"] > 50:
                    maintainability_suggestions.append({
                        "type": "Long functions",
                        "suggestion": "Break down functions into smaller, more focused functions",
                        "priority": "High"
                    })
                
                if maintainability_patterns["Magic numbers"] > 5:
                    maintainability_suggestions.append({
                        "type": "Magic numbers",
                        "suggestion": "Replace magic numbers with named constants",
                        "priority": "Medium"
                    })
                
                if maintainability_patterns["Deep nesting"] > 4:
                    maintainability_suggestions.append({
                        "type": "Deep nesting",
                        "suggestion": "Reduce nesting by using early returns or guard clauses",
                        "priority": "High"
                    })
            
            # Suggerimenti generali per tutti i linguaggi
            lines = code.split('\n')
            
            # Linee troppo lunghe
            long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 100]
            if long_lines:
                improvements.append({
                    "type": "Line length",
                    "description": f"Lines too long: {long_lines[:5]}{'...' if len(long_lines) > 5 else ''}",
                    "suggestion": "Break long lines into multiple shorter lines",
                    "priority": "Low"
                })
            
            # Funzioni troppo complesse
            complexity_score = self._estimate_complexity_score(code)
            if complexity_score > 20:
                improvements.append({
                    "type": "High complexity",
                    "description": f"Estimated complexity score: {complexity_score}",
                    "suggestion": "Consider refactoring to reduce complexity",
                    "priority": "High"
                })
            
            all_suggestions = improvements + performance_suggestions + maintainability_suggestions
            
            # Prioritize suggestions
            high_priority = [s for s in all_suggestions if s.get("priority") == "High"]
            medium_priority = [s for s in all_suggestions if s.get("priority") == "Medium"]
            low_priority = [s for s in all_suggestions if s.get("priority") == "Low"]
            
            return {
                "language": language,
                "total_suggestions": len(all_suggestions),
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority,
                "performance_improvements": performance_suggestions,
                "maintainability_improvements": maintainability_suggestions,
                "overall_rating": self._calculate_code_rating(all_suggestions),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_performance_suggestion(self, pattern_name: str) -> str:
        """Fornisce suggerimenti specifici per miglioramenti delle performance."""
        suggestions = {
            "List comprehension opportunity": "Replace loop with list comprehension for better performance",
            "String concatenation in loop": "Use join() method or f-strings instead of += in loops",
            "Inefficient dictionary lookup": "Remove .keys() - use 'if key in dict' directly",
            "Multiple list iterations": "Combine multiple iterations into a single loop",
            "Nested loops": "Consider using more efficient algorithms or data structures"
        }
        return suggestions.get(pattern_name, "Consider optimizing this pattern")

    def _calculate_max_nesting(self, code: str) -> int:
        """Calcola il livello massimo di nesting."""
        max_nesting = 0
        current_nesting = 0
        
        for line in code.split('\n'):
            stripped = line.lstrip()
            if stripped and not stripped.startswith('#'):
                indent_level = (len(line) - len(stripped)) // 4
                max_nesting = max(max_nesting, indent_level)
        
        return max_nesting

    def _estimate_complexity_score(self, code: str) -> int:
        """Stima un punteggio di complessità del codice."""
        complexity = 0
        
        # Decision points
        complexity += len(re.findall(r'\b(if|elif|while|for|except|and|or)\b', code))
        
        # Nested structures
        complexity += len(re.findall(r'for\s+.*:\s*.*for\s+.*:', code)) * 2
        
        # Function calls
        complexity += len(re.findall(r'\w+\s*\(', code)) // 10
        
        return complexity

    def _calculate_code_rating(self, suggestions: List[Dict]) -> str:
        """Calcola un rating generale del codice basato sui suggerimenti."""
        high_count = len([s for s in suggestions if s.get("priority") == "High"])
        medium_count = len([s for s in suggestions if s.get("priority") == "Medium"])
        
        if high_count > 3:
            return "Needs Improvement"
        elif high_count > 0 or medium_count > 5:
            return "Fair"
        elif medium_count > 2:
            return "Good"
        else:
            return "Excellent"

    @mcp.tool()
    def estimate_test_coverage(code: str, language: str = "python") -> Dict[str, Any]:
        """
        Stima la copertura dei test e fornisce raccomandazioni.
        
        Args:
            code: Il codice da analizzare
            language: Il linguaggio di programmazione
        """
        try:
            test_analysis = {}
            
            if language.lower() == "python":
                # Cerca test patterns
                test_patterns = {
                    "unittest": r'import\s+unittest|from\s+unittest',
                    "pytest": r'import\s+pytest|def\s+test_\w+',
                    "doctest": r'>>>\s+',
                    "assert_statements": r'assert\s+',
                    "test_functions": r'def\s+test_\w+',
                    "test_classes": r'class\s+Test\w+'
                }
                
                test_indicators = {}
                for test_type, pattern in test_patterns.items():
                    matches = re.findall(pattern, code)
                    test_indicators[test_type] = len(matches)
                
                # Analizza funzioni e metodi
                functions = len(re.findall(r'def\s+(?!test_)\w+', code))
                test_functions = test_indicators.get("test_functions", 0)
                
                # Stima copertura
                estimated_coverage = min(100, (test_functions / functions * 100)) if functions > 0 else 0
                
                test_analysis = {
                    "test_framework_detected": any(test_indicators[fw] > 0 for fw in ["unittest", "pytest"]),
                    "total_functions": functions,
                    "test_functions": test_functions,
                    "estimated_coverage_percent": round(estimated_coverage, 2),
                    "test_indicators": test_indicators,
                    "has_assertions": test_indicators["assert_statements"] > 0,
                    "has_doctest": test_indicators["doctest"] > 0
                }
            
            elif language.lower() == "javascript":
                # JavaScript test patterns
                js_test_patterns = {
                    "jest": r'import.*jest|describe\s*\(|test\s*\(|it\s*\(',
                    "mocha": r'describe\s*\(|it\s*\(',
                    "jasmine": r'describe\s*\(|it\s*\(|expect\s*\(',
                    "test_files": r'\.test\.|\.spec\.'
                }
                
                js_test_indicators = {}
                for test_type, pattern in js_test_patterns.items():
                    matches = re.findall(pattern, code)
                    js_test_indicators[test_type] = len(matches)
                
                test_analysis = {
                    "test_framework_detected": any(js_test_indicators.values()),
                    "test_indicators": js_test_indicators,
                    "test_blocks": js_test_indicators.get("jest", 0) + js_test_indicators.get("mocha", 0)
                }
            
            # Genera raccomandazioni
            recommendations = self._generate_test_recommendations(test_analysis, language)
            
            # Rating
            if language.lower() == "python":
                coverage = test_analysis.get("estimated_coverage_percent", 0)
                test_rating = (
                    "Excellent" if coverage >= 80 else
                    "Good" if coverage >= 60 else
                    "Fair" if coverage >= 40 else
                    "Poor"
                )
            else:
                test_rating = "Good" if test_analysis.get("test_framework_detected") else "Poor"
            
            return {
                "language": language,
                "test_analysis": test_analysis,
                "test_rating": test_rating,
                "recommendations": recommendations,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_test_recommendations(self, analysis: Dict, language: str) -> List[str]:
        """Genera raccomandazioni per migliorare i test."""
        recommendations = []
        
        if language.lower() == "python":
            if not analysis.get("test_framework_detected"):
                recommendations.append("Implement a testing framework (unittest or pytest)")
            
            coverage = analysis.get("estimated_coverage_percent", 0)
            if coverage < 50:
                recommendations.append("Increase test coverage - aim for at least 70%")
            
            if not analysis.get("has_assertions"):
                recommendations.append("Add assertion statements to validate test results")
            
            if analysis.get("test_functions", 0) == 0:
                recommendations.append("Write test functions for your code")
        
        elif language.lower() == "javascript":
            if not analysis.get("test_framework_detected"):
                recommendations.append("Implement a testing framework (Jest, Mocha, or Jasmine)")
            
            if analysis.get("test_blocks", 0) < 3:
                recommendations.append("Write more comprehensive test cases")
        
        return recommendations