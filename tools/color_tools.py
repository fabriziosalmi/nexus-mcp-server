# -*- coding: utf-8 -*-
# tools/color_tools.py
import logging
import colorsys
import re

def register_tools(mcp):
    """Registra i tool per la gestione colori con l'istanza del server MCP."""
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