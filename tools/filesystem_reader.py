# -*- coding: utf-8 -*-
# tools/filesystem_reader.py
import logging
import os
import stat
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
import fnmatch
import re

# --- ZONA DI SICUREZZA ---
# Definiamo una directory "sandbox" da cui è permesso leggere i file.
# Qualsiasi tentativo di leggere file al di fuori di questa cartella verrà bloccato.
SAFE_DIRECTORY = Path.cwd() / "safe_files"

# Configurazione sicurezza
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size
MAX_FILES_BATCH = 50  # Max files in batch operations
ALLOWED_EXTENSIONS = {'.txt', '.json', '.csv', '.xml', '.yaml', '.yml', '.md', '.log', '.py', '.js', '.html', '.css'}
BLOCKED_PATTERNS = ['..', '/', '\\', '~', '$', '|', '&', ';', '`', '*', '?']

def _setup_safe_zone():
    """
    Funzione di utility interna per creare la directory sicura e file di esempio
    se non esistono già, rendendo il tool immediatamente testabile.
    """
    if not SAFE_DIRECTORY.exists():
        logging.info(f"Prima esecuzione: creo la directory sandbox in: {SAFE_DIRECTORY}")
        SAFE_DIRECTORY.mkdir()
    
    # Crea struttura di esempio più ricca
    example_files = {
        "esempio.txt": "Questo è un file di esempio che può essere letto in sicurezza dal server Nexus.",
        "config.json": '{\n  "app_name": "Nexus MCP Server",\n  "version": "1.0",\n  "debug": true\n}',
        "data.csv": "name,age,city\nJohn,30,New York\nJane,25,Los Angeles\nBob,35,Chicago",
        "notes.md": "# Note di Esempio\n\nQuesto è un file Markdown di esempio.\n\n## Sezioni\n- Punto 1\n- Punto 2"
    }
    
    # Crea sottodirectory
    (SAFE_DIRECTORY / "logs").mkdir(exist_ok=True)
    (SAFE_DIRECTORY / "configs").mkdir(exist_ok=True)
    
    for filename, content in example_files.items():
        example_file = SAFE_DIRECTORY / filename
        if not example_file.exists():
            example_file.write_text(content, encoding="utf-8")
    
    # Log di esempio
    log_file = SAFE_DIRECTORY / "logs" / "app.log"
    if not log_file.exists():
        log_content = f"""2024-01-01 10:00:00 INFO Application started
2024-01-01 10:01:00 DEBUG Processing request
2024-01-01 10:02:00 WARN Memory usage high
2024-01-01 10:03:00 ERROR Connection failed
2024-01-01 10:04:00 INFO Application stopped"""
        log_file.write_text(log_content, encoding="utf-8")

def _validate_path_security(path_input: str) -> bool:
    """Valida la sicurezza del percorso input."""
    # Controlla pattern bloccati
    for pattern in BLOCKED_PATTERNS:
        if pattern in path_input:
            return False
    
    # Controlla caratteri pericolosi
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in path_input for char in dangerous_chars):
        return False
    
    return True

def _resolve_safe_path(path_input: str) -> Optional[Path]:
    """Risolve e valida un percorso all'interno della sandbox."""
    if not _validate_path_security(path_input):
        return None
    
    target_path = SAFE_DIRECTORY / path_input
    
    # Verifica che il percorso risolto sia dentro la sandbox
    try:
        resolved_path = target_path.resolve()
        if not resolved_path.is_relative_to(SAFE_DIRECTORY.resolve()):
            return None
        return resolved_path
    except:
        return None

