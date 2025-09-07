# -*- coding: utf-8 -*-
# tools/git_tools.py
import subprocess
import os
import tempfile
import logging
from typing import Dict, List, Any, Optional
import re

def register_tools(mcp):
    """Registra i tool Git con l'istanza del server MCP."""
    logging.info("📋 Registrazione tool-set: Git Repository Tools")

    @mcp.tool()
    def analyze_git_repository(repo_path: str = ".") -> Dict[str, Any]:
        """
        Analizza un repository Git e fornisce statistiche generali.
        
        Args:
            repo_path: Percorso del repository (default: directory corrente)
        """
        try:
            if not os.path.exists(os.path.join(repo_path, ".git")):
                return {
                    "success": False,
                    "error": "Not a git repository"
                }
            
            # Cambia directory se necessario
            original_cwd = os.getcwd()
            if repo_path != ".":
                os.chdir(repo_path)
            
            try:
                # Informazioni base del repository
                result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=10)
                remotes = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                # Branch corrente
                result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=10)
                current_branch = result.stdout.strip()
                
                # Lista branch
                result = subprocess.run(['git', 'branch', '-a'], capture_output=True, text=True, timeout=10)
                all_branches = [b.strip().replace('* ', '') for b in result.stdout.split('\n') if b.strip()]
                
                # Ultimo commit
                result = subprocess.run(['git', 'log', '-1', '--oneline'], capture_output=True, text=True, timeout=10)
                last_commit = result.stdout.strip()
                
                # Stato del repository
                result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=10)
                status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                # Conta i tipi di file modificati
                modified_files = len([line for line in status_lines if line.startswith(' M')])
                staged_files = len([line for line in status_lines if line.startswith('M ')])
                untracked_files = len([line for line in status_lines if line.startswith('??')])
                
                # Statistiche commit (ultimi 30 giorni)
                result = subprocess.run(['git', 'log', '--since=30.days.ago', '--oneline'], capture_output=True, text=True, timeout=10)
                recent_commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                
                # Top contributor (ultimi 30 giorni)
                result = subprocess.run(['git', 'shortlog', '-sn', '--since=30.days.ago'], capture_output=True, text=True, timeout=10)
                contributors = []
                for line in result.stdout.strip().split('\n')[:5]:  # Top 5
                    if line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            contributors.append({
                                "name": parts[1],
                                "commits": int(parts[0])
                            })
                
                return {
                    "success": True,
                    "current_branch": current_branch,
                    "total_branches": len(all_branches),
                    "local_branches": len([b for b in all_branches if not b.startswith('remotes/')]),
                    "remote_branches": len([b for b in all_branches if b.startswith('remotes/')]),
                    "remotes": len(remotes) // 2 if remotes else 0,  # fetch + push per remote
                    "last_commit": last_commit,
                    "working_directory_status": {
                        "modified_files": modified_files,
                        "staged_files": staged_files,
                        "untracked_files": untracked_files,
                        "clean": len(status_lines) == 0
                    },
                    "recent_activity": {
                        "commits_last_30_days": recent_commits,
                        "top_contributors": contributors
                    }
                }
            finally:
                os.chdir(original_cwd)
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Git command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def git_diff_analysis(file_path: str = "", staged: bool = False) -> Dict[str, Any]:
        """
        Analizza le differenze Git e fornisce statistiche.
        
        Args:
            file_path: Percorso specifico del file (vuoto per tutti i file)
            staged: Se analizzare i file staged (True) o working directory (False)
        """
        try:
            # Comando git diff
            cmd = ['git', 'diff']
            if staged:
                cmd.append('--staged')
            if file_path:
                cmd.append(file_path)
            cmd.extend(['--numstat'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Failed to get diff"
                }
            
            # Analizza numstat
            total_additions = 0
            total_deletions = 0
            files_changed = []
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        additions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                        filename = parts[2]
                        
                        total_additions += additions
                        total_deletions += deletions
                        files_changed.append({
                            "file": filename,
                            "additions": additions,
                            "deletions": deletions,
                            "net_change": additions - deletions
                        })
            
            # Ottieni il diff dettagliato per analisi più approfondita
            cmd_detailed = ['git', 'diff']
            if staged:
                cmd_detailed.append('--staged')
            if file_path:
                cmd_detailed.append(file_path)
            
            result_detailed = subprocess.run(cmd_detailed, capture_output=True, text=True, timeout=30)
            diff_content = result_detailed.stdout
            
            # Analizza il contenuto del diff
            hunks = len(re.findall(r'^@@.*@@', diff_content, re.MULTILINE))
            added_lines = len(re.findall(r'^\+[^+]', diff_content, re.MULTILINE))
            removed_lines = len(re.findall(r'^-[^-]', diff_content, re.MULTILINE))
            
            return {
                "success": True,
                "mode": "staged" if staged else "working_directory",
                "target": file_path if file_path else "all_files",
                "summary": {
                    "files_changed": len(files_changed),
                    "total_additions": total_additions,
                    "total_deletions": total_deletions,
                    "net_change": total_additions - total_deletions,
                    "hunks": hunks
                },
                "files": files_changed,
                "has_changes": len(files_changed) > 0
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Git diff command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def git_commit_history(limit: int = 10, author: str = "") -> Dict[str, Any]:
        """
        Analizza la cronologia dei commit.
        
        Args:
            limit: Numero massimo di commit da analizzare (1-100)
            author: Filtra per autore specifico
        """
        try:
            if limit < 1 or limit > 100:
                return {
                    "success": False,
                    "error": "Limit must be between 1 and 100"
                }
            
            # Comando base
            cmd = ['git', 'log', f'-{limit}', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=iso']
            if author:
                cmd.extend(['--author', author])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Failed to get commit history"
                }
            
            commits = []
            authors = {}
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 5:
                        commit_hash = parts[0]
                        author_name = parts[1]
                        author_email = parts[2]
                        date = parts[3]
                        message = parts[4]
                        
                        commits.append({
                            "hash": commit_hash[:8],  # Short hash
                            "full_hash": commit_hash,
                            "author": author_name,
                            "email": author_email,
                            "date": date,
                            "message": message
                        })
                        
                        # Conta commits per autore
                        authors[author_name] = authors.get(author_name, 0) + 1
            
            # Analizza le statistiche per ogni commit
            detailed_commits = []
            for commit in commits[:5]:  # Dettagli solo per i primi 5
                cmd_stats = ['git', 'show', '--stat', '--format=', commit['full_hash']]
                result_stats = subprocess.run(cmd_stats, capture_output=True, text=True, timeout=10)
                
                files_changed = 0
                insertions = 0
                deletions = 0
                
                for line in result_stats.stdout.split('\n'):
                    if 'file' in line and 'changed' in line:
                        # Parse line like: "3 files changed, 25 insertions(+), 10 deletions(-)"
                        files_match = re.search(r'(\d+) files? changed', line)
                        if files_match:
                            files_changed = int(files_match.group(1))
                        
                        insertions_match = re.search(r'(\d+) insertions?\(\+\)', line)
                        if insertions_match:
                            insertions = int(insertions_match.group(1))
                        
                        deletions_match = re.search(r'(\d+) deletions?\(-\)', line)
                        if deletions_match:
                            deletions = int(deletions_match.group(1))
                        break
                
                detailed_commits.append({
                    **commit,
                    "stats": {
                        "files_changed": files_changed,
                        "insertions": insertions,
                        "deletions": deletions
                    }
                })
            
            return {
                "success": True,
                "filter": {"limit": limit, "author": author if author else "all"},
                "total_commits": len(commits),
                "commits": detailed_commits,
                "all_commits_summary": commits,
                "author_statistics": dict(sorted(authors.items(), key=lambda x: x[1], reverse=True))
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Git log command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def git_branch_analysis() -> Dict[str, Any]:
        """
        Analizza i branch del repository Git.
        """
        try:
            # Lista tutti i branch
            result = subprocess.run(['git', 'branch', '-a', '-v'], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Failed to list branches"
                }
            
            branches = []
            current_branch = ""
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    is_current = line.startswith('*')
                    clean_line = line.replace('*', '').strip()
                    
                    if clean_line:
                        parts = clean_line.split()
                        if len(parts) >= 2:
                            branch_name = parts[0]
                            commit_hash = parts[1]
                            
                            if is_current:
                                current_branch = branch_name
                            
                            # Ottieni info aggiuntive per ogni branch
                            branch_info = {
                                "name": branch_name,
                                "current": is_current,
                                "commit_hash": commit_hash,
                                "is_remote": branch_name.startswith('remotes/'),
                                "upstream": None,
                                "behind": 0,
                                "ahead": 0
                            }
                            
                            # Solo per branch locali, controlla upstream
                            if not branch_info["is_remote"] and branch_name != "HEAD":
                                try:
                                    # Controlla upstream
                                    upstream_result = subprocess.run(
                                        ['git', 'branch', '-vv'], 
                                        capture_output=True, text=True, timeout=5
                                    )
                                    
                                    for upstream_line in upstream_result.stdout.split('\n'):
                                        if f" {branch_name} " in upstream_line or upstream_line.strip().startswith(f"* {branch_name}"):
                                            # Cerca pattern [origin/branch: ahead 2, behind 1]
                                            upstream_match = re.search(r'\[([^:]+)(?:: (.+))?\]', upstream_line)
                                            if upstream_match:
                                                branch_info["upstream"] = upstream_match.group(1)
                                                if upstream_match.group(2):
                                                    status = upstream_match.group(2)
                                                    ahead_match = re.search(r'ahead (\d+)', status)
                                                    behind_match = re.search(r'behind (\d+)', status)
                                                    if ahead_match:
                                                        branch_info["ahead"] = int(ahead_match.group(1))
                                                    if behind_match:
                                                        branch_info["behind"] = int(behind_match.group(1))
                                            break
                                except:
                                    pass  # Ignora errori per upstream info
                            
                            branches.append(branch_info)
            
            # Statistiche
            local_branches = [b for b in branches if not b["is_remote"]]
            remote_branches = [b for b in branches if b["is_remote"]]
            
            # Branch dietro/avanti
            behind_branches = [b for b in local_branches if b["behind"] > 0]
            ahead_branches = [b for b in local_branches if b["ahead"] > 0]
            
            return {
                "success": True,
                "current_branch": current_branch,
                "total_branches": len(branches),
                "local_branches": len(local_branches),
                "remote_branches": len(remote_branches),
                "branches": branches,
                "sync_status": {
                    "behind_upstream": len(behind_branches),
                    "ahead_of_upstream": len(ahead_branches),
                    "behind_branches": [{"name": b["name"], "behind": b["behind"]} for b in behind_branches],
                    "ahead_branches": [{"name": b["name"], "ahead": b["ahead"]} for b in ahead_branches]
                }
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Git branch command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_gitignore(language: str, additional_patterns: List[str] = []) -> Dict[str, Any]:
        """
        Genera un file .gitignore per un linguaggio specifico.
        
        Args:
            language: Linguaggio di programmazione (python, javascript, java, etc.)
            additional_patterns: Pattern aggiuntivi da includere
        """
        try:
            gitignore_templates = {
                "python": [
                    "# Byte-compiled / optimized / DLL files",
                    "__pycache__/",
                    "*.py[cod]",
                    "*$py.class",
                    "",
                    "# C extensions",
                    "*.so",
                    "",
                    "# Distribution / packaging",
                    ".Python",
                    "build/",
                    "develop-eggs/",
                    "dist/",
                    "downloads/",
                    "eggs/",
                    ".eggs/",
                    "lib/",
                    "lib64/",
                    "parts/",
                    "sdist/",
                    "var/",
                    "wheels/",
                    "*.egg-info/",
                    ".installed.cfg",
                    "*.egg",
                    "",
                    "# Virtual environments",
                    "venv/",
                    "ENV/",
                    "env/",
                    ".venv/",
                    "",
                    "# IDE",
                    ".vscode/",
                    ".idea/",
                    "*.swp",
                    "*.swo",
                    "",
                    "# OS",
                    ".DS_Store",
                    "Thumbs.db"
                ],
                "javascript": [
                    "# Dependencies",
                    "node_modules/",
                    "npm-debug.log*",
                    "yarn-debug.log*",
                    "yarn-error.log*",
                    "",
                    "# Production builds",
                    "build/",
                    "dist/",
                    "",
                    "# Environment variables",
                    ".env",
                    ".env.local",
                    ".env.development.local",
                    ".env.test.local",
                    ".env.production.local",
                    "",
                    "# IDE",
                    ".vscode/",
                    ".idea/",
                    "",
                    "# OS",
                    ".DS_Store",
                    "Thumbs.db"
                ],
                "java": [
                    "# Compiled class files",
                    "*.class",
                    "",
                    "# Log files",
                    "*.log",
                    "",
                    "# Package Files",
                    "*.jar",
                    "*.war",
                    "*.nar",
                    "*.ear",
                    "*.zip",
                    "*.tar.gz",
                    "*.rar",
                    "",
                    "# Maven",
                    "target/",
                    "pom.xml.tag",
                    "pom.xml.releaseBackup",
                    "pom.xml.versionsBackup",
                    "pom.xml.next",
                    "release.properties",
                    "",
                    "# Gradle",
                    ".gradle/",
                    "build/",
                    "",
                    "# IDE",
                    ".idea/",
                    "*.iws",
                    "*.iml",
                    "*.ipr",
                    ".vscode/",
                    "",
                    "# OS",
                    ".DS_Store",
                    "Thumbs.db"
                ],
                "generic": [
                    "# IDE files",
                    ".vscode/",
                    ".idea/",
                    "*.swp",
                    "*.swo",
                    "",
                    "# OS files",
                    ".DS_Store",
                    "Thumbs.db",
                    "",
                    "# Temporary files",
                    "*.tmp",
                    "*.temp",
                    "",
                    "# Logs",
                    "*.log"
                ]
            }
            
            # Ottieni template
            template = gitignore_templates.get(language.lower(), gitignore_templates["generic"])
            
            # Aggiungi pattern personalizzati
            if additional_patterns:
                template.extend(["", "# Custom patterns"])
                template.extend(additional_patterns)
            
            gitignore_content = "\n".join(template)
            
            return {
                "success": True,
                "language": language,
                "gitignore_content": gitignore_content,
                "total_patterns": len([line for line in template if line and not line.startswith("#")]),
                "additional_patterns_count": len(additional_patterns)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }