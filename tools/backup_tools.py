# -*- coding: utf-8 -*-
# tools/backup_tools.py
import os
import shutil
import tempfile
import zipfile
import tarfile
import json
import hashlib
import time
import logging
import sqlite3
import gzip
import bz2
from typing import Dict, List, Any, Optional, Union, Tuple
import fnmatch
from datetime import datetime, timezone, timedelta
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import base64

# Enhanced backup configuration
BACKUP_CONFIG = {
    "max_file_size_mb": 1024,  # 1GB per file
    "max_total_size_gb": 10,   # 10GB per backup
    "chunk_size": 8192,        # For streaming operations
    "hash_algorithms": ["sha256", "md5"],
    "encryption_methods": ["aes256", "simple_xor"],
    "compression_levels": range(1, 10),
    "backup_retention_days": 30
}

class BackupDatabase:
    """Gestisce il database SQLite per tracciare i backup."""
    
    def __init__(self, db_path: str = "safe_files/backup_history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inizializza il database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    source_paths TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    size_bytes INTEGER,
                    file_count INTEGER,
                    compression_ratio REAL,
                    hash_sha256 TEXT,
                    status TEXT DEFAULT 'completed',
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backup_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    size_bytes INTEGER,
                    modified_time REAL,
                    hash_sha256 TEXT,
                    hash_md5 TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
                )
            """)
    
    def add_backup(self, backup_info: Dict[str, Any]) -> str:
        """Aggiunge un backup al database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backups 
                (backup_id, name, source_paths, destination, backup_type, size_bytes, 
                 file_count, compression_ratio, hash_sha256, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                backup_info['backup_id'],
                backup_info['name'],
                json.dumps(backup_info['source_paths']),
                backup_info['destination'],
                backup_info['backup_type'],
                backup_info.get('size_bytes', 0),
                backup_info.get('file_count', 0),
                backup_info.get('compression_ratio', 0),
                backup_info.get('hash_sha256', ''),
                json.dumps(backup_info.get('metadata', {}))
            ))
            return backup_info['backup_id']
    
    def get_backup_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Ottiene la cronologia dei backup."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM backups 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            backups = []
            for row in cursor.fetchall():
                backup = dict(row)
                backup['source_paths'] = json.loads(backup['source_paths'])
                backup['metadata'] = json.loads(backup['metadata'])
                backups.append(backup)
            
            return backups

# Global backup database instance
_backup_db = BackupDatabase()

