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

def register_tools(mcp):
    """Registra i tool di performance con l'istanza del server MCP."""
    logging.info("⚡ Registrazione tool-set: Performance Tools")

    @mcp.tool()
    def benchmark_function_performance(code: str, iterations: int = 1000) -> Dict[str, Any]:
        """
        Esegue benchmark di performance su codice Python.
        
        Args:
            code: Codice Python da benchmarkare
            iterations: Numero di iterazioni (default: 1000)
        """
        try:
            import timeit
            
            # Prepara il codice per l'esecuzione
            setup_code = ""
            
            # Esegui benchmark
            total_time = timeit.timeit(code, setup=setup_code, number=iterations)
            avg_time = total_time / iterations
            
            # Calcola statistiche
            ops_per_second = 1 / avg_time if avg_time > 0 else float('inf')
            
            return {
                "code": code[:100] + "..." if len(code) > 100 else code,
                "iterations": iterations,
                "total_time_seconds": round(total_time, 6),
                "average_time_seconds": round(avg_time, 9),
                "operations_per_second": round(ops_per_second, 2),
                "performance_level": "Eccellente" if avg_time < 0.001 else 
                                  "Buona" if avg_time < 0.01 else 
                                  "Media" if avg_time < 0.1 else "Lenta"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Errore durante benchmark: {str(e)}"
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