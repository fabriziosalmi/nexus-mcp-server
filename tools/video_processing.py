# -*- coding: utf-8 -*-
# tools/video_processing.py
import base64
import io
import logging
import json
import struct
from typing import Dict, List, Optional, Any, Tuple

def register_tools(mcp):
    """Registra i tool di elaborazione video con l'istanza del server MCP."""
    logging.info("🎬 Registrazione tool-set: Video Processing Tools")

    @mcp.tool()
    def analyze_video_metadata(video_base64: str) -> Dict[str, Any]:
        """
        Analizza metadata di un file video da base64 (analisi header base).
        
        Args:
            video_base64: File video codificato in base64
        """
        try:
            # Decodifica base64
            video_data = base64.b64decode(video_base64)
            file_size_kb = len(video_data) / 1024
            
            # Analizza header per riconoscere formato
            format_info = {}
            
            # MP4/M4V
            if video_data[4:8] == b'ftyp':
                format_info["format"] = "MP4/M4V"
                format_info["container"] = "MP4"
                
                # Cerca brand del formato MP4
                brand = video_data[8:12]
                format_info["brand"] = brand.decode('ascii', errors='ignore')
                
            # AVI
            elif video_data[:4] == b'RIFF' and video_data[8:12] == b'AVI ':
                format_info["format"] = "AVI"
                format_info["container"] = "AVI"
                
                # Cerca informazioni AVI header
                try:
                    # Cerca 'avih' chunk per main header
                    avih_pos = video_data.find(b'avih')
                    if avih_pos > 0:
                        # Leggi alcune proprietà di base
                        header_start = avih_pos + 8
                        if len(video_data) > header_start + 32:
                            microsec_per_frame = struct.unpack('<I', video_data[header_start:header_start+4])[0]
                            if microsec_per_frame > 0:
                                format_info["estimated_fps"] = round(1000000 / microsec_per_frame, 2)
                except:
                    pass
                    
            # MOV (QuickTime)
            elif b'moov' in video_data[:50] or b'mdat' in video_data[:50]:
                format_info["format"] = "MOV/QuickTime"
                format_info["container"] = "MOV"
                
            # WebM
            elif video_data[:4] == b'\x1a\x45\xdf\xa3':
                format_info["format"] = "WebM/MKV"
                format_info["container"] = "Matroska/WebM"
                
            # FLV
            elif video_data[:3] == b'FLV':
                format_info["format"] = "FLV"
                format_info["container"] = "FLV"
                format_info["version"] = video_data[3]
                
            else:
                format_info["format"] = "Sconosciuto"
                format_info["container"] = "Non identificato"
            
            # Analisi dimensioni approssimativa per MP4
            estimated_duration = None
            estimated_bitrate = None
            
            if format_info.get("format") == "MP4/M4V":
                # Cerca 'mvhd' (movie header) per durata
                mvhd_pos = video_data.find(b'mvhd')
                if mvhd_pos > 0:
                    try:
                        header_start = mvhd_pos + 8
                        if len(video_data) > header_start + 20:
                            # Versione 0: timescale a offset 12, duration a offset 16
                            timescale = struct.unpack('>I', video_data[header_start+12:header_start+16])[0]
                            duration_ticks = struct.unpack('>I', video_data[header_start+16:header_start+20])[0]
                            if timescale > 0:
                                estimated_duration = duration_ticks / timescale
                                estimated_bitrate = (file_size_kb * 8) / estimated_duration if estimated_duration > 0 else None
                    except:
                        pass
            
            # Ricerca di stream video/audio (pattern base)
            has_video_stream = False
            has_audio_stream = False
            
            # Cerca codec comuni
            codec_patterns = {
                b'avc1': 'H.264/AVC',
                b'h264': 'H.264',
                b'hevc': 'H.265/HEVC',
                b'vp08': 'VP8',
                b'vp09': 'VP9',
                b'mp4a': 'AAC Audio',
                b'mp3 ': 'MP3 Audio'
            }
            
            detected_codecs = []
            for pattern, codec_name in codec_patterns.items():
                if pattern in video_data:
                    detected_codecs.append(codec_name)
                    if 'Audio' not in codec_name:
                        has_video_stream = True
                    else:
                        has_audio_stream = True
            
            return {
                "file_analysis": {
                    "file_size_kb": round(file_size_kb, 2),
                    "file_size_mb": round(file_size_kb / 1024, 2),
                    "format_info": format_info,
                    "analysis_method": "header_inspection"
                },
                "stream_info": {
                    "has_video_stream": has_video_stream,
                    "has_audio_stream": has_audio_stream,
                    "detected_codecs": detected_codecs
                },
                "estimated_properties": {
                    "duration_seconds": round(estimated_duration, 2) if estimated_duration else None,
                    "estimated_bitrate_kbps": round(estimated_bitrate, 2) if estimated_bitrate else None,
                    "fps": format_info.get("estimated_fps")
                },
                "limitations": [
                    "Analisi limitata a header inspection",
                    "Per analisi completa servono librerie come ffmpeg/opencv",
                    "Alcune proprietà sono stimate"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def create_video_thumbnail_placeholder(width: int = 640, height: int = 360, color: str = "#1a1a1a", text: str = "Video Thumbnail") -> Dict[str, Any]:
        """
        Crea un placeholder immagine per thumbnail video.
        
        Args:
            width: Larghezza in pixel (default: 640)
            height: Altezza in pixel (default: 360)
            color: Colore di sfondo hex (default: #1a1a1a)
            text: Testo da visualizzare (default: "Video Thumbnail")
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Limiti di sicurezza
            width = max(100, min(width, 1920))
            height = max(100, min(height, 1080))
            
            # Converte colore hex a RGB
            if color.startswith('#'):
                color = color[1:]
            try:
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
                bg_color = (r, g, b)
            except:
                bg_color = (26, 26, 26)  # Fallback grigio scuro
            
            # Crea immagine
            image = Image.new('RGB', (width, height), bg_color)
            draw = ImageDraw.Draw(image)
            
            # Calcola colore testo (contrasto)
            brightness = (r + g + b) / 3
            text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)
            
            # Prova a usare font di sistema, fallback a font di default
            try:
                font_size = max(16, min(width, height) // 20)
                font = ImageFont.load_default()  # Font di default PIL
            except:
                font = None
            
            # Disegna testo centrato
            if text:
                # Calcola dimensioni testo
                if font:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                else:
                    # Stima per font di default
                    text_width = len(text) * 8
                    text_height = 14
                
                # Centra testo
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                draw.text((x, y), text, fill=text_color, font=font)
            
            # Aggiungi bordo decorativo
            border_color = tuple(min(255, c + 40) for c in bg_color)
            draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=2)
            
            # Aggiungi icona play semplificata al centro
            center_x, center_y = width // 2, height // 2
            play_size = min(width, height) // 8
            
            # Triangolo play
            play_points = [
                (center_x - play_size//2, center_y - play_size//2),
                (center_x - play_size//2, center_y + play_size//2),
                (center_x + play_size//2, center_y)
            ]
            draw.polygon(play_points, fill=text_color)
            
            # Converti a base64
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='PNG', optimize=True)
            thumbnail_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "thumbnail_base64": thumbnail_base64,
                "properties": {
                    "width": width,
                    "height": height,
                    "background_color": f"#{color}",
                    "text": text,
                    "format": "PNG",
                    "file_size_kb": round(len(output_buffer.getvalue()) / 1024, 2)
                },
                "note": "Thumbnail placeholder generato - non estratto da video reale"
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "PIL (Pillow) non installato"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_video_structure(video_base64: str) -> Dict[str, Any]:
        """
        Analizza struttura di un file video MP4 (atom/box analysis).
        
        Args:
            video_base64: File video MP4 codificato in base64
        """
        try:
            # Decodifica base64
            video_data = base64.b64decode(video_base64)
            
            if len(video_data) < 8:
                return {"success": False, "error": "File troppo piccolo per essere un video valido"}
            
            # Verifica che sia MP4
            if video_data[4:8] != b'ftyp':
                return {
                    "success": False,
                    "error": "Non è un file MP4 valido. Usa analyze_video_metadata per altri formati."
                }
            
            # Parser MP4 box structure
            boxes = []
            pos = 0
            
            while pos < len(video_data) - 8:
                try:
                    # Leggi box header
                    size = struct.unpack('>I', video_data[pos:pos+4])[0]
                    box_type = video_data[pos+4:pos+8]
                    
                    if size == 0:  # Box si estende fino alla fine
                        size = len(video_data) - pos
                    elif size == 1:  # 64-bit size
                        if pos + 16 <= len(video_data):
                            size = struct.unpack('>Q', video_data[pos+8:pos+16])[0]
                            pos += 8  # Offset aggiuntivo per 64-bit size
                        else:
                            break
                    
                    if size < 8 or pos + size > len(video_data):
                        break
                    
                    box_info = {
                        "type": box_type.decode('ascii', errors='replace'),
                        "size_bytes": size,
                        "offset": pos
                    }
                    
                    # Analisi specifica per alcuni box
                    if box_type == b'ftyp':
                        # File Type Box
                        if size >= 16:
                            major_brand = video_data[pos+8:pos+12].decode('ascii', errors='replace')
                            minor_version = struct.unpack('>I', video_data[pos+12:pos+16])[0]
                            box_info["major_brand"] = major_brand
                            box_info["minor_version"] = minor_version
                            
                    elif box_type == b'moov':
                        # Movie Box - contiene metadata
                        box_info["description"] = "Movie metadata container"
                        
                    elif box_type == b'mdat':
                        # Media Data Box - contiene dati stream
                        box_info["description"] = "Media data (video/audio streams)"
                        
                    elif box_type == b'mvhd':
                        # Movie Header
                        if size >= 24:
                            try:
                                version = video_data[pos+8]
                                if version == 0:
                                    timescale = struct.unpack('>I', video_data[pos+20:pos+24])[0]
                                    duration = struct.unpack('>I', video_data[pos+24:pos+28])[0]
                                    box_info["timescale"] = timescale
                                    box_info["duration_ticks"] = duration
                                    if timescale > 0:
                                        box_info["duration_seconds"] = round(duration / timescale, 2)
                            except:
                                pass
                                
                    boxes.append(box_info)
                    pos += size
                    
                except (struct.error, UnicodeDecodeError):
                    break
            
            # Analizza struttura
            total_boxes = len(boxes)
            total_size = sum(box["size_bytes"] for box in boxes)
            
            # Trova box principali
            has_moov = any(box["type"] == "moov" for box in boxes)
            has_mdat = any(box["type"] == "mdat" for box in boxes)
            
            mdat_boxes = [box for box in boxes if box["type"] == "mdat"]
            media_data_size = sum(box["size_bytes"] for box in mdat_boxes)
            
            # Calcola statistiche
            box_types = {}
            for box in boxes:
                box_type = box["type"]
                box_types[box_type] = box_types.get(box_type, 0) + 1
            
            return {
                "file_structure": {
                    "total_boxes": total_boxes,
                    "total_analyzed_bytes": total_size,
                    "file_size_bytes": len(video_data),
                    "structure_valid": has_moov and has_mdat
                },
                "box_analysis": {
                    "boxes": boxes[:20],  # Prime 20 box per non sovraccaricare output
                    "box_type_counts": box_types,
                    "media_data_size_bytes": media_data_size,
                    "media_data_percentage": round((media_data_size / len(video_data)) * 100, 2)
                },
                "video_validity": {
                    "has_movie_metadata": has_moov,
                    "has_media_data": has_mdat,
                    "is_streamable": boxes[0]["type"] in ["ftyp", "moov"] if boxes else False,
                    "structure_type": "Fast-start" if boxes and boxes[0]["type"] == "moov" else "Progressive"
                },
                "limitations": [
                    "Analisi limitata a struttura MP4 box",
                    "Non analizza contenuto stream video/audio",
                    "Per analisi codec/frame servono tool specializzati"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def estimate_video_properties(video_base64: str) -> Dict[str, Any]:
        """
        Stima proprietà video da analisi euristica.
        
        Args:
            video_base64: File video codificato in base64
        """
        try:
            # Decodifica base64
            video_data = base64.b64decode(video_base64)
            file_size_mb = len(video_data) / (1024 * 1024)
            
            # Euristica basata su dimensione file e pattern comuni
            estimated_props = {}
            
            # Stima durata basata su dimensione (molto approssimativa)
            # Presuppone video di qualità media
            if file_size_mb < 5:
                estimated_props["duration_range"] = "< 30 secondi"
                estimated_props["likely_content"] = "Clip breve/GIF animata"
            elif file_size_mb < 25:
                estimated_props["duration_range"] = "30 secondi - 5 minuti"
                estimated_props["likely_content"] = "Video clip/trailer"
            elif file_size_mb < 100:
                estimated_props["duration_range"] = "5-20 minuti"
                estimated_props["likely_content"] = "Video medio/tutorial"
            else:
                estimated_props["duration_range"] = "> 20 minuti"
                estimated_props["likely_content"] = "Video lungo/film"
            
            # Analisi pattern per codec/qualità
            codec_indicators = {
                b'avc1': {'codec': 'H.264', 'quality': 'Standard'},
                b'h264': {'codec': 'H.264', 'quality': 'Standard'},
                b'hevc': {'codec': 'H.265', 'quality': 'Alta efficienza'},
                b'vp08': {'codec': 'VP8', 'quality': 'Web optimized'},
                b'vp09': {'codec': 'VP9', 'quality': 'Alta efficienza web'}
            }
            
            detected_codecs = []
            for pattern, info in codec_indicators.items():
                if pattern in video_data:
                    detected_codecs.append(info)
            
            # Stima risoluzione basata su dimensione file
            if file_size_mb < 10:
                estimated_props["likely_resolution"] = "480p o inferiore"
            elif file_size_mb < 50:
                estimated_props["likely_resolution"] = "720p"
            elif file_size_mb < 200:
                estimated_props["likely_resolution"] = "1080p"
            else:
                estimated_props["likely_resolution"] = "1080p+ o 4K"
            
            # Stima bitrate (molto approssimativa)
            if detected_codecs and file_size_mb > 0:
                # Assume durata media basata su size
                assumed_duration_minutes = max(1, file_size_mb / 10)  # Euristica
                estimated_bitrate = (file_size_mb * 8 * 1024) / (assumed_duration_minutes * 60)
                estimated_props["estimated_bitrate_kbps"] = round(estimated_bitrate, 0)
            
            # Analisi compressione
            compression_indicators = []
            if b'mp4a' in video_data:
                compression_indicators.append("Audio AAC")
            if b'mp3' in video_data:
                compression_indicators.append("Audio MP3")
            
            # Qualità generale stimata
            quality_score = 0
            if any(codec['codec'] in ['H.265', 'VP9'] for codec in detected_codecs):
                quality_score += 2
            elif any(codec['codec'] in ['H.264', 'VP8'] for codec in detected_codecs):
                quality_score += 1
            
            if file_size_mb > 20:
                quality_score += 1
            if file_size_mb > 100:
                quality_score += 1
            
            quality_rating = ["Bassa", "Media", "Alta", "Molto Alta"][min(quality_score, 3)]
            
            return {
                "file_info": {
                    "size_mb": round(file_size_mb, 2),
                    "size_category": "Piccolo" if file_size_mb < 10 else "Medio" if file_size_mb < 100 else "Grande"
                },
                "estimated_properties": estimated_props,
                "codec_analysis": {
                    "detected_codecs": detected_codecs,
                    "compression_indicators": compression_indicators,
                    "modern_codecs_used": any(codec['codec'] in ['H.265', 'VP9'] for codec in detected_codecs)
                },
                "quality_assessment": {
                    "estimated_quality": quality_rating,
                    "quality_factors": [
                        "Codec moderni" if any(codec['codec'] in ['H.265', 'VP9'] for codec in detected_codecs) else "Codec standard",
                        f"Dimensione file: {round(file_size_mb, 1)}MB",
                        f"Probabilmente {estimated_props.get('likely_resolution', 'risoluzione media')}"
                    ]
                },
                "disclaimer": [
                    "Stime basate su euristica e pattern di file",
                    "Proprietà reali possono differire significativamente",
                    "Per dati precisi usa tool di analisi video specializzati"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def create_video_info_summary(video_base64: str) -> Dict[str, Any]:
        """
        Crea un riassunto completo delle informazioni video disponibili.
        
        Args:
            video_base64: File video codificato in base64
        """
        try:
            # Combina analisi da altri tool
            metadata_result = analyze_video_metadata(video_base64)
            structure_result = analyze_video_structure(video_base64) if not metadata_result.get("success") == False else None
            properties_result = estimate_video_properties(video_base64)
            
            # Riassunto unificato
            summary = {
                "file_overview": {
                    "file_size_mb": round(len(base64.b64decode(video_base64)) / (1024 * 1024), 2),
                    "analysis_timestamp": "2024-current",
                    "analysis_methods": ["metadata_extraction", "structure_analysis", "heuristic_estimation"]
                }
            }
            
            # Aggiungi risultati se disponibili
            if not metadata_result.get("success") == False:
                summary["format_info"] = metadata_result.get("file_analysis", {})
                summary["stream_info"] = metadata_result.get("stream_info", {})
            
            if structure_result and not structure_result.get("success") == False:
                summary["structure_info"] = structure_result.get("video_validity", {})
                summary["box_count"] = structure_result.get("file_structure", {}).get("total_boxes", 0)
            
            if not properties_result.get("success") == False:
                summary["estimated_properties"] = properties_result.get("estimated_properties", {})
                summary["quality_info"] = properties_result.get("quality_assessment", {})
            
            # Raccomandazioni basate su analisi
            recommendations = []
            
            file_size_mb = summary["file_overview"]["file_size_mb"]
            if file_size_mb > 100:
                recommendations.append("Considera compressione per ridurre dimensioni")
            
            if summary.get("format_info", {}).get("format") == "AVI":
                recommendations.append("Considera conversione a MP4 per migliore compatibilità")
            
            if not summary.get("stream_info", {}).get("has_audio_stream"):
                recommendations.append("Video senza audio - considera aggiunta traccia audio")
            
            summary["recommendations"] = recommendations
            summary["analysis_limitations"] = [
                "Analisi basata su header e pattern di file",
                "Non include decodifica frame video",
                "Per analisi completa usa FFmpeg o tool specializzati"
            ]
            
            return summary
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }