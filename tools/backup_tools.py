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
from typing import Dict, List, Any, Optional
import fnmatch

def register_tools(mcp):
    """Registra i tool di backup con l'istanza del server MCP."""
    logging.info("💾 Registrazione tool-set: Backup & Archive Tools")

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

# Helper functions
def _add_files_to_zip(zipf, source_path, include_patterns, exclude_patterns):
    """Aggiunge file a un archivio ZIP con filtri."""
    files_added = 0
    
    if os.path.isfile(source_path):
        if _should_include_file(source_path, include_patterns, exclude_patterns):
            zipf.write(source_path, os.path.basename(source_path))
            files_added += 1
    else:
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                if _should_include_file(file_path, include_patterns, exclude_patterns):
                    arcname = os.path.relpath(file_path, source_path)
                    zipf.write(file_path, arcname)
                    files_added += 1
    
    return files_added

def _add_files_to_tar(tarf, source_path, include_patterns, exclude_patterns):
    """Aggiunge file a un archivio TAR con filtri."""
    files_added = 0
    
    if os.path.isfile(source_path):
        if _should_include_file(source_path, include_patterns, exclude_patterns):
            tarf.add(source_path, os.path.basename(source_path))
            files_added += 1
    else:
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                if _should_include_file(file_path, include_patterns, exclude_patterns):
                    arcname = os.path.relpath(file_path, source_path)
                    tarf.add(file_path, arcname)
                    files_added += 1
    
    return files_added

def _should_include_file(file_path, include_patterns, exclude_patterns):
    """Determina se un file deve essere incluso nell'archivio."""
    filename = os.path.basename(file_path)
    
    # Controlla esclusioni
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(file_path, pattern):
            return False
    
    # Se non ci sono pattern di inclusione, includi tutto (che non è escluso)
    if not include_patterns:
        return True
    
    # Controlla inclusioni
    for pattern in include_patterns:
        if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(file_path, pattern):
            return True
    
    return False

def _calculate_directory_size(directory_path):
    """Calcola la dimensione totale di una directory."""
    total_size = 0
    if os.path.isfile(directory_path):
        return os.path.getsize(directory_path)
    
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

def _calculate_file_hash(file_path):
    """Calcola l'hash SHA256 di un file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _get_file_info(file_path, relative_path=None):
    """Ottiene informazioni dettagliate su un file."""
    if relative_path is None:
        relative_path = os.path.basename(file_path)
    
    stat_info = os.stat(file_path)
    
    return {
        "relative_path": relative_path,
        "absolute_path": file_path,
        "size_bytes": stat_info.st_size,
        "modified_time": stat_info.st_mtime,
        "modified_time_human": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime)),
        "extension": os.path.splitext(file_path)[1].lower(),
        "sha256_hash": _calculate_file_hash(file_path)
    }