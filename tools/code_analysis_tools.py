# -*- coding: utf-8 -*-
# tools/code_analysis_tools.py
import ast
import re
import os
import subprocess
import tempfile
import logging
from typing import Dict, List, Any, Optional
import json

def register_tools(mcp):
    """Registra i tool di analisi codice con l'istanza del server MCP."""
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