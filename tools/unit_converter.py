# -*- coding: utf-8 -*-
# tools/unit_converter.py
import logging

def register_tools(mcp):
    """Registra i tool di conversione unità con l'istanza del server MCP."""
    logging.info("🔄 Registrazione tool-set: Unit Converter Tools")

    @mcp.tool()
    def convert_length(value: float, from_unit: str, to_unit: str) -> str:
        """
        Converte unità di lunghezza.

        Args:
            value: Il valore da convertire.
            from_unit: Unità di partenza (mm, cm, m, km, in, ft, yd, mi).
            to_unit: Unità di destinazione (mm, cm, m, km, in, ft, yd, mi).
        """
        try:
            # Conversioni verso metri
            to_meters = {
                'mm': 0.001,
                'cm': 0.01,
                'm': 1.0,
                'km': 1000.0,
                'in': 0.0254,
                'ft': 0.3048,
                'yd': 0.9144,
                'mi': 1609.344
            }
            
            if from_unit not in to_meters:
                return f"ERRORE: Unità '{from_unit}' non supportata. Unità disponibili: {', '.join(to_meters.keys())}"
            
            if to_unit not in to_meters:
                return f"ERRORE: Unità '{to_unit}' non supportata. Unità disponibili: {', '.join(to_meters.keys())}"
            
            # Converti in metri, poi nell'unità di destinazione
            meters = value * to_meters[from_unit]
            result = meters / to_meters[to_unit]
            
            return f"{value} {from_unit} = {result:.6f} {to_unit}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def convert_weight(value: float, from_unit: str, to_unit: str) -> str:
        """
        Converte unità di peso.

        Args:
            value: Il valore da convertire.
            from_unit: Unità di partenza (mg, g, kg, t, oz, lb, st).
            to_unit: Unità di destinazione (mg, g, kg, t, oz, lb, st).
        """
        try:
            # Conversioni verso grammi
            to_grams = {
                'mg': 0.001,
                'g': 1.0,
                'kg': 1000.0,
                't': 1000000.0,
                'oz': 28.3495,
                'lb': 453.592,
                'st': 6350.29
            }
            
            if from_unit not in to_grams:
                return f"ERRORE: Unità '{from_unit}' non supportata. Unità disponibili: {', '.join(to_grams.keys())}"
            
            if to_unit not in to_grams:
                return f"ERRORE: Unità '{to_unit}' non supportata. Unità disponibili: {', '.join(to_grams.keys())}"
            
            # Converti in grammi, poi nell'unità di destinazione
            grams = value * to_grams[from_unit]
            result = grams / to_grams[to_unit]
            
            return f"{value} {from_unit} = {result:.6f} {to_unit}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def convert_temperature(value: float, from_unit: str, to_unit: str) -> str:
        """
        Converte unità di temperatura.

        Args:
            value: Il valore da convertire.
            from_unit: Unità di partenza (C, F, K, R).
            to_unit: Unità di destinazione (C, F, K, R).
        """
        try:
            valid_units = ['C', 'F', 'K', 'R']
            
            if from_unit not in valid_units:
                return f"ERRORE: Unità '{from_unit}' non supportata. Unità disponibili: {', '.join(valid_units)}"
            
            if to_unit not in valid_units:
                return f"ERRORE: Unità '{to_unit}' non supportata. Unità disponibili: {', '.join(valid_units)}"
            
            # Converti tutto in Celsius prima
            if from_unit == 'C':
                celsius = value
            elif from_unit == 'F':
                celsius = (value - 32) * 5/9
            elif from_unit == 'K':
                celsius = value - 273.15
            elif from_unit == 'R':
                celsius = (value - 491.67) * 5/9
            
            # Converti da Celsius all'unità di destinazione
            if to_unit == 'C':
                result = celsius
            elif to_unit == 'F':
                result = celsius * 9/5 + 32
            elif to_unit == 'K':
                result = celsius + 273.15
            elif to_unit == 'R':
                result = celsius * 9/5 + 491.67
            
            return f"{value}°{from_unit} = {result:.2f}°{to_unit}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def convert_volume(value: float, from_unit: str, to_unit: str) -> str:
        """
        Converte unità di volume.

        Args:
            value: Il valore da convertire.
            from_unit: Unità di partenza (ml, l, gal, qt, pt, cup, floz).
            to_unit: Unità di destinazione (ml, l, gal, qt, pt, cup, floz).
        """
        try:
            # Conversioni verso millilitri
            to_ml = {
                'ml': 1.0,
                'l': 1000.0,
                'gal': 3785.41,  # US gallon
                'qt': 946.353,   # US quart
                'pt': 473.176,   # US pint
                'cup': 236.588,  # US cup
                'floz': 29.5735  # US fluid ounce
            }
            
            if from_unit not in to_ml:
                return f"ERRORE: Unità '{from_unit}' non supportata. Unità disponibili: {', '.join(to_ml.keys())}"
            
            if to_unit not in to_ml:
                return f"ERRORE: Unità '{to_unit}' non supportata. Unità disponibili: {', '.join(to_ml.keys())}"
            
            # Converti in millilitri, poi nell'unità di destinazione
            milliliters = value * to_ml[from_unit]
            result = milliliters / to_ml[to_unit]
            
            return f"{value} {from_unit} = {result:.6f} {to_unit}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def convert_area(value: float, from_unit: str, to_unit: str) -> str:
        """
        Converte unità di area.

        Args:
            value: Il valore da convertire.
            from_unit: Unità di partenza (mm2, cm2, m2, km2, in2, ft2, yd2, ac, ha).
            to_unit: Unità di destinazione (mm2, cm2, m2, km2, in2, ft2, yd2, ac, ha).
        """
        try:
            # Conversioni verso metri quadrati
            to_m2 = {
                'mm2': 0.000001,
                'cm2': 0.0001,
                'm2': 1.0,
                'km2': 1000000.0,
                'in2': 0.00064516,
                'ft2': 0.092903,
                'yd2': 0.836127,
                'ac': 4046.86,    # acre
                'ha': 10000.0     # hectare
            }
            
            if from_unit not in to_m2:
                return f"ERRORE: Unità '{from_unit}' non supportata. Unità disponibili: {', '.join(to_m2.keys())}"
            
            if to_unit not in to_m2:
                return f"ERRORE: Unità '{to_unit}' non supportata. Unità disponibili: {', '.join(to_m2.keys())}"
            
            # Converti in metri quadrati, poi nell'unità di destinazione
            square_meters = value * to_m2[from_unit]
            result = square_meters / to_m2[to_unit]
            
            return f"{value} {from_unit} = {result:.6f} {to_unit}"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def list_available_units() -> str:
        """
        Elenca tutte le unità di misura disponibili per categoria.
        """
        try:
            categories = {
                "Lunghezza": ["mm", "cm", "m", "km", "in", "ft", "yd", "mi"],
                "Peso": ["mg", "g", "kg", "t", "oz", "lb", "st"],
                "Temperatura": ["C", "F", "K", "R"],
                "Volume": ["ml", "l", "gal", "qt", "pt", "cup", "floz"],
                "Area": ["mm2", "cm2", "m2", "km2", "in2", "ft2", "yd2", "ac", "ha"]
            }
            
            result = "=== UNITÀ DI MISURA DISPONIBILI ===\n"
            for category, units in categories.items():
                result += f"\n{category}:\n"
                result += f"  {', '.join(units)}\n"
            
            return result
        except Exception as e:
            return f"ERRORE: {str(e)}"