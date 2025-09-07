# -*- coding: utf-8 -*-
# tools/archive_tools.py
import logging
import zipfile
import tarfile
import gzip
import os
import tempfile
from datetime import datetime
import json

def register_tools(mcp):
    """Registra i tool per archivi con l'istanza del server MCP."""
    logging.info("📦 Registrazione tool-set: Archive Tools")

    @mcp.tool()
    def create_zip_archive(file_list: str, archive_name: str = "", compression_level: int = 6) -> str:
        """
        Simula la creazione di un archivio ZIP.
        
        Args:
            file_list: Lista file in formato JSON ["file1.txt", "dir/file2.txt"]
            archive_name: Nome dell'archivio (opzionale)
            compression_level: Livello compressione (0-9, 0=nessuna, 9=massima)
        """
        try:
            # Parse file list
            try:
                files = json.loads(file_list)
                if not isinstance(files, list):
                    return "ERRORE: file_list deve essere un array JSON"
            except json.JSONDecodeError:
                return "ERRORE: file_list deve essere un JSON valido"
            
            if not files:
                return "ERRORE: Lista file vuota"
            
            # Valida compression level
            if not 0 <= compression_level <= 9:
                compression_level = 6
            
            # Genera nome archivio se non fornito
            if not archive_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"archive_{timestamp}.zip"
            elif not archive_name.endswith('.zip'):
                archive_name += '.zip'
            
            # Simula analisi file
            total_files = len(files)
            estimated_size = sum(len(f) * 100 for f in files)  # Stima approssimativa
            
            # Analizza struttura directory
            directories = set()
            file_types = {}
            
            for file_path in files:
                # Estrae directory
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    directories.add(dir_path)
                
                # Analizza estensione
                ext = os.path.splitext(file_path)[1].lower()
                if not ext:
                    ext = '[nessuna]'
                file_types[ext] = file_types.get(ext, 0) + 1
            
            # Simula compressione
            compression_ratios = {
                '.txt': 0.4, '.log': 0.3, '.json': 0.5, '.xml': 0.4,
                '.jpg': 0.95, '.png': 0.98, '.gif': 0.96, '.mp4': 0.99,
                '.pdf': 0.9, '.zip': 0.98, '.exe': 0.8, '[nessuna]': 0.6
            }
            
            compressed_size = 0
            for ext, count in file_types.items():
                ratio = compression_ratios.get(ext, 0.7)
                ext_size = (estimated_size // total_files) * count
                compressed_size += int(ext_size * ratio)
            
            # Applica effetto compression level
            level_factor = 1.0 - (compression_level * 0.05)  # Più alto il livello, più compresso
            compressed_size = int(compressed_size * level_factor)
            
            compression_percent = ((estimated_size - compressed_size) / estimated_size * 100) if estimated_size > 0 else 0
            
            result = f"""📦 ARCHIVIO ZIP SIMULATO
Nome archivio: {archive_name}
File inclusi: {total_files}
Directory: {len(directories)}
Livello compressione: {compression_level}/9

DIMENSIONI:
Originale stimata: {estimated_size:,} bytes
Compressa stimata: {compressed_size:,} bytes
Riduzione: {compression_percent:.1f}%

TIPI DI FILE:"""
            
            for ext, count in sorted(file_types.items()):
                result += f"\n{ext:10} {count:3d} file"
            
            result += f"""

DIRECTORY INCLUSE:"""
            if directories:
                for dir_path in sorted(directories)[:10]:
                    result += f"\n  {dir_path}/"
                if len(directories) > 10:
                    result += f"\n  ... e altre {len(directories) - 10} directory"
            else:
                result += "\n  (tutti i file nella root)"
            
            result += f"""

COMANDO EQUIVALENTE:
zip -r -{compression_level} {archive_name} {' '.join(files[:5])}{'...' if len(files) > 5 else ''}

💡 NOTA: Questa è una simulazione. Per creare archivi reali, usa strumenti appropriati del sistema operativo."""
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def analyze_archive_structure(archive_type: str, file_list: str) -> str:
        """
        Analizza la struttura di un archivio.
        
        Args:
            archive_type: Tipo archivio (zip, tar, tar.gz, tar.bz2)
            file_list: Lista file nell'archivio in formato JSON
        """
        try:
            # Parse file list
            try:
                files = json.loads(file_list)
                if not isinstance(files, list):
                    return "ERRORE: file_list deve essere un array JSON"
            except json.JSONDecodeError:
                return "ERRORE: file_list deve essere un JSON valido"
            
            if not files:
                return "ERRORE: Lista file vuota"
            
            # Analizza struttura
            analysis = {
                'total_files': len(files),
                'directories': set(),
                'file_types': {},
                'depth_levels': {},
                'largest_files': [],
                'empty_dirs': set(),
                'duplicates': {}
            }
            
            # Analizza ogni file
            for file_path in files:
                # Directory
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    parts = dir_path.split('/')
                    for i in range(len(parts)):
                        analysis['directories'].add('/'.join(parts[:i+1]))
                
                # Profondità
                depth = len(file_path.split('/')) - 1
                analysis['depth_levels'][depth] = analysis['depth_levels'].get(depth, 0) + 1
                
                # Tipo file
                filename = os.path.basename(file_path)
                ext = os.path.splitext(filename)[1].lower()
                if not ext:
                    ext = '[nessuna estensione]'
                analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
                
                # Possibili duplicati (per nome)
                if filename in analysis['duplicates']:
                    analysis['duplicates'][filename].append(file_path)
                else:
                    analysis['duplicates'][filename] = [file_path]
            
            # Filtra duplicati reali
            real_duplicates = {name: paths for name, paths in analysis['duplicates'].items() if len(paths) > 1}
            
            # Caratteristiche per tipo archivio
            archive_info = {
                'zip': {
                    'compression': 'Deflate/Store',
                    'encryption': 'AES-256 supportata',
                    'metadata': 'Timestamp, attributi file',
                    'max_size': '4GB per file (ZIP64 per maggiori)'
                },
                'tar': {
                    'compression': 'Nessuna (solo archiviazione)',
                    'encryption': 'Non supportata nativamente',
                    'metadata': 'UNIX permissions, ownership, timestamp',
                    'max_size': 'Praticamente illimitata'
                },
                'tar.gz': {
                    'compression': 'Gzip',
                    'encryption': 'Non supportata nativamente',
                    'metadata': 'UNIX permissions, ownership, timestamp',
                    'max_size': 'Praticamente illimitata'
                },
                'tar.bz2': {
                    'compression': 'Bzip2 (migliore compressione)',
                    'encryption': 'Non supportata nativamente',
                    'metadata': 'UNIX permissions, ownership, timestamp',
                    'max_size': 'Praticamente illimitata'
                }
            }
            
            info = archive_info.get(archive_type, {})
            
            result = f"""📊 ANALISI STRUTTURA ARCHIVIO
Tipo: {archive_type.upper()}
File totali: {analysis['total_files']:,}
Directory: {len(analysis['directories']):,}

CARATTERISTICHE FORMATO:
Compressione: {info.get('compression', 'N/A')}
Crittografia: {info.get('encryption', 'N/A')}
Metadata: {info.get('metadata', 'N/A')}
Dimensione max: {info.get('max_size', 'N/A')}

STRUTTURA DIRECTORY:
Profondità massima: {max(analysis['depth_levels'].keys()) if analysis['depth_levels'] else 0}"""
            
            for depth in sorted(analysis['depth_levels'].keys()):
                count = analysis['depth_levels'][depth]
                result += f"\nLivello {depth}: {count} file"
            
            result += f"""

TIPI DI FILE:"""
            for ext, count in sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = count / analysis['total_files'] * 100
                result += f"\n{ext:20} {count:5d} file ({percentage:5.1f}%)"
            
            if len(analysis['file_types']) > 10:
                result += f"\n... e altri {len(analysis['file_types']) - 10} tipi"
            
            # Directory principali
            if analysis['directories']:
                top_dirs = {}
                for dir_path in analysis['directories']:
                    top_level = dir_path.split('/')[0]
                    top_dirs[top_level] = top_dirs.get(top_level, 0) + 1
                
                result += f"""

DIRECTORY PRINCIPALI:"""
                for dir_name, count in sorted(top_dirs.items(), key=lambda x: x[1], reverse=True)[:5]:
                    result += f"\n{dir_name:20} {count:3d} sottodirectory"
            
            # Duplicati
            if real_duplicates:
                result += f"""

POSSIBILI DUPLICATI ({len(real_duplicates)}):"""
                for filename, paths in list(real_duplicates.items())[:5]:
                    result += f"\n{filename}: {len(paths)} occorrenze"
                    for path in paths[:3]:
                        result += f"\n  - {path}"
                    if len(paths) > 3:
                        result += f"\n  ... e altre {len(paths) - 3}"
                
                if len(real_duplicates) > 5:
                    result += f"\n... e altri {len(real_duplicates) - 5} file duplicati"
            
            # Raccomandazioni
            result += f"""

💡 RACCOMANDAZIONI:"""
            
            recommendations = []
            if analysis['total_files'] > 10000:
                recommendations.append("Archivio molto grande: considera di dividere in più parti")
            
            if len(real_duplicates) > 10:
                recommendations.append("Molti duplicati: verifica file ridondanti prima dell'archiviazione")
            
            if max(analysis['depth_levels'].keys()) > 8:
                recommendations.append("Struttura molto profonda: considera di riorganizzare le directory")
            
            text_files = analysis['file_types'].get('.txt', 0) + analysis['file_types'].get('.log', 0)
            if text_files > analysis['total_files'] * 0.7:
                recommendations.append("Molti file di testo: formato con compressione alta consigliato (tar.bz2)")
            
            media_files = sum(analysis['file_types'].get(ext, 0) for ext in ['.jpg', '.png', '.mp4', '.mp3'])
            if media_files > analysis['total_files'] * 0.5:
                recommendations.append("Molti file media: compressione aggiuntiva poco efficace")
            
            if not recommendations:
                recommendations.append("Struttura archivio normale, nessuna ottimizzazione particolare necessaria")
            
            result += '\n'.join(f"\n- {rec}" for rec in recommendations)
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def compare_archive_formats(file_types: str, total_size_mb: int = 100) -> str:
        """
        Confronta diversi formati di archivio per efficienza.
        
        Args:
            file_types: Tipi di file predominanti (text, media, mixed, code, binary)
            total_size_mb: Dimensione totale stimata in MB
        """
        try:
            # Definisce caratteristiche dei formati
            formats = {
                'ZIP': {
                    'compression': {'text': 0.3, 'media': 0.95, 'mixed': 0.6, 'code': 0.4, 'binary': 0.7},
                    'speed': {'compress': 'Media', 'decompress': 'Veloce'},
                    'features': ['Compressione selettiva', 'Crittografia AES', 'Aggiornamento file'],
                    'compatibility': 'Universale',
                    'use_cases': ['Distribuzione software', 'Backup personali', 'Archivi web']
                },
                'TAR': {
                    'compression': {'text': 1.0, 'media': 1.0, 'mixed': 1.0, 'code': 1.0, 'binary': 1.0},
                    'speed': {'compress': 'Velocissima', 'decompress': 'Velocissima'},
                    'features': ['Preserva permissions UNIX', 'Streaming', 'Concatenazione'],
                    'compatibility': 'UNIX/Linux primariamente',
                    'use_cases': ['Backup sistema', 'Distribuzione codice', 'Container Docker']
                },
                'TAR.GZ': {
                    'compression': {'text': 0.35, 'media': 0.97, 'mixed': 0.65, 'code': 0.45, 'binary': 0.75},
                    'speed': {'compress': 'Media', 'decompress': 'Media'},
                    'features': ['Buona compressione', 'Streaming', 'Permissions UNIX'],
                    'compatibility': 'UNIX/Linux, Windows con tool',
                    'use_cases': ['Distribuzione software Linux', 'Backup di testo', 'Codice sorgente']
                },
                'TAR.BZ2': {
                    'compression': {'text': 0.25, 'media': 0.96, 'mixed': 0.55, 'code': 0.35, 'binary': 0.65},
                    'speed': {'compress': 'Lenta', 'decompress': 'Lenta'},
                    'features': ['Ottima compressione', 'Recupero errori', 'Permissions UNIX'],
                    'compatibility': 'UNIX/Linux, Windows con tool',
                    'use_cases': ['Archivi a lungo termine', 'Backup con spazio limitato']
                },
                'TAR.XZ': {
                    'compression': {'text': 0.2, 'media': 0.94, 'mixed': 0.5, 'code': 0.3, 'binary': 0.6},
                    'speed': {'compress': 'Molto lenta', 'decompress': 'Media'},
                    'features': ['Compressione eccellente', 'Multithreading', 'Integrità'],
                    'compatibility': 'Moderno UNIX/Linux',
                    'use_cases': ['Distribuzione software', 'Archivi critici', 'Kernel Linux']
                },
                '7Z': {
                    'compression': {'text': 0.15, 'media': 0.92, 'mixed': 0.45, 'code': 0.25, 'binary': 0.55},
                    'speed': {'compress': 'Lenta', 'decompress': 'Media'},
                    'features': ['Compressione superiore', 'Crittografia AES', 'Volumi multipli'],
                    'compatibility': 'Windows primariamente, tool disponibili',
                    'use_cases': ['Massima compressione', 'Archivi protetti', 'Backup critici']
                }
            }
            
            file_types = file_types.lower()
            if file_types not in ['text', 'media', 'mixed', 'code', 'binary']:
                file_types = 'mixed'
            
            result = f"""📊 CONFRONTO FORMATI ARCHIVIO
Tipo contenuto: {file_types.title()}
Dimensione originale: {total_size_mb} MB

ANALISI COMPRESSIONE:"""
            
            # Calcola dimensioni compresse
            format_results = []
            for format_name, props in formats.items():
                compressed_ratio = props['compression'][file_types]
                compressed_size = total_size_mb * compressed_ratio
                saved_space = total_size_mb - compressed_size
                saved_percent = (1 - compressed_ratio) * 100
                
                format_results.append({
                    'name': format_name,
                    'size': compressed_size,
                    'saved': saved_space,
                    'percent': saved_percent,
                    'props': props
                })
            
            # Ordina per dimensione compressa
            format_results.sort(key=lambda x: x['size'])
            
            for i, fmt in enumerate(format_results, 1):
                result += f"""
{i}. {fmt['name']:8} {fmt['size']:6.1f} MB ({fmt['percent']:4.1f}% riduzione)
   Velocità: Compr.{fmt['props']['speed']['compress']:10} | Decompr.{fmt['props']['speed']['decompress']}
   Compatibilità: {fmt['props']['compatibility']}"""
            
            result += f"""

CARATTERISTICHE DETTAGLIATE:"""
            
            for fmt in format_results:
                result += f"""

{fmt['name']}:
  Dimensione: {fmt['size']:.1f} MB (risparmio: {fmt['saved']:.1f} MB)
  Velocità compressione: {fmt['props']['speed']['compress']}
  Velocità decompressione: {fmt['props']['speed']['decompress']}
  Funzionalità: {', '.join(fmt['props']['features'])}
  Casi d'uso: {', '.join(fmt['props']['use_cases'])}"""
            
            # Raccomandazioni
            result += f"""

🎯 RACCOMANDAZIONI:

Per {file_types}:"""
            
            best_compression = format_results[0]
            fastest = min(format_results, key=lambda x: 0 if x['props']['speed']['compress'] == 'Velocissima' else 1 if x['props']['speed']['compress'] == 'Veloce' else 2)
            most_compatible = next((f for f in format_results if 'Universale' in f['props']['compatibility']), format_results[0])
            
            result += f"""
Massima compressione: {best_compression['name']} ({best_compression['percent']:.1f}% riduzione)
Massima velocità: {fastest['name']} ({fastest['props']['speed']['compress']} compressione)
Massima compatibilità: {most_compatible['name']} ({most_compatible['props']['compatibility']})"""
            
            # Suggerimenti specifici per tipo
            suggestions = {
                'text': "Per file di testo: TAR.XZ o 7Z per massima compressione, TAR.GZ per bilanciamento",
                'media': "Per file media: ZIP o TAR per velocità (compressione poco efficace su media già compressi)",
                'code': "Per codice sorgente: TAR.BZ2 o TAR.XZ, ZIP per distribuzioni cross-platform",
                'binary': "Per binari: 7Z per massima compressione, ZIP per compatibilità",
                'mixed': "Per contenuti misti: ZIP per versatilità, TAR.GZ per sistemi UNIX"
            }
            
            result += f"""

💡 SUGGERIMENTO SPECIFICO:
{suggestions[file_types]}

⚡ CONSIDERAZIONI AGGIUNTIVE:
- Per archivi >1GB: considera formati con supporto streaming (TAR.*)
- Per archivi sicuri: ZIP con AES o 7Z con crittografia
- Per backup automatici: TAR.GZ per velocità e compressione bilanciata
- Per distribuzione: ZIP per compatibilità universale"""
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_archive_script(archive_type: str, source_dir: str, archive_name: str, options: str = "") -> str:
        """
        Genera script per creare archivi con comandi di sistema.
        
        Args:
            archive_type: Tipo archivio (zip, tar, tar.gz, tar.bz2, tar.xz, 7z)
            source_dir: Directory sorgente
            archive_name: Nome archivio di destinazione
            options: Opzioni aggiuntive (exclude, compression_level, etc.)
        """
        try:
            # Parse opzioni
            opts = {}
            if options:
                for opt in options.split(','):
                    if '=' in opt:
                        key, value = opt.split('=', 1)
                        opts[key.strip()] = value.strip()
            
            exclude_patterns = opts.get('exclude', '').split(';') if opts.get('exclude') else []
            compression_level = opts.get('compression_level', '6')
            password = opts.get('password', '')
            
            # Genera comandi
            commands = {
                'zip': {
                    'command': f"zip -r -{compression_level} {archive_name} {source_dir}",
                    'with_exclude': f"zip -r -{compression_level} {archive_name} {source_dir} {' '.join('-x ' + pattern for pattern in exclude_patterns)}",
                    'with_password': f"zip -r -{compression_level} -P {password} {archive_name} {source_dir}",
                    'description': "Archivio ZIP con compressione Deflate"
                },
                'tar': {
                    'command': f"tar -cf {archive_name} {source_dir}",
                    'with_exclude': f"tar --exclude-from=exclude.txt -cf {archive_name} {source_dir}",
                    'with_password': f"tar -cf - {source_dir} | gpg -c > {archive_name}.gpg",
                    'description': "Archivio TAR senza compressione"
                },
                'tar.gz': {
                    'command': f"tar -czf {archive_name} {source_dir}",
                    'with_exclude': f"tar --exclude-from=exclude.txt -czf {archive_name} {source_dir}",
                    'with_password': f"tar -czf - {source_dir} | gpg -c > {archive_name}.gpg",
                    'description': "Archivio TAR con compressione Gzip"
                },
                'tar.bz2': {
                    'command': f"tar -cjf {archive_name} {source_dir}",
                    'with_exclude': f"tar --exclude-from=exclude.txt -cjf {archive_name} {source_dir}",
                    'with_password': f"tar -cjf - {source_dir} | gpg -c > {archive_name}.gpg",
                    'description': "Archivio TAR con compressione Bzip2"
                },
                'tar.xz': {
                    'command': f"tar -cJf {archive_name} {source_dir}",
                    'with_exclude': f"tar --exclude-from=exclude.txt -cJf {archive_name} {source_dir}",
                    'with_password': f"tar -cJf - {source_dir} | gpg -c > {archive_name}.gpg",
                    'description': "Archivio TAR con compressione XZ"
                },
                '7z': {
                    'command': f"7z a -mx={compression_level} {archive_name} {source_dir}",
                    'with_exclude': f"7z a -mx={compression_level} {archive_name} {source_dir} {' '.join('-xr!' + pattern for pattern in exclude_patterns)}",
                    'with_password': f"7z a -mx={compression_level} -p{password} {archive_name} {source_dir}",
                    'description': "Archivio 7Z con compressione LZMA"
                }
            }
            
            if archive_type not in commands:
                available = ', '.join(commands.keys())
                return f"ERRORE: Tipo '{archive_type}' non supportato. Disponibili: {available}"
            
            cmd_info = commands[archive_type]
            
            # Script bash completo
            bash_script = f"""#!/bin/bash
# Script di archiviazione automatica
# Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e  # Termina in caso di errore

# Variabili
SOURCE_DIR="{source_dir}"
ARCHIVE_NAME="{archive_name}"
ARCHIVE_TYPE="{archive_type}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🚀 Avvio creazione archivio..."
echo "Tipo: $ARCHIVE_TYPE"
echo "Sorgente: $SOURCE_DIR"
echo "Destinazione: $ARCHIVE_NAME"
echo "Timestamp: $TIMESTAMP"

# Verifica prerequisiti
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ ERRORE: Directory sorgente non trovata: $SOURCE_DIR"
    exit 1
fi

# Controlla spazio disco
AVAILABLE_SPACE=$(df . | tail -1 | awk '{{print $4}}')
echo "📊 Spazio disponibile: ${{AVAILABLE_SPACE}}K"

# Crea backup del nome archivio se esiste
if [ -f "$ARCHIVE_NAME" ]; then
    echo "⚠️  Archivio esistente trovato, creo backup..."
    mv "$ARCHIVE_NAME" "${{ARCHIVE_NAME}}.backup.$TIMESTAMP"
fi

echo "📦 Creazione archivio in corso..."
START_TIME=$(date +%s)

# Comando principale
{cmd_info['command']}

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $? -eq 0 ]; then
    ARCHIVE_SIZE=$(ls -lh "$ARCHIVE_NAME" | awk '{{print $5}}')
    echo "✅ Archivio creato con successo!"
    echo "📊 Dimensione: $ARCHIVE_SIZE"
    echo "⏱️  Durata: ${{DURATION}}s"
else
    echo "❌ Errore durante la creazione dell'archivio"
    exit 1
fi"""
            
            # Script PowerShell per Windows
            powershell_script = f"""# Script PowerShell per archiviazione
# Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

$ErrorActionPreference = "Stop"

# Variabili
$SourceDir = "{source_dir}"
$ArchiveName = "{archive_name}"
$ArchiveType = "{archive_type}"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "🚀 Avvio creazione archivio..." -ForegroundColor Green
Write-Host "Tipo: $ArchiveType"
Write-Host "Sorgente: $SourceDir"
Write-Host "Destinazione: $ArchiveName"

# Verifica prerequisiti
if (-not (Test-Path $SourceDir)) {{
    Write-Host "❌ ERRORE: Directory sorgente non trovata: $SourceDir" -ForegroundColor Red
    exit 1
}}

# Backup archivio esistente
if (Test-Path $ArchiveName) {{
    Write-Host "⚠️  Archivio esistente trovato, creo backup..."
    Move-Item $ArchiveName "${{ArchiveName}}.backup.$Timestamp"
}}

Write-Host "📦 Creazione archivio in corso..."
$StartTime = Get-Date

try {{"""
            
            if archive_type == 'zip':
                powershell_script += f"""
    Compress-Archive -Path $SourceDir -DestinationPath $ArchiveName -CompressionLevel Optimal"""
            else:
                powershell_script += f"""
    # Per {archive_type}, usa tool esterni come 7-Zip
    & 7z a -mx={compression_level} $ArchiveName $SourceDir"""
            
            powershell_script += f"""
    
    $EndTime = Get-Date
    $Duration = ($EndTime - $StartTime).TotalSeconds
    $ArchiveSize = (Get-Item $ArchiveName).Length
    
    Write-Host "✅ Archivio creato con successo!" -ForegroundColor Green
    Write-Host "📊 Dimensione: $($ArchiveSize / 1MB) MB"
    Write-Host "⏱️  Durata: ${{Duration}}s"
}} catch {{
    Write-Host "❌ Errore durante la creazione dell'archivio: $_" -ForegroundColor Red
    exit 1
}}"""
            
            result = f"""📜 SCRIPT ARCHIVIAZIONE GENERATO
Tipo archivio: {archive_type.upper()}
Sorgente: {source_dir}
Destinazione: {archive_name}
Descrizione: {cmd_info['description']}

COMANDO BASE:
{cmd_info['command']}"""
            
            if exclude_patterns:
                result += f"""

COMANDO CON ESCLUSIONI:
{cmd_info['with_exclude']}

FILE ESCLUSIONI (exclude.txt):"""
                for pattern in exclude_patterns:
                    result += f"\n{pattern}"
            
            if password:
                result += f"""

COMANDO CON PASSWORD:
{cmd_info['with_password']}"""
            
            result += f"""

SCRIPT BASH COMPLETO:
{bash_script}

SCRIPT POWERSHELL:
{powershell_script}

💡 ISTRUZIONI USO:
1. Salva lo script in un file (.sh per Linux/Mac, .ps1 per Windows)
2. Rendi eseguibile: chmod +x script.sh (Linux/Mac)
3. Esegui: ./script.sh o PowerShell -ExecutionPolicy Bypass -File script.ps1
4. Verifica l'archivio creato
5. Testa l'estrazione prima dell'uso in produzione"""
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"