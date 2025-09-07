# -*- coding: utf-8 -*-
# tools/data_analysis.py
import json
import csv
import logging
import statistics
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import re
import io

def register_tools(mcp):
    """Registra i tool di analisi dati con l'istanza del server MCP."""
    logging.info("📊 Registrazione tool-set: Data Analysis Tools")

    @mcp.tool()
    def analyze_csv_data(csv_content: str, delimiter: str = ",") -> Dict[str, Any]:
        """
        Analizza dati CSV e fornisce statistiche dettagliate.
        
        Args:
            csv_content: Contenuto CSV come stringa
            delimiter: Delimitatore CSV (default: ",")
        """
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
            rows = list(csv_reader)
            
            if not rows:
                return {"success": False, "error": "Nessun dato trovato nel CSV"}
            
            # Analisi colonne
            columns = list(rows[0].keys())
            column_analysis = {}
            
            for column in columns:
                values = [row[column] for row in rows if row[column]]
                
                # Tenta conversione numerica
                numeric_values = []
                for value in values:
                    try:
                        numeric_values.append(float(value))
                    except (ValueError, TypeError):
                        pass
                
                analysis = {
                    "total_count": len(values),
                    "non_empty_count": len([v for v in values if v]),
                    "empty_count": len(values) - len([v for v in values if v]),
                    "unique_count": len(set(values)),
                    "data_type": "numeric" if len(numeric_values) > len(values) * 0.8 else "text"
                }
                
                if numeric_values:
                    analysis.update({
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "average": round(statistics.mean(numeric_values), 2),
                        "median": round(statistics.median(numeric_values), 2),
                        "std_dev": round(statistics.stdev(numeric_values), 2) if len(numeric_values) > 1 else 0
                    })
                
                # Top valori più comuni
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1
                
                top_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                analysis["most_common"] = top_values
                
                column_analysis[column] = analysis
            
            return {
                "total_rows": len(rows),
                "total_columns": len(columns),
                "columns": columns,
                "column_analysis": column_analysis,
                "sample_rows": rows[:3],  # Prime 3 righe come campione
                "data_quality": "Buona" if all(a["empty_count"] < len(rows) * 0.1 for a in column_analysis.values()) else "Media"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_json_structure(json_content: str) -> Dict[str, Any]:
        """
        Analizza la struttura di dati JSON.
        
        Args:
            json_content: Contenuto JSON come stringa
        """
        try:
            data = json.loads(json_content)
            
            def analyze_structure(obj, path="root"):
                if isinstance(obj, dict):
                    return {
                        "type": "object",
                        "keys": list(obj.keys()),
                        "key_count": len(obj.keys()),
                        "children": {key: analyze_structure(value, f"{path}.{key}") 
                                   for key, value in list(obj.items())[:10]}  # Limita a 10 per performance
                    }
                elif isinstance(obj, list):
                    return {
                        "type": "array",
                        "length": len(obj),
                        "item_types": list(set(type(item).__name__ for item in obj[:100])),  # Prime 100
                        "sample_item": analyze_structure(obj[0], f"{path}[0]") if obj else None
                    }
                else:
                    return {
                        "type": type(obj).__name__,
                        "value": str(obj)[:100] + "..." if len(str(obj)) > 100 else str(obj)
                    }
            
            structure = analyze_structure(data)
            
            # Statistiche generali
            def count_elements(obj):
                if isinstance(obj, dict):
                    return 1 + sum(count_elements(v) for v in obj.values())
                elif isinstance(obj, list):
                    return 1 + sum(count_elements(item) for item in obj[:100])  # Limita per performance
                else:
                    return 1
            
            return {
                "structure": structure,
                "total_elements": count_elements(data),
                "json_size": len(json_content),
                "is_valid": True,
                "complexity": "Alta" if count_elements(data) > 1000 else "Media" if count_elements(data) > 100 else "Bassa"
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON non valido: {str(e)}",
                "is_valid": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def statistical_analysis(numbers: List[float]) -> Dict[str, Any]:
        """
        Esegue analisi statistica su una lista di numeri.
        
        Args:
            numbers: Lista di numeri da analizzare
        """
        try:
            if not numbers:
                return {"success": False, "error": "Lista vuota fornita"}
            
            # Converti a float e filtra valori non numerici
            clean_numbers = []
            for num in numbers:
                try:
                    clean_numbers.append(float(num))
                except (ValueError, TypeError):
                    continue
            
            if not clean_numbers:
                return {"success": False, "error": "Nessun numero valido trovato"}
            
            n = len(clean_numbers)
            
            # Statistiche di base
            mean = statistics.mean(clean_numbers)
            median = statistics.median(clean_numbers)
            mode_result = None
            try:
                mode_result = statistics.mode(clean_numbers)
            except statistics.StatisticsError:
                pass
            
            # Deviazione standard e varianza
            std_dev = statistics.stdev(clean_numbers) if n > 1 else 0
            variance = statistics.variance(clean_numbers) if n > 1 else 0
            
            # Range e quartili
            sorted_numbers = sorted(clean_numbers)
            min_val = min(clean_numbers)
            max_val = max(clean_numbers)
            range_val = max_val - min_val
            
            # Quartili
            q1 = statistics.median(sorted_numbers[:n//2]) if n > 1 else min_val
            q3 = statistics.median(sorted_numbers[(n+1)//2:]) if n > 1 else max_val
            iqr = q3 - q1
            
            # Outliers (usando metodo IQR)
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = [x for x in clean_numbers if x < lower_bound or x > upper_bound]
            
            # Distribuzione
            def classify_distribution():
                if abs(mean - median) < std_dev * 0.1:
                    return "Normale/Simmetrica"
                elif mean > median:
                    return "Skewed Right (coda a destra)"
                else:
                    return "Skewed Left (coda a sinistra)"
            
            return {
                "sample_size": n,
                "descriptive_stats": {
                    "mean": round(mean, 4),
                    "median": round(median, 4),
                    "mode": round(mode_result, 4) if mode_result is not None else None,
                    "std_deviation": round(std_dev, 4),
                    "variance": round(variance, 4),
                    "coefficient_of_variation": round((std_dev / mean) * 100, 2) if mean != 0 else None
                },
                "range_stats": {
                    "minimum": min_val,
                    "maximum": max_val,
                    "range": round(range_val, 4),
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4)
                },
                "outlier_analysis": {
                    "outlier_count": len(outliers),
                    "outlier_percentage": round((len(outliers) / n) * 100, 2),
                    "outliers": outliers[:10]  # Max 10 outliers
                },
                "distribution": classify_distribution(),
                "data_quality": "Eccellente" if len(outliers) < n * 0.05 else "Buona" if len(outliers) < n * 0.1 else "Media"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def text_analysis(text: str) -> Dict[str, Any]:
        """
        Analizza testo per statistiche e pattern.
        
        Args:
            text: Testo da analizzare
        """
        try:
            # Statistiche di base
            char_count = len(text)
            word_count = len(text.split())
            sentence_count = len(re.split(r'[.!?]+', text)) - 1  # -1 per l'ultimo split vuoto
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            # Analisi parole
            words = re.findall(r'\b\w+\b', text.lower())
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Top parole più comuni
            most_common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Lunghezza media parole
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            
            # Analisi caratteri
            letters = sum(1 for c in text if c.isalpha())
            digits = sum(1 for c in text if c.isdigit())
            spaces = text.count(' ')
            punctuation = sum(1 for c in text if c in '.,!?;:"\'')
            
            # Readability (approssimazione Flesch)
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Sentiment analysis basic (parole positive/negative)
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect', 'love', 'beautiful', 'happy']
            negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'ugly', 'sad', 'angry', 'difficult', 'problem']
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            sentiment = "Positivo" if positive_count > negative_count else "Negativo" if negative_count > positive_count else "Neutro"
            
            return {
                "text_stats": {
                    "characters": char_count,
                    "words": word_count,
                    "sentences": sentence_count,
                    "paragraphs": paragraph_count,
                    "unique_words": len(word_freq),
                    "avg_word_length": round(avg_word_length, 2),
                    "avg_sentence_length": round(avg_sentence_length, 2)
                },
                "character_composition": {
                    "letters": letters,
                    "digits": digits,
                    "spaces": spaces,
                    "punctuation": punctuation,
                    "other": char_count - letters - digits - spaces - punctuation
                },
                "word_frequency": most_common_words,
                "readability": {
                    "level": "Semplice" if avg_sentence_length < 15 else "Media" if avg_sentence_length < 25 else "Complessa",
                    "avg_sentence_length": round(avg_sentence_length, 2)
                },
                "sentiment_analysis": {
                    "sentiment": sentiment,
                    "positive_words": positive_count,
                    "negative_words": negative_count,
                    "neutrality_score": round(abs(positive_count - negative_count) / max(word_count, 1), 3)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def correlation_analysis(dataset1: List[float], dataset2: List[float]) -> Dict[str, Any]:
        """
        Calcola correlazione tra due dataset numerici.
        
        Args:
            dataset1: Primo dataset
            dataset2: Secondo dataset
        """
        try:
            # Converti e pulisci dati
            clean_data1 = [float(x) for x in dataset1 if x is not None]
            clean_data2 = [float(x) for x in dataset2 if x is not None]
            
            if len(clean_data1) != len(clean_data2):
                return {"success": False, "error": "I dataset devono avere la stessa lunghezza"}
            
            if len(clean_data1) < 2:
                return {"success": False, "error": "Servono almeno 2 punti dati"}
            
            # Calcola correlazione di Pearson
            import math
            
            n = len(clean_data1)
            sum1 = sum(clean_data1)
            sum2 = sum(clean_data2)
            sum1_sq = sum(x ** 2 for x in clean_data1)
            sum2_sq = sum(x ** 2 for x in clean_data2)
            sum12 = sum(x * y for x, y in zip(clean_data1, clean_data2))
            
            numerator = n * sum12 - sum1 * sum2
            denominator = math.sqrt((n * sum1_sq - sum1 ** 2) * (n * sum2_sq - sum2 ** 2))
            
            if denominator == 0:
                return {"success": False, "error": "Impossibile calcolare correlazione (denominatore zero)"}
            
            correlation = numerator / denominator
            
            # Interpreta correlazione
            def interpret_correlation(r):
                abs_r = abs(r)
                if abs_r >= 0.9:
                    strength = "Molto forte"
                elif abs_r >= 0.7:
                    strength = "Forte"
                elif abs_r >= 0.5:
                    strength = "Moderata"
                elif abs_r >= 0.3:
                    strength = "Debole"
                else:
                    strength = "Molto debole"
                
                direction = "Positiva" if r > 0 else "Negativa" if r < 0 else "Nessuna"
                return f"{strength} {direction}".strip()
            
            # Calcola R-squared
            r_squared = correlation ** 2
            
            return {
                "sample_size": n,
                "correlation_coefficient": round(correlation, 4),
                "r_squared": round(r_squared, 4),
                "correlation_strength": interpret_correlation(correlation),
                "interpretation": {
                    "relationship": "I dati sono fortemente correlati" if abs(correlation) > 0.7 else
                                   "I dati sono moderatamente correlati" if abs(correlation) > 0.5 else
                                   "I dati sono debolmente correlati" if abs(correlation) > 0.3 else
                                   "I dati non sono significativamente correlati",
                    "variance_explained": f"{round(r_squared * 100, 1)}% della varianza è spiegata dalla relazione"
                },
                "dataset_stats": {
                    "dataset1_mean": round(statistics.mean(clean_data1), 2),
                    "dataset2_mean": round(statistics.mean(clean_data2), 2),
                    "dataset1_std": round(statistics.stdev(clean_data1), 2) if n > 1 else 0,
                    "dataset2_std": round(statistics.stdev(clean_data2), 2) if n > 1 else 0
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }