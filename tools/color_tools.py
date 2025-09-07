# -*- coding: utf-8 -*-
# tools/color_tools.py
import logging
import colorsys
import re
import math
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

def register_tools(mcp):
    """Registra i tool per la gestione colori avanzata con l'istanza del server MCP."""
    logging.info("🎨 Registrazione tool-set: Color Tools")

    @mcp.tool()
    def convert_color_format(color: str, target_format: str) -> str:
        """
        Converte un colore tra diversi formati (hex, rgb, hsl, hsv).
        
        Args:
            color: Colore in formato hex (#FF0000), rgb (255,0,0) o nome
            target_format: Formato di destinazione (hex, rgb, hsl, hsv)
        """
        try:
            # Normalizza il colore di input
            rgb = None
            
            # Parse HEX
            hex_match = re.match(r'^#?([0-9A-Fa-f]{6})$', color.strip())
            if hex_match:
                hex_val = hex_match.group(1)
                rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
            
            # Parse RGB
            rgb_match = re.match(r'^rgb?\(?(\d+),?\s*(\d+),?\s*(\d+)\)?$', color.strip())
            if rgb_match:
                rgb = tuple(int(x) for x in rgb_match.groups())
            
            # Colori predefiniti
            color_names = {
                'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
                'white': (255, 255, 255), 'black': (0, 0, 0), 'yellow': (255, 255, 0),
                'cyan': (0, 255, 255), 'magenta': (255, 0, 255), 'orange': (255, 165, 0),
                'purple': (128, 0, 128), 'pink': (255, 192, 203), 'brown': (165, 42, 42)
            }
            
            if color.lower() in color_names:
                rgb = color_names[color.lower()]
            
            if rgb is None:
                return f"ERRORE: Formato colore '{color}' non riconosciuto"
            
            # Valida RGB
            if not all(0 <= c <= 255 for c in rgb):
                return "ERRORE: Valori RGB devono essere tra 0 e 255"
            
            r, g, b = rgb
            r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
            
            # Conversioni
            conversions = {}
            
            # HEX
            conversions['hex'] = f"#{r:02X}{g:02X}{b:02X}"
            
            # RGB
            conversions['rgb'] = f"rgb({r}, {g}, {b})"
            
            # HSL
            h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
            conversions['hsl'] = f"hsl({int(h*360)}, {int(s*100)}%, {int(l*100)}%)"
            
            # HSV
            h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
            conversions['hsv'] = f"hsv({int(h*360)}, {int(s*100)}%, {int(v*100)}%)"
            
            if target_format not in conversions:
                available = ', '.join(conversions.keys())
                return f"ERRORE: Formato '{target_format}' non disponibile. Disponibili: {available}"
            
            result = f"""🎨 CONVERSIONE COLORE
Colore originale: {color}
Formato target: {target_format}

Risultato: {conversions[target_format]}

Tutti i formati:
HEX: {conversions['hex']}
RGB: {conversions['rgb']}
HSL: {conversions['hsl']}
HSV: {conversions['hsv']}"""
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_color_palette(base_color: str, palette_type: str = "complementary") -> str:
        """
        Genera una palette di colori basata su un colore base.
        
        Args:
            base_color: Colore base in formato hex (#FF0000) o rgb
            palette_type: Tipo di palette (complementary, triadic, analogous, monochromatic)
        """
        try:
            # Parse colore base
            rgb = None
            hex_match = re.match(r'^#?([0-9A-Fa-f]{6})$', base_color.strip())
            if hex_match:
                hex_val = hex_match.group(1)
                rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
            
            if rgb is None:
                return f"ERRORE: Formato colore '{base_color}' non riconosciuto (usa hex: #FF0000)"
            
            r, g, b = rgb
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            h_deg = h * 360
            
            def hsv_to_hex(h, s, v):
                rgb = colorsys.hsv_to_rgb(h, s, v)
                return f"#{int(rgb[0]*255):02X}{int(rgb[1]*255):02X}{int(rgb[2]*255):02X}"
            
            palettes = {
                'complementary': [
                    (h, s, v),  # Base
                    ((h + 180) % 360 / 360, s, v),  # Complementare
                ],
                'triadic': [
                    (h, s, v),  # Base
                    ((h + 120) % 360 / 360, s, v),  # +120°
                    ((h + 240) % 360 / 360, s, v),  # +240°
                ],
                'analogous': [
                    (h, s, v),  # Base
                    ((h + 30) % 360 / 360, s, v),   # +30°
                    ((h - 30) % 360 / 360, s, v),   # -30°
                    ((h + 60) % 360 / 360, s, v),   # +60°
                    ((h - 60) % 360 / 360, s, v),   # -60°
                ],
                'monochromatic': [
                    (h, s, v),                      # Base
                    (h, s, min(1.0, v + 0.2)),     # Più chiaro
                    (h, s, max(0.0, v - 0.2)),     # Più scuro
                    (h, min(1.0, s + 0.2), v),     # Più saturo
                    (h, max(0.0, s - 0.2), v),     # Meno saturo
                ]
            }
            
            if palette_type not in palettes:
                available = ', '.join(palettes.keys())
                return f"ERRORE: Tipo palette '{palette_type}' non disponibile. Disponibili: {available}"
            
            hsv_colors = palettes[palette_type]
            hex_colors = [hsv_to_hex(h_val, s_val, v_val) for h_val, s_val, v_val in hsv_colors]
            
            result = f"""🎨 PALETTE COLORI - {palette_type.upper()}
Colore base: {base_color.upper()}

Palette generata:
"""
            
            for i, hex_color in enumerate(hex_colors, 1):
                # Calcola RGB per info aggiuntiva
                r = int(hex_color[1:3], 16)
                g = int(hex_color[3:5], 16)
                b = int(hex_color[5:7], 16)
                
                name = "Base" if i == 1 else f"Colore {i}"
                result += f"{i}. {name:<12} {hex_color} (RGB: {r:3d}, {g:3d}, {b:3d})\n"
            
            result += f"\nColori totali: {len(hex_colors)}"
            result += f"\nCSS: {', '.join(hex_colors)}"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def analyze_color_contrast(color1: str, color2: str) -> str:
        """
        Analizza il contrasto tra due colori per accessibilità.
        
        Args:
            color1: Primo colore (hex o rgb)
            color2: Secondo colore (hex o rgb)
        """
        try:
            def parse_color(color):
                # Parse HEX
                hex_match = re.match(r'^#?([0-9A-Fa-f]{6})$', color.strip())
                if hex_match:
                    hex_val = hex_match.group(1)
                    return tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
                
                # Parse RGB
                rgb_match = re.match(r'^rgb?\(?(\d+),?\s*(\d+),?\s*(\d+)\)?$', color.strip())
                if rgb_match:
                    return tuple(int(x) for x in rgb_match.groups())
                
                return None
            
            rgb1 = parse_color(color1)
            rgb2 = parse_color(color2)
            
            if rgb1 is None:
                return f"ERRORE: Formato colore1 '{color1}' non riconosciuto"
            if rgb2 is None:
                return f"ERRORE: Formato colore2 '{color2}' non riconosciuto"
            
            def relative_luminance(rgb):
                """Calcola la luminanza relativa per WCAG"""
                def linear_rgb(c):
                    c = c / 255.0
                    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                
                r, g, b = [linear_rgb(c) for c in rgb]
                return 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            lum1 = relative_luminance(rgb1)
            lum2 = relative_luminance(rgb2)
            
            # Calcola contrast ratio WCAG
            lighter = max(lum1, lum2)
            darker = min(lum1, lum2)
            contrast_ratio = (lighter + 0.05) / (darker + 0.05)
            
            # Standard WCAG
            aa_normal = contrast_ratio >= 4.5
            aa_large = contrast_ratio >= 3.0
            aaa_normal = contrast_ratio >= 7.0
            aaa_large = contrast_ratio >= 4.5
            
            # Determina quale colore è più chiaro
            brighter = "Colore 1" if lum1 > lum2 else "Colore 2"
            
            result = f"""🔍 ANALISI CONTRASTO COLORI
Colore 1: {color1} (RGB: {rgb1[0]}, {rgb1[1]}, {rgb1[2]})
Colore 2: {color2} (RGB: {rgb2[0]}, {rgb2[1]}, {rgb2[2]})

Luminanza 1: {lum1:.3f}
Luminanza 2: {lum2:.3f}
Colore più chiaro: {brighter}

Ratio di contrasto: {contrast_ratio:.2f}:1

CONFORMITÀ WCAG:
AA Testo normale (4.5:1):  {'✅ PASS' if aa_normal else '❌ FAIL'}
AA Testo grande (3.0:1):   {'✅ PASS' if aa_large else '❌ FAIL'}
AAA Testo normale (7.0:1): {'✅ PASS' if aaa_normal else '❌ FAIL'}
AAA Testo grande (4.5:1):  {'✅ PASS' if aaa_large else '❌ FAIL'}

RACCOMANDAZIONI:"""
            
            if not aa_normal:
                result += "\n⚠️ Contrasto insufficiente per testo normale"
            if not aa_large:
                result += "\n⚠️ Contrasto insufficiente per testo grande"
            else:
                result += "\n✅ Buon contrasto per accessibilità"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def color_mixer(color1: str, color2: str, ratio: float = 0.5) -> str:
        """
        Mescola due colori in una proporzione specificata.
        
        Args:
            color1: Primo colore (hex)
            color2: Secondo colore (hex)
            ratio: Proporzione del secondo colore (0.0-1.0, default 0.5)
        """
        try:
            def parse_hex_color(color):
                hex_match = re.match(r'^#?([0-9A-Fa-f]{6})$', color.strip())
                if hex_match:
                    hex_val = hex_match.group(1)
                    return tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
                return None
            
            rgb1 = parse_hex_color(color1)
            rgb2 = parse_hex_color(color2)
            
            if rgb1 is None:
                return f"ERRORE: Formato colore1 '{color1}' non riconosciuto (usa hex: #FF0000)"
            if rgb2 is None:
                return f"ERRORE: Formato colore2 '{color2}' non riconosciuto (usa hex: #FF0000)"
            
            if not 0 <= ratio <= 1:
                return "ERRORE: Ratio deve essere tra 0.0 e 1.0"
            
            # Mescola i colori
            mixed_rgb = tuple(
                int(rgb1[i] * (1 - ratio) + rgb2[i] * ratio)
                for i in range(3)
            )
            
            mixed_hex = f"#{mixed_rgb[0]:02X}{mixed_rgb[1]:02X}{mixed_rgb[2]:02X}"
            
            # Calcola step intermedi
            steps = []
            for step_ratio in [0.0, 0.25, 0.5, 0.75, 1.0]:
                step_rgb = tuple(
                    int(rgb1[i] * (1 - step_ratio) + rgb2[i] * step_ratio)
                    for i in range(3)
                )
                step_hex = f"#{step_rgb[0]:02X}{step_rgb[1]:02X}{step_rgb[2]:02X}"
                steps.append((step_ratio, step_hex, step_rgb))
            
            result = f"""🎨 MISCELAZIONE COLORI
Colore 1: {color1.upper()} (RGB: {rgb1[0]}, {rgb1[1]}, {rgb1[2]})
Colore 2: {color2.upper()} (RGB: {rgb2[0]}, {rgb2[1]}, {rgb2[2]})
Ratio: {ratio:.2f} ({int(ratio*100)}% colore 2)

Risultato: {mixed_hex} (RGB: {mixed_rgb[0]}, {mixed_rgb[1]}, {mixed_rgb[2]})

Gradazione completa:"""
            
            for step_ratio, step_hex, step_rgb in steps:
                marker = " ← RISULTATO" if abs(step_ratio - ratio) < 0.01 else ""
                result += f"\n{step_ratio:.2f}: {step_hex} (RGB: {step_rgb[0]:3d}, {step_rgb[1]:3d}, {step_rgb[2]:3d}){marker}"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_gradient(start_color: str, end_color: str, steps: int = 5, 
                         gradient_type: str = "linear") -> Dict[str, Any]:
        """
        Genera un gradiente tra due colori con numero specificato di step.
        
        Args:
            start_color: Colore iniziale (hex)
            end_color: Colore finale (hex)
            steps: Numero di step nel gradiente (3-20)
            gradient_type: Tipo di gradiente (linear, ease-in, ease-out, ease-in-out)
        """
        try:
            if not 3 <= steps <= 20:
                return {"success": False, "error": "Steps deve essere tra 3 e 20"}
            
            start_rgb = _parse_hex_color(start_color)
            end_rgb = _parse_hex_color(end_color)
            
            if not start_rgb:
                return {"success": False, "error": f"Colore iniziale '{start_color}' non valido"}
            if not end_rgb:
                return {"success": False, "error": f"Colore finale '{end_color}' non valido"}
            
            # Funzioni di easing
            def linear(t):
                return t
            
            def ease_in(t):
                return t * t
            
            def ease_out(t):
                return 1 - (1 - t) * (1 - t)
            
            def ease_in_out(t):
                return 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)
            
            easing_functions = {
                "linear": linear,
                "ease-in": ease_in,
                "ease-out": ease_out,
                "ease-in-out": ease_in_out
            }
            
            if gradient_type not in easing_functions:
                return {"success": False, "error": f"Tipo gradiente non supportato: {gradient_type}"}
            
            easing_func = easing_functions[gradient_type]
            gradient_colors = []
            
            for i in range(steps):
                t = i / (steps - 1)
                eased_t = easing_func(t)
                
                # Interpolazione RGB
                interpolated_rgb = tuple(
                    int(start_rgb[j] * (1 - eased_t) + end_rgb[j] * eased_t)
                    for j in range(3)
                )
                
                hex_color = f"#{interpolated_rgb[0]:02X}{interpolated_rgb[1]:02X}{interpolated_rgb[2]:02X}"
                
                gradient_colors.append({
                    "step": i + 1,
                    "position": round(t * 100, 1),
                    "hex": hex_color,
                    "rgb": interpolated_rgb,
                    "css_stop": f"{hex_color} {round(t * 100, 1)}%"
                })
            
            # Genera CSS
            css_linear = f"linear-gradient(90deg, {', '.join([color['css_stop'] for color in gradient_colors])})"
            css_radial = f"radial-gradient(circle, {', '.join([color['css_stop'] for color in gradient_colors])})"
            
            return {
                "success": True,
                "start_color": start_color.upper(),
                "end_color": end_color.upper(),
                "steps": steps,
                "gradient_type": gradient_type,
                "colors": gradient_colors,
                "css": {
                    "linear": css_linear,
                    "radial": css_radial
                },
                "analysis": _analyze_gradient_harmony(gradient_colors)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def simulate_color_blindness(colors: List[str], blindness_type: str = "deuteranopia") -> Dict[str, Any]:
        """
        Simula come i colori appaiono a persone con daltonismo.
        
        Args:
            colors: Lista di colori in formato hex
            blindness_type: Tipo di daltonismo (protanopia, deuteranopia, tritanopia, achromatopsia)
        """
        try:
            if len(colors) > 10:
                return {"success": False, "error": "Massimo 10 colori supportati"}
            
            blindness_types = {
                "protanopia": "Cecità al rosso",
                "deuteranopia": "Cecità al verde", 
                "tritanopia": "Cecità al blu",
                "achromatopsia": "Acromatopsia (scala di grigi)"
            }
            
            if blindness_type not in blindness_types:
                return {"success": False, "error": f"Tipo non supportato. Disponibili: {list(blindness_types.keys())}"}
            
            simulated_colors = []
            
            for color in colors:
                rgb = _parse_hex_color(color)
                if not rgb:
                    return {"success": False, "error": f"Colore '{color}' non valido"}
                
                simulated_rgb = _simulate_colorblind_vision(rgb, blindness_type)
                simulated_hex = f"#{simulated_rgb[0]:02X}{simulated_rgb[1]:02X}{simulated_rgb[2]:02X}"
                
                # Calcola differenza percettiva
                difference = _calculate_color_difference(rgb, simulated_rgb)
                
                simulated_colors.append({
                    "original_color": color.upper(),
                    "original_rgb": rgb,
                    "simulated_color": simulated_hex,
                    "simulated_rgb": simulated_rgb,
                    "difference_score": round(difference, 2),
                    "visibility": "Buona" if difference < 10 else "Media" if difference < 30 else "Scarsa"
                })
            
            return {
                "success": True,
                "blindness_type": blindness_type,
                "description": blindness_types[blindness_type],
                "simulated_colors": simulated_colors,
                "accessibility_analysis": _analyze_colorblind_accessibility(simulated_colors),
                "recommendations": _generate_colorblind_recommendations(simulated_colors)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_color_psychology(colors: List[str]) -> Dict[str, Any]:
        """
        Analizza la psicologia e significato dei colori.
        
        Args:
            colors: Lista di colori in formato hex
        """
        try:
            if len(colors) > 8:
                return {"success": False, "error": "Massimo 8 colori supportati"}
            
            color_analyses = []
            
            for color in colors:
                rgb = _parse_hex_color(color)
                if not rgb:
                    return {"success": False, "error": f"Colore '{color}' non valido"}
                
                analysis = _analyze_single_color_psychology(rgb, color)
                color_analyses.append(analysis)
            
            # Analisi combinazione colori
            combination_analysis = _analyze_color_combination_psychology(color_analyses)
            
            return {
                "success": True,
                "individual_analysis": color_analyses,
                "combination_analysis": combination_analysis,
                "overall_mood": _determine_overall_mood(color_analyses),
                "design_recommendations": _generate_psychology_design_tips(color_analyses)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def find_closest_named_color(color: str, color_system: str = "css") -> Dict[str, Any]:
        """
        Trova il colore nominato più vicino a un colore dato.
        
        Args:
            color: Colore in formato hex
            color_system: Sistema di colori (css, pantone, ral, x11)
        """
        try:
            rgb = _parse_hex_color(color)
            if not rgb:
                return {"success": False, "error": f"Colore '{color}' non valido"}
            
            color_databases = _get_color_databases()
            
            if color_system not in color_databases:
                return {"success": False, "error": f"Sistema non supportato. Disponibili: {list(color_databases.keys())}"}
            
            named_colors = color_databases[color_system]
            closest_matches = []
            
            for name, named_rgb in named_colors.items():
                distance = _calculate_color_distance(rgb, named_rgb)
                closest_matches.append({
                    "name": name,
                    "hex": f"#{named_rgb[0]:02X}{named_rgb[1]:02X}{named_rgb[2]:02X}",
                    "rgb": named_rgb,
                    "distance": round(distance, 2)
                })
            
            # Ordina per distanza
            closest_matches.sort(key=lambda x: x["distance"])
            
            return {
                "success": True,
                "input_color": color.upper(),
                "input_rgb": rgb,
                "color_system": color_system,
                "closest_match": closest_matches[0],
                "alternative_matches": closest_matches[1:6],  # Top 5 alternative
                "exact_match": closest_matches[0]["distance"] == 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_color_scheme(base_color: str, scheme_type: str = "monochromatic", 
                            count: int = 5) -> Dict[str, Any]:
        """
        Genera schemi di colori professionali basati su teoria del colore.
        
        Args:
            base_color: Colore base in formato hex
            scheme_type: Tipo schema (monochromatic, analogous, complementary, triadic, tetradic, split_complementary)
            count: Numero di colori da generare (3-10)
        """
        try:
            if not 3 <= count <= 10:
                return {"success": False, "error": "Count deve essere tra 3 e 10"}
            
            rgb = _parse_hex_color(base_color)
            if not rgb:
                return {"success": False, "error": f"Colore base '{base_color}' non valido"}
            
            h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
            h_deg = h * 360
            
            scheme_generators = {
                "monochromatic": lambda: _generate_monochromatic_scheme(h, s, v, count),
                "analogous": lambda: _generate_analogous_scheme(h, s, v, count),
                "complementary": lambda: _generate_complementary_scheme(h, s, v, count),
                "triadic": lambda: _generate_triadic_scheme(h, s, v, count),
                "tetradic": lambda: _generate_tetradic_scheme(h, s, v, count),
                "split_complementary": lambda: _generate_split_complementary_scheme(h, s, v, count)
            }
            
            if scheme_type not in scheme_generators:
                return {"success": False, "error": f"Schema non supportato. Disponibili: {list(scheme_generators.keys())}"}
            
            hsv_colors = scheme_generators[scheme_type]()
            
            color_scheme = []
            for i, (h_val, s_val, v_val) in enumerate(hsv_colors):
                rgb_color = colorsys.hsv_to_rgb(h_val, s_val, v_val)
                rgb_int = tuple(int(c * 255) for c in rgb_color)
                hex_color = f"#{rgb_int[0]:02X}{rgb_int[1]:02X}{rgb_int[2]:02X}"
                
                color_scheme.append({
                    "index": i + 1,
                    "hex": hex_color,
                    "rgb": rgb_int,
                    "hsv": (round(h_val * 360, 1), round(s_val * 100, 1), round(v_val * 100, 1)),
                    "role": _determine_color_role(i, scheme_type, len(hsv_colors))
                })
            
            return {
                "success": True,
                "base_color": base_color.upper(),
                "scheme_type": scheme_type,
                "color_count": len(color_scheme),
                "color_scheme": color_scheme,
                "harmony_analysis": _analyze_color_harmony(color_scheme),
                "usage_suggestions": _generate_usage_suggestions(scheme_type, color_scheme)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_color_temperature(colors: List[str]) -> Dict[str, Any]:
        """
        Analizza la temperatura dei colori (caldi, freddi, neutri).
        
        Args:
            colors: Lista di colori in formato hex
        """
        try:
            if len(colors) > 10:
                return {"success": False, "error": "Massimo 10 colori supportati"}
            
            color_temperatures = []
            
            for color in colors:
                rgb = _parse_hex_color(color)
                if not rgb:
                    return {"success": False, "error": f"Colore '{color}' non valido"}
                
                temperature_analysis = _calculate_color_temperature(rgb, color)
                color_temperatures.append(temperature_analysis)
            
            # Analisi complessiva
            warm_colors = [c for c in color_temperatures if c["temperature_category"] == "Caldo"]
            cool_colors = [c for c in color_temperatures if c["temperature_category"] == "Freddo"]
            neutral_colors = [c for c in color_temperatures if c["temperature_category"] == "Neutro"]
            
            overall_temperature = _determine_overall_temperature(color_temperatures)
            
            return {
                "success": True,
                "color_temperatures": color_temperatures,
                "summary": {
                    "warm_colors": len(warm_colors),
                    "cool_colors": len(cool_colors),
                    "neutral_colors": len(neutral_colors),
                    "overall_temperature": overall_temperature
                },
                "design_implications": _generate_temperature_design_advice(overall_temperature),
                "seasonal_associations": _get_seasonal_associations(color_temperatures)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def export_color_palette(colors: List[str], export_format: str = "css", 
                           palette_name: str = "Custom Palette") -> Dict[str, Any]:
        """
        Esporta palette di colori in vari formati per tool di design.
        
        Args:
            colors: Lista di colori in formato hex
            export_format: Formato export (css, scss, json, ase, gpl, xml)
            palette_name: Nome della palette
        """
        try:
            if len(colors) > 20:
                return {"success": False, "error": "Massimo 20 colori supportati"}
            
            if not all(_parse_hex_color(color) for color in colors):
                return {"success": False, "error": "Uno o più colori non sono validi"}
            
            export_functions = {
                "css": _export_css_variables,
                "scss": _export_scss_variables,
                "json": _export_json_palette,
                "ase": _export_ase_info,  # Adobe Swatch Exchange info
                "gpl": _export_gimp_palette,
                "xml": _export_xml_palette
            }
            
            if export_format not in export_functions:
                return {"success": False, "error": f"Formato non supportato. Disponibili: {list(export_functions.keys())}"}
            
            exported_content = export_functions[export_format](colors, palette_name)
            
            return {
                "success": True,
                "palette_name": palette_name,
                "export_format": export_format,
                "color_count": len(colors),
                "exported_content": exported_content,
                "filename_suggestion": _suggest_filename(palette_name, export_format),
                "usage_instructions": _get_usage_instructions(export_format)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions for enhanced functionality
    def _parse_hex_color(color: str) -> Optional[Tuple[int, int, int]]:
        """Parse colore hex in RGB."""
        hex_match = re.match(r'^#?([0-9A-Fa-f]{6})$', color.strip())
        if hex_match:
            hex_val = hex_match.group(1)
            return tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
        return None

    def _simulate_colorblind_vision(rgb: Tuple[int, int, int], blindness_type: str) -> Tuple[int, int, int]:
        """Simula visione daltonismo."""
        r, g, b = rgb
        
        if blindness_type == "protanopia":
            # Cecità al rosso
            new_r = int(0.567 * r + 0.433 * g)
            new_g = int(0.558 * r + 0.442 * g)
            new_b = int(0.242 * g + 0.758 * b)
        elif blindness_type == "deuteranopia":
            # Cecità al verde
            new_r = int(0.625 * r + 0.375 * g)
            new_g = int(0.7 * r + 0.3 * g)
            new_b = int(0.3 * g + 0.7 * b)
        elif blindness_type == "tritanopia":
            # Cecità al blu
            new_r = int(0.95 * r + 0.05 * g)
            new_g = int(0.433 * g + 0.567 * b)
            new_b = int(0.475 * g + 0.525 * b)
        elif blindness_type == "achromatopsia":
            # Scala di grigi
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            new_r = new_g = new_b = gray
        else:
            return rgb
        
        return (
            max(0, min(255, new_r)),
            max(0, min(255, new_g)),
            max(0, min(255, new_b))
        )

    def _calculate_color_difference(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        """Calcola differenza percettiva tra colori (Delta E)."""
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        
        # Formula Delta E semplificata
        return math.sqrt((r2-r1)**2 + (g2-g1)**2 + (b2-b1)**2)

    def _analyze_single_color_psychology(rgb: Tuple[int, int, int], hex_color: str) -> Dict[str, Any]:
        """Analizza psicologia di un singolo colore."""
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        h_deg = h * 360
        
        # Determina colore dominante
        if h_deg < 15 or h_deg >= 345:
            base_color = "Rosso"
            psychology = {
                "emotions": ["passione", "energia", "forza", "amore"],
                "traits": ["dinamismo", "aggressività", "leadership"],
                "use_cases": ["call-to-action", "emergency", "food", "entertainment"]
            }
        elif h_deg < 45:
            base_color = "Arancione"
            psychology = {
                "emotions": ["entusiasmo", "creatività", "avventura"],
                "traits": ["socievolezza", "ottimismo", "spontaneità"],
                "use_cases": ["brands giovanili", "sport", "entertainment"]
            }
        elif h_deg < 75:
            base_color = "Giallo"
            psychology = {
                "emotions": ["felicità", "ottimismo", "energia"],
                "traits": ["intelligenza", "creatività", "attenzione"],
                "use_cases": ["bambini", "warning", "food", "education"]
            }
        elif h_deg < 165:
            base_color = "Verde"
            psychology = {
                "emotions": ["natura", "crescita", "armonia", "pace"],
                "traits": ["equilibrio", "freschezza", "salute"],
                "use_cases": ["health", "environment", "finance", "outdoor"]
            }
        elif h_deg < 245:
            base_color = "Blu"
            psychology = {
                "emotions": ["calma", "fiducia", "professionalità"],
                "traits": ["stabilità", "lealtà", "intelletto"],
                "use_cases": ["corporate", "technology", "healthcare", "finance"]
            }
        elif h_deg < 285:
            base_color = "Viola"
            psychology = {
                "emotions": ["lusso", "mistero", "creatività"],
                "traits": ["spiritualità", "immaginazione", "regalità"],
                "use_cases": ["luxury", "beauty", "creative", "spiritual"]
            }
        else:
            base_color = "Rosa/Magenta"
            psychology = {
                "emotions": ["amore", "compassione", "nurturing"],
                "traits": ["femminilità", "dolcezza", "romanticismo"],
                "use_cases": ["beauty", "fashion", "children", "romance"]
            }
        
        return {
            "hex": hex_color.upper(),
            "rgb": rgb,
            "base_color": base_color,
            "saturation_level": "Alta" if s > 0.7 else "Media" if s > 0.3 else "Bassa",
            "brightness_level": "Alta" if v > 0.7 else "Media" if v > 0.3 else "Bassa",
            "psychology": psychology
        }

    def _get_color_databases(self) -> Dict[str, Dict[str, Tuple[int, int, int]]]:
        """Restituisce database di colori nominati."""
        return {
            "css": {
                "red": (255, 0, 0),
                "green": (0, 128, 0),
                "blue": (0, 0, 255),
                "white": (255, 255, 255),
                "black": (0, 0, 0),
                "yellow": (255, 255, 0),
                "cyan": (0, 255, 255),
                "magenta": (255, 0, 255),
                "orange": (255, 165, 0),
                "purple": (128, 0, 128),
                "pink": (255, 192, 203),
                "brown": (165, 42, 42),
                "gray": (128, 128, 128),
                "navy": (0, 0, 128),
                "olive": (128, 128, 0),
                "lime": (0, 255, 0),
                "aqua": (0, 255, 255),
                "teal": (0, 128, 128),
                "silver": (192, 192, 192),
                "maroon": (128, 0, 0)
            }
        }

    def _export_css_variables(self, colors: List[str], palette_name: str) -> str:
        """Esporta palette come variabili CSS."""
        css = f"/* {palette_name} */\n:root {{\n"
        
        for i, color in enumerate(colors, 1):
            var_name = f"--color-{i:02d}"
            css += f"  {var_name}: {color.upper()};\n"
        
        css += "}\n\n/* Usage examples */\n"
        css += ".primary { color: var(--color-01); }\n"
        css += ".secondary { color: var(--color-02); }\n"
        
        return css

    def _export_json_palette(self, colors: List[str], palette_name: str) -> str:
        """Esporta palette come JSON."""
        palette_data = {
            "name": palette_name,
            "created": datetime.now(timezone.utc).isoformat(),
            "colors": []
        }
        
        for i, color in enumerate(colors, 1):
            rgb = _parse_hex_color(color)
            palette_data["colors"].append({
                "id": f"color-{i:02d}",
                "hex": color.upper(),
                "rgb": {"r": rgb[0], "g": rgb[1], "b": rgb[2]} if rgb else None
            })
        
        return json.dumps(palette_data, indent=2)