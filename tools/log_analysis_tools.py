# -*- coding: utf-8 -*-
# tools/log_analysis_tools.py
import re
import os
import json
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import time
from datetime import datetime, timedelta

def register_tools(mcp):
    """Registra i tool di analisi log con l'istanza del server MCP."""
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

# Helper functions
def _detect_log_format(line, patterns):
    """Auto-rileva il formato del log basandosi sulla prima linea."""
    for format_name, pattern in patterns.items():
        if re.match(pattern, line):
            return format_name
    return "generic"

def _normalize_timestamp(timestamp_str):
    """Normalizza timestamp in formato Unix."""
    try:
        # Common timestamp formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S",
            "%b %d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f"
        ]
        
        # Remove timezone info and brackets
        clean_timestamp = re.sub(r'[\[\]+-]\d{4}', '', timestamp_str).strip()
        
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_timestamp, fmt)
                # Se l'anno non è specificato, usa l'anno corrente
                if dt.year == 1900:
                    dt = dt.replace(year=datetime.now().year)
                return dt.timestamp()
            except ValueError:
                continue
        
        return None
    except:
        return None

def _analyze_parsed_entries(entries):
    """Analizza le voci parsate per estrarre statistiche base."""
    if not entries:
        return {}
    
    levels = Counter()
    formats = Counter()
    
    for entry in entries:
        parsed = entry.get("parsed_data", {})
        
        level = parsed.get("level", "UNKNOWN")
        levels[level.upper()] += 1
        
        fmt = entry.get("format", "unknown")
        formats[fmt] += 1
    
    return {
        "log_levels": dict(levels),
        "formats_detected": dict(formats),
        "most_common_level": levels.most_common(1)[0] if levels else None
    }

def _analyze_errors(log_data):
    """Analizza errori specifici nei log."""
    error_entries = []
    for entry in log_data:
        parsed = entry.get("parsed_data", {})
        level = parsed.get("level", "").upper()
        if level in ["ERROR", "CRITICAL", "FATAL"]:
            error_entries.append(entry)
    
    return {
        "total_errors": len(error_entries),
        "error_percentage": (len(error_entries) / len(log_data) * 100) if log_data else 0,
        "sample_errors": error_entries[:5]
    }

def _analyze_common_patterns(log_data):
    """Analizza pattern comuni nei messaggi."""
    messages = []
    for entry in log_data:
        parsed = entry.get("parsed_data", {})
        message = parsed.get("message", "")
        if message:
            messages.append(message)
    
    # Trova le parole più comuni
    all_words = []
    for message in messages:
        words = re.findall(r'\w+', message.lower())
        all_words.extend(words)
    
    word_counts = Counter(all_words)
    
    return {
        "total_messages": len(messages),
        "unique_words": len(word_counts),
        "most_common_words": dict(word_counts.most_common(10))
    }

def _analyze_performance(log_data):
    """Analizza metriche di performance dai log."""
    response_times = []
    
    for entry in log_data:
        line = entry.get("raw_line", "")
        # Cerca pattern di response time
        time_match = re.search(r'(\d+(?:\.\d+)?)\s*ms', line)
        if time_match:
            response_times.append(float(time_match.group(1)))
    
    if response_times:
        return {
            "avg_response_time_ms": round(sum(response_times) / len(response_times), 2),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "samples": len(response_times)
        }
    
    return {"response_time_data": "No performance data found"}

def _format_analysis_as_text(data):
    """Formatta l'analisi come testo."""
    text = "LOG ANALYSIS REPORT\n"
    text += "=" * 50 + "\n\n"
    
    for key, value in data.items():
        if isinstance(value, dict):
            text += f"{key.upper()}:\n"
            for k, v in value.items():
                text += f"  {k}: {v}\n"
        else:
            text += f"{key}: {value}\n"
        text += "\n"
    
    return text

def _format_analysis_as_html(data):
    """Formatta l'analisi come HTML."""
    html = """
    <html>
    <head><title>Log Analysis Report</title></head>
    <body>
    <h1>Log Analysis Report</h1>
    """
    
    for key, value in data.items():
        html += f"<h2>{key.replace('_', ' ').title()}</h2>"
        if isinstance(value, dict):
            html += "<ul>"
            for k, v in value.items():
                html += f"<li><strong>{k}:</strong> {v}</li>"
            html += "</ul>"
        else:
            html += f"<p>{value}</p>"
    
    html += "</body></html>"
    return html

def _format_analysis_as_csv(data):
    """Formatta l'analisi come CSV (semplificato)."""
    csv = "key,value\n"
    
    def flatten_dict(d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    flat_data = flatten_dict(data)
    for key, value in flat_data.items():
        csv += f'"{key}","{value}"\n'
    
    return csv