# -*- coding: utf-8 -*-
# tools/log_analysis_tools.py
import re
import os
import json
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict, deque
import time
import statistics
from datetime import datetime, timedelta
import hashlib
import threading
import queue

def register_tools(mcp):
    """Registra i tool di analisi log avanzati con l'istanza del server MCP."""
    logging.info("📊 Registrazione tool-set: Log Analysis Tools")

    @mcp.tool()
    def parse_log_file(file_path: str, log_format: str = "auto", max_lines: int = 10000) -> Dict[str, Any]:
        """
        Analizza un file di log e estrae informazioni strutturate.
        
        Args:
            file_path: Percorso del file di log
            log_format: Formato del log (auto, apache, nginx, syslog, json, custom)
            max_lines: Numero massimo di righe da analizzare
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "Log file not found"
                }
            
            if max_lines < 1 or max_lines > 50000:
                return {
                    "success": False,
                    "error": "max_lines must be between 1 and 50000"
                }
            
            file_size = os.path.getsize(file_path)
            
            parsed_entries = []
            total_lines = 0
            error_lines = []
            
            # Pattern per diversi formati di log
            log_patterns = {
                "apache": r'(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<size>\S+)',
                "nginx": r'(?P<ip>\S+) - \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<size>\d+)',
                "syslog": r'(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+) (?P<hostname>\S+) (?P<process>\S+): (?P<message>.*)',
                "python": r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})[,\s]+(?P<level>\w+)[:\s]+(?P<message>.*)',
                "generic": r'(?P<timestamp>\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})\s*(?P<level>\w+)?\s*(?P<message>.*)'
            }
            
            detected_format = log_format
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if line_num > max_lines:
                        break
                    
                    total_lines += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Auto-detect format se necessario
                    if detected_format == "auto" and line_num <= 10:
                        detected_format = _detect_log_format(line, log_patterns)
                    
                    # Prova a fare parsing JSON
                    if line.startswith('{'):
                        try:
                            json_entry = json.loads(line)
                            parsed_entries.append({
                                "line_number": line_num,
                                "raw_line": line,
                                "parsed_data": json_entry,
                                "format": "json"
                            })
                            continue
                        except:
                            pass
                    
                    # Usa pattern appropriato
                    pattern = log_patterns.get(detected_format, log_patterns["generic"])
                    match = re.match(pattern, line)
                    
                    if match:
                        parsed_data = match.groupdict()
                        
                        # Normalizza timestamp
                        if "timestamp" in parsed_data:
                            parsed_data["normalized_timestamp"] = _normalize_timestamp(parsed_data["timestamp"])
                        
                        parsed_entries.append({
                            "line_number": line_num,
                            "raw_line": line,
                            "parsed_data": parsed_data,
                            "format": detected_format
                        })
                    else:
                        error_lines.append({
                            "line_number": line_num,
                            "line": line[:100] + "..." if len(line) > 100 else line
                        })
            
            # Statistiche
            parsing_success_rate = (len(parsed_entries) / total_lines * 100) if total_lines > 0 else 0
            
            return {
                "success": True,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "detected_format": detected_format,
                "total_lines": total_lines,
                "parsed_entries": len(parsed_entries),
                "parsing_success_rate": round(parsing_success_rate, 2),
                "unparsed_lines": len(error_lines),
                "sample_entries": parsed_entries[:5],
                "parsing_errors": error_lines[:10],
                "log_analysis": _analyze_parsed_entries(parsed_entries)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_log_patterns(log_data: List[Dict[str, Any]], pattern_type: str = "errors") -> Dict[str, Any]:
        """
        Analizza pattern specifici nei log.
        
        Args:
            log_data: Dati di log parsati
            pattern_type: Tipo di pattern da analizzare (errors, requests, performance, security)
        """
        try:
            if not log_data:
                return {
                    "success": False,
                    "error": "No log data provided"
                }
            
            analysis_results = {
                "pattern_type": pattern_type,
                "total_entries": len(log_data),
                "matches": [],
                "statistics": {},
                "trends": {}
            }
            
            if pattern_type == "errors":
                error_patterns = [
                    (r'\b(error|ERROR|Error)\b', "Error"),
                    (r'\b(exception|EXCEPTION|Exception)\b', "Exception"),
                    (r'\b(fail|FAIL|Fail|failed|FAILED)\b', "Failure"),
                    (r'\b(timeout|TIMEOUT|Timeout)\b', "Timeout"),
                    (r'\b5\d{2}\b', "HTTP 5xx Error"),
                    (r'\b4\d{2}\b', "HTTP 4xx Error")
                ]
                
                error_counts = Counter()
                error_details = []
                
                for entry in log_data:
                    line = entry.get("raw_line", "")
                    parsed = entry.get("parsed_data", {})
                    
                    for pattern, error_type in error_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            error_counts[error_type] += 1
                            error_details.append({
                                "line_number": entry.get("line_number"),
                                "error_type": error_type,
                                "message": parsed.get("message", line[:100]),
                                "timestamp": parsed.get("normalized_timestamp")
                            })
                
                analysis_results["statistics"] = dict(error_counts)
                analysis_results["matches"] = error_details[:50]  # Primi 50 errori
            
            elif pattern_type == "requests":
                if any("method" in entry.get("parsed_data", {}) for entry in log_data):
                    # Analisi richieste HTTP
                    methods = Counter()
                    status_codes = Counter()
                    urls = Counter()
                    
                    for entry in log_data:
                        parsed = entry.get("parsed_data", {})
                        if "method" in parsed:
                            methods[parsed.get("method", "UNKNOWN")] += 1
                            status_codes[parsed.get("status", "UNKNOWN")] += 1
                            urls[parsed.get("url", "UNKNOWN")] += 1
                    
                    analysis_results["statistics"] = {
                        "methods": dict(methods.most_common(10)),
                        "status_codes": dict(status_codes.most_common(10)),
                        "top_urls": dict(urls.most_common(20))
                    }
            
            elif pattern_type == "performance":
                # Analisi performance (response time, size, etc.)
                response_times = []
                request_sizes = []
                
                for entry in log_data:
                    parsed = entry.get("parsed_data", {})
                    
                    # Cerca pattern di response time
                    line = entry.get("raw_line", "")
                    time_match = re.search(r'(\d+(?:\.\d+)?)\s*(ms|milliseconds|s|seconds)', line)
                    if time_match:
                        time_value = float(time_match.group(1))
                        unit = time_match.group(2)
                        if unit in ['s', 'seconds']:
                            time_value *= 1000  # Convert to ms
                        response_times.append(time_value)
                    
                    # Dimensione richiesta/risposta
                    if "size" in parsed and parsed["size"].isdigit():
                        request_sizes.append(int(parsed["size"]))
                
                if response_times:
                    analysis_results["statistics"]["response_times"] = {
                        "avg_ms": round(sum(response_times) / len(response_times), 2),
                        "min_ms": min(response_times),
                        "max_ms": max(response_times),
                        "samples": len(response_times)
                    }
                
                if request_sizes:
                    analysis_results["statistics"]["request_sizes"] = {
                        "avg_bytes": round(sum(request_sizes) / len(request_sizes), 2),
                        "min_bytes": min(request_sizes),
                        "max_bytes": max(request_sizes),
                        "total_bytes": sum(request_sizes)
                    }
            
            elif pattern_type == "security":
                security_patterns = [
                    (r'\b(hack|attack|exploit|injection|xss|csrf)\b', "Potential Attack"),
                    (r'\b(unauthorized|forbidden|denied)\b', "Access Denied"),
                    (r'\b(malware|virus|trojan)\b', "Malware"),
                    (r'\b(brute.*force|dictionary.*attack)\b', "Brute Force"),
                    (r'\b(\d+\.\d+\.\d+\.\d+)\b', "IP Address")
                ]
                
                security_events = []
                ip_addresses = Counter()
                
                for entry in log_data:
                    line = entry.get("raw_line", "")
                    parsed = entry.get("parsed_data", {})
                    
                    for pattern, event_type in security_patterns:
                        matches = re.findall(pattern, line, re.IGNORECASE)
                        if matches:
                            if event_type == "IP Address":
                                for ip in matches:
                                    ip_addresses[ip] += 1
                            else:
                                security_events.append({
                                    "line_number": entry.get("line_number"),
                                    "event_type": event_type,
                                    "matches": matches,
                                    "timestamp": parsed.get("normalized_timestamp")
                                })
                
                analysis_results["matches"] = security_events[:30]
                analysis_results["statistics"] = {
                    "security_events": len(security_events),
                    "unique_ips": len(ip_addresses),
                    "top_ips": dict(ip_addresses.most_common(10))
                }
            
            return {
                "success": True,
                **analysis_results
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_log_report(log_data: List[Dict[str, Any]], report_type: str = "summary") -> Dict[str, Any]:
        """
        Genera un report comprensivo dell'analisi log.
        
        Args:
            log_data: Dati di log parsati
            report_type: Tipo di report (summary, detailed, timeline, alerts)
        """
        try:
            if not log_data:
                return {
                    "success": False,
                    "error": "No log data provided"
                }
            
            report = {
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "total_entries": len(log_data),
                "analysis_summary": {}
            }
            
            if report_type == "summary":
                # Report di riepilogo
                levels = Counter()
                timestamps = []
                
                for entry in log_data:
                    parsed = entry.get("parsed_data", {})
                    
                    # Conta livelli di log
                    level = parsed.get("level", "UNKNOWN")
                    levels[level.upper()] += 1
                    
                    # Raccoglie timestamp
                    if "normalized_timestamp" in parsed:
                        timestamps.append(parsed["normalized_timestamp"])
                
                # Timeframe analisi
                if timestamps:
                    timestamps = [t for t in timestamps if t]  # Rimuovi None
                    if timestamps:
                        report["timeframe"] = {
                            "start": min(timestamps),
                            "end": max(timestamps),
                            "duration_hours": (max(timestamps) - min(timestamps)) / 3600 if len(timestamps) > 1 else 0
                        }
                
                report["analysis_summary"] = {
                    "log_levels": dict(levels),
                    "most_common_level": levels.most_common(1)[0] if levels else None,
                    "unique_levels": len(levels)
                }
            
            elif report_type == "timeline":
                # Report timeline
                timeline_data = defaultdict(list)
                hourly_counts = defaultdict(int)
                
                for entry in log_data:
                    parsed = entry.get("parsed_data", {})
                    timestamp = parsed.get("normalized_timestamp")
                    
                    if timestamp:
                        # Raggruppa per ora
                        hour_key = datetime.fromtimestamp(timestamp).replace(minute=0, second=0, microsecond=0)
                        hourly_counts[hour_key.isoformat()] += 1
                        
                        timeline_data[hour_key.isoformat()].append({
                            "line_number": entry.get("line_number"),
                            "level": parsed.get("level", "UNKNOWN"),
                            "message": parsed.get("message", "")[:100]
                        })
                
                report["timeline"] = {
                    "hourly_counts": dict(hourly_counts),
                    "peak_hour": max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None,
                    "peak_count": max(hourly_counts.values()) if hourly_counts else 0
                }
            
            elif report_type == "alerts":
                # Report di alert
                alerts = []
                
                # Definisci soglie di alert
                thresholds = {
                    "error_rate": 5,  # % di errori
                    "requests_per_minute": 1000,
                    "response_time_ms": 5000
                }
                
                # Calcola metriche per alert
                error_count = 0
                total_entries = len(log_data)
                
                for entry in log_data:
                    parsed = entry.get("parsed_data", {})
                    level = parsed.get("level", "").upper()
                    
                    if level in ["ERROR", "CRITICAL", "FATAL"]:
                        error_count += 1
                
                error_rate = (error_count / total_entries * 100) if total_entries > 0 else 0
                
                if error_rate > thresholds["error_rate"]:
                    alerts.append({
                        "type": "HIGH_ERROR_RATE",
                        "severity": "WARNING" if error_rate < 15 else "CRITICAL",
                        "message": f"Error rate is {error_rate:.2f}% (threshold: {thresholds['error_rate']}%)",
                        "value": error_rate,
                        "threshold": thresholds["error_rate"]
                    })
                
                report["alerts"] = alerts
                report["alert_count"] = len(alerts)
                report["severity_levels"] = Counter([alert["severity"] for alert in alerts])
            
            elif report_type == "detailed":
                # Report dettagliato
                report["detailed_analysis"] = {
                    "error_analysis": _analyze_errors(log_data),
                    "pattern_analysis": _analyze_common_patterns(log_data),
                    "performance_metrics": _analyze_performance(log_data)
                }
            
            return {
                "success": True,
                **report
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def filter_log_entries(log_data: List[Dict[str, Any]], filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filtra le voci di log in base a criteri specifici.
        
        Args:
            log_data: Dati di log da filtrare
            filters: Criteri di filtro (level, time_range, message_contains, etc.)
        """
        try:
            if not log_data:
                return {
                    "success": False,
                    "error": "No log data provided"
                }
            
            filtered_entries = []
            
            for entry in log_data:
                parsed = entry.get("parsed_data", {})
                include_entry = True
                
                # Filtro per livello
                if "level" in filters:
                    required_level = filters["level"].upper()
                    entry_level = parsed.get("level", "").upper()
                    if entry_level != required_level:
                        include_entry = False
                
                # Filtro per contenuto messaggio
                if "message_contains" in filters and include_entry:
                    search_term = filters["message_contains"].lower()
                    message = parsed.get("message", "").lower()
                    raw_line = entry.get("raw_line", "").lower()
                    if search_term not in message and search_term not in raw_line:
                        include_entry = False
                
                # Filtro per regex
                if "message_regex" in filters and include_entry:
                    pattern = filters["message_regex"]
                    message = parsed.get("message", "")
                    raw_line = entry.get("raw_line", "")
                    if not re.search(pattern, message) and not re.search(pattern, raw_line):
                        include_entry = False
                
                # Filtro per range temporale
                if "time_range" in filters and include_entry:
                    time_range = filters["time_range"]
                    entry_timestamp = parsed.get("normalized_timestamp")
                    
                    if entry_timestamp:
                        start_time = time_range.get("start")
                        end_time = time_range.get("end")
                        
                        if start_time and entry_timestamp < start_time:
                            include_entry = False
                        if end_time and entry_timestamp > end_time:
                            include_entry = False
                
                # Filtro per numero di linea
                if "line_range" in filters and include_entry:
                    line_range = filters["line_range"]
                    line_number = entry.get("line_number", 0)
                    
                    start_line = line_range.get("start", 1)
                    end_line = line_range.get("end", float('inf'))
                    
                    if line_number < start_line or line_number > end_line:
                        include_entry = False
                
                if include_entry:
                    filtered_entries.append(entry)
            
            return {
                "success": True,
                "original_count": len(log_data),
                "filtered_count": len(filtered_entries),
                "filters_applied": filters,
                "reduction_percentage": round((1 - len(filtered_entries) / len(log_data)) * 100, 2),
                "filtered_entries": filtered_entries
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def export_log_analysis(analysis_data: Dict[str, Any], export_format: str = "json", file_path: str = "") -> Dict[str, Any]:
        """
        Esporta i risultati dell'analisi log in vari formati.
        
        Args:
            analysis_data: Dati dell'analisi da esportare
            export_format: Formato di export (json, csv, html, text)
            file_path: Percorso del file di output (opzionale)
        """
        try:
            if not analysis_data:
                return {
                    "success": False,
                    "error": "No analysis data provided"
                }
            
            # Genera file path se non fornito
            if not file_path:
                temp_dir = tempfile.mkdtemp(prefix="nexus_log_export_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = {
                    "json": ".json",
                    "csv": ".csv",
                    "html": ".html",
                    "text": ".txt"
                }.get(export_format, ".txt")
                file_path = os.path.join(temp_dir, f"log_analysis_{timestamp}{file_extension}")
            
            content = ""
            
            if export_format == "json":
                content = json.dumps(analysis_data, indent=2, default=str)
            
            elif export_format == "text":
                content = _format_analysis_as_text(analysis_data)
            
            elif export_format == "html":
                content = _format_analysis_as_html(analysis_data)
            
            elif export_format == "csv":
                content = _format_analysis_as_csv(analysis_data)
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported export format. Use: json, csv, html, text"
                }
            
            # Scrivi file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "export_format": export_format,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def detect_log_anomalies(log_data: List[Dict[str, Any]], 
                           anomaly_type: str = "statistical", 
                           sensitivity: float = 0.95) -> Dict[str, Any]:
        """
        Rileva anomalie nei log usando algoritmi di machine learning.
        
        Args:
            log_data: Dati di log da analizzare
            anomaly_type: Tipo di rilevamento (statistical, pattern, frequency, time_series)
            sensitivity: Soglia di sensibilità (0.1-0.99)
        """
        try:
            if not log_data:
                return {"success": False, "error": "No log data provided"}
            
            if not 0.1 <= sensitivity <= 0.99:
                return {"success": False, "error": "Sensitivity must be between 0.1 and 0.99"}
            
            anomalies = []
            baseline_stats = {}
            
            if anomaly_type == "statistical":
                # Anomalie statistiche basate su deviazione standard
                anomalies, baseline_stats = _detect_statistical_anomalies(log_data, sensitivity)
            
            elif anomaly_type == "pattern":
                # Anomalie nei pattern di messaggi
                anomalies, baseline_stats = _detect_pattern_anomalies(log_data, sensitivity)
            
            elif anomaly_type == "frequency":
                # Anomalie nella frequenza degli eventi
                anomalies, baseline_stats = _detect_frequency_anomalies(log_data, sensitivity)
            
            elif anomaly_type == "time_series":
                # Anomalie temporali
                anomalies, baseline_stats = _detect_time_series_anomalies(log_data, sensitivity)
            
            else:
                return {"success": False, "error": "Invalid anomaly_type. Use: statistical, pattern, frequency, time_series"}
            
            # Classifica anomalie per severità
            severity_classification = _classify_anomaly_severity(anomalies)
            
            return {
                "success": True,
                "anomaly_type": anomaly_type,
                "sensitivity": sensitivity,
                "total_entries": len(log_data),
                "anomalies_detected": len(anomalies),
                "anomaly_rate": round((len(anomalies) / len(log_data)) * 100, 2),
                "baseline_statistics": baseline_stats,
                "anomalies": anomalies[:50],  # Limit output
                "severity_breakdown": severity_classification,
                "recommendations": _generate_anomaly_recommendations(anomalies, anomaly_type)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def correlate_log_events(log_data: List[Dict[str, Any]], 
                           correlation_window: int = 300,
                           min_correlation_score: float = 0.7) -> Dict[str, Any]:
        """
        Correlazione eventi nei log per identificare pattern causali.
        
        Args:
            log_data: Dati di log da analizzare
            correlation_window: Finestra temporale per correlazione (secondi)
            min_correlation_score: Score minimo per correlazione (0.0-1.0)
        """
        try:
            if not log_data:
                return {"success": False, "error": "No log data provided"}
            
            # Ordina per timestamp
            sorted_logs = sorted(log_data, key=lambda x: x.get("parsed_data", {}).get("normalized_timestamp", 0))
            
            correlations = []
            event_groups = defaultdict(list)
            
            # Raggruppa eventi per tipo
            for entry in sorted_logs:
                parsed = entry.get("parsed_data", {})
                event_type = _classify_event_type(parsed)
                event_groups[event_type].append(entry)
            
            # Trova correlazioni tra tipi di eventi
            event_types = list(event_groups.keys())
            
            for i, type_a in enumerate(event_types):
                for type_b in event_types[i+1:]:
                    correlation = _calculate_event_correlation(
                        event_groups[type_a], 
                        event_groups[type_b], 
                        correlation_window
                    )
                    
                    if correlation["score"] >= min_correlation_score:
                        correlations.append({
                            "event_type_a": type_a,
                            "event_type_b": type_b,
                            "correlation_score": correlation["score"],
                            "temporal_relationship": correlation["relationship"],
                            "sample_pairs": correlation["sample_pairs"][:5],
                            "confidence": correlation["confidence"]
                        })
            
            # Identifica catene di eventi
            event_chains = _identify_event_chains(correlations, min_correlation_score)
            
            # Analisi pattern temporali
            temporal_patterns = _analyze_temporal_patterns(sorted_logs, correlation_window)
            
            return {
                "success": True,
                "correlation_window_seconds": correlation_window,
                "min_correlation_score": min_correlation_score,
                "total_events": len(log_data),
                "event_types_identified": len(event_types),
                "correlations_found": len(correlations),
                "correlations": correlations,
                "event_chains": event_chains,
                "temporal_patterns": temporal_patterns,
                "insights": _generate_correlation_insights(correlations, event_chains)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_log_dashboard(log_data: List[Dict[str, Any]], 
                           dashboard_type: str = "comprehensive",
                           time_granularity: str = "hour") -> Dict[str, Any]:
        """
        Crea dashboard visualizzazione per analisi log.
        
        Args:
            log_data: Dati di log da visualizzare
            dashboard_type: Tipo dashboard (comprehensive, errors, performance, security)
            time_granularity: Granularità temporale (minute, hour, day)
        """
        try:
            if not log_data:
                return {"success": False, "error": "No log data provided"}
            
            dashboard_data = {
                "dashboard_type": dashboard_type,
                "time_granularity": time_granularity,
                "generated_at": datetime.now().isoformat(),
                "total_entries": len(log_data)
            }
            
            # Analisi temporale
            time_series_data = _generate_time_series_data(log_data, time_granularity)
            dashboard_data["time_series"] = time_series_data
            
            if dashboard_type == "comprehensive":
                dashboard_data.update({
                    "overview_metrics": _generate_overview_metrics(log_data),
                    "log_level_distribution": _generate_log_level_chart_data(log_data),
                    "top_errors": _generate_top_errors_data(log_data),
                    "activity_heatmap": _generate_activity_heatmap(log_data),
                    "response_time_distribution": _generate_response_time_chart(log_data)
                })
            
            elif dashboard_type == "errors":
                dashboard_data.update({
                    "error_trends": _generate_error_trends(log_data, time_granularity),
                    "error_types": _generate_error_types_data(log_data),
                    "error_sources": _generate_error_sources_data(log_data),
                    "error_correlation": _generate_error_correlation_matrix(log_data)
                })
            
            elif dashboard_type == "performance":
                dashboard_data.update({
                    "response_time_trends": _generate_response_time_trends(log_data, time_granularity),
                    "throughput_metrics": _generate_throughput_metrics(log_data),
                    "performance_percentiles": _generate_performance_percentiles(log_data),
                    "slow_requests": _identify_slow_requests(log_data)
                })
            
            elif dashboard_type == "security":
                dashboard_data.update({
                    "security_events": _generate_security_events_data(log_data),
                    "ip_analysis": _generate_ip_analysis_data(log_data),
                    "attack_patterns": _identify_attack_patterns(log_data),
                    "access_patterns": _analyze_access_patterns(log_data)
                })
            
            # Genera HTML dashboard
            html_dashboard = _generate_html_dashboard(dashboard_data)
            
            # Salva dashboard
            temp_dir = tempfile.mkdtemp(prefix="nexus_dashboard_")
            dashboard_file = os.path.join(temp_dir, f"log_dashboard_{dashboard_type}.html")
            
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                f.write(html_dashboard)
            
            return {
                "success": True,
                "dashboard_file": dashboard_file,
                "dashboard_data": dashboard_data,
                "charts_generated": len([k for k in dashboard_data.keys() if k.endswith(('_chart', '_data', '_metrics'))]),
                "html_preview": html_dashboard[:500] + "..." if len(html_dashboard) > 500 else html_dashboard
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def setup_log_monitoring(log_file_path: str, 
                           monitoring_rules: List[Dict[str, Any]],
                           alert_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Configura monitoraggio real-time di file log.
        
        Args:
            log_file_path: Percorso file log da monitorare
            monitoring_rules: Regole di monitoraggio
            alert_thresholds: Soglie per alert
        """
        try:
            if not os.path.exists(log_file_path):
                return {"success": False, "error": "Log file not found"}
            
            alert_thresholds = alert_thresholds or {
                "error_rate_per_minute": 10,
                "response_time_threshold_ms": 5000,
                "unique_errors_threshold": 5
            }
            
            # Configurazione monitoraggio
            monitoring_config = {
                "log_file": log_file_path,
                "file_size": os.path.getsize(log_file_path),
                "last_modified": os.path.getmtime(log_file_path),
                "monitoring_rules": monitoring_rules,
                "alert_thresholds": alert_thresholds,
                "status": "configured"
            }
            
            # Valida regole di monitoraggio
            validated_rules = []
            for rule in monitoring_rules:
                validation_result = _validate_monitoring_rule(rule)
                if validation_result["valid"]:
                    validated_rules.append(rule)
                else:
                    return {"success": False, "error": f"Invalid rule: {validation_result['error']}"}
            
            # Simula setup monitoraggio (in un'implementazione reale, 
            # questo avvierebbe un thread di monitoraggio)
            monitoring_session_id = hashlib.md5(
                f"{log_file_path}_{time.time()}".encode()
            ).hexdigest()[:8]
            
            return {
                "success": True,
                "monitoring_session_id": monitoring_session_id,
                "monitoring_config": monitoring_config,
                "validated_rules": len(validated_rules),
                "status": "Monitoring configured successfully",
                "next_steps": [
                    "Monitor will check file every 30 seconds",
                    "Alerts will be generated based on thresholds",
                    "Use get_monitoring_status() to check alerts"
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_log_performance(log_data: List[Dict[str, Any]], 
                              metrics: List[str] = None) -> Dict[str, Any]:
        """
        Analisi approfondita performance da log applicativi.
        
        Args:
            log_data: Dati di log da analizzare
            metrics: Metriche specifiche da calcolare
        """
        try:
            if not log_data:
                return {"success": False, "error": "No log data provided"}
            
            metrics = metrics or ["response_time", "throughput", "error_rate", "resource_usage"]
            
            performance_analysis = {
                "analysis_period": _get_analysis_timeframe(log_data),
                "total_requests": 0,
                "metrics": {}
            }
            
            # Estrai dati performance
            response_times = []
            error_count = 0
            request_sizes = []
            timestamps = []
            status_codes = Counter()
            
            for entry in log_data:
                parsed = entry.get("parsed_data", {})
                raw_line = entry.get("raw_line", "")
                
                # Response time extraction
                if "response_time" in metrics:
                    rt = _extract_response_time(raw_line, parsed)
                    if rt is not None:
                        response_times.append(rt)
                
                # Throughput calculation
                if "throughput" in metrics:
                    timestamp = parsed.get("normalized_timestamp")
                    if timestamp:
                        timestamps.append(timestamp)
                
                # Error rate calculation
                if "error_rate" in metrics:
                    if _is_error_entry(parsed, raw_line):
                        error_count += 1
                
                # Resource usage
                if "resource_usage" in metrics:
                    size = _extract_request_size(raw_line, parsed)
                    if size is not None:
                        request_sizes.append(size)
                
                # Status codes
                status = parsed.get("status")
                if status:
                    status_codes[status] += 1
                    performance_analysis["total_requests"] += 1
            
            # Calcola metriche
            if "response_time" in metrics and response_times:
                performance_analysis["metrics"]["response_time"] = {
                    "avg_ms": round(statistics.mean(response_times), 2),
                    "median_ms": round(statistics.median(response_times), 2),
                    "p95_ms": round(_percentile(response_times, 95), 2),
                    "p99_ms": round(_percentile(response_times, 99), 2),
                    "min_ms": min(response_times),
                    "max_ms": max(response_times),
                    "std_dev": round(statistics.stdev(response_times) if len(response_times) > 1 else 0, 2),
                    "samples": len(response_times)
                }
            
            if "throughput" in metrics and timestamps:
                throughput_data = _calculate_throughput_metrics(timestamps)
                performance_analysis["metrics"]["throughput"] = throughput_data
            
            if "error_rate" in metrics:
                total_requests = performance_analysis["total_requests"]
                error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
                performance_analysis["metrics"]["error_rate"] = {
                    "percentage": round(error_rate, 2),
                    "total_errors": error_count,
                    "total_requests": total_requests,
                    "error_ratio": f"{error_count}:{total_requests}"
                }
            
            if "resource_usage" in metrics and request_sizes:
                performance_analysis["metrics"]["resource_usage"] = {
                    "avg_bytes": round(statistics.mean(request_sizes), 2),
                    "total_bytes": sum(request_sizes),
                    "max_bytes": max(request_sizes),
                    "min_bytes": min(request_sizes)
                }
            
            # Analisi status codes
            performance_analysis["status_code_distribution"] = dict(status_codes.most_common())
            
            # Performance scoring
            performance_score = _calculate_performance_score(performance_analysis["metrics"])
            performance_analysis["performance_score"] = performance_score
            
            # Raccomandazioni
            recommendations = _generate_performance_recommendations(performance_analysis["metrics"])
            performance_analysis["recommendations"] = recommendations
            
            return {
                "success": True,
                **performance_analysis
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_custom_log_parser(sample_logs: List[str], 
                                parser_name: str = "custom_parser") -> Dict[str, Any]:
        """
        Crea parser personalizzato basato su campioni di log.
        
        Args:
            sample_logs: Campioni di righe log per training
            parser_name: Nome del parser personalizzato
        """
        try:
            if not sample_logs:
                return {"success": False, "error": "No sample logs provided"}
            
            if len(sample_logs) < 3:
                return {"success": False, "error": "At least 3 sample logs required"}
            
            # Analizza pattern comuni
            pattern_analysis = _analyze_log_patterns_for_parser(sample_logs)
            
            # Genera regex pattern
            generated_pattern = _generate_regex_pattern(pattern_analysis)
            
            # Testa pattern sui campioni
            test_results = _test_parser_pattern(generated_pattern, sample_logs)
            
            # Ottimizza pattern
            if test_results["success_rate"] < 0.8:
                optimized_pattern = _optimize_parser_pattern(generated_pattern, sample_logs, test_results)
                final_test = _test_parser_pattern(optimized_pattern, sample_logs)
                
                if final_test["success_rate"] > test_results["success_rate"]:
                    generated_pattern = optimized_pattern
                    test_results = final_test
            
            # Genera documentazione parser
            parser_doc = _generate_parser_documentation(parser_name, generated_pattern, pattern_analysis)
            
            # Salva parser configuration
            parser_config = {
                "name": parser_name,
                "pattern": generated_pattern,
                "field_mappings": pattern_analysis["field_mappings"],
                "confidence_score": test_results["success_rate"],
                "sample_count": len(sample_logs),
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "parser_name": parser_name,
                "generated_pattern": generated_pattern,
                "success_rate": test_results["success_rate"],
                "field_mappings": pattern_analysis["field_mappings"],
                "test_results": test_results,
                "parser_config": parser_config,
                "documentation": parser_doc,
                "usage_example": _generate_parser_usage_example(parser_name, generated_pattern)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def aggregate_multi_source_logs(log_sources: List[Dict[str, Any]], 
                                  aggregation_strategy: str = "time_merge") -> Dict[str, Any]:
        """
        Aggrega log da multiple sorgenti con correlazione temporale.
        
        Args:
            log_sources: Lista di sorgenti log con dati
            aggregation_strategy: Strategia aggregazione (time_merge, event_correlation, source_priority)
        """
        try:
            if not log_sources:
                return {"success": False, "error": "No log sources provided"}
            
            if len(log_sources) > 10:
                return {"success": False, "error": "Too many log sources (max 10)"}
            
            aggregated_data = {
                "aggregation_strategy": aggregation_strategy,
                "source_count": len(log_sources),
                "total_entries": 0,
                "aggregated_entries": [],
                "source_statistics": {}
            }
            
            # Valida e normalizza sorgenti
            normalized_sources = []
            for i, source in enumerate(log_sources):
                source_name = source.get("name", f"source_{i+1}")
                source_data = source.get("log_data", [])
                source_type = source.get("type", "generic")
                
                if not source_data:
                    continue
                
                # Normalizza timestamp per ogni entry
                normalized_entries = []
                for entry in source_data:
                    normalized_entry = dict(entry)
                    normalized_entry["source_name"] = source_name
                    normalized_entry["source_type"] = source_type
                    
                    # Assicura timestamp normalizzato
                    parsed = entry.get("parsed_data", {})
                    if "normalized_timestamp" not in parsed:
                        parsed["normalized_timestamp"] = _extract_and_normalize_timestamp(entry)
                        normalized_entry["parsed_data"] = parsed
                    
                    normalized_entries.append(normalized_entry)
                
                normalized_sources.append({
                    "name": source_name,
                    "type": source_type,
                    "entries": normalized_entries,
                    "count": len(normalized_entries)
                })
                
                aggregated_data["source_statistics"][source_name] = {
                    "entry_count": len(normalized_entries),
                    "type": source_type,
                    "time_range": _get_source_time_range(normalized_entries)
                }
                aggregated_data["total_entries"] += len(normalized_entries)
            
            # Applica strategia di aggregazione
            if aggregation_strategy == "time_merge":
                # Merge cronologico
                all_entries = []
                for source in normalized_sources:
                    all_entries.extend(source["entries"])
                
                # Ordina per timestamp
                aggregated_data["aggregated_entries"] = sorted(
                    all_entries, 
                    key=lambda x: x.get("parsed_data", {}).get("normalized_timestamp", 0)
                )
            
            elif aggregation_strategy == "event_correlation":
                # Correlazione eventi tra sorgenti
                correlated_events = _correlate_cross_source_events(normalized_sources)
                aggregated_data["aggregated_entries"] = correlated_events["merged_timeline"]
                aggregated_data["correlation_groups"] = correlated_events["correlation_groups"]
            
            elif aggregation_strategy == "source_priority":
                # Aggregazione basata su priorità sorgenti
                priority_order = [source["name"] for source in normalized_sources]
                prioritized_entries = _merge_by_source_priority(normalized_sources, priority_order)
                aggregated_data["aggregated_entries"] = prioritized_entries
            
            # Analisi post-aggregazione
            post_analysis = _analyze_aggregated_logs(aggregated_data["aggregated_entries"])
            aggregated_data["post_aggregation_analysis"] = post_analysis
            
            # Identifica gap temporali
            time_gaps = _identify_temporal_gaps(aggregated_data["aggregated_entries"])
            aggregated_data["temporal_gaps"] = time_gaps
            
            return {
                "success": True,
                **aggregated_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Enhanced helper functions
    def _detect_statistical_anomalies(log_data: List[Dict], sensitivity: float) -> Tuple[List[Dict], Dict]:
        """Rileva anomalie statistiche usando Z-score."""
        anomalies = []
        
        # Calcola metriche baseline
        message_lengths = []
        hour_counts = defaultdict(int)
        
        for entry in log_data:
            parsed = entry.get("parsed_data", {})
            message = parsed.get("message", "")
            message_lengths.append(len(message))
            
            timestamp = parsed.get("normalized_timestamp")
            if timestamp:
                hour = int(timestamp // 3600)
                hour_counts[hour] += 1
        
        # Z-score per lunghezza messaggi
        if len(message_lengths) > 1:
            mean_length = statistics.mean(message_lengths)
            std_length = statistics.stdev(message_lengths)
            threshold = 1 - sensitivity  # Convert sensitivity to Z-score threshold
            
            for i, entry in enumerate(log_data):
                parsed = entry.get("parsed_data", {})
                message = parsed.get("message", "")
                z_score = abs((len(message) - mean_length) / std_length) if std_length > 0 else 0
                
                if z_score > (2 * (1 - threshold)):  # Adjusted threshold
                    anomalies.append({
                        "type": "message_length_anomaly",
                        "entry_index": i,
                        "z_score": round(z_score, 2),
                        "actual_length": len(message),
                        "expected_length": round(mean_length, 2),
                        "severity": "high" if z_score > 3 else "medium",
                        "line_number": entry.get("line_number"),
                        "message_preview": message[:100]
                    })
        
        baseline_stats = {
            "mean_message_length": round(statistics.mean(message_lengths), 2) if message_lengths else 0,
            "std_message_length": round(statistics.stdev(message_lengths), 2) if len(message_lengths) > 1 else 0,
            "total_messages": len(message_lengths)
        }
        
        return anomalies, baseline_stats

    def _detect_pattern_anomalies(log_data: List[Dict], sensitivity: float) -> Tuple[List[Dict], Dict]:
        """Rileva anomalie nei pattern di messaggi."""
        anomalies = []
        
        # Analizza pattern di messaggi
        message_patterns = defaultdict(int)
        
        for entry in log_data:
            parsed = entry.get("parsed_data", {})
            message = parsed.get("message", "")
            
            # Estrai pattern (sostituisci numeri e IDs con placeholder)
            pattern = re.sub(r'\d+', '[NUM]', message)
            pattern = re.sub(r'\b[a-f0-9]{8,32}\b', '[ID]', pattern)  # Hash/IDs
            pattern = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', '[IP]', pattern)  # IP addresses
            
            message_patterns[pattern] += 1
        
        # Identifica pattern rari
        total_messages = len(log_data)
        rare_threshold = max(1, int(total_messages * (1 - sensitivity)))
        
        rare_patterns = {pattern: count for pattern, count in message_patterns.items() 
                        if count <= rare_threshold}
        
        # Trova anomalie basate su pattern rari
        for i, entry in enumerate(log_data):
            parsed = entry.get("parsed_data", {})
            message = parsed.get("message", "")
            
            pattern = re.sub(r'\d+', '[NUM]', message)
            pattern = re.sub(r'\b[a-f0-9]{8,32}\b', '[ID]', pattern)
            pattern = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', '[IP]', pattern)
            
            if pattern in rare_patterns:
                anomalies.append({
                    "type": "rare_pattern_anomaly",
                    "entry_index": i,
                    "pattern": pattern,
                    "frequency": rare_patterns[pattern],
                    "rarity_score": round(1 - (rare_patterns[pattern] / total_messages), 3),
                    "severity": "high" if rare_patterns[pattern] == 1 else "medium",
                    "line_number": entry.get("line_number"),
                    "message": message
                })
        
        baseline_stats = {
            "total_patterns": len(message_patterns),
            "rare_patterns": len(rare_patterns),
            "most_common_pattern": max(message_patterns.items(), key=lambda x: x[1]) if message_patterns else None
        }
        
        return anomalies, baseline_stats

    def _classify_event_type(parsed_data: Dict) -> str:
        """Classifica il tipo di evento basandosi sui dati parsed."""
        level = parsed_data.get("level", "").upper()
        message = parsed_data.get("message", "").lower()
        status = parsed_data.get("status", "")
        
        if level in ["ERROR", "CRITICAL", "FATAL"]:
            return "error_event"
        elif level == "WARNING":
            return "warning_event"
        elif "login" in message or "auth" in message:
            return "authentication_event"
        elif status and status.startswith("2"):
            return "success_event"
        elif status and status.startswith(("4", "5")):
            return "error_event"
        elif "start" in message or "begin" in message:
            return "start_event"
        elif "end" in message or "complete" in message:
            return "end_event"
        else:
            return "general_event"

    def _generate_time_series_data(log_data: List[Dict], granularity: str) -> Dict[str, Any]:
        """Genera dati time series per visualizzazione."""
        time_buckets = defaultdict(int)
        
        for entry in log_data:
            parsed = entry.get("parsed_data", {})
            timestamp = parsed.get("normalized_timestamp")
            
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                
                if granularity == "minute":
                    bucket = dt.replace(second=0, microsecond=0)
                elif granularity == "hour":
                    bucket = dt.replace(minute=0, second=0, microsecond=0)
                elif granularity == "day":
                    bucket = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    bucket = dt.replace(minute=0, second=0, microsecond=0)  # default to hour
                
                time_buckets[bucket.isoformat()] += 1
        
        return {
            "granularity": granularity,
            "data_points": dict(sorted(time_buckets.items())),
            "peak_time": max(time_buckets.items(), key=lambda x: x[1])[0] if time_buckets else None,
            "peak_count": max(time_buckets.values()) if time_buckets else 0
        }

    # ...existing code...