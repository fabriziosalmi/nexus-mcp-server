# -*- coding: utf-8 -*-
# tools/image_processing.py
import base64
import io
import logging
from typing import Dict, List, Optional, Any, Tuple
import json

def register_tools(mcp):
    """Registra i tool di elaborazione immagini con l'istanza del server MCP."""
    logging.info("🖼️ Registrazione tool-set: Image Processing Tools")

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