def register_tools(mcp):
    """Registra i tool per la lettura sicura di file con l'istanza del server MCP."""
    logging.info("📁 Registrazione tool-set: Filesystem Reader (Sandbox)")
    _setup_safe_zone()
    
    @mcp.tool()
    def read_safe_file(filename: str) -> str:
        """
        Legge il contenuto di un file dalla directory sicura 'safe_files'.
        L'uso di percorsi relativi come '../' o percorsi assoluti è bloccato.

        Args:
            filename: Il nome del file da leggere (es. 'esempio.txt').
        """
        try:
            # VALIDAZIONE DI SICUREZZA 1: Rifiuta nomi di file sospetti.
            if ".." in filename or "/" in filename or "\\" in filename:
                return "ERRORE DI SICUREZZA: Il nome del file contiene caratteri non validi per la navigazione."

            target_file = SAFE_DIRECTORY / filename
            
            # VALIDAZIONE DI SICUREZZA 2: Verifica che il percorso assoluto del file richiesto
            # sia effettivamente un figlio della nostra directory sicura. È la difesa più forte.
            if not target_file.resolve().is_relative_to(SAFE_DIRECTORY.resolve()):
                return "ERRORE DI SICUREZZA: Tentativo di accesso a un file al di fuori della directory sandbox."

            if not target_file.is_file():
                return f"ERRORE: Il file '{filename}' non è stato trovato nella directory sicura."

            content = target_file.read_text(encoding="utf-8")
            return f"--- Contenuto di '{filename}' ---\n{content}"
        
        except Exception as e:
            logging.error(f"[FileSystemReader] Errore imprevisto durante la lettura di '{filename}': {e}")
            return f"ERRORE: Si è verificato un problema tecnico durante la lettura del file."

    @mcp.tool()
    def list_safe_directory(directory_path: str = "") -> Dict[str, Any]:
        """
        Lista il contenuto di una directory all'interno della sandbox sicura.
        
        Args:
            directory_path: Percorso relativo della directory (vuoto per root sandbox)
        """
        try:
            if directory_path:
                target_dir = _resolve_safe_path(directory_path)
                if not target_dir or not target_dir.is_dir():
                    return {
                        "success": False,
                        "error": f"Directory '{directory_path}' non trovata o non valida"
                    }
            else:
                target_dir = SAFE_DIRECTORY
            
            items = []
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for item in sorted(target_dir.iterdir()):
                try:
                    stat_info = item.stat()
                    is_file = item.is_file()
                    
                    item_info = {
                        "name": item.name,
                        "type": "file" if is_file else "directory",
                        "size": stat_info.st_size if is_file else 0,
                        "modified": datetime.fromtimestamp(stat_info.st_mtime, timezone.utc).isoformat(),
                        "permissions": oct(stat_info.st_mode)[-3:],
                        "extension": item.suffix.lower() if is_file else None
                    }
                    
                    if is_file:
                        file_count += 1
                        total_size += stat_info.st_size
                        item_info["mime_type"] = mimetypes.guess_type(item.name)[0]
                        item_info["readable"] = item.suffix.lower() in ALLOWED_EXTENSIONS
                    else:
                        dir_count += 1
                        # Conta elementi nella sottodirectory
                        try:
                            subdir_count = len(list(item.iterdir()))
                            item_info["items_count"] = subdir_count
                        except:
                            item_info["items_count"] = 0
                    
                    items.append(item_info)
                    
                except Exception as e:
                    logging.warning(f"Errore lettura info per {item.name}: {e}")
                    continue
            
            return {
                "success": True,
                "directory": str(target_dir.relative_to(SAFE_DIRECTORY)) if directory_path else ".",
                "items": items,
                "summary": {
                    "total_items": len(items),
                    "files": file_count,
                    "directories": dir_count,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
            }
            
        except Exception as e:
            logging.error(f"Errore listing directory: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_file_metadata(filepath: str) -> Dict[str, Any]:
        """
        Ottiene metadati dettagliati di un file.
        
        Args:
            filepath: Percorso del file nella sandbox
        """
        try:
            target_file = _resolve_safe_path(filepath)
            if not target_file or not target_file.is_file():
                return {
                    "success": False,
                    "error": f"File '{filepath}' non trovato"
                }
            
            stat_info = target_file.stat()
            
            # Informazioni base
            metadata = {
                "success": True,
                "filepath": str(target_file.relative_to(SAFE_DIRECTORY)),
                "filename": target_file.name,
                "extension": target_file.suffix.lower(),
                "size_bytes": stat_info.st_size,
                "size_human": _format_file_size(stat_info.st_size),
                "created": datetime.fromtimestamp(stat_info.st_ctime, timezone.utc).isoformat(),
                "modified": datetime.fromtimestamp(stat_info.st_mtime, timezone.utc).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime, timezone.utc).isoformat(),
                "permissions": oct(stat_info.st_mode)[-3:],
                "is_readable": target_file.suffix.lower() in ALLOWED_EXTENSIONS
            }
            
            # MIME type
            mime_type, encoding = mimetypes.guess_type(target_file.name)
            metadata["mime_type"] = mime_type
            metadata["encoding"] = encoding
            
            # Hash del file (per file piccoli)
            if stat_info.st_size <= 1024 * 1024:  # Max 1MB per hash
                try:
                    content = target_file.read_bytes()
                    metadata["checksums"] = {
                        "md5": hashlib.md5(content).hexdigest(),
                        "sha256": hashlib.sha256(content).hexdigest()
                    }
                except:
                    metadata["checksums"] = None
            else:
                metadata["checksums"] = "File too large for checksum calculation"
            
            # Analisi contenuto per file di testo
            if target_file.suffix.lower() in ['.txt', '.log', '.md', '.py', '.js', '.json', '.csv', '.xml']:
                try:
                    content = target_file.read_text(encoding='utf-8')
                    metadata["content_analysis"] = {
                        "lines": len(content.split('\n')),
                        "words": len(content.split()),
                        "characters": len(content),
                        "encoding": "utf-8"
                    }
                except UnicodeDecodeError:
                    metadata["content_analysis"] = {"error": "Unable to decode as UTF-8"}
                except:
                    metadata["content_analysis"] = {"error": "Unable to analyze content"}
            
            return metadata
            
        except Exception as e:
            logging.error(f"Errore getting metadata per {filepath}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def search_files(pattern: str, search_type: str = "name", 
                    directory: str = "", include_content: bool = False) -> Dict[str, Any]:
        """
        Cerca file nella sandbox in base a pattern.
        
        Args:
            pattern: Pattern di ricerca
            search_type: Tipo ricerca (name, extension, content)
            directory: Directory dove cercare (vuoto per tutta la sandbox)
            include_content: Se includere preview del contenuto
        """
        try:
            if directory:
                search_dir = _resolve_safe_path(directory)
                if not search_dir or not search_dir.is_dir():
                    return {"success": False, "error": f"Directory '{directory}' non valida"}
            else:
                search_dir = SAFE_DIRECTORY
            
            results = []
            total_searched = 0
            
            # Cerca ricorsivamente
            for file_path in search_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                
                total_searched += 1
                matched = False
                match_reason = ""
                
                # Controllo dimensione file
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
                
                relative_path = str(file_path.relative_to(SAFE_DIRECTORY))
                
                if search_type == "name":
                    if fnmatch.fnmatch(file_path.name.lower(), pattern.lower()):
                        matched = True
                        match_reason = "filename"
                
                elif search_type == "extension":
                    if file_path.suffix.lower() == pattern.lower():
                        matched = True
                        match_reason = "extension"
                
                elif search_type == "content":
                    if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                        try:
                            content = file_path.read_text(encoding='utf-8')
                            if re.search(pattern, content, re.IGNORECASE):
                                matched = True
                                match_reason = "content"
                        except:
                            continue
                
                if matched:
                    result_item = {
                        "filepath": relative_path,
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime, timezone.utc
                        ).isoformat(),
                        "match_reason": match_reason
                    }
                    
                    # Include content preview se richiesto
                    if include_content and search_type == "content":
                        try:
                            content = file_path.read_text(encoding='utf-8')
                            # Trova linee che contengono il pattern
                            matching_lines = []
                            for i, line in enumerate(content.split('\n'), 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    matching_lines.append({
                                        "line_number": i,
                                        "content": line.strip()[:200]  # Max 200 chars per line
                                    })
                                    if len(matching_lines) >= 5:  # Max 5 matching lines
                                        break
                            result_item["matching_lines"] = matching_lines
                        except:
                            pass
                    
                    results.append(result_item)
                    
                    # Limite risultati
                    if len(results) >= MAX_FILES_BATCH:
                        break
            
            return {
                "success": True,
                "pattern": pattern,
                "search_type": search_type,
                "directory": directory or ".",
                "results": results,
                "summary": {
                    "matches_found": len(results),
                    "files_searched": total_searched,
                    "search_truncated": len(results) >= MAX_FILES_BATCH
                }
            }
            
        except Exception as e:
            logging.error(f"Errore search: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_file_content(filepath: str, analysis_type: str = "basic") -> Dict[str, Any]:
        """
        Analizza il contenuto di un file con vari livelli di dettaglio.
        
        Args:
            filepath: Percorso del file
            analysis_type: Tipo analisi (basic, detailed, structure)
        """
        try:
            target_file = _resolve_safe_path(filepath)
            if not target_file or not target_file.is_file():
                return {"success": False, "error": f"File '{filepath}' non trovato"}
            
            # Controllo dimensione
            file_size = target_file.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return {"success": False, "error": "File troppo grande per l'analisi"}
            
            # Controllo estensione
            if target_file.suffix.lower() not in ALLOWED_EXTENSIONS:
                return {"success": False, "error": "Tipo di file non supportato per l'analisi"}
            
            try:
                content = target_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                return {"success": False, "error": "File non leggibile come testo UTF-8"}
            
            analysis = {
                "success": True,
                "filepath": str(target_file.relative_to(SAFE_DIRECTORY)),
                "analysis_type": analysis_type,
                "file_info": {
                    "size_bytes": file_size,
                    "extension": target_file.suffix.lower(),
                    "mime_type": mimetypes.guess_type(target_file.name)[0]
                }
            }
            
            # Analisi basic
            lines = content.split('\n')
            words = content.split()
            
            basic_stats = {
                "total_lines": len(lines),
                "non_empty_lines": len([line for line in lines if line.strip()]),
                "total_words": len(words),
                "total_characters": len(content),
                "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
            }
            analysis["basic_statistics"] = basic_stats
            
            if analysis_type in ["detailed", "structure"]:
                # Analisi dettagliata
                char_freq = {}
                for char in content.lower():
                    char_freq[char] = char_freq.get(char, 0) + 1
                
                # Top caratteri più frequenti
                top_chars = sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                
                detailed_stats = {
                    "unique_characters": len(char_freq),
                    "most_common_chars": top_chars,
                    "whitespace_ratio": (content.count(' ') + content.count('\t') + content.count('\n')) / len(content),
                    "longest_line": max(len(line) for line in lines) if lines else 0,
                    "shortest_line": min(len(line) for line in lines if line.strip()) if any(line.strip() for line in lines) else 0
                }
                analysis["detailed_statistics"] = detailed_stats
            
            if analysis_type == "structure":
                # Analisi struttura specifica per tipo file
                structure_analysis = _analyze_file_structure(content, target_file.suffix.lower())
                analysis["structure_analysis"] = structure_analysis
            
            return analysis
            
        except Exception as e:
            logging.error(f"Errore analysis per {filepath}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def read_file_range(filepath: str, start_line: int = 1, end_line: int = None, 
                       max_lines: int = 100) -> Dict[str, Any]:
        """
        Legge un range specifico di righe da un file.
        
        Args:
            filepath: Percorso del file
            start_line: Riga di inizio (1-indexed)
            end_line: Riga di fine (None per fine file)
            max_lines: Massimo numero di righe da leggere
        """
        try:
            target_file = _resolve_safe_path(filepath)
            if not target_file or not target_file.is_file():
                return {"success": False, "error": f"File '{filepath}' non trovato"}
            
            if target_file.suffix.lower() not in ALLOWED_EXTENSIONS:
                return {"success": False, "error": "Tipo di file non supportato"}
            
            if start_line < 1:
                return {"success": False, "error": "start_line deve essere >= 1"}
            
            if max_lines > 1000:
                max_lines = 1000  # Limite di sicurezza
            
            try:
                content = target_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                total_lines = len(lines)
                
                # Calcola range effettivo
                start_idx = start_line - 1
                if end_line is None:
                    end_idx = min(start_idx + max_lines, total_lines)
                else:
                    end_idx = min(end_line, start_idx + max_lines, total_lines)
                
                if start_idx >= total_lines:
                    return {"success": False, "error": f"start_line {start_line} oltre la fine del file"}
                
                selected_lines = []
                for i in range(start_idx, end_idx):
                    selected_lines.append({
                        "line_number": i + 1,
                        "content": lines[i]
                    })
                
                return {
                    "success": True,
                    "filepath": str(target_file.relative_to(SAFE_DIRECTORY)),
                    "total_lines": total_lines,
                    "range_requested": {
                        "start_line": start_line,
                        "end_line": end_line,
                        "max_lines": max_lines
                    },
                    "range_returned": {
                        "start_line": start_line,
                        "end_line": end_idx,
                        "lines_count": len(selected_lines)
                    },
                    "lines": selected_lines
                }
                
            except UnicodeDecodeError:
                return {"success": False, "error": "File non leggibile come testo UTF-8"}
            
        except Exception as e:
            logging.error(f"Errore reading range per {filepath}: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_sandbox_info() -> Dict[str, Any]:
        """
        Ottiene informazioni sulla sandbox e configurazione sicurezza.
        """
        try:
            # Statistiche directory sandbox
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for item in SAFE_DIRECTORY.rglob("*"):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
                elif item.is_dir():
                    dir_count += 1
            
            return {
                "success": True,
                "sandbox_info": {
                    "path": str(SAFE_DIRECTORY),
                    "exists": SAFE_DIRECTORY.exists(),
                    "total_files": file_count,
                    "total_directories": dir_count,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                },
                "security_config": {
                    "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
                    "max_files_batch": MAX_FILES_BATCH,
                    "allowed_extensions": list(ALLOWED_EXTENSIONS),
                    "blocked_patterns": BLOCKED_PATTERNS
                },
                "capabilities": [
                    "read_safe_file",
                    "list_safe_directory", 
                    "get_file_metadata",
                    "search_files",
                    "analyze_file_content",
                    "read_file_range"
                ]
            }
            
        except Exception as e:
            logging.error(f"Errore getting sandbox info: {e}")
            return {"success": False, "error": str(e)}

    # Helper functions
    def _format_file_size(size_bytes: int) -> str:
        """Formatta dimensione file in formato human-readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _analyze_file_structure(content: str, extension: str) -> Dict[str, Any]:
        """Analizza struttura specifica per tipo di file."""
        analysis = {}
        
        if extension == '.json':
            try:
                import json
                data = json.loads(content)
                analysis = {
                    "valid_json": True,
                    "data_type": type(data).__name__,
                    "keys_count": len(data) if isinstance(data, dict) else None,
                    "array_length": len(data) if isinstance(data, list) else None
                }
            except:
                analysis = {"valid_json": False}
        
        elif extension == '.csv':
            lines = content.split('\n')
            if lines:
                first_line = lines[0]
                delimiter_counts = {
                    ',': first_line.count(','),
                    ';': first_line.count(';'),
                    '\t': first_line.count('\t')
                }
                likely_delimiter = max(delimiter_counts.items(), key=lambda x: x[1])[0]
                
                analysis = {
                    "csv_structure": True,
                    "estimated_columns": delimiter_counts[likely_delimiter] + 1,
                    "likely_delimiter": likely_delimiter,
                    "data_rows": len(lines) - 1 if len(lines) > 1 else 0
                }
        
        elif extension in ['.py', '.js']:
            lines = content.split('\n')
            code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            comment_lines = [line for line in lines if line.strip().startswith('#')]
            
            analysis = {
                "code_analysis": True,
                "code_lines": len(code_lines),
                "comment_lines": len(comment_lines),
                "blank_lines": len(lines) - len(code_lines) - len(comment_lines),
                "functions_count": content.count('def ') if extension == '.py' else content.count('function ')
            }
        
        return analysis