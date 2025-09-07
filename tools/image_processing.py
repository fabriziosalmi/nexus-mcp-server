# -*- coding: utf-8 -*-
# tools/image_processing.py
import base64
import io
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
import hashlib
import numpy as np
from datetime import datetime

# Configurazione sicurezza
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB max file size
MAX_DIMENSION = 4096  # Max width/height
SUPPORTED_FORMATS = ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'GIF']
MAX_BATCH_SIZE = 10  # Max images in batch operations

def register_tools(mcp):
    """Registra i tool di elaborazione immagini avanzati con l'istanza del server MCP."""
    logging.info("🖼️ Registrazione tool-set: Image Processing Tools")

    def _validate_image_input(image_base64: str) -> Tuple[bool, str, Optional[bytes]]:
        """Valida input immagine per sicurezza."""
        try:
            if len(image_base64) > MAX_IMAGE_SIZE * 4 / 3:  # Base64 overhead
                return False, "Image too large (max 10MB)", None
            
            image_data = base64.b64decode(image_base64)
            
            if len(image_data) > MAX_IMAGE_SIZE:
                return False, "Image file size exceeds limit", None
            
            # Verifica header per formato valido
            headers = {
                b'\xff\xd8\xff': 'JPEG',
                b'\x89PNG\r\n\x1a\n': 'PNG',
                b'RIFF': 'WEBP',
                b'BM': 'BMP',
                b'GIF87a': 'GIF',
                b'GIF89a': 'GIF'
            }
            
            is_valid_format = any(image_data.startswith(header) for header in headers.keys())
            if not is_valid_format:
                return False, "Invalid or unsupported image format", None
            
            return True, "Valid", image_data
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", None

    @mcp.tool()
    def analyze_image_metadata(image_base64: str) -> Dict[str, Any]:
        """
        Analizza metadata di un'immagine da base64.
        
        Args:
            image_base64: Immagine codificata in base64
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            # Decodifica base64
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Informazioni di base
            info = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "aspect_ratio": round(image.width / image.height, 2),
                "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            # EXIF data se disponibile
            exif_data = {}
            if hasattr(image, '_getexif') and image._getexif() is not None:
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)[:100]  # Limita lunghezza valori
            
            # Analisi colori (campiona pixel)
            if image.mode == 'RGB':
                # Ridimensiona per analisi più veloce
                small_image = image.resize((50, 50))
                pixels = list(small_image.getdata())
                
                # Calcola colori medi
                avg_r = sum(p[0] for p in pixels) // len(pixels)
                avg_g = sum(p[1] for p in pixels) // len(pixels)
                avg_b = sum(p[2] for p in pixels) // len(pixels)
                
                # Luminosità media
                brightness = (avg_r + avg_g + avg_b) / 3
                
                info.update({
                    "average_color": {"r": avg_r, "g": avg_g, "b": avg_b},
                    "brightness": round(brightness, 2),
                    "dominant_channel": "Red" if avg_r > avg_g and avg_r > avg_b else 
                                      "Green" if avg_g > avg_b else "Blue"
                })
            
            return {
                "image_info": info,
                "exif_data": exif_data,
                "file_size_kb": round(len(image_data) / 1024, 2),
                "analysis_status": "success"
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "PIL (Pillow) non installato - impossibile elaborare immagini"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def resize_image(image_base64: str, width: int, height: int, maintain_aspect: bool = True) -> Dict[str, Any]:
        """
        Ridimensiona un'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
            width: Nuova larghezza
            height: Nuova altezza
            maintain_aspect: Mantieni proporzioni (default: True)
        """
        try:
            from PIL import Image
            
            # Decodifica base64
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            original_size = image.size
            
            if maintain_aspect:
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
                new_size = image.size
            else:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
                new_size = (width, height)
            
            # Converti a base64
            output_buffer = io.BytesIO()
            image_format = image.format or 'PNG'
            image.save(output_buffer, format=image_format)
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "resized_image_base64": output_base64,
                "original_size": original_size,
                "new_size": new_size,
                "aspect_ratio_maintained": maintain_aspect,
                "format": image_format,
                "size_reduction_percent": round((1 - len(output_base64) / len(image_base64)) * 100, 2)
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
    def convert_image_format(image_base64: str, target_format: str) -> Dict[str, Any]:
        """
        Converte formato di un'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
            target_format: Formato target (JPEG, PNG, WEBP, BMP)
        """
        try:
            from PIL import Image
            
            supported_formats = ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF']
            target_format = target_format.upper()
            
            if target_format not in supported_formats:
                return {
                    "success": False,
                    "error": f"Formato non supportato. Supportati: {', '.join(supported_formats)}"
                }
            
            # Decodifica base64
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            original_format = image.format
            original_size_kb = len(image_data) / 1024
            
            # Converte RGBA a RGB se necessario per JPEG
            if target_format == 'JPEG' and image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Salva nel nuovo formato
            output_buffer = io.BytesIO()
            save_kwargs = {}
            
            if target_format == 'JPEG':
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
            elif target_format == 'PNG':
                save_kwargs['optimize'] = True
            elif target_format == 'WEBP':
                save_kwargs['quality'] = 95
                save_kwargs['method'] = 6
            
            image.save(output_buffer, format=target_format, **save_kwargs)
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            new_size_kb = len(output_buffer.getvalue()) / 1024
            
            return {
                "converted_image_base64": output_base64,
                "original_format": original_format,
                "new_format": target_format,
                "original_size_kb": round(original_size_kb, 2),
                "new_size_kb": round(new_size_kb, 2),
                "size_change_percent": round(((new_size_kb - original_size_kb) / original_size_kb) * 100, 2)
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
    def apply_image_filters(image_base64: str, filters: List[str]) -> Dict[str, Any]:
        """
        Applica filtri a un'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
            filters: Lista di filtri (blur, sharpen, edge_enhance, grayscale, sepia)
        """
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            
            available_filters = ['blur', 'sharpen', 'edge_enhance', 'grayscale', 'sepia', 'brightness', 'contrast']
            
            # Decodifica base64
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            applied_filters = []
            
            for filter_name in filters:
                filter_name = filter_name.lower()
                
                if filter_name == 'blur':
                    image = image.filter(ImageFilter.GaussianBlur(radius=2))
                    applied_filters.append('blur')
                
                elif filter_name == 'sharpen':
                    image = image.filter(ImageFilter.SHARPEN)
                    applied_filters.append('sharpen')
                
                elif filter_name == 'edge_enhance':
                    image = image.filter(ImageFilter.EDGE_ENHANCE)
                    applied_filters.append('edge_enhance')
                
                elif filter_name == 'grayscale':
                    if image.mode != 'L':
                        image = image.convert('L').convert('RGB')
                    applied_filters.append('grayscale')
                
                elif filter_name == 'sepia':
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    pixels = image.load()
                    for i in range(image.width):
                        for j in range(image.height):
                            r, g, b = pixels[i, j]
                            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                            pixels[i, j] = (min(255, tr), min(255, tg), min(255, tb))
                    applied_filters.append('sepia')
                
                elif filter_name == 'brightness':
                    enhancer = ImageEnhance.Brightness(image)
                    image = enhancer.enhance(1.2)  # 20% più luminosa
                    applied_filters.append('brightness')
                
                elif filter_name == 'contrast':
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(1.2)  # 20% più contrasto
                    applied_filters.append('contrast')
            
            # Converti a base64
            output_buffer = io.BytesIO()
            image_format = image.format or 'PNG'
            image.save(output_buffer, format=image_format)
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "filtered_image_base64": output_base64,
                "applied_filters": applied_filters,
                "available_filters": available_filters,
                "format": image_format,
                "filters_count": len(applied_filters)
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
    def create_thumbnail(image_base64: str, size: int = 150, quality: int = 85) -> Dict[str, Any]:
        """
        Crea thumbnail di un'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
            size: Dimensione massima del thumbnail (default: 150)
            quality: Qualità JPEG (default: 85)
        """
        try:
            from PIL import Image
            
            # Decodifica base64
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            original_size = image.size
            original_size_kb = len(image_data) / 1024
            
            # Crea thumbnail mantenendo proporzioni
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            thumbnail_size = image.size
            
            # Salva come JPEG per dimensioni ridotte
            output_buffer = io.BytesIO()
            
            # Converte a RGB se necessario
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            thumbnail_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            thumbnail_size_kb = len(output_buffer.getvalue()) / 1024
            compression_ratio = round((1 - thumbnail_size_kb / original_size_kb) * 100, 1)
            
            return {
                "thumbnail_base64": thumbnail_base64,
                "original_size": original_size,
                "thumbnail_size": thumbnail_size,
                "original_size_kb": round(original_size_kb, 2),
                "thumbnail_size_kb": round(thumbnail_size_kb, 2),
                "compression_ratio": compression_ratio,
                "quality": quality,
                "format": "JPEG"
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
    def extract_dominant_colors(image_base64: str, num_colors: int = 5) -> Dict[str, Any]:
        """
        Estrae colori dominanti da un'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
            num_colors: Numero di colori dominanti da estrarre (default: 5)
        """
        try:
            from PIL import Image
            import colorsys
            
            # Decodifica base64
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Converte a RGB se necessario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Ridimensiona per performance
            image = image.resize((150, 150))
            
            # Ottieni tutti i pixel
            pixels = list(image.getdata())
            
            # Conta occorrenze colori (campiona ogni N pixel per performance)
            color_count = {}
            step = max(1, len(pixels) // 1000)  # Campiona max 1000 pixel
            
            for i in range(0, len(pixels), step):
                color = pixels[i]
                color_count[color] = color_count.get(color, 0) + 1
            
            # Ottieni top colori
            top_colors = sorted(color_count.items(), key=lambda x: x[1], reverse=True)[:num_colors]
            
            # Analizza colori
            color_analysis = []
            for color, count in top_colors:
                r, g, b = color
                
                # Converte a HSV per analisi
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                
                # Determina nome colore approssimativo
                def get_color_name(r, g, b):
                    if r > 200 and g > 200 and b > 200:
                        return "Bianco"
                    elif r < 50 and g < 50 and b < 50:
                        return "Nero"
                    elif r > g and r > b:
                        return "Rosso"
                    elif g > r and g > b:
                        return "Verde"
                    elif b > r and b > g:
                        return "Blu"
                    elif r > 150 and g > 150 and b < 100:
                        return "Giallo"
                    elif r > 150 and g < 100 and b > 150:
                        return "Magenta"
                    elif r < 100 and g > 150 and b > 150:
                        return "Ciano"
                    else:
                        return "Grigio"
                
                color_info = {
                    "rgb": {"r": r, "g": g, "b": b},
                    "hex": f"#{r:02x}{g:02x}{b:02x}",
                    "hsv": {
                        "h": round(h * 360, 1),
                        "s": round(s * 100, 1),
                        "v": round(v * 100, 1)
                    },
                    "percentage": round((count / len(pixels)) * 100, 2),
                    "color_name": get_color_name(r, g, b)
                }
                
                color_analysis.append(color_info)
            
            # Analisi generale palette
            avg_brightness = sum(sum(color["rgb"].values()) for color in color_analysis) / (len(color_analysis) * 3 * 255) * 100
            
            return {
                "dominant_colors": color_analysis,
                "palette_analysis": {
                    "average_brightness": round(avg_brightness, 1),
                    "palette_type": "Scura" if avg_brightness < 30 else "Media" if avg_brightness < 70 else "Chiara",
                    "colors_extracted": len(color_analysis)
                },
                "image_size_analyzed": image.size
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
    def transform_image(image_base64: str, transformations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applica trasformazioni geometriche a un'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
            transformations: Dict con trasformazioni (rotate, flip, crop, etc.)
        """
        try:
            from PIL import Image, ImageOps
            
            # Validazione input
            is_valid, error_msg, image_data = _validate_image_input(image_base64)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            image = Image.open(io.BytesIO(image_data))
            original_size = image.size
            applied_transformations = []
            
            # Rotazione
            if 'rotate' in transformations:
                angle = transformations['rotate']
                if isinstance(angle, (int, float)) and -360 <= angle <= 360:
                    image = image.rotate(angle, expand=True, fillcolor='white')
                    applied_transformations.append(f"rotate_{angle}")
            
            # Flip orizzontale/verticale
            if 'flip_horizontal' in transformations and transformations['flip_horizontal']:
                image = ImageOps.mirror(image)
                applied_transformations.append("flip_horizontal")
            
            if 'flip_vertical' in transformations and transformations['flip_vertical']:
                image = ImageOps.flip(image)
                applied_transformations.append("flip_vertical")
            
            # Crop
            if 'crop' in transformations:
                crop_params = transformations['crop']
                if isinstance(crop_params, dict):
                    x = crop_params.get('x', 0)
                    y = crop_params.get('y', 0)
                    width = crop_params.get('width', image.width)
                    height = crop_params.get('height', image.height)
                    
                    # Validazione crop bounds
                    x = max(0, min(x, image.width))
                    y = max(0, min(y, image.height))
                    width = min(width, image.width - x)
                    height = min(height, image.height - y)
                    
                    if width > 0 and height > 0:
                        image = image.crop((x, y, x + width, y + height))
                        applied_transformations.append("crop")
            
            # Auto-orient (usa EXIF se disponibile)
            if 'auto_orient' in transformations and transformations['auto_orient']:
                image = ImageOps.exif_transpose(image)
                applied_transformations.append("auto_orient")
            
            # Converti a base64
            output_buffer = io.BytesIO()
            image_format = image.format or 'PNG'
            
            # Salva con ottimizzazioni
            save_kwargs = {'format': image_format, 'optimize': True}
            if image_format == 'JPEG':
                save_kwargs['quality'] = 95
            
            image.save(output_buffer, **save_kwargs)
            transformed_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "success": True,
                "transformed_image_base64": transformed_base64,
                "original_size": original_size,
                "new_size": image.size,
                "applied_transformations": applied_transformations,
                "format": image_format,
                "size_change_percent": round(((len(transformed_base64) - len(image_base64)) / len(image_base64)) * 100, 2)
            }
            
        except ImportError:
            return {"success": False, "error": "PIL (Pillow) not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def enhance_image(image_base64: str, enhancements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applica miglioramenti automatici all'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
            enhancements: Dict con miglioramenti (auto_level, noise_reduction, etc.)
        """
        try:
            from PIL import Image, ImageEnhance, ImageFilter, ImageOps
            
            # Validazione input
            is_valid, error_msg, image_data = _validate_image_input(image_base64)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            image = Image.open(io.BytesIO(image_data))
            applied_enhancements = []
            
            # Auto levels (migliora contrasto)
            if enhancements.get('auto_level', False):
                image = ImageOps.autocontrast(image)
                applied_enhancements.append("auto_level")
            
            # Equalizza istogramma
            if enhancements.get('equalize', False):
                if image.mode == 'RGB':
                    # Equalizza per canale
                    r, g, b = image.split()
                    r = ImageOps.equalize(r)
                    g = ImageOps.equalize(g)
                    b = ImageOps.equalize(b)
                    image = Image.merge('RGB', (r, g, b))
                else:
                    image = ImageOps.equalize(image)
                applied_enhancements.append("equalize")
            
            # Riduzione rumore
            if enhancements.get('noise_reduction', False):
                image = image.filter(ImageFilter.MedianFilter(size=3))
                applied_enhancements.append("noise_reduction")
            
            # Miglioramento nitidezza
            if enhancements.get('sharpen', False):
                enhancer = ImageEnhance.Sharpness(image)
                factor = enhancements.get('sharpen_factor', 1.2)
                image = enhancer.enhance(max(0.1, min(3.0, factor)))
                applied_enhancements.append(f"sharpen_{factor}")
            
            # Correzione gamma
            if 'gamma' in enhancements:
                gamma = enhancements['gamma']
                if 0.1 <= gamma <= 3.0:
                    # Applica correzione gamma
                    gamma_lut = [int(((i / 255.0) ** (1.0 / gamma)) * 255) for i in range(256)]
                    image = image.point(gamma_lut * (len(image.getbands())))
                    applied_enhancements.append(f"gamma_{gamma}")
            
            # Bilanciamento colore automatico
            if enhancements.get('auto_color', False):
                image = ImageOps.autocontrast(image, cutoff=2)
                applied_enhancements.append("auto_color")
            
            # Converti a base64
            output_buffer = io.BytesIO()
            image_format = image.format or 'PNG'
            
            save_kwargs = {'format': image_format, 'optimize': True}
            if image_format == 'JPEG':
                save_kwargs['quality'] = 95
            
            image.save(output_buffer, **save_kwargs)
            enhanced_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "success": True,
                "enhanced_image_base64": enhanced_base64,
                "applied_enhancements": applied_enhancements,
                "format": image_format,
                "original_size_kb": round(len(image_data) / 1024, 2),
                "enhanced_size_kb": round(len(output_buffer.getvalue()) / 1024, 2)
            }
            
        except ImportError:
            return {"success": False, "error": "PIL (Pillow) not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def add_watermark(image_base64: str, watermark_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggiunge watermark (testo o immagine) a un'immagine.
        
        Args:
            image_base64: Immagine base codificata in base64
            watermark_config: Configurazione watermark
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Validazione input
            is_valid, error_msg, image_data = _validate_image_input(image_base64)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            image = Image.open(io.BytesIO(image_data))
            
            # Crea layer per watermark
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Crea overlay trasparente
            overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            watermark_type = watermark_config.get('type', 'text')
            
            if watermark_type == 'text':
                # Watermark testo
                text = watermark_config.get('text', 'Watermark')
                font_size = watermark_config.get('font_size', 36)
                color = watermark_config.get('color', (255, 255, 255, 128))
                position = watermark_config.get('position', 'bottom_right')
                
                try:
                    # Prova a usare font di sistema
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
                
                # Calcola posizione
                if font:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                else:
                    text_width = len(text) * font_size // 2
                    text_height = font_size
                
                positions = {
                    'top_left': (10, 10),
                    'top_right': (image.width - text_width - 10, 10),
                    'bottom_left': (10, image.height - text_height - 10),
                    'bottom_right': (image.width - text_width - 10, image.height - text_height - 10),
                    'center': ((image.width - text_width) // 2, (image.height - text_height) // 2)
                }
                
                pos = positions.get(position, positions['bottom_right'])
                
                # Disegna testo
                if font:
                    draw.text(pos, text, font=font, fill=color)
                else:
                    draw.text(pos, text, fill=color)
            
            elif watermark_type == 'image':
                # Watermark immagine
                watermark_base64 = watermark_config.get('watermark_image_base64')
                if not watermark_base64:
                    return {"success": False, "error": "watermark_image_base64 required for image watermark"}
                
                try:
                    watermark_data = base64.b64decode(watermark_base64)
                    watermark_img = Image.open(io.BytesIO(watermark_data))
                    
                    # Ridimensiona watermark se troppo grande
                    max_size = min(image.width // 4, image.height // 4)
                    if watermark_img.width > max_size or watermark_img.height > max_size:
                        watermark_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Applica trasparenza
                    opacity = watermark_config.get('opacity', 0.5)
                    if watermark_img.mode != 'RGBA':
                        watermark_img = watermark_img.convert('RGBA')
                    
                    # Modifica alpha channel
                    alpha = watermark_img.split()[-1]
                    alpha = alpha.point(lambda p: int(p * opacity))
                    watermark_img.putalpha(alpha)
                    
                    # Posiziona watermark
                    position = watermark_config.get('position', 'bottom_right')
                    positions = {
                        'top_left': (10, 10),
                        'top_right': (image.width - watermark_img.width - 10, 10),
                        'bottom_left': (10, image.height - watermark_img.height - 10),
                        'bottom_right': (image.width - watermark_img.width - 10, image.height - watermark_img.height - 10),
                        'center': ((image.width - watermark_img.width) // 2, (image.height - watermark_img.height) // 2)
                    }
                    
                    pos = positions.get(position, positions['bottom_right'])
                    overlay.paste(watermark_img, pos, watermark_img)
                    
                except Exception as e:
                    return {"success": False, "error": f"Error processing watermark image: {str(e)}"}
            
            # Combina immagine originale con overlay
            watermarked = Image.alpha_composite(image, overlay)
            
            # Converti al formato originale se necessario
            if watermarked.mode == 'RGBA' and image.format == 'JPEG':
                background = Image.new('RGB', watermarked.size, (255, 255, 255))
                background.paste(watermarked, mask=watermarked.split()[-1])
                watermarked = background
            
            # Salva
            output_buffer = io.BytesIO()
            image_format = image.format or 'PNG'
            
            save_kwargs = {'format': image_format, 'optimize': True}
            if image_format == 'JPEG':
                save_kwargs['quality'] = 95
            
            watermarked.save(output_buffer, **save_kwargs)
            watermarked_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "success": True,
                "watermarked_image_base64": watermarked_base64,
                "watermark_type": watermark_type,
                "watermark_config": watermark_config,
                "format": image_format
            }
            
        except ImportError:
            return {"success": False, "error": "PIL (Pillow) non installato"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_image_histogram(image_base64: str) -> Dict[str, Any]:
        """
        Analizza istogramma colori dell'immagine.
        
        Args:
            image_base64: Immagine codificata in base64
        """
        try:
            from PIL import Image
            
            # Validazione input
            is_valid, error_msg, image_data = _validate_image_input(image_base64)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            image = Image.open(io.BytesIO(image_data))
            
            # Converti a RGB se necessario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calcola istogramma per ogni canale
            histograms = {
                'red': image.histogram()[0:256],
                'green': image.histogram()[256:512],
                'blue': image.histogram()[512:768]
            }
            
            # Statistiche per canale
            def analyze_channel(hist):
                total_pixels = sum(hist)
                if total_pixels == 0:
                    return {'mean': 0, 'std': 0, 'min': 0, 'max': 255}
                
                # Calcola media pesata
                mean = sum(i * count for i, count in enumerate(hist)) / total_pixels
                
                # Calcola deviazione standard
                variance = sum(count * (i - mean) ** 2 for i, count in enumerate(hist)) / total_pixels
                std = variance ** 0.5
                
                # Min e max con pixel significativi (>1% del totale)
                threshold = total_pixels * 0.01
                min_val = next((i for i, count in enumerate(hist) if count > threshold), 0)
                max_val = next((255 - i for i, count in enumerate(reversed(hist)) if count > threshold), 255)
                
                return {
                    'mean': round(mean, 2),
                    'std': round(std, 2),
                    'min': min_val,
                    'max': max_val
                }
            
            channel_stats = {
                channel: analyze_channel(hist) 
                for channel, hist in histograms.items()
            }
            
            # Analisi generale
            overall_brightness = (channel_stats['red']['mean'] + 
                                channel_stats['green']['mean'] + 
                                channel_stats['blue']['mean']) / 3
            
            # Contrasto generale (media delle deviazioni standard)
            overall_contrast = (channel_stats['red']['std'] + 
                              channel_stats['green']['std'] + 
                              channel_stats['blue']['std']) / 3
            
            # Bilanciamento colori
            color_balance = {
                'red_dominant': channel_stats['red']['mean'] > max(channel_stats['green']['mean'], channel_stats['blue']['mean']),
                'green_dominant': channel_stats['green']['mean'] > max(channel_stats['red']['mean'], channel_stats['blue']['mean']),
                'blue_dominant': channel_stats['blue']['mean'] > max(channel_stats['red']['mean'], channel_stats['green']['mean']),
                'balanced': abs(channel_stats['red']['mean'] - channel_stats['green']['mean']) < 20 and 
                           abs(channel_stats['green']['mean'] - channel_stats['blue']['mean']) < 20
            }
            
            # Classificazione immagine
            def classify_image():
                if overall_brightness < 50:
                    return "Dark"
                elif overall_brightness > 200:
                    return "Bright"
                elif overall_contrast < 30:
                    return "Low Contrast"
                elif overall_contrast > 80:
                    return "High Contrast"
                else:
                    return "Balanced"
            
            return {
                "success": True,
                "histograms": histograms,
                "channel_statistics": channel_stats,
                "overall_analysis": {
                    "brightness": round(overall_brightness, 2),
                    "contrast": round(overall_contrast, 2),
                    "classification": classify_image(),
                    "color_balance": color_balance
                },
                "recommendations": _generate_enhancement_recommendations(overall_brightness, overall_contrast, color_balance)
            }
            
        except ImportError:
            return {"success": False, "error": "PIL (Pillow) non installato"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def batch_process_images(images_data: List[Dict[str, Any]], 
                           operation: str, operation_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Elabora batch di immagini con la stessa operazione.
        
        Args:
            images_data: Lista di dict con 'image_base64' e opzionale 'name'
            operation: Operazione da applicare (resize, convert, filter, etc.)
            operation_params: Parametri per l'operazione
        """
        try:
            if len(images_data) > MAX_BATCH_SIZE:
                return {"success": False, "error": f"Too many images (max {MAX_BATCH_SIZE})"}
            
            operation_params = operation_params or {}
            results = []
            successful_operations = 0
            
            for i, image_data in enumerate(images_data):
                image_name = image_data.get('name', f'image_{i+1}')
                image_base64 = image_data.get('image_base64', '')
                
                if not image_base64:
                    results.append({
                        'name': image_name,
                        'success': False,
                        'error': 'No image data provided'
                    })
                    continue
                
                try:
                    # Applica operazione specifica
                    if operation == 'resize':
                        result = resize_image(
                            image_base64,
                            operation_params.get('width', 800),
                            operation_params.get('height', 600),
                            operation_params.get('maintain_aspect', True)
                        )
                    
                    elif operation == 'convert':
                        result = convert_image_format(
                            image_base64,
                            operation_params.get('target_format', 'JPEG')
                        )
                    
                    elif operation == 'thumbnail':
                        result = create_thumbnail(
                            image_base64,
                            operation_params.get('size', 150),
                            operation_params.get('quality', 85)
                        )
                    
                    elif operation == 'filter':
                        result = apply_image_filters(
                            image_base64,
                            operation_params.get('filters', ['grayscale'])
                        )
                    
                    elif operation == 'enhance':
                        result = enhance_image(
                            image_base64,
                            operation_params.get('enhancements', {'auto_level': True})
                        )
                    
                    else:
                        result = {'success': False, 'error': f'Unsupported operation: {operation}'}
                    
                    if result.get('success', True):  # Some functions don't return success field
                        successful_operations += 1
                        results.append({
                            'name': image_name,
                            'success': True,
                            'result': result
                        })
                    else:
                        results.append({
                            'name': image_name,
                            'success': False,
                            'error': result.get('error', 'Unknown error')
                        })
                
                except Exception as e:
                    results.append({
                        'name': image_name,
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                "success": True,
                "operation": operation,
                "operation_params": operation_params,
                "total_images": len(images_data),
                "successful_operations": successful_operations,
                "failed_operations": len(images_data) - successful_operations,
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def compare_images(image1_base64: str, image2_base64: str, 
                      comparison_type: str = "structural") -> Dict[str, Any]:
        """
        Confronta due immagini per similarità.
        
        Args:
            image1_base64: Prima immagine
            image2_base64: Seconda immagine
            comparison_type: Tipo confronto (structural, histogram, hash)
        """
        try:
            from PIL import Image
            import hashlib
            
            # Validazione input
            is_valid1, error1, data1 = _validate_image_input(image1_base64)
            is_valid2, error2, data2 = _validate_image_input(image2_base64)
            
            if not is_valid1:
                return {"success": False, "error": f"Image 1: {error1}"}
            if not is_valid2:
                return {"success": False, "error": f"Image 2: {error2}"}
            
            image1 = Image.open(io.BytesIO(data1))
            image2 = Image.open(io.BytesIO(data2))
            
            comparison_results = {
                "success": True,
                "comparison_type": comparison_type,
                "image1_size": image1.size,
                "image2_size": image2.size,
                "same_dimensions": image1.size == image2.size
            }
            
            if comparison_type == "hash":
                # Hash comparison (veloce ma approssimativo)
                hash1 = hashlib.md5(data1).hexdigest()
                hash2 = hashlib.md5(data2).hexdigest()
                
                comparison_results.update({
                    "identical": hash1 == hash2,
                    "hash1": hash1,
                    "hash2": hash2,
                    "similarity_score": 100.0 if hash1 == hash2 else 0.0
                })
            
            elif comparison_type == "histogram":
                # Confronto istogrammi
                if image1.mode != 'RGB':
                    image1 = image1.convert('RGB')
                if image2.mode != 'RGB':
                    image2 = image2.convert('RGB')
                
                # Ridimensiona a dimensione comune per confronto
                common_size = (min(image1.width, image2.width), min(image1.height, image2.height))
                img1_resized = image1.resize(common_size)
                img2_resized = image2.resize(common_size)
                
                hist1 = img1_resized.histogram()
                hist2 = img2_resized.histogram()
                
                # Calcola correlazione istogrammi
                def histogram_correlation(h1, h2):
                    # Normalizza istogrammi
                    sum1, sum2 = sum(h1), sum(h2)
                    if sum1 == 0 or sum2 == 0:
                        return 0.0
                    
                    h1_norm = [x / sum1 for x in h1]
                    h2_norm = [x / sum2 for x in h2]
                    
                    # Calcola correlazione
                    mean1 = sum(h1_norm) / len(h1_norm)
                    mean2 = sum(h2_norm) / len(h2_norm)
                    
                    num = sum((x - mean1) * (y - mean2) for x, y in zip(h1_norm, h2_norm))
                    den1 = sum((x - mean1) ** 2 for x in h1_norm) ** 0.5
                    den2 = sum((y - mean2) ** 2 for y in h2_norm) ** 0.5
                    
                    if den1 == 0 or den2 == 0:
                        return 0.0
                    
                    return num / (den1 * den2)
                
                correlation = histogram_correlation(hist1, hist2)
                similarity_score = max(0, correlation * 100)
                
                comparison_results.update({
                    "histogram_correlation": round(correlation, 4),
                    "similarity_score": round(similarity_score, 2),
                    "comparison_size": common_size
                })
            
            elif comparison_type == "structural":
                # Confronto strutturale pixel-by-pixel
                if image1.size != image2.size:
                    # Ridimensiona alla dimensione più piccola
                    target_size = (min(image1.width, image2.width), min(image1.height, image2.height))
                    image1 = image1.resize(target_size)
                    image2 = image2.resize(target_size)
                
                # Converti a RGB
                if image1.mode != 'RGB':
                    image1 = image1.convert('RGB')
                if image2.mode != 'RGB':
                    image2 = image2.convert('RGB')
                
                # Campiona pixel per performance (max 10000 pixel)
                total_pixels = image1.width * image1.height
                sample_rate = max(1, total_pixels // 10000)
                
                pixels1 = list(image1.getdata())[::sample_rate]
                pixels2 = list(image2.getdata())[::sample_rate]
                
                # Calcola differenza media
                total_diff = 0
                max_diff = 0
                
                for p1, p2 in zip(pixels1, pixels2):
                    # Differenza euclidea tra pixel RGB
                    diff = ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2) ** 0.5
                    total_diff += diff
                    max_diff = max(max_diff, diff)
                
                avg_diff = total_diff / len(pixels1) if pixels1 else 0
                max_possible_diff = (255 ** 2 * 3) ** 0.5  # ~441.67
                
                similarity_score = max(0, (1 - avg_diff / max_possible_diff) * 100)
                
                comparison_results.update({
                    "average_pixel_difference": round(avg_diff, 2),
                    "max_pixel_difference": round(max_diff, 2),
                    "similarity_score": round(similarity_score, 2),
                    "pixels_compared": len(pixels1),
                    "sample_rate": sample_rate
                })
            
            # Classificazione similarità
            score = comparison_results.get("similarity_score", 0)
            if score >= 95:
                similarity_level = "Nearly Identical"
            elif score >= 80:
                similarity_level = "Very Similar"
            elif score >= 60:
                similarity_level = "Moderately Similar"
            elif score >= 30:
                similarity_level = "Somewhat Similar"
            else:
                similarity_level = "Different"
            
            comparison_results["similarity_level"] = similarity_level
            
            return comparison_results
            
        except ImportError:
            return {"success": False, "error": "PIL (Pillow) non installato"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions
    def _generate_enhancement_recommendations(brightness: float, contrast: float, color_balance: Dict) -> List[str]:
        """Genera raccomandazioni per miglioramento immagine."""
        recommendations = []
        
        if brightness < 50:
            recommendations.append("Image is dark - consider increasing brightness")
        elif brightness > 200:
            recommendations.append("Image is very bright - consider reducing exposure")
        
        if contrast < 30:
            recommendations.append("Low contrast - consider auto-level or contrast enhancement")
        elif contrast > 100:
            recommendations.append("Very high contrast - consider reducing contrast")
        
        if not color_balance.get('balanced', False):
            dominant_colors = [k.replace('_dominant', '') for k, v in color_balance.items() if v and k.endswith('_dominant')]
            if dominant_colors:
                recommendations.append(f"Color cast detected ({', '.join(dominant_colors)}) - consider color correction")
        
        if not recommendations:
            recommendations.append("Image appears well-balanced")
        
        return recommendations