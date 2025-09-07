# -*- coding: utf-8 -*-
# tools/git_tools.py
import subprocess
import os
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

def register_tools(mcp):
    """Registra i tool Git avanzati con l'istanza del server MCP."""
    logging.info("🔀 Registrazione tool-set: Git Repository Tools")

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

    @mcp.tool()
    def manage_git_remotes(action: str, remote_name: str = "", remote_url: str = "") -> Dict[str, Any]:
        """
        Gestisce remote Git (list, add, remove, update).
        
        Args:
            action: Azione da eseguire (list, add, remove, set-url, fetch, push)
            remote_name: Nome del remote
            remote_url: URL del remote (per add/set-url)
        """
        try:
            if action == "list":
                # Lista remotes con dettagli
                result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": "Failed to list remotes"}
                
                remotes = {}
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            name = parts[0]
                            url = parts[1]
                            operation = parts[2].strip('()')
                            
                            if name not in remotes:
                                remotes[name] = {}
                            remotes[name][operation] = url
                
                # Ottieni info aggiuntive per ogni remote
                remote_details = []
                for name, urls in remotes.items():
                    # Controlla connettività
                    connectivity_result = subprocess.run(
                        ['git', 'ls-remote', '--exit-code', name], 
                        capture_output=True, text=True, timeout=30
                    )
                    
                    remote_info = {
                        "name": name,
                        "fetch_url": urls.get("fetch", ""),
                        "push_url": urls.get("push", ""),
                        "reachable": connectivity_result.returncode == 0,
                        "refs_count": len(connectivity_result.stdout.split('\n')) if connectivity_result.returncode == 0 else 0
                    }
                    remote_details.append(remote_info)
                
                return {
                    "success": True,
                    "action": action,
                    "remotes": remote_details,
                    "total_remotes": len(remote_details)
                }
            
            elif action == "add":
                if not remote_name or not remote_url:
                    return {"success": False, "error": "remote_name and remote_url required for add"}
                
                result = subprocess.run(['git', 'remote', 'add', remote_name, remote_url], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "action": action,
                    "remote_name": remote_name,
                    "remote_url": remote_url,
                    "message": f"Remote '{remote_name}' added successfully"
                }
            
            elif action == "remove":
                if not remote_name:
                    return {"success": False, "error": "remote_name required for remove"}
                
                result = subprocess.run(['git', 'remote', 'remove', remote_name], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "action": action,
                    "remote_name": remote_name,
                    "message": f"Remote '{remote_name}' removed successfully"
                }
            
            elif action == "set-url":
                if not remote_name or not remote_url:
                    return {"success": False, "error": "remote_name and remote_url required for set-url"}
                
                result = subprocess.run(['git', 'remote', 'set-url', remote_name, remote_url], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "action": action,
                    "remote_name": remote_name,
                    "new_url": remote_url,
                    "message": f"Remote '{remote_name}' URL updated successfully"
                }
            
            elif action in ["fetch", "push"]:
                if not remote_name:
                    return {"success": False, "error": f"remote_name required for {action}"}
                
                cmd = ['git', action, remote_name]
                if action == "fetch":
                    cmd.append('--dry-run')  # Safe fetch simulation
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                return {
                    "success": result.returncode == 0,
                    "action": action,
                    "remote_name": remote_name,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip() if result.returncode != 0 else None
                }
            
            else:
                return {"success": False, "error": f"Unsupported action: {action}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Git {action} command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_file_blame(file_path: str, start_line: int = 1, end_line: int = None) -> Dict[str, Any]:
        """
        Analizza blame/annotazioni per un file.
        
        Args:
            file_path: Percorso del file
            start_line: Riga di inizio (1-indexed)
            end_line: Riga di fine (None per tutto il file)
        """
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File {file_path} not found"}
            
            # Comando git blame
            cmd = ['git', 'blame', '--line-porcelain', file_path]
            if start_line > 1 or end_line:
                range_spec = f"{start_line},{end_line or ''}"
                cmd.extend(['-L', range_spec])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}
            
            # Parse blame output
            blame_data = []
            current_commit = {}
            author_stats = defaultdict(int)
            commit_stats = defaultdict(int)
            
            for line in result.stdout.split('\n'):
                if line.startswith('\t'):
                    # Riga di codice
                    blame_data.append({
                        **current_commit,
                        "line_content": line[1:]  # Rimuovi tab
                    })
                    author_stats[current_commit.get('author', 'Unknown')] += 1
                    commit_stats[current_commit.get('commit_hash', 'Unknown')] += 1
                elif ' ' in line:
                    # Metadati commit
                    key, value = line.split(' ', 1)
                    if key == 'author':
                        current_commit['author'] = value
                    elif key == 'author-time':
                        current_commit['author_time'] = datetime.fromtimestamp(int(value)).isoformat()
                    elif key == 'summary':
                        current_commit['summary'] = value
                    elif len(key) == 40:  # SHA hash
                        current_commit['commit_hash'] = key[:8]
            
            # Calcola statistiche
            total_lines = len(blame_data)
            
            return {
                "success": True,
                "file_path": file_path,
                "range": {
                    "start_line": start_line,
                    "end_line": end_line or total_lines,
                    "total_lines": total_lines
                },
                "blame_data": blame_data,
                "statistics": {
                    "total_lines": total_lines,
                    "unique_authors": len(author_stats),
                    "unique_commits": len(commit_stats),
                    "top_authors": dict(Counter(author_stats).most_common(5)),
                    "most_recent_commits": dict(Counter(commit_stats).most_common(5))
                }
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git blame command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def manage_git_tags(action: str, tag_name: str = "", commit_hash: str = "", 
                       message: str = "") -> Dict[str, Any]:
        """
        Gestisce tag Git (list, create, delete, show).
        
        Args:
            action: Azione (list, create, delete, show)
            tag_name: Nome del tag
            commit_hash: Hash commit per tag (default: HEAD)
            message: Messaggio per tag annotato
        """
        try:
            if action == "list":
                # Lista tutti i tag
                result = subprocess.run(['git', 'tag', '--sort=-version:refname'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": "Failed to list tags"}
                
                tags = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                # Ottieni dettagli per ogni tag
                tag_details = []
                for tag in tags[:20]:  # Limita a 20 tag per performance
                    # Ottieni info tag
                    show_result = subprocess.run(['git', 'show', '--format=%H|%an|%ad|%s', 
                                                '--no-patch', tag], 
                                               capture_output=True, text=True, timeout=5)
                    
                    tag_info = {"name": tag}
                    
                    if show_result.returncode == 0 and show_result.stdout.strip():
                        parts = show_result.stdout.strip().split('|')
                        if len(parts) >= 4:
                            tag_info.update({
                                "commit_hash": parts[0][:8],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3]
                            })
                    
                    # Verifica se è tag annotato
                    type_result = subprocess.run(['git', 'cat-file', '-t', tag], 
                                               capture_output=True, text=True, timeout=5)
                    tag_info["annotated"] = type_result.stdout.strip() == "tag"
                    
                    tag_details.append(tag_info)
                
                return {
                    "success": True,
                    "action": action,
                    "total_tags": len(tags),
                    "tags": tag_details,
                    "latest_tag": tags[0] if tags else None
                }
            
            elif action == "create":
                if not tag_name:
                    return {"success": False, "error": "tag_name required for create"}
                
                cmd = ['git', 'tag']
                
                if message:
                    cmd.extend(['-a', tag_name, '-m', message])
                else:
                    cmd.append(tag_name)
                
                if commit_hash:
                    cmd.append(commit_hash)
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "action": action,
                    "tag_name": tag_name,
                    "annotated": bool(message),
                    "commit_hash": commit_hash or "HEAD",
                    "message": f"Tag '{tag_name}' created successfully"
                }
            
            elif action == "delete":
                if not tag_name:
                    return {"success": False, "error": "tag_name required for delete"}
                
                result = subprocess.run(['git', 'tag', '-d', tag_name], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "action": action,
                    "tag_name": tag_name,
                    "message": f"Tag '{tag_name}' deleted successfully"
                }
            
            elif action == "show":
                if not tag_name:
                    return {"success": False, "error": "tag_name required for show"}
                
                result = subprocess.run(['git', 'show', tag_name], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "action": action,
                    "tag_name": tag_name,
                    "tag_info": result.stdout[:2000]  # Limita output per sicurezza
                }
            
            else:
                return {"success": False, "error": f"Unsupported action: {action}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Git tag {action} command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def detect_merge_conflicts() -> Dict[str, Any]:
        """
        Rileva e analizza merge conflicts nel repository.
        """
        try:
            # Controlla se siamo in uno stato di merge
            merge_head_exists = os.path.exists('.git/MERGE_HEAD')
            
            # Ottieni file con conflitti
            result = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=U'], 
                                  capture_output=True, text=True, timeout=10)
            
            conflict_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Analizza ogni file con conflitti
            conflict_details = []
            total_conflicts = 0
            
            for file_path in conflict_files:
                if not os.path.exists(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Conta marker di conflitto
                    conflict_markers = {
                        'start': content.count('<<<<<<<'),
                        'separator': content.count('======='),
                        'end': content.count('>>>>>>>')
                    }
                    
                    file_conflicts = min(conflict_markers.values())
                    total_conflicts += file_conflicts
                    
                    # Trova posizioni conflitti
                    conflict_positions = []
                    lines = content.split('\n')
                    in_conflict = False
                    conflict_start = None
                    
                    for i, line in enumerate(lines, 1):
                        if line.startswith('<<<<<<<'):
                            in_conflict = True
                            conflict_start = i
                        elif line.startswith('>>>>>>>') and in_conflict:
                            conflict_positions.append({
                                'start_line': conflict_start,
                                'end_line': i,
                                'lines_affected': i - conflict_start + 1
                            })
                            in_conflict = False
                    
                    conflict_details.append({
                        'file': file_path,
                        'conflicts_count': file_conflicts,
                        'conflict_positions': conflict_positions,
                        'file_size_lines': len(lines)
                    })
                    
                except Exception as e:
                    conflict_details.append({
                        'file': file_path,
                        'error': f"Could not analyze: {str(e)}"
                    })
            
            # Ottieni info merge se in corso
            merge_info = {}
            if merge_head_exists:
                try:
                    with open('.git/MERGE_HEAD', 'r') as f:
                        merge_commit = f.read().strip()
                    
                    # Ottieni info sui commit che si stanno mergiando
                    current_result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                                  capture_output=True, text=True, timeout=5)
                    
                    if current_result.returncode == 0:
                        merge_info = {
                            'current_commit': current_result.stdout.strip()[:8],
                            'merging_commit': merge_commit[:8],
                            'merge_in_progress': True
                        }
                except:
                    merge_info = {'merge_in_progress': True}
            
            return {
                "success": True,
                "has_conflicts": len(conflict_files) > 0,
                "merge_in_progress": merge_head_exists,
                "conflict_summary": {
                    "files_with_conflicts": len(conflict_files),
                    "total_conflicts": total_conflicts
                },
                "conflicted_files": conflict_details,
                "merge_info": merge_info,
                "resolution_suggestions": _generate_conflict_resolution_suggestions(conflict_details)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_repository_health() -> Dict[str, Any]:
        """
        Analizza la salute generale del repository Git.
        """
        try:
            health_report = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "overall_health": "unknown",
                "checks": {}
            }
            
            issues = []
            warnings = []
            recommendations = []
            
            # 1. Controlla integrità repository
            fsck_result = subprocess.run(['git', 'fsck', '--no-progress'], 
                                       capture_output=True, text=True, timeout=30)
            health_report["checks"]["integrity"] = {
                "passed": fsck_result.returncode == 0,
                "issues": fsck_result.stderr.split('\n') if fsck_result.stderr else []
            }
            
            if fsck_result.returncode != 0:
                issues.append("Repository integrity issues detected")
            
            # 2. Controlla dimensioni repository
            du_result = subprocess.run(['du', '-sh', '.git'], 
                                     capture_output=True, text=True, timeout=10)
            repo_size = du_result.stdout.split()[0] if du_result.returncode == 0 else "unknown"
            
            # 3. Conta oggetti
            count_result = subprocess.run(['git', 'count-objects', '-v'], 
                                        capture_output=True, text=True, timeout=10)
            object_stats = {}
            if count_result.returncode == 0:
                for line in count_result.stdout.split('\n'):
                    if ' ' in line:
                        key, value = line.split(' ', 1)
                        try:
                            object_stats[key] = int(value)
                        except ValueError:
                            object_stats[key] = value
            
            health_report["checks"]["size_analysis"] = {
                "repository_size": repo_size,
                "object_statistics": object_stats
            }
            
            # 4. Controlla branch non merged
            merged_result = subprocess.run(['git', 'branch', '--merged'], 
                                         capture_output=True, text=True, timeout=10)
            all_result = subprocess.run(['git', 'branch'], 
                                      capture_output=True, text=True, timeout=10)
            
            if merged_result.returncode == 0 and all_result.returncode == 0:
                merged_branches = set(b.strip().replace('* ', '') for b in merged_result.stdout.split('\n') if b.strip())
                all_branches = set(b.strip().replace('* ', '') for b in all_result.stdout.split('\n') if b.strip())
                unmerged_branches = all_branches - merged_branches
                
                health_report["checks"]["branch_hygiene"] = {
                    "total_branches": len(all_branches),
                    "merged_branches": len(merged_branches),
                    "unmerged_branches": len(unmerged_branches),
                    "unmerged_list": list(unmerged_branches)
                }
                
                if len(unmerged_branches) > 10:
                    warnings.append(f"Many unmerged branches ({len(unmerged_branches)})")
            
            # 5. Controlla commit recenti
            recent_result = subprocess.run(['git', 'log', '--since=30.days.ago', '--oneline'], 
                                         capture_output=True, text=True, timeout=10)
            recent_commits = len(recent_result.stdout.split('\n')) if recent_result.stdout.strip() else 0
            
            health_report["checks"]["activity"] = {
                "commits_last_30_days": recent_commits,
                "active": recent_commits > 0
            }
            
            if recent_commits == 0:
                warnings.append("No commits in the last 30 days")
            
            # 6. Controlla file grandi
            large_files_result = subprocess.run(['git', 'rev-list', '--objects', '--all'], 
                                              capture_output=True, text=True, timeout=30)
            
            if large_files_result.returncode == 0:
                # Analizza file grandi (>10MB)
                large_files = []
                for line in large_files_result.stdout.split('\n')[:1000]:  # Limita per performance
                    if ' ' in line:
                        obj_hash, filename = line.split(' ', 1)
                        try:
                            size_result = subprocess.run(['git', 'cat-file', '-s', obj_hash], 
                                                       capture_output=True, text=True, timeout=2)
                            if size_result.returncode == 0:
                                size = int(size_result.stdout.strip())
                                if size > 10 * 1024 * 1024:  # >10MB
                                    large_files.append({
                                        'file': filename,
                                        'size_mb': round(size / (1024 * 1024), 2)
                                    })
                        except:
                            continue
                        
                        if len(large_files) >= 10:  # Limita risultati
                            break
                
                health_report["checks"]["large_files"] = {
                    "files_over_10mb": len(large_files),
                    "large_files": large_files
                }
                
                if len(large_files) > 0:
                    warnings.append(f"Found {len(large_files)} large files (>10MB)")
            
            # Genera raccomandazioni
            if object_stats.get('size-pack', 0) > 100 * 1024 * 1024:  # >100MB
                recommendations.append("Consider running 'git gc --aggressive' to optimize repository")
            
            if len(unmerged_branches) > 5:
                recommendations.append("Consider cleaning up old branches that are no longer needed")
            
            # Calcola salute generale
            critical_issues = len(issues)
            total_warnings = len(warnings)
            
            if critical_issues > 0:
                overall_health = "poor"
            elif total_warnings > 3:
                overall_health = "fair"
            elif total_warnings > 0:
                overall_health = "good"
            else:
                overall_health = "excellent"
            
            health_report.update({
                "overall_health": overall_health,
                "issues": issues,
                "warnings": warnings,
                "recommendations": recommendations,
                "summary": {
                    "critical_issues": critical_issues,
                    "warnings": total_warnings,
                    "recommendations": len(recommendations)
                }
            })
            
            return health_report
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def search_git_history(query: str, search_type: str = "commit", 
                          author: str = "", since: str = "", until: str = "") -> Dict[str, Any]:
        """
        Cerca nella cronologia Git.
        
        Args:
            query: Termine di ricerca
            search_type: Tipo ricerca (commit, file, content)
            author: Filtra per autore
            since: Data inizio (es. "2024-01-01")
            until: Data fine (es. "2024-12-31")
        """
        try:
            results = []
            
            if search_type == "commit":
                # Cerca nei messaggi di commit
                cmd = ['git', 'log', '--grep', query, '--oneline']
                
                if author:
                    cmd.extend(['--author', author])
                if since:
                    cmd.extend(['--since', since])
                if until:
                    cmd.extend(['--until', until])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split(' ', 1)
                            if len(parts) >= 2:
                                results.append({
                                    'type': 'commit',
                                    'hash': parts[0],
                                    'message': parts[1],
                                    'match_type': 'commit_message'
                                })
            
            elif search_type == "file":
                # Cerca file per nome
                cmd = ['git', 'log', '--name-only', '--pretty=format:', '--all']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    unique_files = set()
                    for line in result.stdout.split('\n'):
                        if line.strip() and query.lower() in line.lower():
                            unique_files.add(line.strip())
                    
                    for file_path in list(unique_files)[:50]:  # Limita risultati
                        results.append({
                            'type': 'file',
                            'path': file_path,
                            'match_type': 'filename'
                        })
            
            elif search_type == "content":
                # Cerca nel contenuto dei file
                cmd = ['git', 'log', '-S', query, '--oneline']
                
                if author:
                    cmd.extend(['--author', author])
                if since:
                    cmd.extend(['--since', since])
                if until:
                    cmd.extend(['--until', until])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split(' ', 1)
                            if len(parts) >= 2:
                                results.append({
                                    'type': 'content_change',
                                    'hash': parts[0],
                                    'message': parts[1],
                                    'match_type': 'content_modification'
                                })
            
            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "filters": {
                    "author": author or None,
                    "since": since or None,
                    "until": until or None
                },
                "results": results,
                "total_matches": len(results)
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git search command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions
    def _generate_conflict_resolution_suggestions(conflict_details: List[Dict]) -> List[str]:
        """Genera suggerimenti per risolvere conflitti."""
        suggestions = []
        
        if not conflict_details:
            return ["No conflicts detected"]
        
        total_conflicts = sum(d.get('conflicts_count', 0) for d in conflict_details)
        
        suggestions.append(f"Found {total_conflicts} conflicts in {len(conflict_details)} files")
        suggestions.append("Use 'git status' to see all conflicted files")
        suggestions.append("Edit each file to resolve conflicts between <<<<<<< and >>>>>>>")
        suggestions.append("After resolving, use 'git add <file>' to mark as resolved")
        suggestions.append("Finally, use 'git commit' to complete the merge")
        
        # Suggerimenti specifici
        if len(conflict_details) > 5:
            suggestions.append("Consider using a merge tool: 'git mergetool'")
        
        return suggestions