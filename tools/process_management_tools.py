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