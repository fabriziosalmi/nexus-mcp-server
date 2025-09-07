# -*- coding: utf-8 -*-
# tools/workflows.py
import logging
import os
import tempfile
import shutil
import subprocess
import re
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

def register_tools(mcp):
    """Registra i tool di orchestrazione workflow con l'istanza del server MCP."""
    logging.info("🔄 Registrazione tool-set: Workflow Orchestration Tools")

    @mcp.tool()
    def analyze_repository(url: str, analysis_depth: str = "standard") -> Dict[str, Any]:
        """
        Meta-tool per l'analisi completa di un repository Git.
        Orchestrazione di più tool in una singola operazione.
        
        Args:
            url: URL del repository Git da analizzare
            analysis_depth: Livello di analisi ("quick", "standard", "deep")
        """
        workflow_start = datetime.now()
        workflow_id = f"repo_analysis_{workflow_start.strftime('%Y%m%d_%H%M%S')}"
        
        results = {
            "workflow_id": workflow_id,
            "repository_url": url,
            "analysis_depth": analysis_depth,
            "started_at": workflow_start.isoformat(),
            "steps_completed": [],
            "steps_failed": [],
            "final_status": "running",
            "reports": {},
            "artifacts": []
        }
        
        temp_dir = None
        repo_name = url.split('/')[-1].replace('.git', '')
        
        try:
            # Step 1: Clona il repository
            logging.info(f"🔄 Workflow {workflow_id}: Step 1 - Cloning repository")
            temp_dir = tempfile.mkdtemp(prefix=f"nexus_repo_{repo_name}_")
            clone_result = _clone_repository(url, temp_dir)
            
            if not clone_result["success"]:
                results["steps_failed"].append("repository_clone")
                results["final_status"] = "failed"
                results["error"] = clone_result["error"]
                return results
            
            results["steps_completed"].append("repository_clone")
            results["reports"]["clone_info"] = clone_result
            repo_path = clone_result["local_path"]
            
            # Step 2: Analizza complessità del codice
            logging.info(f"🔄 Workflow {workflow_id}: Step 2 - Analyzing code complexity")
            complexity_result = _analyze_repository_complexity(repo_path, analysis_depth)
            results["steps_completed"].append("code_complexity")
            results["reports"]["complexity_analysis"] = complexity_result
            
            # Step 3: Rileva segreti esposti (se richiesto)
            if analysis_depth in ["standard", "deep"]:
                logging.info(f"🔄 Workflow {workflow_id}: Step 3 - Scanning for exposed secrets")
                secrets_result = _detect_exposed_secrets(repo_path)
                results["steps_completed"].append("secret_detection")
                results["reports"]["security_scan"] = secrets_result
            
            # Step 4: Analizza struttura repository
            logging.info(f"🔄 Workflow {workflow_id}: Step 4 - Analyzing repository structure")
            structure_result = _analyze_repository_structure(repo_path)
            results["steps_completed"].append("structure_analysis") 
            results["reports"]["repository_structure"] = structure_result
            
            # Step 5: Crea archivio del repository (se richiesto)
            if analysis_depth == "deep":
                logging.info(f"🔄 Workflow {workflow_id}: Step 5 - Creating repository archive")
                archive_result = _create_repository_archive(repo_path, repo_name, workflow_id)
                results["steps_completed"].append("archive_creation")
                results["reports"]["archive_info"] = archive_result
                if archive_result.get("success"):
                    results["artifacts"].append(archive_result.get("archive_path"))
            
            results["final_status"] = "completed"
            
        except Exception as e:
            logging.error(f"🔄 Workflow {workflow_id}: Critical error - {str(e)}")
            results["final_status"] = "failed"
            results["error"] = str(e)
        
        finally:
            # Step 6: Cleanup - sempre eseguito
            if temp_dir and os.path.exists(temp_dir):
                logging.info(f"🔄 Workflow {workflow_id}: Final step - Cleaning up temporary directory")
                cleanup_result = _cleanup_directory(temp_dir)
                if cleanup_result["success"]:
                    results["steps_completed"].append("cleanup")
                else:
                    results["steps_failed"].append("cleanup")
                results["reports"]["cleanup"] = cleanup_result
        
        workflow_end = datetime.now()
        results["completed_at"] = workflow_end.isoformat()
        results["duration_seconds"] = (workflow_end - workflow_start).total_seconds()
        
        # Genera report aggregato
        results["summary"] = _generate_workflow_summary(results)
        
        return results

    def _clone_repository(url: str, target_dir: str) -> Dict[str, Any]:
        """Clona un repository Git in una directory temporanea."""
        try:
            # Validazione URL
            if not url or not url.startswith(('http://', 'https://', 'git://')):
                return {
                    "success": False,
                    "error": "Invalid repository URL format"
                }
            
            # Clona il repository
            cmd = ['git', 'clone', '--depth=1', url, target_dir]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Git clone failed: {result.stderr.strip()}"
                }
            
            # Verifica che la directory contenga un repository Git
            git_dir = os.path.join(target_dir, '.git')
            if not os.path.exists(git_dir):
                return {
                    "success": False,
                    "error": "Cloned directory does not contain a valid Git repository"
                }
            
            # Ottieni informazioni base del repository
            os.chdir(target_dir)
            
            # Branch corrente
            branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                         capture_output=True, text=True, timeout=10)
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Ultimo commit
            commit_result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                                         capture_output=True, text=True, timeout=10)
            last_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
            
            # Conta file
            file_count = sum([len(files) for r, d, files in os.walk(target_dir) if '.git' not in r])
            
            return {
                "success": True,
                "local_path": target_dir,
                "current_branch": current_branch,
                "last_commit": last_commit,
                "file_count": file_count,
                "clone_method": "shallow (depth=1)"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Git clone operation timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Clone operation failed: {str(e)}"
            }

    def _analyze_repository_complexity(repo_path: str, depth: str) -> Dict[str, Any]:
        """Analizza la complessità del codice nel repository."""
        try:
            analysis = {
                "files_analyzed": 0,
                "total_lines": 0,
                "code_lines": 0,
                "comment_lines": 0,
                "blank_lines": 0,
                "languages": {},
                "complexity_metrics": {},
                "files_by_size": []
            }
            
            # Trova tutti i file di codice
            code_extensions = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift'}
            
            for root, dirs, files in os.walk(repo_path):
                # Salta directory .git e node_modules
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in code_extensions:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                lines = content.split('\n')
                                
                            file_lines = len(lines)
                            file_code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
                            file_comment_lines = len([l for l in lines if l.strip().startswith('#')])
                            file_blank_lines = len([l for l in lines if not l.strip()])
                            
                            analysis["files_analyzed"] += 1
                            analysis["total_lines"] += file_lines
                            analysis["code_lines"] += file_code_lines
                            analysis["comment_lines"] += file_comment_lines
                            analysis["blank_lines"] += file_blank_lines
                            
                            # Raggruppa per linguaggio
                            lang = _get_language_from_extension(file_ext)
                            if lang not in analysis["languages"]:
                                analysis["languages"][lang] = {"files": 0, "lines": 0}
                            analysis["languages"][lang]["files"] += 1
                            analysis["languages"][lang]["lines"] += file_lines
                            
                            # File più grandi (solo per analisi deep)
                            if depth == "deep" and file_lines > 100:
                                analysis["files_by_size"].append({
                                    "file": os.path.relpath(file_path, repo_path),
                                    "lines": file_lines,
                                    "language": lang
                                })
                        
                        except Exception:
                            continue  # Salta file che non possono essere letti
            
            # Calcola metriche di complessità
            if analysis["files_analyzed"] > 0:
                analysis["complexity_metrics"] = {
                    "avg_lines_per_file": round(analysis["total_lines"] / analysis["files_analyzed"], 2),
                    "code_to_comment_ratio": round(analysis["code_lines"] / max(analysis["comment_lines"], 1), 2),
                    "comment_percentage": round((analysis["comment_lines"] / analysis["total_lines"]) * 100, 2) if analysis["total_lines"] > 0 else 0
                }
            
            # Ordina file per dimensione (per analisi deep)
            if depth == "deep":
                analysis["files_by_size"].sort(key=lambda x: x["lines"], reverse=True)
                analysis["files_by_size"] = analysis["files_by_size"][:10]  # Top 10
            
            return analysis
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Complexity analysis failed: {str(e)}"
            }

    def _detect_exposed_secrets(repo_path: str) -> Dict[str, Any]:
        """Rileva potenziali segreti esposti nel codice."""
        try:
            secrets_found = []
            files_scanned = 0
            
            # Pattern per rilevare segreti comuni
            secret_patterns = {
                "API Key": re.compile(r'api[_-]?key[\'"\s]*[=:][\'"\s]*[a-zA-Z0-9]{20,}', re.IGNORECASE),
                "Password": re.compile(r'password[\'"\s]*[=:][\'"\s]*[\'"][^\'"]{8,}[\'"]', re.IGNORECASE),
                "Private Key": re.compile(r'-----BEGIN [A-Z]+ PRIVATE KEY-----'),
                "AWS Access Key": re.compile(r'AKIA[0-9A-Z]{16}'),
                "GitHub Token": re.compile(r'ghp_[a-zA-Z0-9]{36}'),
                "JWT Token": re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'),
                "Database URL": re.compile(r'(mongodb|mysql|postgres)://[^\s]+', re.IGNORECASE)
            }
            
            # Scansiona file di testo
            text_extensions = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift', 
                             '.txt', '.md', '.yml', '.yaml', '.json', '.xml', '.env', '.config'}
            
            for root, dirs, files in os.walk(repo_path):
                # Salta directory .git
                dirs[:] = [d for d in dirs if d != '.git']
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in text_extensions or file in ['.env', '.config', 'config']:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            files_scanned += 1
                            
                            # Cerca pattern di segreti
                            for secret_type, pattern in secret_patterns.items():
                                matches = pattern.finditer(content)
                                for match in matches:
                                    # Trova il numero di linea
                                    line_num = content[:match.start()].count('\n') + 1
                                    
                                    secrets_found.append({
                                        "type": secret_type,
                                        "file": os.path.relpath(file_path, repo_path),
                                        "line": line_num,
                                        "matched_text": match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
                                        "severity": "HIGH" if secret_type in ["Private Key", "AWS Access Key", "GitHub Token"] else "MEDIUM"
                                    })
                        
                        except Exception:
                            continue  # Salta file che non possono essere letti
            
            return {
                "files_scanned": files_scanned,
                "secrets_found": len(secrets_found),
                "findings": secrets_found,
                "security_risk": "HIGH" if len(secrets_found) > 0 else "LOW"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Secret detection failed: {str(e)}"
            }

    def _analyze_repository_structure(repo_path: str) -> Dict[str, Any]:
        """Analizza la struttura del repository."""
        try:
            structure = {
                "total_files": 0,
                "total_directories": 0,
                "directory_tree": {},
                "file_types": {},
                "has_common_files": {}
            }
            
            # File comuni da cercare
            common_files = [
                'README.md', 'README.txt', 'readme.md', 'LICENSE', 'license.txt',
                'package.json', 'requirements.txt', 'Dockerfile', 'docker-compose.yml',
                '.gitignore', 'Makefile', 'setup.py', 'pom.xml', 'build.gradle'
            ]
            
            for root, dirs, files in os.walk(repo_path):
                # Salta directory .git
                dirs[:] = [d for d in dirs if d != '.git']
                
                structure["total_directories"] += len(dirs)
                structure["total_files"] += len(files)
                
                for file in files:
                    # Analizza estensioni file
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                    
                    # Cerca file comuni
                    if file in common_files:
                        structure["has_common_files"][file] = True
            
            # Inizializza file comuni mancanti
            for common_file in common_files:
                if common_file not in structure["has_common_files"]:
                    structure["has_common_files"][common_file] = False
            
            return structure
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Structure analysis failed: {str(e)}"
            }

    def _create_repository_archive(repo_path: str, repo_name: str, workflow_id: str) -> Dict[str, Any]:
        """Crea un archivio del repository analizzato."""
        try:
            import zipfile
            
            # Crea archivio nella directory safe_files
            safe_dir = os.path.join(os.getcwd(), "safe_files")
            os.makedirs(safe_dir, exist_ok=True)
            
            archive_name = f"{repo_name}_{workflow_id}.zip"
            archive_path = os.path.join(safe_dir, archive_name)
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_added = 0
                
                for root, dirs, files in os.walk(repo_path):
                    # Salta directory .git
                    dirs[:] = [d for d in dirs if d != '.git']
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, repo_path)
                        
                        try:
                            zipf.write(file_path, arc_path)
                            files_added += 1
                        except Exception:
                            continue  # Salta file che non possono essere aggiunti
            
            archive_size = os.path.getsize(archive_path)
            
            return {
                "success": True,
                "archive_path": archive_path,
                "archive_name": archive_name,
                "files_archived": files_added,
                "archive_size_bytes": archive_size,
                "archive_size_mb": round(archive_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Archive creation failed: {str(e)}"
            }

    def _cleanup_directory(temp_dir: str) -> Dict[str, Any]:
        """Pulisce la directory temporanea."""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                return {
                    "success": True,
                    "cleaned_directory": temp_dir,
                    "message": "Temporary directory cleaned successfully"
                }
            else:
                return {
                    "success": True,
                    "message": "Directory already cleaned or does not exist"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Cleanup failed: {str(e)}"
            }

    def _get_language_from_extension(ext: str) -> str:
        """Mappa estensioni file ai linguaggi di programmazione."""
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift'
        }
        return lang_map.get(ext, 'Other')

    def _generate_workflow_summary(results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un riassunto aggregato del workflow."""
        summary = {
            "status": results["final_status"],
            "total_steps": len(results["steps_completed"]) + len(results["steps_failed"]),
            "successful_steps": len(results["steps_completed"]),
            "failed_steps": len(results["steps_failed"]),
            "duration_seconds": results.get("duration_seconds", 0)
        }
        
        # Aggiungi informazioni chiave dai report
        reports = results.get("reports", {})
        
        if "complexity_analysis" in reports:
            complexity = reports["complexity_analysis"]
            summary["code_analysis"] = {
                "files_analyzed": complexity.get("files_analyzed", 0),
                "total_lines": complexity.get("total_lines", 0),
                "languages_detected": len(complexity.get("languages", {}))
            }
        
        if "security_scan" in reports:
            security = reports["security_scan"]
            summary["security_analysis"] = {
                "files_scanned": security.get("files_scanned", 0),
                "secrets_found": security.get("secrets_found", 0),
                "risk_level": security.get("security_risk", "UNKNOWN")
            }
        
        if "archive_info" in reports:
            archive = reports["archive_info"]
            summary["archive_created"] = archive.get("success", False)
            if archive.get("success"):
                summary["archive_size_mb"] = archive.get("archive_size_mb", 0)
        
        return summary