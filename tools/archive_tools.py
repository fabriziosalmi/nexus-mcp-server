# -*- coding: utf-8 -*-
# tools/archive_tools.py
import logging
import os
import tempfile
from datetime import datetime
import json
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple

def register_tools(mcp):
    """Registra i tool per archivi con l'istanza del server MCP."""
    logging.info("📦 Registrazione tool-set: Archive Tools")

    @mcp.tool()
    def create_zip_archive(file_list: str, archive_name: str = "", compression_level: int = 6) -> str:
        """
        Simula la creazione di un archivio ZIP con analisi avanzata.
        
        Args:
            file_list: Lista file in formato JSON ["file1.txt", "dir/file2.txt"]
            archive_name: Nome dell'archivio (opzionale)
            compression_level: Livello compressione (0-9, 0=nessuna, 9=massima)
        """
        try:
            # Parse e valida file list
            try:
                files = json.loads(file_list)
                if not isinstance(files, list):
                    return "❌ ERRORE: file_list deve essere un array JSON"
            except json.JSONDecodeError as e:
                return f"❌ ERRORE: JSON non valido - {str(e)}"
            
            if not files:
                return "❌ ERRORE: Lista file vuota"
            
            # Valida nomi file
            invalid_files = []
            for file_path in files:
                if not isinstance(file_path, str):
                    invalid_files.append(f"{file_path} (non è una stringa)")
                elif not file_path.strip():
                    invalid_files.append("(percorso vuoto)")
                elif len(file_path) > 260:  # Limite Windows
                    invalid_files.append(f"{file_path[:50]}... (percorso troppo lungo)")
            
            if invalid_files:
                return f"❌ ERRORE: File non validi trovati:\n" + "\n".join(f"- {f}" for f in invalid_files[:5])
            
            # Valida compression level
            if not isinstance(compression_level, int) or not 0 <= compression_level <= 9:
                compression_level = 6
                logging.warning(f"Livello compressione non valido, uso default: {compression_level}")
            
            # Genera nome archivio se non fornito
            if not archive_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"archive_{timestamp}.zip"
            elif not archive_name.lower().endswith('.zip'):
                archive_name += '.zip'
            
            # Analisi avanzata file
            analysis = _analyze_file_structure(files)
            
            # Calcola dimensioni stimate
            size_estimation = _estimate_compression(files, compression_level, "zip")
            
            # Genera informazioni di sicurezza
            security_analysis = _analyze_security_risks(files)
            
            # Tempo stimato di creazione
            estimated_time = _estimate_processing_time(analysis['total_size'], "zip", compression_level)
            
            result = f"""📦 ARCHIVIO ZIP SIMULATO
┌─────────────────────────────────────────────────────────
│ Nome archivio: {archive_name}
│ File inclusi: {analysis['total_files']:,}
│ Directory: {len(analysis['directories']):,}
│ Livello compressione: {compression_level}/9
│ Tempo stimato: {estimated_time}
│ Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
└─────────────────────────────────────────────────────────

📊 DIMENSIONI:
Originale stimata: {analysis['total_size']:,} bytes ({analysis['total_size']/1024/1024:.1f} MB)
Compressa stimata: {size_estimation['compressed_size']:,} bytes ({size_estimation['compressed_size']/1024/1024:.1f} MB)
Riduzione: {size_estimation['compression_ratio']:.1f}%
Efficienza: {size_estimation['efficiency']}

📋 TIPI DI FILE:"""
            
            for ext, info in sorted(analysis['file_types'].items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
                count = info['count']
                size_mb = info['size'] / 1024 / 1024
                result += f"\n{ext:15} {count:4d} file ({size_mb:6.1f} MB)"
            
            if len(analysis['file_types']) > 10:
                result += f"\n... e altri {len(analysis['file_types']) - 10} tipi"
            
            result += f"""

📁 STRUTTURA DIRECTORY:
Profondità massima: {analysis['max_depth']} livelli
Directory vuote: {analysis['empty_dirs']}"""
            
            if analysis['top_directories']:
                result += f"\nDirectory principali:"
                for dir_name, count in analysis['top_directories'][:5]:
                    result += f"\n  {dir_name}: {count} file"
            
            # Aggiungi analisi sicurezza se ci sono problemi
            if security_analysis['risks']:
                result += f"""

⚠️  ANALISI SICUREZZA:"""
                for risk in security_analysis['risks'][:3]:
                    result += f"\n- {risk}"
                if len(security_analysis['risks']) > 3:
                    result += f"\n... e altri {len(security_analysis['risks']) - 3} problemi"
            
            result += f"""

🔧 COMANDO EQUIVALENTE:
# Comando base
zip -r -{compression_level} {archive_name} {' '.join(f'"{f}"' for f in files[:3])}{'...' if len(files) > 3 else ''}

# Con esclusioni tipiche
zip -r -{compression_level} {archive_name} . -x "*.tmp" "*.log" ".DS_Store" "Thumbs.db"

# Con progress e test
zip -r -{compression_level} {archive_name} . && zip -T {archive_name}

💡 SUGGERIMENTI OTTIMIZZAZIONE:
{chr(10).join(f'• {tip}' for tip in size_estimation['optimization_tips'])}"""
            
            return result
            
        except Exception as e:
            logging.error(f"Errore in create_zip_archive: {e}")
            return f"❌ ERRORE INTERNO: {str(e)}"

    @mcp.tool()
    def analyze_archive_structure(archive_type: str, file_list: str) -> str:
        """
        Analizza la struttura di un archivio con controlli avanzati.
        
        Args:
            archive_type: Tipo archivio (zip, tar, tar.gz, tar.bz2, tar.xz, 7z, rar)
            file_list: Lista file nell'archivio in formato JSON
        """
        try:
            # Parse e valida file list
            try:
                files = json.loads(file_list)
                if not isinstance(files, list):
                    return "❌ ERRORE: file_list deve essere un array JSON"
            except json.JSONDecodeError as e:
                return f"❌ ERRORE: JSON non valido - {str(e)}"
            
            if not files:
                return "❌ ERRORE: Lista file vuota"
            
            # Valida tipo archivio
            supported_types = ['zip', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', '7z', 'rar', 'tar.lz4', 'tar.zst']
            if archive_type.lower() not in supported_types:
                return f"❌ ERRORE: Tipo '{archive_type}' non supportato. Disponibili: {', '.join(supported_types)}"
            
            # Analisi completa struttura
            analysis = _analyze_file_structure(files)
            
            # Analisi duplicati avanzata
            duplicates_analysis = _analyze_duplicates(files)
            
            # Analisi percorsi problematici
            path_analysis = _analyze_path_issues(files)
            
            # Caratteristiche dettagliate per tipo archivio
            format_details = _get_archive_format_details(archive_type.lower())
            
            result = f"""📊 ANALISI STRUTTURA ARCHIVIO
┌─────────────────────────────────────────────────────────
│ Tipo: {archive_type.upper()}
│ File totali: {analysis['total_files']:,}
│ Directory: {len(analysis['directories']):,}
│ Dimensione totale: {analysis['total_size']/1024/1024:.1f} MB
│ Analizzato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
└─────────────────────────────────────────────────────────

📦 CARATTERISTICHE FORMATO:
Compressione: {format_details['compression']}
Crittografia: {format_details['encryption']}
Metadata: {format_details['metadata']}
Dimensione max file: {format_details['max_file_size']}
Supporto Unicode: {format_details['unicode_support']}
Streaming: {format_details['streaming_support']}

📁 STRUTTURA DIRECTORY:
Profondità massima: {analysis['max_depth']} livelli
Directory vuote: {analysis['empty_dirs']}
Percorsi lunghi: {path_analysis['long_paths']} (>100 caratteri)
Caratteri speciali: {path_analysis['special_chars']} file"""
            
            # Distribuzione per profondità
            if analysis['depth_distribution']:
                result += f"\n\nDistribuzione per livello:"
                for depth in sorted(analysis['depth_distribution'].keys()):
                    count = analysis['depth_distribution'][depth]
                    result += f"\n  Livello {depth}: {count:,} file"
            
            result += f"""

📄 TIPI DI FILE (Top 15):"""
            for ext, info in sorted(analysis['file_types'].items(), key=lambda x: x[1]['count'], reverse=True)[:15]:
                count = info['count']
                size_mb = info['size'] / 1024 / 1024
                percentage = count / analysis['total_files'] * 100
                result += f"\n{ext:20} {count:6,} file ({percentage:5.1f}%) - {size_mb:8.1f} MB"
            
            # Directory principali con statistiche
            if analysis['top_directories']:
                result += f"""

📂 DIRECTORY PRINCIPALI:"""
                for dir_name, count in analysis['top_directories'][:10]:
                    result += f"\n{dir_name:30} {count:5,} file"
            
            # Analisi duplicati dettagliata
            if duplicates_analysis['duplicates']:
                result += f"""

🔄 DUPLICATI RILEVATI ({len(duplicates_analysis['duplicates'])}):
Spazio potenzialmente recuperabile: {duplicates_analysis['waste_size']/1024/1024:.1f} MB"""
                
                for filename, paths in list(duplicates_analysis['duplicates'].items())[:5]:
                    result += f"\n{filename} ({len(paths)} copie):"
                    for path in paths[:3]:
                        result += f"\n  • {path}"
                    if len(paths) > 3:
                        result += f"\n  • ... e altre {len(paths) - 3} copie"
                
                if len(duplicates_analysis['duplicates']) > 5:
                    result += f"\n... e altri {len(duplicates_analysis['duplicates']) - 5} file duplicati"
            
            # Problemi nei percorsi
            if path_analysis['issues']:
                result += f"""

⚠️  PROBLEMI NEI PERCORSI:"""
                for issue in path_analysis['issues'][:5]:
                    result += f"\n• {issue}"
                if len(path_analysis['issues']) > 5:
                    result += f"\n• ... e altri {len(path_analysis['issues']) - 5} problemi"
            
            # Raccomandazioni intelligenti
            recommendations = _generate_archive_recommendations(analysis, duplicates_analysis, path_analysis, archive_type)
            
            result += f"""

💡 RACCOMANDAZIONI:"""
            for rec in recommendations[:8]:
                result += f"\n• {rec}"
            
            # Comandi utili per il tipo di archivio
            useful_commands = _get_useful_commands(archive_type, analysis)
            result += f"""

🔧 COMANDI UTILI:"""
            for cmd_desc, cmd in useful_commands.items():
                result += f"\n{cmd_desc}:\n  {cmd}"
            
            return result
            
        except Exception as e:
            logging.error(f"Errore in analyze_archive_structure: {e}")
            return f"❌ ERRORE INTERNO: {str(e)}"

    @mcp.tool()
    def estimate_archive_performance(source_size_mb: float, archive_type: str, compression_level: int = 6, 
                                   cpu_cores: int = 4, storage_type: str = "ssd") -> str:
        """
        Stima le prestazioni di creazione/estrazione di un archivio.
        
        Args:
            source_size_mb: Dimensione sorgente in MB
            archive_type: Tipo archivio (zip, tar.gz, tar.bz2, tar.xz, 7z)
            compression_level: Livello compressione (0-9)
            cpu_cores: Numero core CPU disponibili
            storage_type: Tipo storage (hdd, ssd, nvme, network)
        """
        try:
            if source_size_mb <= 0:
                return "❌ ERRORE: Dimensione deve essere positiva"
            
            if not 1 <= cpu_cores <= 128:
                cpu_cores = 4
                
            if storage_type not in ['hdd', 'ssd', 'nvme', 'network']:
                storage_type = 'ssd'
            
            # Fattori di prestazione per tipo storage
            storage_factors = {
                'hdd': {'read': 100, 'write': 80, 'seek': 0.1},      # MB/s
                'ssd': {'read': 500, 'write': 400, 'seek': 1.0},     # MB/s
                'nvme': {'read': 3000, 'write': 2500, 'seek': 1.0},  # MB/s
                'network': {'read': 50, 'write': 30, 'seek': 0.01}    # MB/s (1Gbps network)
            }
            
            # Caratteristiche algoritmi compressione
            compression_algos = {
                'zip': {
                    'cpu_intensive': 0.3, 'parallel': False, 'memory_mb': 50,
                    'compression_ratios': [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4, 0.35, 0.3]
                },
                'tar': {
                    'cpu_intensive': 0.1, 'parallel': True, 'memory_mb': 20,
                    'compression_ratios': [1.0] * 10  # No compression
                },
                'tar.gz': {
                    'cpu_intensive': 0.4, 'parallel': False, 'memory_mb': 100,
                    'compression_ratios': [1.0, 0.85, 0.75, 0.65, 0.55, 0.45, 0.4, 0.35, 0.3, 0.25]
                },
                'tar.bz2': {
                    'cpu_intensive': 0.8, 'parallel': True, 'memory_mb': 200,
                    'compression_ratios': [1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2]
                },
                'tar.xz': {
                    'cpu_intensive': 0.9, 'parallel': True, 'memory_mb': 400,
                    'compression_ratios': [1.0, 0.75, 0.65, 0.55, 0.45, 0.35, 0.3, 0.25, 0.2, 0.15]
                },
                '7z': {
                    'cpu_intensive': 0.95, 'parallel': True, 'memory_mb': 600,
                    'compression_ratios': [1.0, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1]
                }
            }
            
            if archive_type not in compression_algos:
                available = ', '.join(compression_algos.keys())
                return f"❌ ERRORE: Tipo '{archive_type}' non supportato. Disponibili: {available}"
            
            algo = compression_algos[archive_type]
            storage = storage_factors[storage_type]
            
            # Calcola tempo di compressione
            compression_ratio = algo['compression_ratios'][min(compression_level, 9)]
            compressed_size_mb = source_size_mb * compression_ratio
            
            # Tempo CPU per compressione
            cpu_factor = algo['cpu_intensive'] * (compression_level / 9.0)
            base_cpu_time = source_size_mb * cpu_factor / 100  # secondi per MB
            
            # Parallelizzazione
            if algo['parallel'] and cpu_cores > 1:
                parallel_factor = min(cpu_cores, 8) * 0.7  # Non scala linearmente
                cpu_time = base_cpu_time / parallel_factor
            else:
                cpu_time = base_cpu_time
            
            # Tempo I/O
            read_time = source_size_mb / storage['read']
            write_time = compressed_size_mb / storage['write']
            io_time = read_time + write_time
            
            # Tempo totale (il maggiore tra CPU e I/O)
            total_time = max(cpu_time, io_time)
            
            # Stima estrazione (generalmente più veloce)
            extraction_time = total_time * 0.3  # Estrazione ~30% del tempo di compressione
            
            # Memoria richiesta
            memory_required = algo['memory_mb'] + (source_size_mb * 0.1)  # 10% della dimensione sorgente
            
            # Throughput
            compression_throughput = source_size_mb / total_time if total_time > 0 else 0
            extraction_throughput = source_size_mb / extraction_time if extraction_time > 0 else 0
            
            def format_time(seconds):
                if seconds < 60:
                    return f"{seconds:.1f}s"
                elif seconds < 3600:
                    return f"{seconds/60:.1f}m"
                else:
                    return f"{seconds/3600:.1f}h"
            
            result = f"""⚡ STIMA PRESTAZIONI ARCHIVIO
┌─────────────────────────────────────────────────────────
│ Tipo: {archive_type.upper()}
│ Dimensione sorgente: {source_size_mb:,.1f} MB
│ Livello compressione: {compression_level}/9
│ CPU cores: {cpu_cores}
│ Storage: {storage_type.upper()}
│ Stimato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
└─────────────────────────────────────────────────────────

📊 RISULTATI COMPRESSIONE:
Dimensione compressa: {compressed_size_mb:,.1f} MB
Riduzione dimensione: {((source_size_mb - compressed_size_mb) / source_size_mb * 100):.1f}%
Tempo stimato: {format_time(total_time)}
Throughput: {compression_throughput:.1f} MB/s
Memoria richiesta: {memory_required:.0f} MB

📈 BREAKDOWN TEMPI COMPRESSIONE:
Elaborazione CPU: {format_time(cpu_time)} ({'Limitante' if cpu_time >= io_time else 'OK'})
I/O Storage: {format_time(io_time)} ({'Limitante' if io_time > cpu_time else 'OK'})
  • Lettura: {format_time(read_time)}
  • Scrittura: {format_time(write_time)}

📤 ESTRAZIONE:
Tempo stimato: {format_time(extraction_time)}
Throughput: {extraction_throughput:.1f} MB/s"""
            
            # Confronti con altri formati
            comparison_results = []
            for other_type, other_algo in compression_algos.items():
                if other_type != archive_type:
                    other_ratio = other_algo['compression_ratios'][compression_level]
                    other_cpu_factor = other_algo['cpu_intensive'] * (compression_level / 9.0)
                    other_base_time = source_size_mb * other_cpu_factor / 100
                    
                    if other_algo['parallel'] and cpu_cores > 1:
                        other_cpu_time = other_base_time / (min(cpu_cores, 8) * 0.7)
                    else:
                        other_cpu_time = other_base_time
                    
                    other_compressed = source_size_mb * other_ratio
                    other_write_time = other_compressed / storage['write']
                    other_total_time = max(other_cpu_time, read_time + other_write_time)
                    
                    comparison_results.append({
                        'type': other_type,
                        'time': other_total_time,
                        'size': other_compressed,
                        'ratio': other_ratio
                    })
            
            comparison_results.sort(key=lambda x: x['time'])
            
            result += f"""

🆚 CONFRONTO CON ALTRI FORMATI:"""
            for i, comp in enumerate(comparison_results[:4], 1):
                time_diff = comp['time'] - total_time
                size_diff = comp['size'] - compressed_size_mb
                result += f"""
{i}. {comp['type'].upper()}: {format_time(comp['time'])} ({'+' if time_diff > 0 else ''}{format_time(abs(time_diff))})
   Dimensione: {comp['size']:.1f} MB ({'+' if size_diff > 0 else ''}{size_diff:.1f} MB)"""
            
            # Raccomandazioni
            recommendations = []
            
            if cpu_time > io_time * 2:
                recommendations.append("CPU è il collo di bottiglia - considera più core o livello compressione minore")
            elif io_time > cpu_time * 2:
                recommendations.append(f"Storage è il collo di bottleneck - considera upgrade a storage più veloce")
            
            if memory_required > 8000:
                recommendations.append("Utilizzo memoria alto - monitor RAM durante l'operazione")
            
            if total_time > 3600:
                recommendations.append("Operazione lunga - considera divisione in archivi più piccoli")
            
            if compression_ratio > 0.9:
                recommendations.append("Compressione poco efficace - file già compressi o binari")
            
            if not recommendations:
                recommendations.append("Configurazione bilanciata per il carico di lavoro")
            
            result += f"""

💡 RACCOMANDAZIONI:"""
            for rec in recommendations:
                result += f"\n• {rec}"
            
            # Comandi ottimizzati
            optimized_commands = _get_optimized_commands(archive_type, compression_level, cpu_cores)
            result += f"""

🔧 COMANDI OTTIMIZZATI:
{optimized_commands}

📝 NOTE:
• Tempi basati su hardware di riferimento
• Prestazioni reali possono variare del ±30%
• Test su campione piccolo prima di operazioni massive
• Monitor risorse sistema durante l'esecuzione"""
            
            return result
            
        except Exception as e:
            logging.error(f"Errore in estimate_archive_performance: {e}")
            return f"❌ ERRORE INTERNO: {str(e)}"

def _analyze_file_structure(files: List[str]) -> Dict[str, Any]:
    """Analizza la struttura dei file forniti."""
    analysis = {
        'total_files': len(files),
        'total_size': 0,
        'directories': set(),
        'file_types': {},
        'max_depth': 0,
        'empty_dirs': 0,
        'depth_distribution': {},
        'top_directories': []
    }
    
    # Simula dimensioni file basate su estensione e nome
    size_estimates = {
        '.txt': (1024, 50000), '.log': (500, 100000), '.json': (512, 10000),
        '.py': (1000, 20000), '.js': (800, 15000), '.html': (2000, 50000),
        '.jpg': (100000, 5000000), '.png': (50000, 2000000), '.gif': (20000, 500000),
        '.mp4': (10000000, 500000000), '.mp3': (3000000, 10000000),
        '.pdf': (100000, 10000000), '.doc': (50000, 5000000),
        '.zip': (1000000, 100000000), '.exe': (500000, 50000000),
        '': (1000, 10000)  # File senza estensione
    }
    
    dir_file_count = {}
    
    for file_path in files:
        # Profondità
        depth = len(file_path.split('/')) - 1
        analysis['max_depth'] = max(analysis['max_depth'], depth)
        analysis['depth_distribution'][depth] = analysis['depth_distribution'].get(depth, 0) + 1
        
        # Directory
        dir_path = os.path.dirname(file_path)
        if dir_path:
            analysis['directories'].add(dir_path)
            top_dir = dir_path.split('/')[0]
            dir_file_count[top_dir] = dir_file_count.get(top_dir, 0) + 1
        
        # Tipo file e dimensione stimata
        ext = os.path.splitext(file_path)[1].lower()
        if not ext:
            ext = '[nessuna]'
        
        min_size, max_size = size_estimates.get(ext, size_estimates[''])
        # Stima dimensione basata su lunghezza nome file
        estimated_size = min_size + (len(os.path.basename(file_path)) * 100)
        estimated_size = min(estimated_size, max_size)
        
        if ext not in analysis['file_types']:
            analysis['file_types'][ext] = {'count': 0, 'size': 0}
        
        analysis['file_types'][ext]['count'] += 1
        analysis['file_types'][ext]['size'] += estimated_size
        analysis['total_size'] += estimated_size
    
    # Top directory per numero di file
    analysis['top_directories'] = sorted(dir_file_count.items(), key=lambda x: x[1], reverse=True)
    
    return analysis

def _analyze_duplicates(files: List[str]) -> Dict[str, Any]:
    """Analizza i file duplicati basandosi sui nomi."""
    duplicates = {}
    total_waste = 0
    
    for file_path in files:
        filename = os.path.basename(file_path)
        if filename in duplicates:
            duplicates[filename].append(file_path)
        else:
            duplicates[filename] = [file_path]
    
    # Filtra solo i duplicati reali
    real_duplicates = {name: paths for name, paths in duplicates.items() if len(paths) > 1}
    
    # Stima spazio sprecato
    for filename, paths in real_duplicates.items():
        # Stima dimensione file
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.png', '.mp4']:
            avg_size = 1000000  # 1MB per media
        elif ext in ['.txt', '.log']:
            avg_size = 10000    # 10KB per testo
        else:
            avg_size = 50000    # 50KB default
        
        total_waste += avg_size * (len(paths) - 1)  # Spazio per copie extra
    
    return {
        'duplicates': real_duplicates,
        'waste_size': total_waste,
        'duplicate_count': len(real_duplicates)
    }

def _analyze_path_issues(files: List[str]) -> Dict[str, Any]:
    """Analizza problemi nei percorsi dei file."""
    issues = []
    long_paths = 0
    special_chars = 0
    
    for file_path in files:
        # Percorsi lunghi
        if len(file_path) > 100:
            long_paths += 1
            if len(file_path) > 200:
                issues.append(f"Percorso molto lungo: {file_path[:50]}...")
        
        # Caratteri speciali problematici
        problematic_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in file_path for char in problematic_chars):
            special_chars += 1
            issues.append(f"Caratteri speciali in: {os.path.basename(file_path)}")
        
        # Nomi con spazi multipli o caratteri unicode
        if '  ' in file_path:
            issues.append(f"Spazi multipli in: {os.path.basename(file_path)}")
        
        # File che iniziano con punto (nascosti)
        if os.path.basename(file_path).startswith('.') and len(os.path.basename(file_path)) > 1:
            issues.append(f"File nascosto: {os.path.basename(file_path)}")
    
    return {
        'issues': issues[:10],  # Limita a 10 problemi
        'long_paths': long_paths,
        'special_chars': special_chars
    }

def _estimate_compression(files: List[str], compression_level: int, archive_type: str) -> Dict[str, Any]:
    """Stima la compressione per i file forniti."""
    # Analizza tipi di file per stimare compressione
    analysis = _analyze_file_structure(files)
    total_size = analysis['total_size']
    
    # Fattori di compressione per tipo file
    compression_factors = {
        '.txt': 0.3, '.log': 0.25, '.json': 0.4, '.xml': 0.35, '.html': 0.4,
        '.py': 0.35, '.js': 0.4, '.css': 0.3, '.sql': 0.3,
        '.jpg': 0.98, '.png': 0.95, '.gif': 0.97, '.bmp': 0.1,
        '.mp4': 0.99, '.mp3': 0.98, '.avi': 0.95,
        '.pdf': 0.9, '.doc': 0.8, '.docx': 0.7,
        '.zip': 0.98, '.rar': 0.98, '.7z': 0.98,
        '.exe': 0.85, '.dll': 0.8,
        '[nessuna]': 0.6
    }
    
    # Calcola dimensione compressa
    compressed_size = 0
    for ext, info in analysis['file_types'].items():
        factor = compression_factors.get(ext, 0.7)
        
        # Ajusta per livello compressione
        level_adjustment = 1.0 - (compression_level * 0.05)
        adjusted_factor = factor * level_adjustment
        
        compressed_size += info['size'] * adjusted_factor
    
    compression_ratio = ((total_size - compressed_size) / total_size * 100) if total_size > 0 else 0
    
    # Determina efficienza
    if compression_ratio > 70:
        efficiency = "Eccellente"
    elif compression_ratio > 50:
        efficiency = "Buona"
    elif compression_ratio > 30:
        efficiency = "Media"
    elif compression_ratio > 10:
        efficiency = "Bassa"
    else:
        efficiency = "Scarsa"
    
    # Suggerimenti ottimizzazione
    optimization_tips = []
    
    text_ratio = sum(info['size'] for ext, info in analysis['file_types'].items() 
                    if ext in ['.txt', '.log', '.json', '.py', '.js']) / total_size
    
    if text_ratio > 0.7:
        optimization_tips.append("Molti file di testo: considera tar.xz o 7z per massima compressione")
    
    media_ratio = sum(info['size'] for ext, info in analysis['file_types'].items() 
                     if ext in ['.jpg', '.png', '.mp4', '.mp3']) / total_size
    
    if media_ratio > 0.5:
        optimization_tips.append("Molti file media: compressione aggiuntiva poco efficace, usa ZIP store o TAR")
    
    if compression_level < 5 and text_ratio > 0.3:
        optimization_tips.append("Livello compressione basso per file di testo: considera di aumentarlo")
    
    if len(files) > 10000:
        optimization_tips.append("Molti file: considera compressione solida (7z) per migliori risultati")
    
    if not optimization_tips:
        optimization_tips.append("Configurazione appropriata per il tipo di contenuto")
    
    return {
        'compressed_size': int(compressed_size),
        'compression_ratio': compression_ratio,
        'efficiency': efficiency,
        'optimization_tips': optimization_tips
    }

def _estimate_processing_time(size_bytes: int, archive_type: str, compression_level: int) -> str:
    """Stima il tempo di processing."""
    # Velocità base in MB/s per diversi formati
    base_speeds = {
        'zip': 50, 'tar': 200, 'tar.gz': 30, 'tar.bz2': 15, 'tar.xz': 10, '7z': 8
    }
    
    speed = base_speeds.get(archive_type, 50)
    
    # Ajusta per livello compressione
    speed_factor = 1.0 - (compression_level * 0.08)
    adjusted_speed = speed * speed_factor
    
    size_mb = size_bytes / 1024 / 1024
    time_seconds = size_mb / adjusted_speed
    
    if time_seconds < 60:
        return f"{time_seconds:.0f} secondi"
    elif time_seconds < 3600:
        return f"{time_seconds/60:.1f} minuti"
    else:
        return f"{time_seconds/3600:.1f} ore"

def _analyze_security_risks(files: List[str]) -> Dict[str, Any]:
    """Analizza rischi di sicurezza nei file."""
    risks = []
    
    # Cerca file potenzialmente pericolosi
    dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.js', '.jar']
    sensitive_names = ['password', 'secret', 'key', 'token', 'credential']
    
    for file_path in files:
        filename = os.path.basename(file_path).lower()
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in dangerous_extensions:
            risks.append(f"File eseguibile: {os.path.basename(file_path)}")
        
        if any(sensitive in filename for sensitive in sensitive_names):
            risks.append(f"Nome file sensibile: {os.path.basename(file_path)}")
        
        # Percorsi che tentano directory traversal
        if '..' in file_path or file_path.startswith('/'):
            risks.append(f"Percorso sospetto: {file_path}")
    
    return {'risks': risks[:5]}  # Limita a 5 rischi

def _get_archive_format_details(archive_type: str) -> Dict[str, str]:
    """Restituisce dettagli per il formato archivio."""
    formats = {
        'zip': {
            'compression': 'Deflate, Store, Bzip2',
            'encryption': 'Traditional, AES-128/192/256',
            'metadata': 'Timestamp, attributi DOS/Unix',
            'max_file_size': '4GB (16EB con ZIP64)',
            'unicode_support': 'Sì (UTF-8)',
            'streaming_support': 'Limitato'
        },
        'tar': {
            'compression': 'Nessuna (container)',
            'encryption': 'No (usa GPG esternamente)',
            'metadata': 'POSIX (owner, group, permissions)',
            'max_file_size': '8GB (estensioni GNU)',
            'unicode_support': 'Sì',
            'streaming_support': 'Eccellente'
        },
        'tar.gz': {
            'compression': 'Gzip (Deflate)',
            'encryption': 'No (usa GPG esternamente)',
            'metadata': 'POSIX completo',
            'max_file_size': '8GB',
            'unicode_support': 'Sì',
            'streaming_support': 'Buono'
        },
        'tar.bz2': {
            'compression': 'Bzip2 (Burrows-Wheeler)',
            'encryption': 'No (usa GPG esternamente)',
            'metadata': 'POSIX completo',
            'max_file_size': '8GB',
            'unicode_support': 'Sì',
            'streaming_support': 'Limitato'
        },
        'tar.xz': {
            'compression': 'LZMA2',
            'encryption': 'No (usa GPG esternamente)',
            'metadata': 'POSIX completo',
            'max_file_size': '8GB',
            'unicode_support': 'Sì',
            'streaming_support': 'Limitato'
        },
        '7z': {
            'compression': 'LZMA, LZMA2, PPMd, BZip2',
            'encryption': 'AES-256',
            'metadata': 'Esteso (NTFS, Unix)',
            'max_file_size': '16EB',
            'unicode_support': 'Sì (UTF-16)',
            'streaming_support': 'No'
        },
        'rar': {
            'compression': 'RAR, RAR5',
            'encryption': 'AES-128/256',
            'metadata': 'Esteso',
            'max_file_size': '8EB',
            'unicode_support': 'Sì',
            'streaming_support': 'Limitato'
        }
    }
    
    return formats.get(archive_type, {
        'compression': 'Sconosciuto',
        'encryption': 'Sconosciuto',
        'metadata': 'Sconosciuto',
        'max_file_size': 'Sconosciuto',
        'unicode_support': 'Sconosciuto',
        'streaming_support': 'Sconosciuto'
    })

def _generate_archive_recommendations(analysis: Dict, duplicates: Dict, path_analysis: Dict, archive_type: str) -> List[str]:
    """Genera raccomandazioni intelligenti."""
    recommendations = []
    
    # Basato su dimensioni
    if analysis['total_files'] > 50000:
        recommendations.append("Archivio molto grande: considera divisione in volumi o formato con compressione solida")
    
    # Basato su duplicati
    if duplicates['duplicate_count'] > 20:
        recommendations.append(f"Molti duplicati ({duplicates['duplicate_count']}): rimuovi file ridondanti per risparmiare spazio")
    
    # Basato su profondità
    if analysis['max_depth'] > 10:
        recommendations.append("Struttura molto profonda: considera riorganizzazione per compatibilità")
    
    # Basato su tipi file
    text_files = sum(info['count'] for ext, info in analysis['file_types'].items() 
                    if ext in ['.txt', '.log', '.json', '.py'])
    if text_files > analysis['total_files'] * 0.8:
        recommendations.append("Prevalentemente file di testo: usa tar.xz o 7z per massima compressione")
    
    # Basato su problemi percorsi
    if path_analysis['special_chars'] > 10:
        recommendations.append("Molti caratteri speciali: verifica compatibilità cross-platform")
    
    # Raccomandazioni specifiche per formato
    if archive_type == 'zip' and analysis['total_size'] > 4000000000:  # 4GB
        recommendations.append("Dimensione >4GB: considera ZIP64 o altri formati")
    
    if not recommendations:
        recommendations.append("Struttura archivio ottimale per il formato scelto")
    
    return recommendations

def _get_useful_commands(archive_type: str, analysis: Dict) -> Dict[str, str]:
    """Restituisce comandi utili per il tipo di archivio."""
    commands = {}
    
    if archive_type == 'zip':
        commands['Crea con esclusioni'] = 'zip -r archive.zip . -x "*.tmp" "*.log"'
        commands['Testa integrità'] = 'zip -T archive.zip'
        commands['Lista contenuto'] = 'unzip -l archive.zip'
        commands['Estrai in directory'] = 'unzip archive.zip -d destination/'
    
    elif archive_type.startswith('tar'):
        commands['Crea con progress'] = f'tar -czf archive.{archive_type.split(".", 1)[1] if "." in archive_type else "tar"} . --checkpoint=1000'
        commands['Lista contenuto'] = f'tar -tzf archive.{archive_type.split(".", 1)[1] if "." in archive_type else "tar"}'
        commands['Estrai in directory'] = f'tar -xzf archive.{archive_type.split(".", 1)[1] if "." in archive_type else "tar"} -C destination/'
        commands['Verifica integrità'] = f'tar -tzf archive.{archive_type.split(".", 1)[1] if "." in archive_type else "tar"} > /dev/null'
    
    elif archive_type == '7z':
        commands['Crea con password'] = '7z a -p archive.7z .'
        commands['Testa integrità'] = '7z t archive.7z'
        commands['Lista dettagliata'] = '7z l archive.7z'
        commands['Estrai con percorsi'] = '7z x archive.7z -odestination/'
    
    return commands

def _get_optimized_commands(archive_type: str, compression_level: int, cpu_cores: int) -> str:
    """Genera comandi ottimizzati per le prestazioni."""
    commands = []
    
    if archive_type == 'zip':
        commands.append(f'zip -r -{compression_level} archive.zip . -x "*.tmp" "*.log"')
        if cpu_cores > 1:
            commands.append('# ZIP non supporta parallelizzazione nativa')
    
    elif archive_type == 'tar.gz':
        if cpu_cores > 1:
            commands.append(f'tar -I "gzip -{compression_level}" -cf archive.tar.gz .')
        else:
            commands.append(f'tar -czf archive.tar.gz .')
    
    elif archive_type == 'tar.bz2':
        if cpu_cores > 1:
            commands.append(f'tar -I "pbzip2 -{compression_level} -p{cpu_cores}" -cf archive.tar.bz2 .')
        else:
            commands.append(f'tar -cjf archive.tar.bz2 .')
    
    elif archive_type == 'tar.xz':
        if cpu_cores > 1:
            commands.append(f'tar -I "xz -{compression_level} -T{cpu_cores}" -cf archive.tar.xz .')
        else:
            commands.append(f'tar -cJf archive.tar.xz .')
    
    elif archive_type == '7z':
        commands.append(f'7z a -mx={compression_level} -mmt{cpu_cores} archive.7z .')
    
    return '\n'.join(commands)