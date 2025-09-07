# -*- coding: utf-8 -*-
# tools/calculator.py
import logging
import math
import re
from typing import Dict, List, Any, Union, Optional, Tuple
from decimal import Decimal, getcontext, InvalidOperation
import statistics
from fractions import Fraction

# Set high precision for decimal operations
getcontext().prec = 50

def register_tools(mcp):
    """Registra i tool matematici avanzati con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Calcolatrice Avanzata")

    @mcp.tool()
    def add(a: float, b: float) -> float:
        """
        Calcola la somma di due numeri (a + b).

        Args:
            a: Il primo addendo.
            b: Il secondo addendo.
        """
        return a + b

    @mcp.tool()
    def multiply(a: float, b: float) -> float:
        """
        Calcola il prodotto di due numeri (a * b).

        Args:
            a: Il primo fattore.
            b: Il secondo fattore.
        """
        return a * b

    @mcp.tool()
    def subtract(a: float, b: float) -> float:
        """
        Calcola la differenza di due numeri (a - b).

        Args:
            a: Il minuendo.
            b: Il sottraendo.
        """
        return a - b

    @mcp.tool()
    def divide(a: float, b: float) -> Dict[str, Any]:
        """
        Calcola la divisione di due numeri (a / b) con controlli di sicurezza.

        Args:
            a: Il dividendo.
            b: Il divisore.
        """
        try:
            if b == 0:
                return {
                    "success": False,
                    "error": "Divisione per zero non permessa",
                    "result": None
                }
            
            result = a / b
            
            return {
                "success": True,
                "result": result,
                "dividend": a,
                "divisor": b,
                "quotient": result,
                "remainder": a % b if b != 0 else None,
                "is_integer": result.is_integer() if isinstance(result, float) else False
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def power(base: float, exponent: float) -> Dict[str, Any]:
        """
        Calcola la potenza di un numero (base^exponent).

        Args:
            base: La base.
            exponent: L'esponente.
        """
        try:
            # Controlli di sicurezza per evitare overflow
            if abs(base) > 1000 and abs(exponent) > 100:
                return {
                    "success": False,
                    "error": "Operazione troppo grande, potrebbe causare overflow"
                }
            
            result = base ** exponent
            
            # Controllo se il risultato è troppo grande
            if abs(result) > 1e15:
                return {
                    "success": False,
                    "error": "Risultato troppo grande per essere rappresentato accuratamente"
                }
            
            return {
                "success": True,
                "result": result,
                "base": base,
                "exponent": exponent,
                "operation": f"{base}^{exponent}",
                "is_integer": isinstance(result, int) or (isinstance(result, float) and result.is_integer())
            }
        except (OverflowError, ValueError) as e:
            return {"success": False, "error": f"Errore nel calcolo: {str(e)}"}

    @mcp.tool()
    def square_root(number: float) -> Dict[str, Any]:
        """
        Calcola la radice quadrata di un numero.

        Args:
            number: Il numero di cui calcolare la radice quadrata.
        """
        try:
            if number < 0:
                return {
                    "success": False,
                    "error": "Impossibile calcolare la radice quadrata di un numero negativo",
                    "suggestion": "Usa complex_square_root per numeri complessi"
                }
            
            result = math.sqrt(number)
            
            return {
                "success": True,
                "result": result,
                "input": number,
                "verification": result * result,
                "is_perfect_square": result.is_integer()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def nth_root(number: float, n: int) -> Dict[str, Any]:
        """
        Calcola la radice n-esima di un numero.

        Args:
            number: Il numero.
            n: L'indice della radice.
        """
        try:
            if n == 0:
                return {"success": False, "error": "L'indice della radice non può essere zero"}
            
            if number < 0 and n % 2 == 0:
                return {
                    "success": False,
                    "error": "Impossibile calcolare radice pari di numero negativo nei reali"
                }
            
            # Per radici dispari di numeri negativi
            if number < 0 and n % 2 == 1:
                result = -(abs(number) ** (1/n))
            else:
                result = number ** (1/n)
            
            return {
                "success": True,
                "result": result,
                "number": number,
                "root_index": n,
                "verification": result ** n,
                "operation": f"√[{n}]{number}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def factorial(n: int) -> Dict[str, Any]:
        """
        Calcola il fattoriale di un numero intero.

        Args:
            n: Il numero di cui calcolare il fattoriale (deve essere >= 0).
        """
        try:
            if not isinstance(n, int):
                n = int(n)
            
            if n < 0:
                return {"success": False, "error": "Il fattoriale non è definito per numeri negativi"}
            
            if n > 170:
                return {"success": False, "error": "Numero troppo grande, risultato causerebbe overflow"}
            
            result = math.factorial(n)
            
            return {
                "success": True,
                "result": result,
                "input": n,
                "operation": f"{n}!",
                "digits_count": len(str(result))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def trigonometric_functions(angle: float, unit: str = "radians", functions: List[str] = None) -> Dict[str, Any]:
        """
        Calcola funzioni trigonometriche per un angolo.

        Args:
            angle: L'angolo.
            unit: Unità dell'angolo ("radians", "degrees").
            functions: Lista delle funzioni da calcolare ["sin", "cos", "tan", "cot", "sec", "csc"].
        """
        try:
            if functions is None:
                functions = ["sin", "cos", "tan"]
            
            # Converti in radianti se necessario
            if unit.lower() == "degrees":
                angle_rad = math.radians(angle)
                angle_display = f"{angle}°"
            else:
                angle_rad = angle
                angle_display = f"{angle} rad"
            
            results = {}
            
            for func in functions:
                try:
                    if func.lower() == "sin":
                        results["sin"] = math.sin(angle_rad)
                    elif func.lower() == "cos":
                        results["cos"] = math.cos(angle_rad)
                    elif func.lower() == "tan":
                        results["tan"] = math.tan(angle_rad)
                    elif func.lower() == "cot":
                        tan_val = math.tan(angle_rad)
                        results["cot"] = 1 / tan_val if tan_val != 0 else float('inf')
                    elif func.lower() == "sec":
                        cos_val = math.cos(angle_rad)
                        results["sec"] = 1 / cos_val if cos_val != 0 else float('inf')
                    elif func.lower() == "csc":
                        sin_val = math.sin(angle_rad)
                        results["csc"] = 1 / sin_val if sin_val != 0 else float('inf')
                except ValueError as e:
                    results[func] = f"Errore: {str(e)}"
            
            return {
                "success": True,
                "angle": angle_display,
                "angle_radians": angle_rad,
                "results": results,
                "quadrant": self._get_quadrant(angle_rad)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_quadrant(self, angle_rad: float) -> int:
        """Determina il quadrante di un angolo."""
        # Normalizza l'angolo tra 0 e 2π
        normalized = angle_rad % (2 * math.pi)
        
        if 0 <= normalized < math.pi/2:
            return 1
        elif math.pi/2 <= normalized < math.pi:
            return 2
        elif math.pi <= normalized < 3*math.pi/2:
            return 3
        else:
            return 4

    @mcp.tool()
    def logarithms(number: float, base: Optional[float] = None) -> Dict[str, Any]:
        """
        Calcola logaritmi in diverse basi.

        Args:
            number: Il numero di cui calcolare il logaritmo.
            base: La base del logaritmo (None per logaritmo naturale).
        """
        try:
            if number <= 0:
                return {"success": False, "error": "Il logaritmo è definito solo per numeri positivi"}
            
            results = {}
            
            # Logaritmo naturale
            results["ln"] = math.log(number)
            
            # Logaritmo in base 10
            results["log10"] = math.log10(number)
            
            # Logaritmo in base 2
            results["log2"] = math.log2(number)
            
            # Logaritmo in base specifica se fornita
            if base is not None:
                if base <= 0 or base == 1:
                    return {"success": False, "error": "La base del logaritmo deve essere positiva e diversa da 1"}
                results[f"log_{base}"] = math.log(number, base)
            
            return {
                "success": True,
                "number": number,
                "logarithms": results,
                "base_used": base
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def statistics_functions(numbers: List[float], operation: str = "all") -> Dict[str, Any]:
        """
        Calcola statistiche per una lista di numeri.

        Args:
            numbers: Lista di numeri.
            operation: Operazione specifica o "all" per tutte.
        """
        try:
            if not numbers:
                return {"success": False, "error": "La lista non può essere vuota"}
            
            results = {}
            
            if operation in ["mean", "all"]:
                results["mean"] = statistics.mean(numbers)
            
            if operation in ["median", "all"]:
                results["median"] = statistics.median(numbers)
            
            if operation in ["mode", "all"]:
                try:
                    results["mode"] = statistics.mode(numbers)
                except statistics.StatisticsError:
                    results["mode"] = "Nessuna moda unica"
            
            if operation in ["stdev", "all"] and len(numbers) > 1:
                results["standard_deviation"] = statistics.stdev(numbers)
                results["variance"] = statistics.variance(numbers)
            
            if operation in ["range", "all"]:
                results["range"] = max(numbers) - min(numbers)
                results["min"] = min(numbers)
                results["max"] = max(numbers)
            
            if operation in ["sum", "all"]:
                results["sum"] = sum(numbers)
                results["count"] = len(numbers)
            
            return {
                "success": True,
                "data": numbers,
                "statistics": results,
                "sample_size": len(numbers)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def number_theory(a: int, b: Optional[int] = None, operation: str = "gcd") -> Dict[str, Any]:
        """
        Funzioni di teoria dei numeri.

        Args:
            a: Primo numero intero.
            b: Secondo numero intero (opzionale).
            operation: Operazione ("gcd", "lcm", "prime_factors", "is_prime").
        """
        try:
            results = {}
            
            if operation == "gcd" and b is not None:
                results["gcd"] = math.gcd(a, b)
                results["operation"] = f"GCD({a}, {b})"
            
            elif operation == "lcm" and b is not None:
                gcd_val = math.gcd(a, b)
                lcm_val = abs(a * b) // gcd_val
                results["lcm"] = lcm_val
                results["gcd"] = gcd_val
                results["operation"] = f"LCM({a}, {b})"
            
            elif operation == "prime_factors":
                results["prime_factors"] = self._prime_factorization(abs(a))
                results["number"] = a
            
            elif operation == "is_prime":
                results["is_prime"] = self._is_prime(abs(a))
                results["number"] = a
                if results["is_prime"]:
                    results["prime_type"] = self._classify_prime(abs(a))
            
            else:
                return {"success": False, "error": f"Operazione '{operation}' non supportata o parametri mancanti"}
            
            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _prime_factorization(self, n: int) -> List[int]:
        """Fattorizzazione in numeri primi."""
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors

    def _is_prime(self, n: int) -> bool:
        """Verifica se un numero è primo."""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True

    def _classify_prime(self, n: int) -> str:
        """Classifica il tipo di numero primo."""
        if n == 2:
            return "Unico primo pari"
        elif (n - 1) % 4 == 0:
            return "Primo della forma 4k+1"
        else:
            return "Primo della forma 4k+3"

    @mcp.tool()
    def unit_converter(value: float, from_unit: str, to_unit: str, unit_type: str) -> Dict[str, Any]:
        """
        Converte unità di misura.

        Args:
            value: Il valore da convertire.
            from_unit: Unità di partenza.
            to_unit: Unità di destinazione.
            unit_type: Tipo di unità ("length", "weight", "temperature", "volume", "time").
        """
        try:
            conversions = {
                "length": {
                    "meter": 1.0,
                    "kilometer": 1000.0,
                    "centimeter": 0.01,
                    "millimeter": 0.001,
                    "inch": 0.0254,
                    "foot": 0.3048,
                    "yard": 0.9144,
                    "mile": 1609.344
                },
                "weight": {
                    "kilogram": 1.0,
                    "gram": 0.001,
                    "pound": 0.453592,
                    "ounce": 0.0283495,
                    "ton": 1000.0
                },
                "volume": {
                    "liter": 1.0,
                    "milliliter": 0.001,
                    "gallon": 3.78541,
                    "quart": 0.946353,
                    "pint": 0.473176,
                    "cup": 0.236588
                },
                "time": {
                    "second": 1.0,
                    "minute": 60.0,
                    "hour": 3600.0,
                    "day": 86400.0,
                    "week": 604800.0,
                    "year": 31536000.0
                }
            }
            
            if unit_type not in conversions:
                return {"success": False, "error": f"Tipo di unità '{unit_type}' non supportato"}
            
            unit_dict = conversions[unit_type]
            
            if from_unit not in unit_dict or to_unit not in unit_dict:
                return {
                    "success": False,
                    "error": f"Unità non supportate per il tipo '{unit_type}'",
                    "available_units": list(unit_dict.keys())
                }
            
            # Temperatura richiede trattamento speciale
            if unit_type == "temperature":
                result = self._convert_temperature(value, from_unit, to_unit)
            else:
                # Converti in unità base, poi nell'unità target
                base_value = value * unit_dict[from_unit]
                result = base_value / unit_dict[to_unit]
            
            return {
                "success": True,
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": result,
                "converted_unit": to_unit,
                "conversion_factor": unit_dict[to_unit] / unit_dict[from_unit] if unit_type != "temperature" else "N/A",
                "unit_type": unit_type
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Converte temperature tra Celsius, Fahrenheit e Kelvin."""
        # Converti tutto in Celsius prima
        if from_unit.lower() == "fahrenheit":
            celsius = (value - 32) * 5/9
        elif from_unit.lower() == "kelvin":
            celsius = value - 273.15
        else:  # celsius
            celsius = value
        
        # Converti da Celsius all'unità target
        if to_unit.lower() == "fahrenheit":
            return celsius * 9/5 + 32
        elif to_unit.lower() == "kelvin":
            return celsius + 273.15
        else:  # celsius
            return celsius

    @mcp.tool()
    def financial_calculator(principal: float, rate: float, time: float, 
                           calculation_type: str = "simple_interest", 
                           compound_frequency: int = 1) -> Dict[str, Any]:
        """
        Calcoli finanziari per interessi e investimenti.

        Args:
            principal: Capitale iniziale.
            rate: Tasso di interesse (in percentuale).
            time: Tempo (in anni).
            calculation_type: Tipo di calcolo ("simple_interest", "compound_interest", "present_value").
            compound_frequency: Frequenza di capitalizzazione per anno.
        """
        try:
            rate_decimal = rate / 100  # Converti percentuale in decimale
            
            results = {}
            
            if calculation_type == "simple_interest":
                interest = principal * rate_decimal * time
                total = principal + interest
                results = {
                    "simple_interest": interest,
                    "total_amount": total,
                    "principal": principal,
                    "effective_rate": (total / principal - 1) * 100
                }
            
            elif calculation_type == "compound_interest":
                total = principal * (1 + rate_decimal / compound_frequency) ** (compound_frequency * time)
                compound_interest = total - principal
                results = {
                    "compound_interest": compound_interest,
                    "total_amount": total,
                    "principal": principal,
                    "effective_annual_rate": ((total / principal) ** (1/time) - 1) * 100,
                    "compound_frequency": compound_frequency
                }
            
            elif calculation_type == "present_value":
                present_value = principal / (1 + rate_decimal) ** time
                results = {
                    "present_value": present_value,
                    "future_value": principal,
                    "discount_rate": rate,
                    "time_period": time
                }
            
            return {
                "success": True,
                "calculation_type": calculation_type,
                "parameters": {
                    "principal": principal,
                    "rate_percent": rate,
                    "time_years": time
                },
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def expression_evaluator(expression: str, variables: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Valuta espressioni matematiche sicure.

        Args:
            expression: Espressione matematica da valutare.
            variables: Dizionario di variabili (opzionale).
        """
        try:
            # Lista di funzioni sicure permesse
            safe_functions = {
                'abs': abs, 'round': round, 'min': min, 'max': max,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
                'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
                'log': math.log, 'log10': math.log10, 'log2': math.log2,
                'sqrt': math.sqrt, 'exp': math.exp, 'pow': pow,
                'pi': math.pi, 'e': math.e, 'factorial': math.factorial
            }
            
            # Combina funzioni sicure con variabili dell'utente
            safe_dict = safe_functions.copy()
            if variables:
                # Valida che le variabili siano numeriche
                for name, value in variables.items():
                    if not isinstance(value, (int, float)):
                        return {"success": False, "error": f"Variabile '{name}' deve essere numerica"}
                    safe_dict[name] = value
            
            # Verifica che l'espressione contenga solo caratteri sicuri
            allowed_chars = set('0123456789+-*/().abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ ')
            if not all(c in allowed_chars for c in expression):
                return {"success": False, "error": "Espressione contiene caratteri non permessi"}
            
            # Vieta certe parole chiave pericolose
            dangerous_keywords = ['import', 'exec', 'eval', '__', 'open', 'file']
            for keyword in dangerous_keywords:
                if keyword in expression.lower():
                    return {"success": False, "error": f"Parola chiave '{keyword}' non permessa"}
            
            # Valuta l'espressione in ambiente sicuro
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            # Verifica che il risultato sia un numero
            if not isinstance(result, (int, float, complex)):
                return {"success": False, "error": "Il risultato deve essere un numero"}
            
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "variables_used": variables or {},
                "result_type": type(result).__name__
            }
        except SyntaxError:
            return {"success": False, "error": "Errore di sintassi nell'espressione"}
        except ZeroDivisionError:
            return {"success": False, "error": "Divisione per zero nell'espressione"}
        except Exception as e:
            return {"success": False, "error": f"Errore nella valutazione: {str(e)}"}

    @mcp.tool()
    def mathematical_constants() -> Dict[str, Any]:
        """
        Restituisce costanti matematiche importanti con descrizioni.
        """
        constants = {
            "pi": {
                "value": math.pi,
                "description": "Rapporto tra circonferenza e diametro di un cerchio",
                "symbol": "π"
            },
            "e": {
                "value": math.e,
                "description": "Base del logaritmo naturale (numero di Eulero)",
                "symbol": "e"
            },
            "golden_ratio": {
                "value": (1 + math.sqrt(5)) / 2,
                "description": "Sezione aurea (phi)",
                "symbol": "φ"
            },
            "sqrt_2": {
                "value": math.sqrt(2),
                "description": "Radice quadrata di 2",
                "symbol": "√2"
            },
            "sqrt_3": {
                "value": math.sqrt(3),
                "description": "Radice quadrata di 3",
                "symbol": "√3"
            },
            "euler_gamma": {
                "value": 0.5772156649015329,
                "description": "Costante di Eulero-Mascheroni",
                "symbol": "γ"
            }
        }
        
        return {
            "constants": constants,
            "usage_note": "Queste costanti possono essere usate nell'expression_evaluator"
        }