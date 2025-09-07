# -*- coding: utf-8 -*-
# tools/process_management_tools.py
import subprocess
import psutil
import signal
import os
import tempfile
import resource
import logging
from typing import Dict, List, Any, Optional
import time
import json
import hashlib
from datetime import datetime, timedelta
import threading

def register_tools(mcp):
    """Registra i tool di gestione processi con l'istanza del server MCP."""
    logging.info("⚙️ Registrazione tool-set: Process Management Tools")

    @mcp.tool()
    def list_processes_by_criteria(criteria: str = "cpu", limit: int = 10) -> Dict[str, Any]:
        """
        Lista i processi in base a criteri specifici.
        
        Args:
            criteria: Criterio di ordinamento (cpu, memory, name, pid)
            limit: Numero massimo di processi da mostrare (1-50)
        """
        try:
            if limit < 1 or limit > 50:
                return {
                    "success": False,
                    "error": "Limit must be between 1 and 50"
                }
            
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time', 'cmdline']):
                try:
                    proc_info = proc.info
                    proc_info['cpu_percent'] = proc_info.get('cpu_percent', 0) or 0
                    proc_info['memory_percent'] = proc_info.get('memory_percent', 0) or 0
                    proc_info['cmdline'] = ' '.join(proc_info.get('cmdline', [])[:3])  # Primi 3 argomenti
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Ordina in base al criterio
            if criteria.lower() == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif criteria.lower() == "memory":
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            elif criteria.lower() == "name":
                processes.sort(key=lambda x: x['name'].lower())
            elif criteria.lower() == "pid":
                processes.sort(key=lambda x: x['pid'])
            else:
                return {
                    "success": False,
                    "error": "Invalid criteria. Use: cpu, memory, name, pid"
                }
            
            # Prendi solo i primi N
            top_processes = processes[:limit]
            
            # Calcola statistiche
            total_cpu = sum(p['cpu_percent'] for p in processes)
            total_memory = sum(p['memory_percent'] for p in processes)
            running_count = len([p for p in processes if p['status'] == 'running'])
            
            return {
                "success": True,
                "criteria": criteria,
                "limit": limit,
                "total_processes": len(processes),
                "running_processes": running_count,
                "system_stats": {
                    "total_cpu_usage": round(total_cpu, 2),
                    "total_memory_usage": round(total_memory, 2)
                },
                "processes": top_processes
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def monitor_process(pid: int, duration: int = 30) -> Dict[str, Any]:
        """
        Monitora un processo specifico per un periodo di tempo.
        
        Args:
            pid: ID del processo da monitorare
            duration: Durata del monitoraggio in secondi (5-300)
        """
        try:
            if duration < 5 or duration > 300:
                return {
                    "success": False,
                    "error": "Duration must be between 5 and 300 seconds"
                }
            
            try:
                proc = psutil.Process(pid)
            except psutil.NoSuchProcess:
                return {
                    "success": False,
                    "error": f"Process with PID {pid} not found"
                }
            
            # Informazioni iniziali
            initial_info = {
                "name": proc.name(),
                "status": proc.status(),
                "create_time": proc.create_time(),
                "cmdline": ' '.join(proc.cmdline()[:5])  # Primi 5 argomenti
            }
            
            # Campionamento
            samples = []
            sample_interval = max(1, duration // 10)  # Massimo 10 campioni
            
            for i in range(0, duration, sample_interval):
                try:
                    if not proc.is_running():
                        break
                    
                    sample = {
                        "timestamp": time.time(),
                        "cpu_percent": proc.cpu_percent(),
                        "memory_percent": proc.memory_percent(),
                        "memory_rss": proc.memory_info().rss,
                        "memory_vms": proc.memory_info().vms,
                        "num_threads": proc.num_threads(),
                        "status": proc.status()
                    }
                    samples.append(sample)
                    
                    if i < duration - sample_interval:
                        time.sleep(sample_interval)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
            
            if not samples:
                return {
                    "success": False,
                    "error": "Could not collect any samples"
                }
            
            # Calcola statistiche
            cpu_values = [s['cpu_percent'] for s in samples if s['cpu_percent'] is not None]
            memory_values = [s['memory_percent'] for s in samples if s['memory_percent'] is not None]
            
            stats = {
                "avg_cpu": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0,
                "max_cpu": round(max(cpu_values), 2) if cpu_values else 0,
                "avg_memory": round(sum(memory_values) / len(memory_values), 2) if memory_values else 0,
                "max_memory": round(max(memory_values), 2) if memory_values else 0,
                "avg_threads": round(sum(s['num_threads'] for s in samples) / len(samples), 1)
            }
            
            return {
                "success": True,
                "pid": pid,
                "duration": duration,
                "process_info": initial_info,
                "samples_collected": len(samples),
                "statistics": stats,
                "samples": samples[-5:]  # Ultimi 5 campioni per dettaglio
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def execute_with_limits(command: str, timeout: int = 30, memory_limit_mb: int = 100) -> Dict[str, Any]:
        """
        Esegue un comando con limiti di risorse per sicurezza.
        
        Args:
            command: Comando da eseguire
            timeout: Timeout in secondi (5-300)
            memory_limit_mb: Limite memoria in MB (10-1000)
        """
        try:
            if timeout < 5 or timeout > 300:
                return {
                    "success": False,
                    "error": "Timeout must be between 5 and 300 seconds"
                }
            
            if memory_limit_mb < 10 or memory_limit_mb > 1000:
                return {
                    "success": False,
                    "error": "Memory limit must be between 10 and 1000 MB"
                }
            
            # Comandi vietati per sicurezza
            dangerous_commands = [
                'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs',
                'dd', 'shred', 'sudo', 'su', 'chmod', 'chown',
                'passwd', 'useradd', 'userdel', 'mount', 'umount'
            ]
            
            command_parts = command.lower().split()
            if any(dangerous in command_parts for dangerous in dangerous_commands):
                return {
                    "success": False,
                    "error": "Command contains potentially dangerous operations"
                }
            
            # Funzione per impostare limiti nel processo figlio
            def set_limits():
                # Limite memoria (soft, hard)
                memory_bytes = memory_limit_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
                
                # Limite CPU (30 secondi)
                resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
                
                # Limite file aperti
                resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
            
            start_time = time.time()
            
            try:
                # Esegui comando con limiti
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    preexec_fn=set_limits if os.name != 'nt' else None  # Linux/Unix only
                )
                
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": round(execution_time, 3),
                    "limits": {
                        "timeout": timeout,
                        "memory_limit_mb": memory_limit_mb
                    }
                }
            
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "timeout": True
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_system_resources() -> Dict[str, Any]:
        """
        Analizza l'utilizzo delle risorse di sistema.
        """
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memoria
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disco
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Rete
            net_io = psutil.net_io_counters()
            
            # Processi
            process_count = len(psutil.pids())
            
            # Load average (Linux/Unix)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except:
                pass
            
            # Analisi dello stato
            analysis = []
            
            # CPU Analysis
            if cpu_percent > 80:
                analysis.append("High CPU usage detected")
            elif cpu_percent < 20:
                analysis.append("Low CPU usage - system idle")
            
            # Memory Analysis
            memory_percent = memory.percent
            if memory_percent > 90:
                analysis.append("Critical memory usage")
            elif memory_percent > 70:
                analysis.append("High memory usage")
            
            # Disk Analysis
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            if disk_percent > 90:
                analysis.append("Disk space critically low")
            elif disk_percent > 80:
                analysis.append("Disk space running low")
            
            return {
                "success": True,
                "timestamp": time.time(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent": memory_percent
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "percent": swap.percent
                },
                "disk": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "percent": round(disk_percent, 1)
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                } if net_io else None,
                "processes": {
                    "count": process_count
                },
                "load_average": load_avg,
                "analysis": analysis,
                "system_health": "Critical" if any("critical" in a.lower() for a in analysis) else
                                "Warning" if any("high" in a.lower() for a in analysis) else
                                "Good"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def kill_process_safe(pid: int, force: bool = False) -> Dict[str, Any]:
        """
        Termina un processo in modo sicuro con controlli.
        
        Args:
            pid: ID del processo da terminare
            force: Se usare SIGKILL invece di SIGTERM
        """
        try:
            try:
                proc = psutil.Process(pid)
            except psutil.NoSuchProcess:
                return {
                    "success": False,
                    "error": f"Process with PID {pid} not found"
                }
            
            # Informazioni processo prima della terminazione
            proc_info = {
                "pid": pid,
                "name": proc.name(),
                "status": proc.status(),
                "cmdline": ' '.join(proc.cmdline()[:3])
            }
            
            # Controlli di sicurezza
            critical_processes = [
                'init', 'kernel', 'systemd', 'kthreadd', 'ksoftirqd',
                'migration', 'watchdog', 'sshd', 'NetworkManager'
            ]
            
            if any(critical in proc.name().lower() for critical in critical_processes):
                return {
                    "success": False,
                    "error": f"Cannot terminate critical system process: {proc.name()}"
                }
            
            # Controlla se è un processo del sistema
            try:
                if proc.username() in ['root', 'system'] and proc.pid < 1000:
                    return {
                        "success": False,
                        "error": "Cannot terminate system process with low PID"
                    }
            except psutil.AccessDenied:
                pass
            
            # Termina il processo
            try:
                if force:
                    proc.kill()  # SIGKILL
                    method = "SIGKILL"
                else:
                    proc.terminate()  # SIGTERM
                    method = "SIGTERM"
                
                # Aspetta un po' per vedere se il processo è terminato
                try:
                    proc.wait(timeout=5)
                    terminated = True
                except psutil.TimeoutExpired:
                    terminated = False
                
                return {
                    "success": True,
                    "process_info": proc_info,
                    "method": method,
                    "terminated": terminated,
                    "message": f"Process {pid} terminated successfully" if terminated else f"Termination signal sent to process {pid}"
                }
                
            except psutil.AccessDenied:
                return {
                    "success": False,
                    "error": "Access denied - insufficient permissions"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def create_sandbox_environment() -> Dict[str, Any]:
        """
        Crea un ambiente sandbox temporaneo per l'esecuzione sicura.
        """
        try:
            # Crea directory temporanea
            sandbox_dir = tempfile.mkdtemp(prefix="nexus_sandbox_")
            
            # Crea sottodirectory standard
            subdirs = ['bin', 'tmp', 'work', 'output']
            created_dirs = []
            
            for subdir in subdirs:
                full_path = os.path.join(sandbox_dir, subdir)
                os.makedirs(full_path, exist_ok=True)
                created_dirs.append(full_path)
            
            # Crea un file di configurazione sandbox
            config = {
                "created_at": time.time(),
                "sandbox_id": os.path.basename(sandbox_dir),
                "allowed_commands": ["echo", "cat", "ls", "pwd", "wc", "grep", "sort", "head", "tail"],
                "max_execution_time": 30,
                "max_memory_mb": 50,
                "max_file_size_mb": 10
            }
            
            config_file = os.path.join(sandbox_dir, "sandbox_config.json")
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Crea script di cleanup
            cleanup_script = f"""#!/bin/bash
# Cleanup script for sandbox {config['sandbox_id']}
rm -rf {sandbox_dir}
echo "Sandbox {config['sandbox_id']} cleaned up"
"""
            
            cleanup_file = os.path.join(sandbox_dir, "cleanup.sh")
            with open(cleanup_file, 'w') as f:
                f.write(cleanup_script)
            os.chmod(cleanup_file, 0o755)
            
            return {
                "success": True,
                "sandbox_id": config['sandbox_id'],
                "sandbox_path": sandbox_dir,
                "config": config,
                "created_directories": created_dirs,
                "cleanup_script": cleanup_file,
                "usage_instructions": [
                    f"Use sandbox directory: {sandbox_dir}",
                    "Only approved commands are allowed",
                    f"Max execution time: {config['max_execution_time']} seconds",
                    f"Max memory: {config['max_memory_mb']} MB",
                    f"Run cleanup script when done: {cleanup_file}"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_process_tree(root_pid: Optional[int] = None) -> Dict[str, Any]:
        """
        Analizza l'albero dei processi e le relazioni parent-child.
        
        Args:
            root_pid: PID radice da analizzare (None per tutti i processi)
        """
        try:
            process_tree = {}
            orphaned_processes = []
            
            # Raccoglie tutti i processi
            all_processes = {}
            for proc in psutil.process_iter(['pid', 'ppid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time', 'cmdline']):
                try:
                    pinfo = proc.info
                    pinfo['children'] = []
                    pinfo['depth'] = 0
                    pinfo['cmdline_short'] = ' '.join(pinfo.get('cmdline', [])[:3])
                    all_processes[pinfo['pid']] = pinfo
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Costruisce l'albero
            for pid, pinfo in all_processes.items():
                ppid = pinfo.get('ppid')
                if ppid and ppid in all_processes:
                    all_processes[ppid]['children'].append(pid)
                elif ppid and ppid not in all_processes:
                    orphaned_processes.append(pid)
            
            # Calcola la profondità ricorsivamente
            def calculate_depth(pid, depth=0):
                if pid in all_processes:
                    all_processes[pid]['depth'] = depth
                    for child_pid in all_processes[pid]['children']:
                        calculate_depth(child_pid, depth + 1)
            
            # Se root_pid specificato, analizza solo quel sottoalbero
            if root_pid:
                if root_pid not in all_processes:
                    return {
                        "success": False,
                        "error": f"Process {root_pid} not found"
                    }
                calculate_depth(root_pid, 0)
                # Filtra solo i processi nel sottoalbero
                relevant_pids = set()
                
                def collect_subtree(pid):
                    relevant_pids.add(pid)
                    if pid in all_processes:
                        for child in all_processes[pid]['children']:
                            collect_subtree(child)
                
                collect_subtree(root_pid)
                filtered_processes = {pid: pinfo for pid, pinfo in all_processes.items() if pid in relevant_pids}
                process_tree = filtered_processes
            else:
                # Analizza tutto l'albero
                root_processes = [pid for pid, pinfo in all_processes.items() if not pinfo.get('ppid') or pinfo.get('ppid') not in all_processes]
                for root_pid in root_processes:
                    calculate_depth(root_pid, 0)
                process_tree = all_processes
            
            # Statistiche dell'albero
            max_depth = max((pinfo['depth'] for pinfo in process_tree.values()), default=0)
            total_processes = len(process_tree)
            
            # Processi per livello
            processes_by_level = {}
            for pid, pinfo in process_tree.items():
                level = pinfo['depth']
                if level not in processes_by_level:
                    processes_by_level[level] = []
                processes_by_level[level].append(pid)
            
            # Top parent processes (con più figli)
            parent_stats = []
            for pid, pinfo in process_tree.items():
                if pinfo['children']:
                    total_descendants = count_descendants(pid, process_tree)
                    parent_stats.append({
                        "pid": pid,
                        "name": pinfo['name'],
                        "direct_children": len(pinfo['children']),
                        "total_descendants": total_descendants,
                        "cpu_percent": pinfo.get('cpu_percent', 0),
                        "memory_percent": pinfo.get('memory_percent', 0)
                    })
            
            parent_stats.sort(key=lambda x: x['total_descendants'], reverse=True)
            
            return {
                "success": True,
                "analysis_timestamp": datetime.now().isoformat(),
                "root_pid": root_pid,
                "tree_statistics": {
                    "total_processes": total_processes,
                    "max_depth": max_depth,
                    "orphaned_processes": len(orphaned_processes),
                    "processes_by_level": {str(k): len(v) for k, v in processes_by_level.items()}
                },
                "top_parent_processes": parent_stats[:10],
                "orphaned_processes": orphaned_processes[:20],
                "process_tree": process_tree if total_processes <= 100 else "Tree too large - use specific root_pid"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing process tree: {str(e)}"
            }

    @mcp.tool()
    def manage_system_services(action: str, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Gestisce i servizi di sistema (lista, stato, controllo).
        
        Args:
            action: Azione da eseguire (list, status, start, stop, restart, enable, disable)
            service_name: Nome del servizio (richiesto per azioni specifiche)
        """
        try:
            if action not in ['list', 'status', 'start', 'stop', 'restart', 'enable', 'disable']:
                return {
                    "success": False,
                    "error": "Invalid action. Use: list, status, start, stop, restart, enable, disable"
                }
            
            if action != 'list' and not service_name:
                return {
                    "success": False,
                    "error": "service_name required for this action"
                }
            
            # Rileva il sistema di init
            init_system = detect_init_system()
            
            if action == 'list':
                return list_system_services(init_system)
            elif action == 'status':
                return get_service_status(service_name, init_system)
            else:
                # Azioni che modificano i servizi - extra sicurezza
                dangerous_services = [
                    'ssh', 'sshd', 'network', 'networking', 'systemd-networkd',
                    'init', 'kernel', 'systemd', 'dbus'
                ]
                
                if any(dangerous in service_name.lower() for dangerous in dangerous_services):
                    return {
                        "success": False,
                        "error": f"Cannot modify critical system service: {service_name}"
                    }
                
                return control_service(service_name, action, init_system)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error managing services: {str(e)}"
            }

    @mcp.tool()
    def monitor_resource_usage(duration_seconds: int = 60, interval_seconds: int = 5) -> Dict[str, Any]:
        """
        Monitora l'utilizzo delle risorse nel tempo con dettagli sui processi.
        
        Args:
            duration_seconds: Durata del monitoraggio (10-600 secondi)
            interval_seconds: Intervallo tra campionamenti (1-30 secondi)
        """
        try:
            duration_seconds = max(10, min(duration_seconds, 600))
            interval_seconds = max(1, min(interval_seconds, 30))
            
            samples = []
            process_history = {}
            start_time = time.time()
            
            # Raccogli campioni
            for i in range(0, duration_seconds, interval_seconds):
                sample_time = time.time()
                
                # Sistema generale
                system_sample = {
                    "timestamp": sample_time,
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory": psutil.virtual_memory()._asdict(),
                    "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                    "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
                }
                
                # Top 5 processi per CPU e memoria
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        pinfo = proc.info
                        if pinfo['cpu_percent'] is not None and pinfo['memory_percent'] is not None:
                            processes.append(pinfo)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Top processi
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                top_cpu = processes[:5]
                
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
                top_memory = processes[:5]
                
                system_sample["top_cpu_processes"] = top_cpu
                system_sample["top_memory_processes"] = top_memory
                
                samples.append(system_sample)
                
                # Storia processi specifici
                for proc_info in top_cpu + top_memory:
                    pid = proc_info['pid']
                    if pid not in process_history:
                        process_history[pid] = {
                            "name": proc_info['name'],
                            "samples": []
                        }
                    
                    process_history[pid]["samples"].append({
                        "timestamp": sample_time,
                        "cpu_percent": proc_info['cpu_percent'],
                        "memory_percent": proc_info['memory_percent']
                    })
                
                if i < duration_seconds - interval_seconds:
                    time.sleep(interval_seconds)
            
            # Analisi dei dati raccolti
            cpu_values = [s['cpu_percent'] for s in samples]
            memory_values = [s['memory']['percent'] for s in samples]
            
            # Rileva picchi e anomalie
            cpu_avg = sum(cpu_values) / len(cpu_values)
            cpu_spikes = [s for s in samples if s['cpu_percent'] > cpu_avg * 1.5]
            
            memory_avg = sum(memory_values) / len(memory_values)
            memory_spikes = [s for s in samples if s['memory']['percent'] > memory_avg * 1.2]
            
            # Processi più attivi
            most_active_processes = []
            for pid, history in process_history.items():
                if len(history['samples']) >= 3:
                    cpu_samples = [s['cpu_percent'] for s in history['samples']]
                    avg_cpu = sum(cpu_samples) / len(cpu_samples)
                    max_cpu = max(cpu_samples)
                    
                    most_active_processes.append({
                        "pid": pid,
                        "name": history['name'],
                        "avg_cpu": round(avg_cpu, 2),
                        "max_cpu": round(max_cpu, 2),
                        "samples_count": len(history['samples'])
                    })
            
            most_active_processes.sort(key=lambda x: x['avg_cpu'], reverse=True)
            
            return {
                "success": True,
                "monitoring_config": {
                    "duration_seconds": duration_seconds,
                    "interval_seconds": interval_seconds,
                    "samples_collected": len(samples)
                },
                "system_statistics": {
                    "cpu": {
                        "average": round(cpu_avg, 2),
                        "min": round(min(cpu_values), 2),
                        "max": round(max(cpu_values), 2),
                        "spikes_detected": len(cpu_spikes)
                    },
                    "memory": {
                        "average_percent": round(memory_avg, 2),
                        "min_percent": round(min(memory_values), 2),
                        "max_percent": round(max(memory_values), 2),
                        "spikes_detected": len(memory_spikes)
                    }
                },
                "most_active_processes": most_active_processes[:10],
                "anomalies": {
                    "cpu_spikes": len(cpu_spikes),
                    "memory_spikes": len(memory_spikes),
                    "spike_timestamps": [s['timestamp'] for s in cpu_spikes + memory_spikes]
                },
                "samples": samples[-10:],  # Ultimi 10 campioni
                "process_history": {k: v for k, v in list(process_history.items())[:5]}  # Top 5 processi con storia
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error monitoring resources: {str(e)}"
            }

    @mcp.tool()
    def batch_process_operations(operations: str) -> Dict[str, Any]:
        """
        Esegue operazioni batch sui processi (JSON con lista operazioni).
        
        Args:
            operations: JSON string con array di operazioni {action, target, params}
        """
        try:
            # Parse operazioni
            try:
                ops_list = json.loads(operations)
                if not isinstance(ops_list, list):
                    return {
                        "success": False,
                        "error": "Operations must be a JSON array"
                    }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON: {str(e)}"
                }
            
            if len(ops_list) > 20:
                return {
                    "success": False,
                    "error": "Maximum 20 operations per batch"
                }
            
            results = []
            successful_ops = 0
            failed_ops = 0
            
            for i, operation in enumerate(ops_list):
                if not isinstance(operation, dict):
                    results.append({
                        "operation_index": i,
                        "success": False,
                        "error": "Operation must be an object"
                    })
                    failed_ops += 1
                    continue
                
                action = operation.get('action')
                target = operation.get('target')
                params = operation.get('params', {})
                
                # Validazione operazione
                valid_actions = ['list', 'monitor', 'info', 'children', 'terminate']
                if action not in valid_actions:
                    results.append({
                        "operation_index": i,
                        "action": action,
                        "success": False,
                        "error": f"Invalid action. Use: {', '.join(valid_actions)}"
                    })
                    failed_ops += 1
                    continue
                
                # Esegui operazione
                try:
                    op_result = execute_batch_operation(action, target, params)
                    op_result["operation_index"] = i
                    op_result["action"] = action
                    op_result["target"] = target
                    
                    if op_result.get("success", False):
                        successful_ops += 1
                    else:
                        failed_ops += 1
                    
                    results.append(op_result)
                    
                except Exception as e:
                    results.append({
                        "operation_index": i,
                        "action": action,
                        "target": target,
                        "success": False,
                        "error": f"Operation failed: {str(e)}"
                    })
                    failed_ops += 1
            
            return {
                "success": True,
                "batch_summary": {
                    "total_operations": len(ops_list),
                    "successful": successful_ops,
                    "failed": failed_ops,
                    "success_rate": round((successful_ops / len(ops_list)) * 100, 1) if ops_list else 0
                },
                "results": results,
                "execution_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Batch operation error: {str(e)}"
            }

    @mcp.tool()
    def analyze_process_security(pid: Optional[int] = None) -> Dict[str, Any]:
        """
        Analizza gli aspetti di sicurezza dei processi.
        
        Args:
            pid: PID specifico da analizzare (None per analisi generale)
        """
        try:
            security_report = {
                "analysis_timestamp": datetime.now().isoformat(),
                "scan_type": "specific" if pid else "system-wide"
            }
            
            if pid:
                # Analisi processo specifico
                try:
                    proc = psutil.Process(pid)
                    security_report["process_security"] = analyze_single_process_security(proc)
                except psutil.NoSuchProcess:
                    return {
                        "success": False,
                        "error": f"Process {pid} not found"
                    }
            else:
                # Analisi sistema generale
                suspicious_processes = []
                privileged_processes = []
                network_processes = []
                high_resource_processes = []
                
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'connections']):
                    try:
                        pinfo = proc.info
                        
                        # Processi privilegiati
                        if pinfo.get('username') in ['root', 'SYSTEM', 'Administrator']:
                            privileged_processes.append({
                                "pid": pinfo['pid'],
                                "name": pinfo['name'],
                                "username": pinfo['username']
                            })
                        
                        # Processi con connessioni di rete
                        if pinfo.get('connections'):
                            network_processes.append({
                                "pid": pinfo['pid'],
                                "name": pinfo['name'],
                                "connections_count": len(pinfo['connections'])
                            })
                        
                        # Processi ad alto consumo risorse
                        cpu_percent = pinfo.get('cpu_percent', 0) or 0
                        memory_percent = pinfo.get('memory_percent', 0) or 0
                        
                        if cpu_percent > 50 or memory_percent > 20:
                            high_resource_processes.append({
                                "pid": pinfo['pid'],
                                "name": pinfo['name'],
                                "cpu_percent": cpu_percent,
                                "memory_percent": memory_percent
                            })
                        
                        # Processi sospetti (nomi insoliti, posizioni anomale)
                        if is_suspicious_process(proc):
                            suspicious_processes.append({
                                "pid": pinfo['pid'],
                                "name": pinfo['name'],
                                "reason": get_suspicious_reason(proc)
                            })
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                security_report["system_security"] = {
                    "privileged_processes": len(privileged_processes),
                    "network_processes": len(network_processes),
                    "high_resource_processes": len(high_resource_processes),
                    "suspicious_processes": len(suspicious_processes),
                    "details": {
                        "privileged": privileged_processes[:10],
                        "network": network_processes[:10],
                        "high_resource": high_resource_processes[:10],
                        "suspicious": suspicious_processes
                    }
                }
                
                # Raccomandazioni di sicurezza
                recommendations = []
                if len(suspicious_processes) > 0:
                    recommendations.append(f"Investigate {len(suspicious_processes)} suspicious processes")
                if len(privileged_processes) > 20:
                    recommendations.append("High number of privileged processes - review necessity")
                if len(network_processes) > 50:
                    recommendations.append("Many processes with network connections - audit network activity")
                
                security_report["security_recommendations"] = recommendations
            
            return {
                "success": True,
                **security_report
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Security analysis error: {str(e)}"
            }

# Helper functions

def count_descendants(pid: int, process_tree: Dict) -> int:
    """Conta ricorsivamente tutti i discendenti di un processo."""
    if pid not in process_tree:
        return 0
    
    count = len(process_tree[pid]['children'])
    for child_pid in process_tree[pid]['children']:
        count += count_descendants(child_pid, process_tree)
    
    return count

def detect_init_system() -> str:
    """Rileva il sistema di init utilizzato."""
    if os.path.exists('/run/systemd/system'):
        return 'systemd'
    elif os.path.exists('/sbin/initctl'):
        return 'upstart'
    elif os.path.exists('/etc/init.d'):
        return 'sysv'
    else:
        return 'unknown'

def list_system_services(init_system: str) -> Dict[str, Any]:
    """Lista i servizi di sistema."""
    try:
        services = []
        
        if init_system == 'systemd':
            result = subprocess.run(['systemctl', 'list-units', '--type=service', '--no-pager'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if '.service' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            services.append({
                                "name": parts[0].replace('.service', ''),
                                "status": parts[2],
                                "active": parts[1] == 'active'
                            })
        
        return {
            "success": True,
            "init_system": init_system,
            "services_count": len(services),
            "services": services[:50]  # Limit output
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list services: {str(e)}"
        }

def get_service_status(service_name: str, init_system: str) -> Dict[str, Any]:
    """Ottiene lo stato di un servizio specifico."""
    try:
        if init_system == 'systemd':
            result = subprocess.run(['systemctl', 'status', service_name], 
                                  capture_output=True, text=True, timeout=5)
            
            return {
                "success": True,
                "service_name": service_name,
                "status_output": result.stdout,
                "active": result.returncode == 0,
                "return_code": result.returncode
            }
        else:
            return {
                "success": False,
                "error": f"Service management not supported for {init_system}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get service status: {str(e)}"
        }

def control_service(service_name: str, action: str, init_system: str) -> Dict[str, Any]:
    """Controlla un servizio (start/stop/restart/enable/disable)."""
    try:
        if init_system != 'systemd':
            return {
                "success": False,
                "error": f"Service control not supported for {init_system}"
            }
        
        # Solo operazioni di lettura o controllo non distruttivo
        safe_actions = ['status', 'is-active', 'is-enabled']
        
        if action not in safe_actions:
            return {
                "success": False,
                "error": f"Action '{action}' not allowed for security reasons"
            }
        
        result = subprocess.run(['systemctl', action, service_name], 
                              capture_output=True, text=True, timeout=10)
        
        return {
            "success": result.returncode == 0,
            "service_name": service_name,
            "action": action,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "return_code": result.returncode
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Service control failed: {str(e)}"
        }

def execute_batch_operation(action: str, target: Any, params: Dict) -> Dict[str, Any]:
    """Esegue una singola operazione batch."""
    try:
        if action == 'list':
            criteria = params.get('criteria', 'cpu')
            limit = params.get('limit', 10)
            return list_processes_by_criteria(criteria, limit)
        
        elif action == 'info':
            if not isinstance(target, int):
                return {"success": False, "error": "Target must be PID (integer)"}
            
            try:
                proc = psutil.Process(target)
                return {
                    "success": True,
                    "process_info": {
                        "pid": target,
                        "name": proc.name(),
                        "status": proc.status(),
                        "cpu_percent": proc.cpu_percent(),
                        "memory_percent": proc.memory_percent(),
                        "create_time": proc.create_time(),
                        "cmdline": ' '.join(proc.cmdline()[:5])
                    }
                }
            except psutil.NoSuchProcess:
                return {"success": False, "error": f"Process {target} not found"}
        
        elif action == 'children':
            if not isinstance(target, int):
                return {"success": False, "error": "Target must be PID (integer)"}
            
            try:
                proc = psutil.Process(target)
                children = proc.children(recursive=params.get('recursive', False))
                children_info = []
                for child in children:
                    try:
                        children_info.append({
                            "pid": child.pid,
                            "name": child.name(),
                            "status": child.status()
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return {
                    "success": True,
                    "parent_pid": target,
                    "children_count": len(children_info),
                    "children": children_info
                }
            except psutil.NoSuchProcess:
                return {"success": False, "error": f"Process {target} not found"}
        
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
            
    except Exception as e:
        return {"success": False, "error": f"Operation failed: {str(e)}"}

def analyze_single_process_security(proc: psutil.Process) -> Dict[str, Any]:
    """Analizza la sicurezza di un singolo processo."""
    try:
        security_info = {
            "pid": proc.pid,
            "name": proc.name(),
            "security_analysis": {}
        }
        
        # Controlla username/privilegi
        try:
            username = proc.username()
            security_info["security_analysis"]["username"] = username
            security_info["security_analysis"]["privileged"] = username in ['root', 'SYSTEM', 'Administrator']
        except psutil.AccessDenied:
            security_info["security_analysis"]["username"] = "Access Denied"
        
        # Controlla connessioni di rete
        try:
            connections = proc.connections()
            security_info["security_analysis"]["network_connections"] = len(connections)
            security_info["security_analysis"]["has_network_activity"] = len(connections) > 0
        except psutil.AccessDenied:
            security_info["security_analysis"]["network_connections"] = "Access Denied"
        
        # Controlla file aperti
        try:
            open_files = proc.open_files()
            security_info["security_analysis"]["open_files_count"] = len(open_files)
            
            # Cerca file in posizioni sensibili
            sensitive_paths = ['/etc', '/var/log', '/proc', '/sys']
            sensitive_files = [f for f in open_files if any(f.path.startswith(p) for p in sensitive_paths)]
            security_info["security_analysis"]["sensitive_files_accessed"] = len(sensitive_files)
        except psutil.AccessDenied:
            security_info["security_analysis"]["open_files_count"] = "Access Denied"
        
        # Analizza percorso eseguibile
        try:
            exe_path = proc.exe()
            security_info["security_analysis"]["executable_path"] = exe_path
            
            # Controlla se l'eseguibile è in posizioni standard
            standard_paths = ['/usr/bin', '/bin', '/usr/sbin', '/sbin', '/usr/local/bin']
            security_info["security_analysis"]["standard_location"] = any(exe_path.startswith(p) for p in standard_paths)
        except psutil.AccessDenied:
            security_info["security_analysis"]["executable_path"] = "Access Denied"
        
        return security_info
        
    except Exception as e:
        return {"error": f"Security analysis failed: {str(e)}"}

def is_suspicious_process(proc: psutil.Process) -> bool:
    """Determina se un processo è potenzialmente sospetto."""
    try:
        name = proc.name().lower()
        
        # Nomi sospetti comuni
        suspicious_names = [
            'nc', 'netcat', 'ncat', 'socat', 'telnet',
            'wget', 'curl', 'python', 'perl', 'ruby',
            'bash', 'sh', 'cmd', 'powershell'
        ]
        
        # Processi con nomi molto corti o casuali
        if len(name) <= 2 or name.isdigit():
            return True
        
        # Processi con nomi sospetti
        if any(suspicious in name for suspicious in suspicious_names):
            try:
                # Solo se non in posizioni standard
                exe_path = proc.exe()
                standard_paths = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
                if not any(exe_path.startswith(p) for p in standard_paths):
                    return True
            except psutil.AccessDenied:
                return True
        
        return False
        
    except Exception:
        return False

def get_suspicious_reason(proc: psutil.Process) -> str:
    """Ottiene la ragione per cui un processo è considerato sospetto."""
    try:
        name = proc.name().lower()
        
        if len(name) <= 2:
            return "Very short process name"
        if name.isdigit():
            return "Numeric process name"
        
        suspicious_names = ['nc', 'netcat', 'wget', 'curl']
        for suspicious in suspicious_names:
            if suspicious in name:
                return f"Potentially suspicious tool: {suspicious}"
        
        return "Unusual characteristics detected"
        
    except Exception:
        return "Analysis failed"