def register_tools(mcp):
    """Registra i tool di backup con l'istanza del server MCP."""
    logging.info("💾 Registrazione tool-set: Enhanced Backup & Archive Tools")

    @mcp.tool()
    def create_incremental_backup(source_paths: List[str], backup_name: str, 
                                base_backup_id: str = "", compression_level: int = 6,
                                encryption_key: str = "", exclude_patterns: List[str] = []) -> Dict[str, Any]:
        """
        Crea un backup incrementale basato su un backup precedente.
        
        Args:
            source_paths: Lista di percorsi da includere nel backup
            backup_name: Nome descrittivo del backup
            base_backup_id: ID del backup base (vuoto per backup completo)
            compression_level: Livello di compressione (1-9)
            encryption_key: Chiave per crittografia (opzionale)
            exclude_patterns: Pattern di file da escludere
        """
        try:
            # Validazione parametri
            if not source_paths:
                return {"success": False, "error": "Nessun percorso sorgente specificato"}
            
            if not all(os.path.exists(path) for path in source_paths):
                missing_paths = [path for path in source_paths if not os.path.exists(path)]
                return {"success": False, "error": f"Percorsi non trovati: {missing_paths}"}
            
            # Genera ID backup univoco
            backup_id = _generate_backup_id(backup_name)
            backup_type = "incremental" if base_backup_id else "full"
            
            # Directory di destinazione
            backup_dir = f"safe_files/backups/{backup_id}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Carica informazioni backup base se incrementale
            base_files = {}
            if base_backup_id:
                base_files = _load_base_backup_files(base_backup_id)
                if not base_files:
                    return {"success": False, "error": f"Backup base {base_backup_id} non trovato"}
            
            # Scansiona file correnti
            current_files = {}
            total_size = 0
            file_count = 0
            
            for source_path in source_paths:
                files_info = _scan_directory_enhanced(source_path, exclude_patterns)
                current_files.update(files_info)
                
                for file_info in files_info.values():
                    total_size += file_info['size_bytes']
                    file_count += 1
            
            # Determina file da includere (per incrementale: solo modificati/nuovi)
            files_to_backup = {}
            if backup_type == "incremental":
                for file_path, file_info in current_files.items():
                    base_info = base_files.get(file_path)
                    if not base_info or _file_changed(file_info, base_info):
                        files_to_backup[file_path] = file_info
            else:
                files_to_backup = current_files
            
            if not files_to_backup:
                return {
                    "success": True,
                    "backup_id": backup_id,
                    "message": "Nessun file modificato - backup non necessario",
                    "backup_type": backup_type
                }
            
            # Crea archivio
            archive_path = os.path.join(backup_dir, f"{backup_name}_{backup_type}.tar.gz")
            
            with tarfile.open(archive_path, f'w:gz', compresslevel=compression_level) as tar:
                for file_path, file_info in files_to_backup.items():
                    if os.path.exists(file_path):
                        tar.add(file_path, file_info['relative_path'])
            
            # Applica crittografia se richiesta
            if encryption_key:
                encrypted_path = archive_path + ".enc"
                _encrypt_file(archive_path, encrypted_path, encryption_key)
                os.remove(archive_path)
                archive_path = encrypted_path
            
            # Calcola hash e statistiche
            archive_size = os.path.getsize(archive_path)
            archive_hash = _calculate_file_hash(archive_path, "sha256")
            compression_ratio = (1 - archive_size / total_size) * 100 if total_size > 0 else 0
            
            # Salva nel database
            backup_info = {
                "backup_id": backup_id,
                "name": backup_name,
                "source_paths": source_paths,
                "destination": archive_path,
                "backup_type": backup_type,
                "size_bytes": archive_size,
                "file_count": len(files_to_backup),
                "compression_ratio": compression_ratio,
                "hash_sha256": archive_hash,
                "metadata": {
                    "base_backup_id": base_backup_id,
                    "encryption_enabled": bool(encryption_key),
                    "compression_level": compression_level,
                    "exclude_patterns": exclude_patterns,
                    "total_source_size": total_size
                }
            }
            
            _backup_db.add_backup(backup_info)
            
            # Salva file list per futuri backup incrementali
            _save_backup_files(backup_id, current_files)
            
            return {
                "success": True,
                "backup_id": backup_id,
                "backup_type": backup_type,
                "archive_path": archive_path,
                "files_backed_up": len(files_to_backup),
                "total_files_scanned": file_count,
                "backup_size_mb": round(archive_size / (1024 * 1024), 2),
                "compression_ratio_percent": round(compression_ratio, 2),
                "archive_hash_sha256": archive_hash,
                "base_backup_id": base_backup_id if backup_type == "incremental" else None
            }
            
        except Exception as e:
            logging.error(f"Errore in create_incremental_backup: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_archive(source_path: str, archive_type: str = "zip", include_patterns: List[str] = [], exclude_patterns: List[str] = []) -> Dict[str, Any]:
        """
        Crea un archivio di file e directory.
        
        Args:
            source_path: Percorso sorgente da archiviare
            archive_type: Tipo di archivio (zip, tar, tar.gz, tar.bz2)
            include_patterns: Pattern di file da includere (es. ["*.py", "*.txt"])
            exclude_patterns: Pattern di file da escludere (es. ["*.pyc", "__pycache__"])
        """
        try:
            if not os.path.exists(source_path):
                return {
                    "success": False,
                    "error": "Source path does not exist"
                }
            
            # Default exclude patterns for common unwanted files
            default_excludes = [
                "*.pyc", "__pycache__", ".git", ".svn", ".DS_Store", 
                "Thumbs.db", "*.tmp", "*.temp", "node_modules", ".env"
            ]
            
            all_exclude_patterns = default_excludes + exclude_patterns
            
            # Crea archivio in directory temporanea
            temp_dir = tempfile.mkdtemp(prefix="nexus_archive_")
            source_name = os.path.basename(source_path.rstrip('/\\'))
            
            if archive_type == "zip":
                archive_path = os.path.join(temp_dir, f"{source_name}.zip")
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    files_added = _add_files_to_zip(zipf, source_path, include_patterns, all_exclude_patterns)
            
            elif archive_type in ["tar", "tar.gz", "tar.bz2"]:
                ext = archive_type.replace("tar", "tar")
                mode_map = {
                    "tar": "w",
                    "tar.gz": "w:gz", 
                    "tar.bz2": "w:bz2"
                }
                archive_path = os.path.join(temp_dir, f"{source_name}.{ext}")
                with tarfile.open(archive_path, mode_map[archive_type]) as tarf:
                    files_added = _add_files_to_tar(tarf, source_path, include_patterns, all_exclude_patterns)
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported archive type. Use: zip, tar, tar.gz, tar.bz2"
                }
            
            # Calcola statistiche
            archive_size = os.path.getsize(archive_path)
            original_size = _calculate_directory_size(source_path)
            compression_ratio = (1 - archive_size / original_size) * 100 if original_size > 0 else 0
            
            # Calcola hash dell'archivio
            archive_hash = _calculate_file_hash(archive_path)
            
            return {
                "success": True,
                "source_path": source_path,
                "archive_path": archive_path,
                "archive_type": archive_type,
                "files_included": files_added,
                "archive_size_bytes": archive_size,
                "archive_size_mb": round(archive_size / (1024 * 1024), 2),
                "original_size_bytes": original_size,
                "compression_ratio_percent": round(compression_ratio, 2),
                "archive_hash_sha256": archive_hash,
                "include_patterns": include_patterns,
                "exclude_patterns": all_exclude_patterns
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def extract_archive(archive_path: str, destination_path: str = "", verify_integrity: bool = True) -> Dict[str, Any]:
        """
        Estrae un archivio in una directory di destinazione.
        
        Args:
            archive_path: Percorso dell'archivio da estrarre
            destination_path: Directory di destinazione (opzionale, usa temp se vuoto)
            verify_integrity: Se verificare l'integrità dell'archivio prima dell'estrazione
        """
        try:
            if not os.path.exists(archive_path):
                return {
                    "success": False,
                    "error": "Archive file does not exist"
                }
            
            # Determina tipo archivio dall'estensione
            archive_type = None
            if archive_path.endswith('.zip'):
                archive_type = "zip"
            elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                archive_type = "tar.gz"
            elif archive_path.endswith('.tar.bz2'):
                archive_type = "tar.bz2"
            elif archive_path.endswith('.tar'):
                archive_type = "tar"
            else:
                return {
                    "success": False,
                    "error": "Unsupported archive format"
                }
            
            # Directory di destinazione
            if not destination_path:
                destination_path = tempfile.mkdtemp(prefix="nexus_extract_")
            else:
                os.makedirs(destination_path, exist_ok=True)
            
            files_extracted = []
            
            # Verifica integrità se richiesto
            integrity_check = {"passed": True, "error": None}
            if verify_integrity:
                try:
                    if archive_type == "zip":
                        with zipfile.ZipFile(archive_path, 'r') as zipf:
                            bad_file = zipf.testzip()
                            if bad_file:
                                integrity_check = {"passed": False, "error": f"Corrupted file: {bad_file}"}
                    elif archive_type.startswith("tar"):
                        mode_map = {
                            "tar": "r",
                            "tar.gz": "r:gz",
                            "tar.bz2": "r:bz2"
                        }
                        with tarfile.open(archive_path, mode_map[archive_type]) as tarf:
                            # Basic integrity check by listing members
                            tarf.getmembers()
                except Exception as e:
                    integrity_check = {"passed": False, "error": str(e)}
            
            if not integrity_check["passed"]:
                return {
                    "success": False,
                    "error": f"Archive integrity check failed: {integrity_check['error']}"
                }
            
            # Estrazione
            if archive_type == "zip":
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    members = zipf.namelist()
                    for member in members:
                        # Controllo sicurezza: evita path traversal
                        if os.path.isabs(member) or ".." in member:
                            continue
                        zipf.extract(member, destination_path)
                        files_extracted.append(member)
            
            elif archive_type.startswith("tar"):
                mode_map = {
                    "tar": "r",
                    "tar.gz": "r:gz", 
                    "tar.bz2": "r:bz2"
                }
                with tarfile.open(archive_path, mode_map[archive_type]) as tarf:
                    members = tarf.getmembers()
                    for member in members:
                        # Controllo sicurezza: evita path traversal
                        if os.path.isabs(member.name) or ".." in member.name:
                            continue
                        tarf.extract(member, destination_path)
                        files_extracted.append(member.name)
            
            # Calcola dimensione estratta
            extracted_size = _calculate_directory_size(destination_path)
            
            return {
                "success": True,
                "archive_path": archive_path,
                "destination_path": destination_path,
                "archive_type": archive_type,
                "files_extracted": len(files_extracted),
                "extracted_files": files_extracted[:20],  # Prime 20 per non appesantire
                "extracted_size_bytes": extracted_size,
                "extracted_size_mb": round(extracted_size / (1024 * 1024), 2),
                "integrity_check": integrity_check
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def create_backup_manifest(backup_path: str, source_paths: List[str], metadata: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Crea un manifest di backup con metadata e checksums.
        
        Args:
            backup_path: Percorso dove salvare il manifest
            source_paths: Lista dei percorsi inclusi nel backup
            metadata: Metadata aggiuntivi del backup
        """
        try:
            manifest_data = {
                "backup_info": {
                    "timestamp": time.time(),
                    "timestamp_human": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "backup_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:16],
                    "source_paths": source_paths,
                    "total_sources": len(source_paths)
                },
                "metadata": metadata,
                "files": [],
                "statistics": {
                    "total_files": 0,
                    "total_size_bytes": 0,
                    "file_types": {}
                }
            }
            
            total_files = 0
            total_size = 0
            file_types = {}
            
            # Analizza tutti i file nei percorsi sorgente
            for source_path in source_paths:
                if not os.path.exists(source_path):
                    continue
                
                if os.path.isfile(source_path):
                    # Singolo file
                    file_info = _get_file_info(source_path)
                    manifest_data["files"].append(file_info)
                    total_files += 1
                    total_size += file_info["size_bytes"]
                    
                    ext = file_info["extension"]
                    file_types[ext] = file_types.get(ext, 0) + 1
                
                elif os.path.isdir(source_path):
                    # Directory
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, source_path)
                            
                            file_info = _get_file_info(file_path, relative_path)
                            manifest_data["files"].append(file_info)
                            total_files += 1
                            total_size += file_info["size_bytes"]
                            
                            ext = file_info["extension"]
                            file_types[ext] = file_types.get(ext, 0) + 1
            
            # Aggiorna statistiche
            manifest_data["statistics"] = {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "largest_files": sorted(manifest_data["files"], 
                                      key=lambda x: x["size_bytes"], reverse=True)[:10]
            }
            
            # Salva manifest
            manifest_path = os.path.join(backup_path, "backup_manifest.json")
            os.makedirs(backup_path, exist_ok=True)
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            
            return {
                "success": True,
                "manifest_path": manifest_path,
                "backup_id": manifest_data["backup_info"]["backup_id"],
                "files_cataloged": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "manifest_size_bytes": os.path.getsize(manifest_path)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def verify_backup_integrity(manifest_path: str, backup_base_path: str = "") -> Dict[str, Any]:
        """
        Verifica l'integrità di un backup usando il manifest.
        
        Args:
            manifest_path: Percorso del file manifest
            backup_base_path: Percorso base del backup (se diverso dalla directory del manifest)
        """
        try:
            if not os.path.exists(manifest_path):
                return {
                    "success": False,
                    "error": "Manifest file not found"
                }
            
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            if not backup_base_path:
                backup_base_path = os.path.dirname(manifest_path)
            
            verification_results = {
                "files_verified": 0,
                "files_missing": 0,
                "files_corrupted": 0,
                "files_modified": 0,
                "missing_files": [],
                "corrupted_files": [],
                "modified_files": []
            }
            
            total_files = len(manifest_data.get("files", []))
            
            for file_info in manifest_data.get("files", []):
                file_path = os.path.join(backup_base_path, file_info["relative_path"])
                
                if not os.path.exists(file_path):
                    verification_results["files_missing"] += 1
                    verification_results["missing_files"].append(file_info["relative_path"])
                    continue
                
                # Verifica dimensione
                current_size = os.path.getsize(file_path)
                if current_size != file_info["size_bytes"]:
                    verification_results["files_modified"] += 1
                    verification_results["modified_files"].append({
                        "path": file_info["relative_path"],
                        "reason": "Size mismatch",
                        "expected_size": file_info["size_bytes"],
                        "actual_size": current_size
                    })
                    continue
                
                # Verifica hash se presente
                if "sha256_hash" in file_info:
                    current_hash = _calculate_file_hash(file_path)
                    if current_hash != file_info["sha256_hash"]:
                        verification_results["files_corrupted"] += 1
                        verification_results["corrupted_files"].append({
                            "path": file_info["relative_path"],
                            "expected_hash": file_info["sha256_hash"],
                            "actual_hash": current_hash
                        })
                        continue
                
                verification_results["files_verified"] += 1
            
            # Calcola percentuale di integrità
            integrity_percentage = (verification_results["files_verified"] / total_files * 100) if total_files > 0 else 0
            
            integrity_status = "Excellent"
            if verification_results["files_missing"] > 0 or verification_results["files_corrupted"] > 0:
                integrity_status = "Poor"
            elif verification_results["files_modified"] > 0:
                integrity_status = "Fair"
            elif integrity_percentage >= 99:
                integrity_status = "Excellent"
            else:
                integrity_status = "Good"
            
            return {
                "success": True,
                "manifest_path": manifest_path,
                "backup_base_path": backup_base_path,
                "total_files": total_files,
                "integrity_percentage": round(integrity_percentage, 2),
                "integrity_status": integrity_status,
                "verification_results": verification_results,
                "backup_info": manifest_data.get("backup_info", {})
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def compress_files(file_paths: List[str], compression_level: int = 6, algorithm: str = "gzip") -> Dict[str, Any]:
        """
        Comprime file individuali con diversi algoritmi.
        
        Args:
            file_paths: Lista di file da comprimere
            compression_level: Livello di compressione (1-9)
            algorithm: Algoritmo di compressione (gzip, bzip2, zip)
        """
        try:
            if compression_level < 1 or compression_level > 9:
                return {
                    "success": False,
                    "error": "Compression level must be between 1 and 9"
                }
            
            if algorithm not in ["gzip", "bzip2", "zip"]:
                return {
                    "success": False,
                    "error": "Unsupported algorithm. Use: gzip, bzip2, zip"
                }
            
            compression_results = []
            total_original_size = 0
            total_compressed_size = 0
            
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    compression_results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": "File not found"
                    })
                    continue
                
                if not os.path.isfile(file_path):
                    compression_results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": "Not a file"
                    })
                    continue
                
                try:
                    original_size = os.path.getsize(file_path)
                    total_original_size += original_size
                    
                    # Determina estensione compressa
                    if algorithm == "gzip":
                        compressed_path = file_path + ".gz"
                        import gzip
                        with open(file_path, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb', compresslevel=compression_level) as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    
                    elif algorithm == "bzip2":
                        compressed_path = file_path + ".bz2"
                        import bz2
                        with open(file_path, 'rb') as f_in:
                            with bz2.open(compressed_path, 'wb', compresslevel=compression_level) as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    
                    elif algorithm == "zip":
                        compressed_path = file_path + ".zip"
                        with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
                            zipf.write(file_path, os.path.basename(file_path))
                    
                    compressed_size = os.path.getsize(compressed_path)
                    total_compressed_size += compressed_size
                    compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                    
                    compression_results.append({
                        "file_path": file_path,
                        "compressed_path": compressed_path,
                        "success": True,
                        "original_size_bytes": original_size,
                        "compressed_size_bytes": compressed_size,
                        "compression_ratio_percent": round(compression_ratio, 2),
                        "space_saved_bytes": original_size - compressed_size
                    })
                
                except Exception as e:
                    compression_results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": str(e)
                    })
            
            successful_compressions = len([r for r in compression_results if r.get("success", False)])
            overall_compression_ratio = (1 - total_compressed_size / total_original_size) * 100 if total_original_size > 0 else 0
            
            return {
                "success": True,
                "algorithm": algorithm,
                "compression_level": compression_level,
                "files_processed": len(file_paths),
                "successful_compressions": successful_compressions,
                "total_original_size_bytes": total_original_size,
                "total_compressed_size_bytes": total_compressed_size,
                "overall_compression_ratio_percent": round(overall_compression_ratio, 2),
                "total_space_saved_bytes": total_original_size - total_compressed_size,
                "results": compression_results
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def restore_backup_selective(backup_id: str, restore_path: str, 
                                file_patterns: List[str] = [], 
                                decrypt_key: str = "") -> Dict[str, Any]:
        """
        Ripristina selettivamente file da un backup.
        
        Args:
            backup_id: ID del backup da ripristinare
            restore_path: Directory di destinazione
            file_patterns: Pattern di file da ripristinare (vuoto = tutti)
            decrypt_key: Chiave di decrittografia se necessaria
        """
        try:
            # Trova backup nel database
            backup_info = _get_backup_info(backup_id)
            if not backup_info:
                return {"success": False, "error": f"Backup {backup_id} non trovato"}
            
            archive_path = backup_info['destination']
            if not os.path.exists(archive_path):
                return {"success": False, "error": f"File di backup non trovato: {archive_path}"}
            
            # Prepara directory di ripristino
            os.makedirs(restore_path, exist_ok=True)
            
            # Gestisci decrittografia se necessario
            working_archive = archive_path
            if archive_path.endswith('.enc'):
                if not decrypt_key:
                    return {"success": False, "error": "Backup crittografato richiede chiave di decrittografia"}
                
                temp_path = tempfile.mktemp(suffix='.tar.gz')
                if not _decrypt_file(archive_path, temp_path, decrypt_key):
                    return {"success": False, "error": "Decrittografia fallita - chiave incorretta"}
                working_archive = temp_path
            
            # Estrai file selettivamente
            files_restored = []
            files_skipped = []
            
            with tarfile.open(working_archive, 'r:gz') as tar:
                members = tar.getmembers()
                
                for member in members:
                    if not member.isfile():
                        continue
                    
                    # Applica filtri se specificati
                    if file_patterns:
                        match_found = False
                        for pattern in file_patterns:
                            if fnmatch.fnmatch(member.name, pattern):
                                match_found = True
                                break
                        if not match_found:
                            files_skipped.append(member.name)
                            continue
                    
                    # Controlla sicurezza path
                    if _is_safe_path(member.name):
                        tar.extract(member, restore_path)
                        files_restored.append(member.name)
                    else:
                        files_skipped.append(f"{member.name} (unsafe path)")
            
            # Cleanup file temporaneo se usato
            if working_archive != archive_path:
                os.remove(working_archive)
            
            return {
                "success": True,
                "backup_id": backup_id,
                "restore_path": restore_path,
                "files_restored": len(files_restored),
                "files_skipped": len(files_skipped),
                "restored_files": files_restored[:20],  # Prime 20
                "file_patterns_used": file_patterns,
                "backup_info": {
                    "name": backup_info['name'],
                    "created_at": backup_info['created_at'],
                    "backup_type": backup_info['backup_type']
                }
            }
            
        except Exception as e:
            logging.error(f"Errore in restore_backup_selective: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_backup_history(limit: int = 20, backup_type: str = "") -> Dict[str, Any]:
        """
        Ottiene la cronologia dei backup con filtri.
        
        Args:
            limit: Numero massimo di backup da restituire (1-100)
            backup_type: Filtra per tipo backup ('full', 'incremental')
        """
        try:
            if limit < 1 or limit > 100:
                limit = 20
            
            backups = _backup_db.get_backup_history(limit)
            
            # Applica filtro tipo se specificato
            if backup_type:
                backups = [b for b in backups if b['backup_type'] == backup_type]
            
            # Aggiungi statistiche
            total_size = sum(b['size_bytes'] for b in backups)
            total_files = sum(b['file_count'] for b in backups)
            
            # Raggruppa per tipo
            type_stats = {}
            for backup in backups:
                btype = backup['backup_type']
                if btype not in type_stats:
                    type_stats[btype] = {"count": 0, "total_size": 0}
                type_stats[btype]["count"] += 1
                type_stats[btype]["total_size"] += backup['size_bytes']
            
            return {
                "success": True,
                "backups": backups,
                "statistics": {
                    "total_backups": len(backups),
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "total_files": total_files,
                    "backup_types": type_stats,
                    "oldest_backup": backups[-1]['created_at'] if backups else None,
                    "newest_backup": backups[0]['created_at'] if backups else None
                },
                "filter_applied": {"limit": limit, "backup_type": backup_type}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def cleanup_old_backups(retention_days: int = 30, dry_run: bool = True) -> Dict[str, Any]:
        """
        Rimuove backup vecchi secondo policy di retention.
        
        Args:
            retention_days: Giorni di retention (1-365)
            dry_run: Se True, simula senza cancellare
        """
        try:
            if retention_days < 1 or retention_days > 365:
                return {"success": False, "error": "retention_days deve essere tra 1 e 365"}
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            backups = _backup_db.get_backup_history(1000)  # Prendi molti backup
            
            old_backups = []
            total_size_to_free = 0
            
            for backup in backups:
                backup_date = datetime.fromisoformat(backup['created_at'])
                if backup_date < cutoff_date:
                    old_backups.append(backup)
                    if os.path.exists(backup['destination']):
                        total_size_to_free += os.path.getsize(backup['destination'])
            
            if not old_backups:
                return {
                    "success": True,
                    "message": "Nessun backup da rimuovere",
                    "retention_days": retention_days,
                    "dry_run": dry_run
                }
            
            removed_backups = []
            errors = []
            
            if not dry_run:
                for backup in old_backups:
                    try:
                        if os.path.exists(backup['destination']):
                            os.remove(backup['destination'])
                        
                        # Rimuovi directory se vuota
                        backup_dir = os.path.dirname(backup['destination'])
                        if os.path.exists(backup_dir) and not os.listdir(backup_dir):
                            os.rmdir(backup_dir)
                        
                        removed_backups.append(backup['backup_id'])
                        
                    except Exception as e:
                        errors.append(f"Errore rimozione {backup['backup_id']}: {str(e)}")
            
            return {
                "success": True,
                "dry_run": dry_run,
                "retention_days": retention_days,
                "old_backups_found": len(old_backups),
                "space_to_free_mb": round(total_size_to_free / (1024 * 1024), 2),
                "removed_backups": removed_backups if not dry_run else [],
                "errors": errors,
                "old_backup_details": [
                    {
                        "backup_id": b['backup_id'],
                        "name": b['name'],
                        "created_at": b['created_at'],
                        "size_mb": round(b['size_bytes'] / (1024 * 1024), 2)
                    } for b in old_backups
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def verify_backup_chain(backup_id: str) -> Dict[str, Any]:
        """
        Verifica la catena di backup incrementali.
        
        Args:
            backup_id: ID del backup da verificare
        """
        try:
            backup_chain = _build_backup_chain(backup_id)
            if not backup_chain:
                return {"success": False, "error": f"Backup {backup_id} non trovato"}
            
            verification_results = {
                "chain_valid": True,
                "missing_backups": [],
                "corrupted_backups": [],
                "backup_details": []
            }
            
            for backup_info in backup_chain:
                backup_result = {
                    "backup_id": backup_info['backup_id'],
                    "name": backup_info['name'],
                    "backup_type": backup_info['backup_type'],
                    "created_at": backup_info['created_at'],
                    "exists": False,
                    "hash_valid": False,
                    "size_bytes": backup_info['size_bytes']
                }
                
                # Verifica esistenza file
                if os.path.exists(backup_info['destination']):
                    backup_result["exists"] = True
                    
                    # Verifica hash
                    current_hash = _calculate_file_hash(backup_info['destination'], "sha256")
                    if current_hash == backup_info['hash_sha256']:
                        backup_result["hash_valid"] = True
                    else:
                        verification_results["corrupted_backups"].append(backup_info['backup_id'])
                        verification_results["chain_valid"] = False
                else:
                    verification_results["missing_backups"].append(backup_info['backup_id'])
                    verification_results["chain_valid"] = False
                
                verification_results["backup_details"].append(backup_result)
            
            return {
                "success": True,
                "target_backup_id": backup_id,
                "chain_length": len(backup_chain),
                "verification_results": verification_results,
                "chain_integrity": "Valid" if verification_results["chain_valid"] else "Broken"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Enhanced existing functions
    # ...existing code...

# Enhanced helper functions
def _generate_backup_id(backup_name: str) -> str:
    """Genera un ID univoco per il backup."""
    timestamp = int(time.time())
    name_hash = hashlib.md5(backup_name.encode()).hexdigest()[:8]
    return f"backup_{timestamp}_{name_hash}"

def _scan_directory_enhanced(source_path: str, exclude_patterns: List[str]) -> Dict[str, Dict[str, Any]]:
    """Scansiona directory con informazioni estese sui file."""
    files_info = {}
    
    default_excludes = [
        "*.pyc", "__pycache__", ".git", ".svn", ".DS_Store", 
        "Thumbs.db", "*.tmp", "*.temp", "node_modules", ".env"
    ]
    all_excludes = default_excludes + exclude_patterns
    
    if os.path.isfile(source_path):
        if _should_include_file(source_path, [], all_excludes):
            files_info[source_path] = _get_file_info_enhanced(source_path)
    else:
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                if _should_include_file(file_path, [], all_excludes):
                    relative_path = os.path.relpath(file_path, source_path)
                    files_info[file_path] = _get_file_info_enhanced(file_path, relative_path)
    
    return files_info

def _get_file_info_enhanced(file_path: str, relative_path: str = None) -> Dict[str, Any]:
    """Ottiene informazioni estese su un file."""
    if relative_path is None:
        relative_path = os.path.basename(file_path)
    
    stat_info = os.stat(file_path)
    
    # Calcola hash multipli per file piccoli
    hashes = {}
    if stat_info.st_size < 100 * 1024 * 1024:  # < 100MB
        hashes["sha256"] = _calculate_file_hash(file_path, "sha256")
        hashes["md5"] = _calculate_file_hash(file_path, "md5")
    else:
        # Per file grandi, calcola hash solo del primo chunk
        hashes["sha256_partial"] = _calculate_partial_hash(file_path, "sha256")
    
    return {
        "relative_path": relative_path,
        "absolute_path": file_path,
        "size_bytes": stat_info.st_size,
        "modified_time": stat_info.st_mtime,
        "created_time": stat_info.st_ctime,
        "modified_time_human": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime)),
        "extension": os.path.splitext(file_path)[1].lower(),
        "hashes": hashes,
        "permissions": oct(stat_info.st_mode)[-3:]
    }

def _file_changed(current_info: Dict[str, Any], base_info: Dict[str, Any]) -> bool:
    """Determina se un file è cambiato rispetto al backup base."""
    # Confronta dimensione e tempo di modifica
    if (current_info['size_bytes'] != base_info['size_bytes'] or
        current_info['modified_time'] != base_info['modified_time']):
        return True
    
    # Confronta hash se disponibili
    current_hashes = current_info.get('hashes', {})
    base_hashes = base_info.get('hashes', {})
    
    for hash_type in ['sha256', 'md5']:
        if (hash_type in current_hashes and hash_type in base_hashes and
            current_hashes[hash_type] != base_hashes[hash_type]):
            return True
    
    return False

def _encrypt_file(input_path: str, output_path: str, key: str) -> bool:
    """Crittografa un file con chiave semplice (per demo - usare librerie crypto reali in produzione)."""
    try:
        # Implementazione semplificata XOR per demo
        key_bytes = hashlib.sha256(key.encode()).digest()
        
        with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            while True:
                chunk = infile.read(8192)
                if not chunk:
                    break
                
                encrypted_chunk = bytearray()
                for i, byte in enumerate(chunk):
                    encrypted_chunk.append(byte ^ key_bytes[i % len(key_bytes)])
                
                outfile.write(encrypted_chunk)
        
        return True
    except Exception as e:
        logging.error(f"Errore crittografia: {e}")
        return False

def _decrypt_file(input_path: str, output_path: str, key: str) -> bool:
    """Decrittografa un file."""
    # XOR è simmetrico, quindi usa la stessa funzione
    return _encrypt_file(input_path, output_path, key)

def _calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Calcola hash di un file con algoritmo specificato."""
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Algoritmo hash non supportato: {algorithm}")
    
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def _calculate_partial_hash(file_path: str, algorithm: str = "sha256", chunk_size: int = 1024*1024) -> str:
    """Calcola hash parziale per file grandi."""
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Algoritmo hash non supportato: {algorithm}")
    
    with open(file_path, "rb") as f:
        chunk = f.read(chunk_size)
        hasher.update(chunk)
    
    return hasher.hexdigest()

def _is_safe_path(path: str) -> bool:
    """Verifica che il path sia sicuro (no path traversal)."""
    return not (os.path.isabs(path) or ".." in path or path.startswith("/"))

def _get_backup_info(backup_id: str) -> Optional[Dict[str, Any]]:
    """Ottiene informazioni su un backup dal database."""
    backups = _backup_db.get_backup_history(1000)
    for backup in backups:
        if backup['backup_id'] == backup_id:
            return backup
    return None

def _build_backup_chain(backup_id: str) -> List[Dict[str, Any]]:
    """Costruisce la catena di backup incrementali."""
    chain = []
    current_backup = _get_backup_info(backup_id)
    
    while current_backup:
        chain.append(current_backup)
        
        # Se è un backup completo, ferma la catena
        if current_backup['backup_type'] == 'full':
            break
        
        # Trova il backup base
        base_id = current_backup.get('metadata', {}).get('base_backup_id')
        if not base_id:
            break
        
        current_backup = _get_backup_info(base_id)
    
    return list(reversed(chain))  # Ordine cronologico

def _load_base_backup_files(backup_id: str) -> Dict[str, Dict[str, Any]]:
    """Carica la lista file da un backup precedente."""
    try:
        with sqlite3.connect(_backup_db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM backup_files WHERE backup_id = ?
            """, (backup_id,))
            
            files = {}
            for row in cursor.fetchall():
                files[row['file_path']] = {
                    'relative_path': row['relative_path'],
                    'size_bytes': row['size_bytes'],
                    'modified_time': row['modified_time'],
                    'hashes': {
                        'sha256': row['hash_sha256'],
                        'md5': row['hash_md5']
                    }
                }
            
            return files
    except Exception as e:
        logging.error(f"Errore caricamento file backup base: {e}")
        return {}

def _save_backup_files(backup_id: str, files_info: Dict[str, Dict[str, Any]]):
    """Salva la lista file di un backup nel database."""
    try:
        with sqlite3.connect(_backup_db.db_path) as conn:
            cursor = conn.cursor()
            
            for file_path, file_info in files_info.items():
                hashes = file_info.get('hashes', {})
                cursor.execute("""
                    INSERT INTO backup_files 
                    (backup_id, file_path, relative_path, size_bytes, modified_time, hash_sha256, hash_md5)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    backup_id,
                    file_path,
                    file_info['relative_path'],
                    file_info['size_bytes'],
                    file_info['modified_time'],
                    hashes.get('sha256', ''),
                    hashes.get('md5', '')
                ))
                
    except Exception as e:
        logging.error(f"Errore salvataggio file backup: {e}")

# ...existing helper functions...