# -*- coding: utf-8 -*-
# tools/data_analysis.py
import json
import csv
import logging
import statistics
import math
import re
import io
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

def register_tools(mcp):
    """Registra i tool di analisi dati avanzata con l'istanza del server MCP."""
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

    @mcp.tool()
    def analyze_time_series(data: List[Dict[str, Any]], date_column: str, 
                           value_column: str, analysis_type: str = "trend") -> Dict[str, Any]:
        """
        Analizza serie temporali per trend, stagionalità e pattern.
        
        Args:
            data: Lista di dict con dati temporali
            date_column: Nome colonna data/timestamp
            value_column: Nome colonna valori numerici
            analysis_type: Tipo analisi (trend, seasonal, decomposition, forecast)
        """
        try:
            if not data:
                return {"success": False, "error": "Dataset vuoto"}
            
            # Parse e ordina dati per data
            time_series = []
            for row in data:
                try:
                    date_val = _parse_date(row.get(date_column))
                    value_val = float(row.get(value_column, 0))
                    time_series.append((date_val, value_val))
                except (ValueError, TypeError) as e:
                    continue
            
            if len(time_series) < 3:
                return {"success": False, "error": "Servono almeno 3 punti dati validi"}
            
            time_series.sort(key=lambda x: x[0])
            dates, values = zip(*time_series)
            
            result = {
                "success": True,
                "data_points": len(time_series),
                "time_range": {
                    "start": dates[0].isoformat(),
                    "end": dates[-1].isoformat(),
                    "duration_days": (dates[-1] - dates[0]).days
                }
            }
            
            if analysis_type in ["trend", "all"]:
                trend_analysis = _analyze_trend(dates, values)
                result["trend_analysis"] = trend_analysis
            
            if analysis_type in ["seasonal", "all"]:
                seasonal_analysis = _analyze_seasonality(dates, values)
                result["seasonal_analysis"] = seasonal_analysis
            
            if analysis_type in ["decomposition", "all"]:
                decomposition = _decompose_time_series(dates, values)
                result["decomposition"] = decomposition
            
            if analysis_type in ["forecast", "all"]:
                forecast = _simple_forecast(dates, values)
                result["forecast"] = forecast
            
            # Statistiche generali
            result["statistics"] = {
                "mean": round(statistics.mean(values), 4),
                "std_dev": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "volatility": round(statistics.stdev(values) / statistics.mean(values), 4) if statistics.mean(values) != 0 else 0
            }
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def detect_anomalies(data: List[float], method: str = "iqr", 
                        sensitivity: float = 1.5) -> Dict[str, Any]:
        """
        Rileva anomalie in dataset numerico usando vari metodi.
        
        Args:
            data: Lista di valori numerici
            method: Metodo rilevamento (iqr, zscore, isolation, statistical)
            sensitivity: Sensibilità rilevamento (1.0-3.0)
        """
        try:
            if not data:
                return {"success": False, "error": "Dataset vuoto"}
            
            # Pulizia dati
            clean_data = []
            for val in data:
                try:
                    clean_data.append(float(val))
                except (ValueError, TypeError):
                    continue
            
            if len(clean_data) < 3:
                return {"success": False, "error": "Servono almeno 3 valori numerici"}
            
            anomalies = []
            anomaly_indices = []
            
            if method == "iqr":
                q1 = statistics.median(clean_data[:len(clean_data)//2])
                q3 = statistics.median(clean_data[len(clean_data)//2:])
                iqr = q3 - q1
                lower_bound = q1 - sensitivity * iqr
                upper_bound = q3 + sensitivity * iqr
                
                for i, val in enumerate(clean_data):
                    if val < lower_bound or val > upper_bound:
                        anomalies.append(val)
                        anomaly_indices.append(i)
            
            elif method == "zscore":
                mean = statistics.mean(clean_data)
                std_dev = statistics.stdev(clean_data) if len(clean_data) > 1 else 0
                
                if std_dev == 0:
                    return {"success": False, "error": "Deviazione standard zero - impossibile calcolare z-score"}
                
                for i, val in enumerate(clean_data):
                    z_score = abs(val - mean) / std_dev
                    if z_score > sensitivity + 1:  # Adjusted for sensitivity
                        anomalies.append(val)
                        anomaly_indices.append(i)
            
            elif method == "statistical":
                # Modified Thompson Tau test approximation
                mean = statistics.mean(clean_data)
                std_dev = statistics.stdev(clean_data) if len(clean_data) > 1 else 0
                
                if std_dev == 0:
                    return {"success": False, "error": "Deviazione standard zero"}
                
                # Calcola threshold basato su distribuzione normale
                threshold = sensitivity * std_dev
                
                for i, val in enumerate(clean_data):
                    if abs(val - mean) > threshold:
                        anomalies.append(val)
                        anomaly_indices.append(i)
            
            else:
                return {"success": False, "error": f"Metodo '{method}' non supportato"}
            
            # Calcola statistiche anomalie
            anomaly_percentage = (len(anomalies) / len(clean_data)) * 100
            
            # Classifica severità
            if anomaly_percentage > 20:
                severity = "Molto alta"
            elif anomaly_percentage > 10:
                severity = "Alta"
            elif anomaly_percentage > 5:
                severity = "Media"
            else:
                severity = "Bassa"
            
            return {
                "success": True,
                "method": method,
                "sensitivity": sensitivity,
                "total_points": len(clean_data),
                "anomalies_found": len(anomalies),
                "anomaly_percentage": round(anomaly_percentage, 2),
                "anomaly_severity": severity,
                "anomaly_values": anomalies[:20],  # Max 20 per output
                "anomaly_indices": anomaly_indices[:20],
                "statistics": {
                    "mean": round(statistics.mean(clean_data), 4),
                    "std_dev": round(statistics.stdev(clean_data), 4) if len(clean_data) > 1 else 0,
                    "median": round(statistics.median(clean_data), 4)
                },
                "recommendations": _generate_anomaly_recommendations(anomaly_percentage, method)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def data_quality_assessment(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valuta qualità complessiva del dataset.
        
        Args:
            dataset: Lista di record (dict)
        """
        try:
            if not dataset:
                return {"success": False, "error": "Dataset vuoto"}
            
            total_records = len(dataset)
            all_columns = set()
            
            # Raccoglie tutte le colonne
            for record in dataset:
                if isinstance(record, dict):
                    all_columns.update(record.keys())
            
            column_quality = {}
            
            for column in all_columns:
                values = []
                missing_count = 0
                
                for record in dataset:
                    value = record.get(column)
                    if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
                        missing_count += 1
                    else:
                        values.append(value)
                
                # Analizza tipo dati
                type_counts = Counter(type(v).__name__ for v in values)
                dominant_type = type_counts.most_common(1)[0][0] if type_counts else "unknown"
                type_consistency = (type_counts.most_common(1)[0][1] / len(values) * 100) if values else 0
                
                # Duplicati
                duplicate_count = len(values) - len(set(str(v) for v in values))
                
                # Pattern validation per tipi comuni
                pattern_validity = _validate_data_patterns(values, column)
                
                column_quality[column] = {
                    "total_values": total_records,
                    "non_missing_values": len(values),
                    "missing_count": missing_count,
                    "missing_percentage": round((missing_count / total_records) * 100, 2),
                    "dominant_type": dominant_type,
                    "type_consistency": round(type_consistency, 2),
                    "duplicate_count": duplicate_count,
                    "duplicate_percentage": round((duplicate_count / len(values)) * 100, 2) if values else 0,
                    "unique_values": len(set(str(v) for v in values)),
                    "pattern_validity": pattern_validity
                }
            
            # Calcola quality score generale
            overall_scores = []
            for col_quality in column_quality.values():
                score = 100
                score -= col_quality["missing_percentage"]
                score -= (100 - col_quality["type_consistency"]) * 0.5
                score -= col_quality["duplicate_percentage"] * 0.3
                if not col_quality["pattern_validity"]["is_valid"]:
                    score -= 20
                overall_scores.append(max(0, score))
            
            overall_quality = statistics.mean(overall_scores) if overall_scores else 0
            
            # Genera raccomandazioni
            recommendations = _generate_quality_recommendations(column_quality, overall_quality)
            
            return {
                "success": True,
                "total_records": total_records,
                "total_columns": len(all_columns),
                "overall_quality_score": round(overall_quality, 2),
                "quality_rating": _classify_quality_rating(overall_quality),
                "column_quality": column_quality,
                "recommendations": recommendations,
                "summary": {
                    "high_quality_columns": len([c for c in column_quality.values() if c["missing_percentage"] < 5]),
                    "medium_quality_columns": len([c for c in column_quality.values() if 5 <= c["missing_percentage"] < 20]),
                    "low_quality_columns": len([c for c in column_quality.values() if c["missing_percentage"] >= 20])
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def hypothesis_testing(sample1: List[float], sample2: List[float], 
                          test_type: str = "ttest", alpha: float = 0.05) -> Dict[str, Any]:
        """
        Esegue test statistici di ipotesi tra due campioni.
        
        Args:
            sample1: Primo campione
            sample2: Secondo campione
            test_type: Tipo test (ttest, welch, mannwhitney, kstest)
            alpha: Livello significatività (default 0.05)
        """
        try:
            # Pulizia dati
            clean_sample1 = [float(x) for x in sample1 if x is not None]
            clean_sample2 = [float(x) for x in sample2 if x is not None]
            
            if len(clean_sample1) < 2 or len(clean_sample2) < 2:
                return {"success": False, "error": "Ogni campione deve avere almeno 2 valori"}
            
            # Statistiche descrittive
            stats1 = {
                "n": len(clean_sample1),
                "mean": statistics.mean(clean_sample1),
                "std": statistics.stdev(clean_sample1),
                "median": statistics.median(clean_sample1)
            }
            
            stats2 = {
                "n": len(clean_sample2),
                "mean": statistics.mean(clean_sample2),
                "std": statistics.stdev(clean_sample2),
                "median": statistics.median(clean_sample2)
            }
            
            result = {
                "success": True,
                "test_type": test_type,
                "alpha": alpha,
                "sample1_stats": stats1,
                "sample2_stats": stats2
            }
            
            if test_type == "ttest":
                # T-test a due campioni (assumendo varianze uguali)
                test_result = _two_sample_ttest(clean_sample1, clean_sample2, alpha)
                result.update(test_result)
            
            elif test_type == "welch":
                # Welch's t-test (varianze diverse)
                test_result = _welch_ttest(clean_sample1, clean_sample2, alpha)
                result.update(test_result)
            
            elif test_type == "mannwhitney":
                # Mann-Whitney U test (non-parametrico)
                test_result = _mann_whitney_test(clean_sample1, clean_sample2, alpha)
                result.update(test_result)
            
            else:
                return {"success": False, "error": f"Test '{test_type}' non supportato"}
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def cluster_analysis(data: List[List[float]], n_clusters: int = 3, 
                        method: str = "kmeans") -> Dict[str, Any]:
        """
        Esegue analisi di clustering su dati multidimensionali.
        
        Args:
            data: Lista di punti dati (ogni punto è una lista di coordinate)
            n_clusters: Numero di cluster desiderati
            method: Metodo clustering (kmeans, hierarchical)
        """
        try:
            if not data or not all(isinstance(point, list) for point in data):
                return {"success": False, "error": "Dati non validi - serve lista di liste"}
            
            # Verifica dimensioni consistenti
            dimensions = len(data[0]) if data else 0
            if not all(len(point) == dimensions for point in data):
                return {"success": False, "error": "Tutti i punti devono avere le stesse dimensioni"}
            
            if len(data) < n_clusters:
                return {"success": False, "error": "Numero punti dati deve essere >= numero cluster"}
            
            # Converte a float
            clean_data = []
            for point in data:
                try:
                    clean_point = [float(coord) for coord in point]
                    clean_data.append(clean_point)
                except (ValueError, TypeError):
                    continue
            
            if method == "kmeans":
                cluster_result = _kmeans_clustering(clean_data, n_clusters)
            elif method == "hierarchical":
                cluster_result = _hierarchical_clustering(clean_data, n_clusters)
            else:
                return {"success": False, "error": f"Metodo '{method}' non supportato"}
            
            # Calcola statistiche cluster
            cluster_stats = _calculate_cluster_stats(clean_data, cluster_result["assignments"])
            
            return {
                "success": True,
                "method": method,
                "n_clusters": n_clusters,
                "n_points": len(clean_data),
                "dimensions": dimensions,
                "cluster_assignments": cluster_result["assignments"],
                "cluster_centers": cluster_result.get("centers", []),
                "cluster_statistics": cluster_stats,
                "quality_metrics": {
                    "within_cluster_sum_squares": cluster_result.get("wcss", 0),
                    "silhouette_approximation": _approximate_silhouette_score(clean_data, cluster_result["assignments"])
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def prepare_visualization_data(data: List[Dict[str, Any]], chart_type: str,
                                 x_column: str, y_column: str = None) -> Dict[str, Any]:
        """
        Prepara dati per visualizzazioni grafiche.
        
        Args:
            data: Dataset come lista di dict
            chart_type: Tipo grafico (line, bar, scatter, histogram, pie)
            x_column: Colonna per asse X
            y_column: Colonna per asse Y (se necessaria)
        """
        try:
            if not data:
                return {"success": False, "error": "Dataset vuoto"}
            
            chart_data = {"success": True, "chart_type": chart_type}
            
            if chart_type == "histogram":
                # Istogramma - solo X necessario
                values = []
                for row in data:
                    try:
                        val = float(row.get(x_column, 0))
                        values.append(val)
                    except (ValueError, TypeError):
                        continue
                
                if not values:
                    return {"success": False, "error": "Nessun valore numerico valido trovato"}
                
                # Calcola bins
                n_bins = min(20, int(math.sqrt(len(values))))
                min_val, max_val = min(values), max(values)
                bin_width = (max_val - min_val) / n_bins if n_bins > 0 else 1
                
                bins = []
                counts = []
                for i in range(n_bins):
                    bin_start = min_val + i * bin_width
                    bin_end = min_val + (i + 1) * bin_width
                    count = sum(1 for v in values if bin_start <= v < bin_end)
                    bins.append(f"{bin_start:.2f}-{bin_end:.2f}")
                    counts.append(count)
                
                chart_data.update({
                    "bins": bins,
                    "counts": counts,
                    "statistics": {
                        "total_values": len(values),
                        "mean": round(statistics.mean(values), 2),
                        "std_dev": round(statistics.stdev(values), 2) if len(values) > 1 else 0
                    }
                })
            
            elif chart_type == "pie":
                # Grafico a torta - conta frequenze
                value_counts = Counter()
                for row in data:
                    value = str(row.get(x_column, "")).strip()
                    if value:
                        value_counts[value] += 1
                
                # Prendi top 10 per leggibilità
                top_values = value_counts.most_common(10)
                others_count = sum(count for _, count in value_counts.most_common()[10:])
                
                if others_count > 0:
                    top_values.append(("Others", others_count))
                
                labels, counts = zip(*top_values) if top_values else ([], [])
                total = sum(counts)
                percentages = [round((count/total)*100, 1) for count in counts] if total > 0 else []
                
                chart_data.update({
                    "labels": list(labels),
                    "values": list(counts),
                    "percentages": percentages,
                    "total": total
                })
            
            elif chart_type in ["line", "bar", "scatter"]:
                # Grafici che richiedono X e Y
                if not y_column:
                    return {"success": False, "error": f"Grafico {chart_type} richiede y_column"}
                
                chart_points = []
                for row in data:
                    try:
                        x_val = row.get(x_column)
                        y_val = float(row.get(y_column, 0))
                        
                        # Prova a convertire X a numero, altrimenti tieni come stringa
                        try:
                            x_val = float(x_val)
                        except (ValueError, TypeError):
                            pass
                        
                        chart_points.append({"x": x_val, "y": y_val})
                    except (ValueError, TypeError):
                        continue
                
                if not chart_points:
                    return {"success": False, "error": "Nessun punto dati valido trovato"}
                
                # Ordina per X se numerici
                if all(isinstance(p["x"], (int, float)) for p in chart_points):
                    chart_points.sort(key=lambda p: p["x"])
                
                chart_data.update({
                    "data_points": chart_points,
                    "point_count": len(chart_points),
                    "x_range": {
                        "min": min(p["x"] for p in chart_points if isinstance(p["x"], (int, float))),
                        "max": max(p["x"] for p in chart_points if isinstance(p["x"], (int, float)))
                    } if any(isinstance(p["x"], (int, float)) for p in chart_points) else None,
                    "y_range": {
                        "min": min(p["y"] for p in chart_points),
                        "max": max(p["y"] for p in chart_points)
                    }
                })
            
            else:
                return {"success": False, "error": f"Tipo grafico '{chart_type}' non supportato"}
            
            return chart_data
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions for enhanced functionality
    def _parse_date(date_str):
        """Parse vari formati di data."""
        if isinstance(date_str, datetime):
            return date_str
        
        formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Formato data non riconosciuto: {date_str}")

    def _analyze_trend(dates, values):
        """Analizza trend temporale."""
        n = len(values)
        if n < 2:
            return {"trend": "Indeterminato", "slope": 0}
        
        # Regressione lineare semplice
        x_numeric = [(d - dates[0]).days for d in dates]
        x_mean = statistics.mean(x_numeric)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_numeric, values))
        denominator = sum((x - x_mean) ** 2 for x in x_numeric)
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Classifica trend
        if abs(slope) < 0.01:
            trend = "Stabile"
        elif slope > 0:
            trend = "Crescente"
        else:
            trend = "Decrescente"
        
        return {
            "trend": trend,
            "slope": round(slope, 6),
            "correlation": _calculate_correlation(x_numeric, values)
        }

    def _calculate_correlation(x, y):
        """Calcola correlazione di Pearson."""
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        sum_sq_x = sum((xi - x_mean) ** 2 for xi in x)
        sum_sq_y = sum((yi - y_mean) ** 2 for yi in y)
        
        denominator = math.sqrt(sum_sq_x * sum_sq_y)
        
        return numerator / denominator if denominator != 0 else 0

    def _two_sample_ttest(sample1, sample2, alpha):
        """T-test a due campioni."""
        n1, n2 = len(sample1), len(sample2)
        mean1, mean2 = statistics.mean(sample1), statistics.mean(sample2)
        var1 = statistics.variance(sample1) if n1 > 1 else 0
        var2 = statistics.variance(sample2) if n2 > 1 else 0
        
        # Pooled variance
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        se = math.sqrt(pooled_var * (1/n1 + 1/n2))
        
        t_stat = (mean1 - mean2) / se if se != 0 else 0
        df = n1 + n2 - 2
        
        # Critical value approximation (t-distribution)
        t_critical = _get_t_critical(alpha, df)
        
        p_value_approx = _approximate_t_pvalue(abs(t_stat), df)
        significant = p_value_approx < alpha
        
        return {
            "t_statistic": round(t_stat, 4),
            "degrees_of_freedom": df,
            "p_value_approx": round(p_value_approx, 4),
            "critical_value": round(t_critical, 4),
            "significant": significant,
            "conclusion": "Reject null hypothesis" if significant else "Fail to reject null hypothesis",
            "mean_difference": round(mean1 - mean2, 4)
        }

    def _welch_ttest(sample1, sample2, alpha):
        """Welch's t-test (varianze diverse)."""
        n1, n2 = len(sample1), len(sample2)
        mean1, mean2 = statistics.mean(sample1), statistics.mean(sample2)
        var1 = statistics.variance(sample1) if n1 > 1 else 0
        var2 = statistics.variance(sample2) if n2 > 1 else 0
        
        se = math.sqrt(var1/n1 + var2/n2) if n1 > 0 and n2 > 0 else 0
        t_stat = (mean1 - mean2) / se if se != 0 else 0
        
        # Gradi di libertà approssimati
        df_numerator = (var1/n1 + var2/n2) ** 2
        df_denominator = ((var1/n1) ** 2) / (n1 - 1) + ((var2/n2) ** 2) / (n2 - 1)
        df = df_numerator / df_denominator if df_denominator != 0 else 0
        
        p_value_approx = _approximate_t_pvalue(abs(t_stat), df)
        significant = p_value_approx < alpha
        
        return {
            "t_statistic": round(t_stat, 4),
            "degrees_of_freedom": df,
            "p_value_approx": round(p_value_approx, 4),
            "significant": significant,
            "conclusion": "Reject null hypothesis" if significant else "Fail to reject null hypothesis",
            "mean_difference": round(mean1 - mean2, 4)
        }

    def _mann_whitney_test(sample1, sample2, alpha):
        """Mann-Whitney U test (non-parametrico)."""
        from scipy.stats import mannwhitneyu
        
        # Rank dei dati
        all_data = sorted((x, 1) for x in sample1) + sorted((x, 2) for x in sample2)
        ranks = []
        current_rank = 1
        for i, (value, group) in enumerate(all_data):
            if i > 0 and value != all_data[i-1][0]:
                current_rank = i + 1
            ranks.append((value, group, current_rank))
        
        rank_sum1 = sum(rank for value, group, rank in ranks if group == 1)
        rank_sum2 = sum(rank for value, group, rank in ranks if group == 2)
        
        n1, n2 = len(sample1), len(sample2)
        u_statistic = rank_sum1 - n1 * (n1 + 1) / 2
        u_statistic_2 = rank_sum2 - n2 * (n2 + 1) / 2
        u_statistic = min(u_statistic, u_statistic_2)  # U di Mann-Whitney è il minore dei due U
        
        # Approximazione normale per grandi campioni
        mean_u = n1 * n2 / 2
        std_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        
        z_statistic = (u_statistic - mean_u) / std_u if std_u != 0 else 0
        p_value_approx = 2 * (1 - _normal_cdf(abs(z_statistic)))  # Bilaterale
        
        significant = p_value_approx < alpha
        
        return {
            "u_statistic": round(u_statistic, 4),
            "z_statistic": round(z_statistic, 4),
            "p_value_approx": round(p_value_approx, 4),
            "significant": significant,
            "conclusion": "Reject null hypothesis" if significant else "Fail to reject null hypothesis"
        }

    def _normal_cdf(x):
        """Funzione di distribuzione cumulativa per la normale standard."""
        return (1 + math.erf(x / math.sqrt(2))) / 2

    def _kmeans_clustering(data, n_clusters):
        """Esegue clustering K-means."""
        from sklearn.cluster import KMeans
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10, max_iter=300)
        kmeans.fit(data)
        
        return {
            "centers": kmeans.cluster_centers_.tolist(),
            "assignments": kmeans.labels_.tolist(),
            "inertia": kmeans.inertia_
        }

    def _hierarchical_clustering(data, n_clusters):
        """Esegue clustering gerarchico."""
        from sklearn.cluster import AgglomerativeClustering
        
        clustering = AgglomerativeClustering(n_clusters=n_clusters)
        clustering.fit(data)
        
        return {
            "assignments": clustering.labels_.tolist()
        }

    def _calculate_cluster_stats(data, assignments):
        """Calcola statistiche per ogni cluster."""
        n_clusters = max(assignments) + 1 if assignments else 0
        cluster_stats = [{} for _ in range(n_clusters)]
        
        for i, point in enumerate(data):
            cluster_id = assignments[i]
            if cluster_id < 0 or cluster_id >= n_clusters:
                continue
            
            if "points" not in cluster_stats[cluster_id]:
                cluster_stats[cluster_id]["points"] = []
            
            cluster_stats[cluster_id]["points"].append(point)
        
        # Calcola statistiche riassuntive
        for i, stats in enumerate(cluster_stats):
            if "points" in stats:
                points = stats["points"]
                stats["mean"] = [round(statistics.mean(dim), 4) for dim in zip(*points)]
                stats["std_dev"] = [round(statistics.stdev(dim), 4) for dim in zip(*points)] if len(points) > 1 else [0] * len(points[0])
                stats["size"] = len(points)
        
        return cluster_stats

    def _approximate_silhouette_score(data, assignments):
        """Approssima il punteggio di silhouette."""
        from sklearn.metrics import silhouette_samples
        import numpy as np
        
        if len(data) != len(assignments):
            return 0
        
        # Calcola i campioni di silhouette
        sample_silhouette_values = silhouette_samples(np.array(data), np.array(assignments))
        
        # Restituisce la media come punteggio approssimato
        return round(np.mean(sample_silhouette_values), 4)

    def _validate_data_patterns(values, column_name):
        """Valida i pattern dei dati in base al tipo di colonna atteso."""
        # Esempi di validazione basati su nomi di colonne
        if "email" in column_name.lower():
            pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        elif "data" in column_name.lower() or "timestamp" in column_name.lower():
            pattern = r"^\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?$"
        elif "telefono" in column_name.lower() or "phone" in column_name.lower():
            pattern = r"^\+?\d{10,15}$"
        else:
            return {"is_valid": True}  # Nessun pattern specificato, considera valido
        
        # Controlla i valori contro il pattern
        compiled_pattern = re.compile(pattern)
        invalid_values = [v for v in values if not compiled_pattern.match(str(v))]
        
        return {
            "is_valid": len(invalid_values) == 0,
            "invalid_values": invalid_values[:10],  # Mostra max 10 valori non validi
            "pattern": pattern
        }

    def _generate_anomaly_recommendations(anomaly_percentage, method):
        """Genera raccomandazioni per anomalie rilevate."""
        if method == "iqr":
            return {
                "action": "Controlla valori anomali",
                "threshold": "IQR",
                "sensitivity": "Regola la sensibilità in base al dominio"
            }
        elif method == "zscore":
            return {
                "action": "Controlla valori con alto z-score",
                "threshold": "Z-score",
                "sensitivity": "Regola la sensibilità sopra 3.0 per outliers estremi"
            }
        elif method == "statistical":
            return {
                "action": "Esamina valori lontani dalla media",
                "threshold": "Deviazione dalla media",
                "sensitivity": "Regola in base alla varianza del dominio"
            }
        else:
            return {
                "action": "Esamina anomalie",
                "details": "Metodo sconosciuto per la rilevazione delle anomalie"
            }

    def _generate_quality_recommendations(column_quality, overall_quality):
        """Genera raccomandazioni per migliorare la qualità dei dati."""
        recommendations = []
        
        for column, quality in column_quality.items():
            if quality["missing_percentage"] > 10:
                recommendations.append(f"Riduci i valori mancanti in '{column}' sotto il 10%")
            if quality["duplicate_percentage"] > 5:
                recommendations.append(f"Rimuovi i duplicati nella colonna '{column}'")
            if not quality["pattern_validity"]["is_valid"]:
                recommendations.append(f"Correggi i valori non conformi nel pattern per '{column}'")
        
        if overall_quality < 70:
            recommendations.append("Migliora la qualità dei dati per raggiungere un punteggio sopra 70")
        
        return recommendations

    def _classify_quality_rating(quality_score):
        """Classifica la qualità in base al punteggio."""
        if quality_score >= 85:
            return "Eccellente"
        elif quality_score >= 70:
            return "Buona"
        elif quality_score >= 50:
            return "Media"
        else:
            return "Bassa"