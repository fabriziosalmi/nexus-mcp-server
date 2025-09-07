# -*- coding: utf-8 -*-
# tools/performance_tools.py
import time
import logging
import psutil
import threading
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import subprocess
import os
import hashlib
import platform

def register_tools(mcp):
    """Registra i tool di performance con l'istanza del server MCP."""
    logging.info("⚡ Registrazione tool-set: Performance Tools")

    @mcp.tool()
    def benchmark_function_performance(code: str, iterations: int = 1000, setup_code: str = "") -> Dict[str, Any]:
        """
        Esegue benchmark di performance su codice Python con analisi avanzata.
        
        Args:
            code: Codice Python da benchmarkare
            iterations: Numero di iterazioni (default: 1000, max: 100000)
            setup_code: Codice di setup da eseguire una volta (opzionale)
        """
        try:
            import timeit
            import gc
            
            # Validazione input
            iterations = min(max(iterations, 1), 100000)  # Clamp tra 1 e 100k
            
            if not code.strip():
                return {"success": False, "error": "Codice non può essere vuoto"}
            
            # Prepara il codice per l'esecuzione
            setup_code = setup_code or ""
            
            # Memoria pre-test
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Test multipli per stabilità
            test_runs = min(5, max(1, iterations // 1000))
            run_times = []
            
            for run in range(test_runs):
                # Forza garbage collection
                gc.collect()
                
                # Esegui benchmark
                run_time = timeit.timeit(code, setup=setup_code, number=iterations // test_runs)
                run_times.append(run_time)
            
            # Memoria post-test
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_after - memory_before
            
            # Calcola statistiche avanzate
            total_time = sum(run_times)
            avg_time_per_iteration = total_time / iterations
            min_run_time = min(run_times)
            max_run_time = max(run_times)
            
            # Stabilità del test (coefficiente di variazione)
            import statistics
            if len(run_times) > 1:
                std_dev = statistics.stdev(run_times)
                mean_time = statistics.mean(run_times)
                cv = (std_dev / mean_time) * 100 if mean_time > 0 else 0
            else:
                cv = 0
            
            # Calcola metriche performance
            ops_per_second = 1 / avg_time_per_iteration if avg_time_per_iteration > 0 else float('inf')
            
            # Classificazione performance
            if avg_time_per_iteration < 0.000001:  # < 1 microsecondo
                perf_level = "Eccellente"
                perf_score = 10
            elif avg_time_per_iteration < 0.00001:  # < 10 microsecondi
                perf_level = "Ottima" 
                perf_score = 8
            elif avg_time_per_iteration < 0.0001:  # < 100 microsecondi
                perf_level = "Buona"
                perf_score = 6
            elif avg_time_per_iteration < 0.001:   # < 1 millisecondo
                perf_level = "Media"
                perf_score = 4
            else:
                perf_level = "Lenta"
                perf_score = 2
            
            return {
                "code_snippet": code[:100] + "..." if len(code) > 100 else code,
                "test_configuration": {
                    "total_iterations": iterations,
                    "test_runs": test_runs,
                    "iterations_per_run": iterations // test_runs
                },
                "timing_results": {
                    "total_time_seconds": round(total_time, 6),
                    "average_time_per_iteration": round(avg_time_per_iteration, 9),
                    "min_run_time": round(min_run_time, 6),
                    "max_run_time": round(max_run_time, 6),
                    "time_stability_cv_percent": round(cv, 2)
                },
                "performance_metrics": {
                    "operations_per_second": round(ops_per_second, 2),
                    "performance_level": perf_level,
                    "performance_score": perf_score,
                    "stability_rating": "Stabile" if cv < 5 else "Variabile" if cv < 15 else "Instabile"
                },
                "memory_usage": {
                    "memory_before_mb": round(memory_before, 2),
                    "memory_after_mb": round(memory_after, 2),
                    "memory_delta_mb": round(memory_delta, 2),
                    "memory_leak_detected": memory_delta > 10  # >10MB delta
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Errore durante benchmark: {str(e)}",
                "code_snippet": code[:100] + "..." if len(code) > 100 else code
            }

    @mcp.tool()
    def monitor_system_performance(duration_seconds: int = 10) -> Dict[str, Any]:
        """
        Monitora performance del sistema per un periodo specificato.
        
        Args:
            duration_seconds: Durata del monitoraggio in secondi (default: 10)
        """
        try:
            samples = []
            interval = 1  # Campiona ogni secondo
            
            start_time = datetime.now()
            
            for _ in range(min(duration_seconds, 60)):  # Max 60 secondi per sicurezza
                sample = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                    "network_io": psutil.net_io_counters()._asdict(),
                    "processes_count": len(psutil.pids())
                }
                samples.append(sample)
                time.sleep(interval)
            
            # Calcola statistiche
            cpu_values = [s["cpu_percent"] for s in samples]
            memory_values = [s["memory_percent"] for s in samples]
            
            return {
                "monitoring_duration": duration_seconds,
                "samples_collected": len(samples),
                "cpu_stats": {
                    "average": round(sum(cpu_values) / len(cpu_values), 2),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory_stats": {
                    "average": round(sum(memory_values) / len(memory_values), 2),
                    "max": max(memory_values),
                    "min": min(memory_values)
                },
                "process_count": samples[-1]["processes_count"],
                "samples": samples[:10],  # Restituisce solo i primi 10 campioni per brevità
                "warning": "Dati limitati ai primi 10 campioni per output compatto"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_memory_usage() -> Dict[str, Any]:
        """
        Analizza l'utilizzo dettagliato della memoria del sistema.
        """
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            # Top processi per memoria
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    if pinfo['memory_percent'] > 0.1:  # Solo processi > 0.1%
                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "memory_percent": round(pinfo['memory_percent'], 2),
                            "memory_mb": round(pinfo['memory_info'].rss / 1024 / 1024, 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordina per utilizzo memoria
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return {
                "virtual_memory": {
                    "total_gb": round(virtual_mem.total / (1024**3), 2),
                    "available_gb": round(virtual_mem.available / (1024**3), 2),
                    "used_gb": round(virtual_mem.used / (1024**3), 2),
                    "percent_used": virtual_mem.percent
                },
                "swap_memory": {
                    "total_gb": round(swap_mem.total / (1024**3), 2),
                    "used_gb": round(swap_mem.used / (1024**3), 2),
                    "percent_used": swap_mem.percent
                },
                "top_memory_consumers": processes[:10],
                "memory_pressure": "Alta" if virtual_mem.percent > 90 else 
                                 "Media" if virtual_mem.percent > 70 else "Bassa"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def disk_performance_test(test_size_mb: int = 10) -> Dict[str, Any]:
        """
        Esegue test di performance del disco.
        
        Args:
            test_size_mb: Dimensione del file di test in MB (default: 10)
        """
        try:
            import tempfile
            import os
            
            test_size_mb = min(test_size_mb, 100)  # Max 100MB per sicurezza
            test_size_bytes = test_size_mb * 1024 * 1024
            
            # Test di scrittura
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Scrittura sequenziale
                start_time = time.time()
                data = b'0' * 1024  # 1KB di dati
                for _ in range(test_size_mb * 1024):
                    temp_file.write(data)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                write_time = time.time() - start_time
            
            # Test di lettura
            start_time = time.time()
            with open(temp_path, 'rb') as f:
                while f.read(1024):
                    pass
            read_time = time.time() - start_time
            
            # Cleanup
            os.unlink(temp_path)
            
            # Calcola velocità
            write_speed_mbps = test_size_mb / write_time if write_time > 0 else 0
            read_speed_mbps = test_size_mb / read_time if read_time > 0 else 0
            
            return {
                "test_size_mb": test_size_mb,
                "write_performance": {
                    "time_seconds": round(write_time, 3),
                    "speed_mbps": round(write_speed_mbps, 2)
                },
                "read_performance": {
                    "time_seconds": round(read_time, 3),
                    "speed_mbps": round(read_speed_mbps, 2)
                },
                "disk_rating": "Eccellente" if min(write_speed_mbps, read_speed_mbps) > 100 else
                             "Buona" if min(write_speed_mbps, read_speed_mbps) > 50 else
                             "Media" if min(write_speed_mbps, read_speed_mbps) > 10 else "Lenta"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def network_latency_test(hosts: List[str] = ["8.8.8.8", "1.1.1.1"]) -> Dict[str, Any]:
        """
        Testa la latenza di rete verso host specificati.
        
        Args:
            hosts: Lista di host da testare (default: DNS pubblici)
        """
        try:
            results = {}
            
            for host in hosts[:5]:  # Max 5 host per sicurezza
                try:
                    # Usa ping per testare latenza
                    result = subprocess.run(
                        ['ping', '-c', '4', host],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        # Analizza output ping per estrarre statistiche
                        lines = result.stdout.split('\n')
                        stats_line = [line for line in lines if 'min/avg/max' in line]
                        
                        if stats_line:
                            # Estrai statistiche da: rtt min/avg/max/mdev = 1.234/5.678/9.012/1.345 ms
                            stats_part = stats_line[0].split('=')[1].strip()
                            times = stats_part.split('/')[:-1]  # Escludi mdev
                            
                            results[host] = {
                                "success": True,
                                "min_ms": float(times[0]),
                                "avg_ms": float(times[1]),
                                "max_ms": float(times[2]),
                                "rating": "Eccellente" if float(times[1]) < 20 else
                                        "Buona" if float(times[1]) < 50 else
                                        "Media" if float(times[1]) < 100 else "Lenta"
                            }
                        else:
                            results[host] = {"success": True, "raw_output": result.stdout}
                    else:
                        results[host] = {"success": False, "error": "Ping fallito"}
                        
                except subprocess.TimeoutExpired:
                    results[host] = {"success": False, "error": "Timeout"}
                except Exception as e:
                    results[host] = {"success": False, "error": str(e)}
            
            return {
                "hosts_tested": len(results),
                "results": results,
                "overall_rating": "Buona" if any(r.get("success") for r in results.values()) else "Problemi"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def cpu_stress_test(duration_seconds: int = 5) -> Dict[str, Any]:
        """
        Esegue stress test della CPU per misurare performance.
        
        Args:
            duration_seconds: Durata del test in secondi (max 30)
        """
        try:
            import multiprocessing
            
            duration_seconds = min(duration_seconds, 30)  # Max 30 secondi per sicurezza
            cpu_count = multiprocessing.cpu_count()
            
            # Baseline CPU
            baseline_cpu = psutil.cpu_percent(interval=1)
            
            # Funzione per stress CPU
            def cpu_intensive_task():
                end_time = time.time() + duration_seconds
                counter = 0
                while time.time() < end_time:
                    # Calcoli matematici intensivi
                    counter += 1
                    _ = counter ** 0.5
                return counter
            
            # Avvia test
            start_time = time.time()
            
            # Monitora CPU durante test
            threads = []
            for _ in range(cpu_count):
                thread = threading.Thread(target=cpu_intensive_task)
                threads.append(thread)
                thread.start()
            
            # Campiona CPU usage durante test
            cpu_samples = []
            while any(t.is_alive() for t in threads):
                cpu_samples.append(psutil.cpu_percent(interval=0.1))
            
            # Aspetta completamento
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # CPU usage post-test
            post_test_cpu = psutil.cpu_percent(interval=1)
            
            # Analizza risultati
            max_cpu = max(cpu_samples) if cpu_samples else 0
            avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            
            return {
                "test_duration": round(actual_duration, 2),
                "cpu_cores_used": cpu_count,
                "baseline_cpu_percent": baseline_cpu,
                "max_cpu_percent": round(max_cpu, 2),
                "average_cpu_percent": round(avg_cpu, 2),
                "post_test_cpu_percent": post_test_cpu,
                "cpu_performance": "Eccellente" if max_cpu > 90 else
                                 "Buona" if max_cpu > 70 else
                                 "Media" if max_cpu > 50 else "Limitata",
                "samples_collected": len(cpu_samples)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def comprehensive_system_health() -> Dict[str, Any]:
        """
        Analisi completa dello stato di salute del sistema.
        """
        try:
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "platform": platform.platform(),
                    "processor": platform.processor(),
                    "architecture": platform.architecture()[0],
                    "python_version": platform.python_version(),
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
                }
            }
            
            # CPU Health
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            
            health_report["cpu_health"] = {
                "usage_percent": cpu_percent,
                "logical_cores": cpu_count,
                "physical_cores": psutil.cpu_count(logical=False),
                "current_frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else "N/A",
                "max_frequency_mhz": round(cpu_freq.max, 2) if cpu_freq else "N/A",
                "health_score": 10 - min(cpu_percent // 10, 9),  # 10 = idle, 1 = 90%+
                "status": "Ottimo" if cpu_percent < 20 else "Buono" if cpu_percent < 50 else 
                         "Carico" if cpu_percent < 80 else "Critico"
            }
            
            # Memory Health
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            health_report["memory_health"] = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent,
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_used_percent": swap.percent,
                "health_score": 10 - min(memory.percent // 10, 9),
                "status": "Ottimo" if memory.percent < 30 else "Buono" if memory.percent < 60 else
                         "Pieno" if memory.percent < 85 else "Critico"
            }
            
            # Disk Health
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            health_report["disk_health"] = {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "used_percent": round((disk_usage.used / disk_usage.total) * 100, 2),
                "read_count": disk_io.read_count if disk_io else 0,
                "write_count": disk_io.write_count if disk_io else 0,
                "health_score": 10 - min((disk_usage.used / disk_usage.total * 100) // 10, 9),
                "status": "Ottimo" if disk_usage.used / disk_usage.total < 0.5 else 
                         "Buono" if disk_usage.used / disk_usage.total < 0.8 else "Pieno"
            }
            
            # Network Health
            network_io = psutil.net_io_counters()
            network_connections = len(psutil.net_connections())
            
            health_report["network_health"] = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_received": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_received": network_io.packets_recv,
                "active_connections": network_connections,
                "errors_in": network_io.errin,
                "errors_out": network_io.errout,
                "status": "Buono" if network_io.errin + network_io.errout < 10 else "Problemi"
            }
            
            # Process Health
            processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
            active_processes = len(processes)
            zombie_processes = len([p for p in processes if p.info['name'] == '<defunct>'])
            
            health_report["process_health"] = {
                "total_processes": active_processes,
                "zombie_processes": zombie_processes,
                "status": "Buono" if zombie_processes == 0 else "Attenzione"
            }
            
            # Temperature (se disponibile)
            try:
                temperatures = psutil.sensors_temperatures()
                if temperatures:
                    temp_values = []
                    for name, entries in temperatures.items():
                        for entry in entries:
                            if entry.current:
                                temp_values.append(entry.current)
                    
                    if temp_values:
                        avg_temp = sum(temp_values) / len(temp_values)
                        max_temp = max(temp_values)
                        
                        health_report["temperature_health"] = {
                            "average_celsius": round(avg_temp, 1),
                            "maximum_celsius": round(max_temp, 1),
                            "status": "Normale" if max_temp < 70 else "Caldo" if max_temp < 85 else "Critico"
                        }
            except:
                health_report["temperature_health"] = {"status": "Non disponibile"}
            
            # GPU Info (se disponibile)
            health_report["gpu_info"] = detect_gpu_info()
            
            # Calcola punteggio salute generale
            scores = [
                health_report["cpu_health"]["health_score"],
                health_report["memory_health"]["health_score"], 
                health_report["disk_health"]["health_score"]
            ]
            overall_score = sum(scores) / len(scores)
            
            health_report["overall_health"] = {
                "score": round(overall_score, 1),
                "rating": "Eccellente" if overall_score >= 8 else "Buono" if overall_score >= 6 else
                         "Medio" if overall_score >= 4 else "Problematico",
                "recommendations": generate_health_recommendations(health_report)
            }
            
            return health_report
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Errore nell'analisi salute sistema: {str(e)}"
            }

    @mcp.tool()
    def detect_gpu_info() -> Dict[str, Any]:
        """
        Rileva informazioni sulla GPU del sistema.
        """
        try:
            gpu_info = {
                "gpu_detected": False,
                "gpu_count": 0,
                "gpus": []
            }
            
            # Prova con nvidia-smi
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for i, line in enumerate(lines):
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 5:
                            gpu_info["gpus"].append({
                                "id": i,
                                "name": parts[0],
                                "memory_total_mb": int(parts[1]) if parts[1].isdigit() else 0,
                                "memory_used_mb": int(parts[2]) if parts[2].isdigit() else 0,
                                "utilization_percent": int(parts[3]) if parts[3].isdigit() else 0,
                                "temperature_celsius": int(parts[4]) if parts[4].isdigit() else 0,
                                "type": "NVIDIA"
                            })
                    
                    gpu_info["gpu_detected"] = len(gpu_info["gpus"]) > 0
                    gpu_info["gpu_count"] = len(gpu_info["gpus"])
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Prova con lspci per rilevamento GPU generale
            if not gpu_info["gpu_detected"]:
                try:
                    result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        gpu_lines = [line for line in result.stdout.split('\n') 
                                   if 'VGA' in line or 'Display' in line or '3D' in line]
                        
                        for i, line in enumerate(gpu_lines):
                            gpu_name = line.split(': ')[-1] if ': ' in line else line
                            gpu_info["gpus"].append({
                                "id": i,
                                "name": gpu_name.strip(),
                                "type": "Generic",
                                "detected_via": "lspci"
                            })
                        
                        gpu_info["gpu_detected"] = len(gpu_info["gpus"]) > 0
                        gpu_info["gpu_count"] = len(gpu_info["gpus"])
                        
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Fallback: controlla driver
            if not gpu_info["gpu_detected"]:
                drivers_to_check = ['/proc/driver/nvidia/version', '/sys/kernel/debug/dri']
                for driver_path in drivers_to_check:
                    if os.path.exists(driver_path):
                        gpu_info["gpu_detected"] = True
                        gpu_info["gpus"].append({
                            "name": "GPU rilevata via driver",
                            "type": "Driver Detection",
                            "driver_path": driver_path
                        })
                        break
            
            return gpu_info
            
        except Exception as e:
            return {
                "gpu_detected": False,
                "error": f"Errore rilevamento GPU: {str(e)}"
            }

    @mcp.tool()
    def profile_top_processes(limit: int = 10) -> Dict[str, Any]:
        """
        Profila i processi più impattanti sul sistema.
        
        Args:
            limit: Numero massimo di processi da analizzare (default: 10, max: 50)
        """
        try:
            limit = min(max(limit, 1), 50)
            
            # Raccoglie info processi
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'memory_info', 'create_time', 'num_threads', 'status']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] is not None and pinfo['memory_percent'] is not None:
                        # Calcola età processo
                        age_seconds = time.time() - pinfo['create_time']
                        
                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "cpu_percent": round(pinfo['cpu_percent'], 2),
                            "memory_percent": round(pinfo['memory_percent'], 2),
                            "memory_mb": round(pinfo['memory_info'].rss / 1024 / 1024, 2),
                            "threads": pinfo['num_threads'],
                            "status": pinfo['status'],
                            "age_hours": round(age_seconds / 3600, 1),
                            "impact_score": (pinfo['cpu_percent'] * 0.6) + (pinfo['memory_percent'] * 0.4)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Ordina per impact score
            processes.sort(key=lambda x: x['impact_score'], reverse=True)
            top_processes = processes[:limit]
            
            # Analisi aggregata
            total_cpu = sum(p['cpu_percent'] for p in processes)
            total_memory = sum(p['memory_percent'] for p in processes)
            
            # Trova processi problematici
            high_cpu_procs = [p for p in top_processes if p['cpu_percent'] > 20]
            high_memory_procs = [p for p in top_processes if p['memory_percent'] > 10]
            many_threads_procs = [p for p in top_processes if p['threads'] > 100]
            zombie_procs = [p for p in processes if p['status'] == 'zombie']
            
            return {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_processes_analyzed": len(processes),
                "top_processes": top_processes,
                "system_totals": {
                    "total_cpu_percent": round(total_cpu, 2),
                    "total_memory_percent": round(total_memory, 2),
                    "active_processes": len([p for p in processes if p['status'] == 'running'])
                },
                "problem_indicators": {
                    "high_cpu_processes": len(high_cpu_procs),
                    "high_memory_processes": len(high_memory_procs),
                    "high_thread_processes": len(many_threads_procs),
                    "zombie_processes": len(zombie_procs)
                },
                "recommendations": {
                    "action_needed": len(high_cpu_procs) > 0 or len(zombie_procs) > 0,
                    "suggestions": generate_process_recommendations(high_cpu_procs, high_memory_procs, zombie_procs)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Errore nel profiling processi: {str(e)}"
            }

    @mcp.tool()
    def performance_comparison_test() -> Dict[str, Any]:
        """
        Esegue una suite di test per confrontare performance relative del sistema.
        """
        try:
            test_results = {
                "test_timestamp": datetime.now().isoformat(),
                "system_identifier": hashlib.md5(platform.node().encode()).hexdigest()[:8]
            }
            
            # Test 1: CPU Integer Math
            start_time = time.time()
            result = 0
            for i in range(1000000):
                result += i * i
            cpu_int_time = time.time() - start_time
            
            # Test 2: CPU Float Math  
            start_time = time.time()
            result = 0.0
            for i in range(1000000):
                result += (i * 3.14159) / 2.71828
            cpu_float_time = time.time() - start_time
            
            # Test 3: Memory Allocation
            start_time = time.time()
            arrays = []
            for i in range(1000):
                arrays.append([j for j in range(1000)])
            memory_alloc_time = time.time() - start_time
            del arrays  # Cleanup
            
            # Test 4: String Operations
            start_time = time.time()
            text = ""
            for i in range(10000):
                text += f"test string {i} "
            string_time = time.time() - start_time
            
            # Test 5: File I/O
            import tempfile
            start_time = time.time()
            with tempfile.NamedTemporaryFile(mode='w+', delete=True) as f:
                for i in range(10000):
                    f.write(f"line {i}\n")
                f.flush()
                f.seek(0)
                content = f.read()
            file_io_time = time.time() - start_time
            
            # Normalizza i risultati (lower is better)
            test_results["benchmark_results"] = {
                "cpu_integer_math": {
                    "time_seconds": round(cpu_int_time, 4),
                    "operations_per_second": round(1000000 / cpu_int_time, 0),
                    "relative_score": round(1.0 / cpu_int_time, 2)
                },
                "cpu_float_math": {
                    "time_seconds": round(cpu_float_time, 4), 
                    "operations_per_second": round(1000000 / cpu_float_time, 0),
                    "relative_score": round(1.0 / cpu_float_time, 2)
                },
                "memory_allocation": {
                    "time_seconds": round(memory_alloc_time, 4),
                    "allocations_per_second": round(1000 / memory_alloc_time, 0),
                    "relative_score": round(1.0 / memory_alloc_time, 2)
                },
                "string_operations": {
                    "time_seconds": round(string_time, 4),
                    "operations_per_second": round(10000 / string_time, 0),
                    "relative_score": round(1.0 / string_time, 2)
                },
                "file_io": {
                    "time_seconds": round(file_io_time, 4),
                    "operations_per_second": round(10000 / file_io_time, 0),
                    "relative_score": round(1.0 / file_io_time, 2)
                }
            }
            
            # Calcola punteggio composito
            scores = [result["relative_score"] for result in test_results["benchmark_results"].values()]
            composite_score = sum(scores) / len(scores)
            
            test_results["overall_performance"] = {
                "composite_score": round(composite_score, 2),
                "performance_class": classify_performance(composite_score),
                "strongest_area": max(test_results["benchmark_results"].items(), key=lambda x: x[1]["relative_score"])[0],
                "weakest_area": min(test_results["benchmark_results"].items(), key=lambda x: x[1]["relative_score"])[0]
            }
            
            return test_results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Errore nei test di performance: {str(e)}"
            }

def generate_health_recommendations(health_report: Dict[str, Any]) -> List[str]:
    """Genera raccomandazioni basate sul report di salute."""
    recommendations = []
    
    if health_report["cpu_health"]["usage_percent"] > 80:
        recommendations.append("CPU sotto stress - chiudi applicazioni non necessarie")
    
    if health_report["memory_health"]["used_percent"] > 85:
        recommendations.append("Memoria quasi esaurita - libera RAM o aggiungi memoria")
    
    if health_report["disk_health"]["used_percent"] > 90:
        recommendations.append("Spazio disco critico - libera spazio o espandi storage")
    
    if health_report.get("temperature_health", {}).get("maximum_celsius", 0) > 80:
        recommendations.append("Temperature elevate - verifica ventilazione e pulizia")
    
    if health_report["process_health"]["zombie_processes"] > 0:
        recommendations.append("Processi zombie rilevati - riavvio consigliato")
    
    if not recommendations:
        recommendations.append("Sistema in buone condizioni - nessuna azione richiesta")
    
    return recommendations

def generate_process_recommendations(high_cpu: List, high_memory: List, zombies: List) -> List[str]:
    """Genera raccomandazioni basate sull'analisi dei processi."""
    recommendations = []
    
    if high_cpu:
        recommendations.append(f"{len(high_cpu)} processi con alto uso CPU - considera terminazione se non necessari")
    
    if high_memory:
        recommendations.append(f"{len(high_memory)} processi con alto uso memoria - verifica memory leak")
    
    if zombies:
        recommendations.append(f"{len(zombies)} processi zombie - riavvio processo padre consigliato")
    
    if not recommendations:
        recommendations.append("Processi in stato normale - monitoraggio continuo")
    
    return recommendations

def classify_performance(score: float) -> str:
    """Classifica il livello di performance basato sul punteggio."""
    if score > 50:
        return "Eccellente"
    elif score > 20:
        return "Buona"
    elif score > 10:
        return "Media"
    elif score > 5:
        return "Bassa"
    else:
        return "Molto Bassa"