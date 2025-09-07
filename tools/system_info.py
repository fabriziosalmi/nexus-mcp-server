# -*- coding: utf-8 -*-
# tools/system_info.py
import platform
import sys
import os
import psutil
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import subprocess
import time
import uuid

def register_tools(mcp):
    """Registra i tool di informazioni sistema con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: System Information Tools")

    @mcp.tool()
    def system_overview() -> str:
        """
        Fornisce una panoramica completa del sistema.
        """
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            
            return f"""=== INFORMAZIONI SISTEMA ===
Sistema Operativo: {system}
Release: {release}
Versione: {version}
Architettura: {machine}
Processore: {processor}
Nome Host: {socket.gethostname()}
Python: {sys.version.split()[0]}
Piattaforma Python: {platform.platform()}"""
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def memory_usage() -> str:
        """
        Mostra l'utilizzo della memoria del sistema.
        """
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            def bytes_to_gb(bytes_val):
                return round(bytes_val / (1024**3), 2)
            
            result = f"""=== UTILIZZO MEMORIA ===
RAM Totale: {bytes_to_gb(memory.total)} GB
RAM Utilizzata: {bytes_to_gb(memory.used)} GB ({memory.percent}%)
RAM Disponibile: {bytes_to_gb(memory.available)} GB

SWAP Totale: {bytes_to_gb(swap.total)} GB
SWAP Utilizzato: {bytes_to_gb(swap.used)} GB ({swap.percent}%)
SWAP Libero: {bytes_to_gb(swap.free)} GB"""
            
            return result
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def cpu_info() -> str:
        """
        Mostra informazioni sulla CPU e il suo utilizzo.
        """
        try:
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            cpu_freq = psutil.cpu_freq()
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            
            result = f"""=== INFORMAZIONI CPU ===
Core Fisici: {cpu_count_physical}
Core Logici: {cpu_count_logical}"""
            
            if cpu_freq:
                result += f"\nFrequenza Corrente: {cpu_freq.current:.0f} MHz"
                result += f"\nFrequenza Minima: {cpu_freq.min:.0f} MHz"
                result += f"\nFrequenza Massima: {cpu_freq.max:.0f} MHz"
            
            result += f"\nUtilizzo Medio CPU: {sum(cpu_percent)/len(cpu_percent):.1f}%"
            result += f"\nUtilizzo per Core:"
            for i, percent in enumerate(cpu_percent, 1):
                result += f"\n  Core {i}: {percent:.1f}%"
            
            return result
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def disk_usage(path: str = "/") -> str:
        """
        Mostra l'utilizzo del disco per un percorso specificato.

        Args:
            path: Il percorso da analizzare (default: root).
        """
        try:
            # Su Windows, usa C:\ se non specificato diversamente
            if platform.system() == "Windows" and path == "/":
                path = "C:\\"
            
            if not os.path.exists(path):
                return f"ERRORE: Il percorso '{path}' non esiste"
            
            disk_usage = psutil.disk_usage(path)
            
            def bytes_to_gb(bytes_val):
                return round(bytes_val / (1024**3), 2)
            
            percent_used = (disk_usage.used / disk_usage.total) * 100
            
            result = f"""=== UTILIZZO DISCO ===
Percorso: {path}
Spazio Totale: {bytes_to_gb(disk_usage.total)} GB
Spazio Utilizzato: {bytes_to_gb(disk_usage.used)} GB ({percent_used:.1f}%)
Spazio Libero: {bytes_to_gb(disk_usage.free)} GB"""
            
            return result
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def network_info() -> str:
        """
        Mostra informazioni sulla rete e le interfacce.
        """
        try:
            hostname = socket.gethostname()
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            result = f"""=== INFORMAZIONI RETE ===
Hostname: {hostname}

Interfacce di Rete:"""
            
            for interface_name, addresses in interfaces.items():
                if interface_name in stats:
                    status = "UP" if stats[interface_name].isup else "DOWN"
                    speed = stats[interface_name].speed
                    result += f"\n\n{interface_name} ({status}"
                    if speed > 0:
                        result += f", {speed} Mbps"
                    result += "):"
                else:
                    result += f"\n\n{interface_name}:"
                
                for addr in addresses:
                    if addr.family == socket.AF_INET:
                        result += f"\n  IPv4: {addr.address}"
                        if addr.netmask:
                            result += f" (Netmask: {addr.netmask})"
                    elif addr.family == socket.AF_INET6:
                        result += f"\n  IPv6: {addr.address}"
            
            return result
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def running_processes(limit: int = 10) -> str:
        """
        Mostra i processi in esecuzione ordinati per utilizzo CPU.

        Args:
            limit: Il numero massimo di processi da mostrare (1-50).
        """
        try:
            if limit < 1 or limit > 50:
                return "ERRORE: Il limite deve essere tra 1 e 50"
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Ordina per utilizzo CPU decrescente
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            result = f"=== TOP {limit} PROCESSI (per CPU) ===\n"
            result += f"{'PID':<8} {'CPU%':<6} {'MEM%':<6} {'NOME':<30}\n"
            result += "-" * 50 + "\n"
            
            for proc in processes[:limit]:
                pid = proc['pid']
                name = (proc['name'] or 'N/A')[:29]
                cpu = f"{proc['cpu_percent'] or 0:.1f}%"
                mem = f"{proc['memory_percent'] or 0:.1f}%"
                result += f"{pid:<8} {cpu:<6} {mem:<6} {name:<30}\n"
            
            return result
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def comprehensive_system_report() -> Dict[str, Any]:
        """
        Genera un report completo del sistema con tutte le informazioni disponibili.
        """
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "report_id": str(uuid.uuid4())[:8],
                "system": {},
                "hardware": {},
                "performance": {},
                "network": {},
                "storage": {},
                "processes": {},
                "environment": {}
            }
            
            # System Information
            report["system"] = {
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": socket.gethostname(),
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "uptime_seconds": int(time.time() - psutil.boot_time()),
                "uptime_human": str(timedelta(seconds=int(time.time() - psutil.boot_time())))
            }
            
            # Hardware Information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            report["hardware"] = {
                "cpu": {
                    "physical_cores": psutil.cpu_count(logical=False),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
                    "min_frequency": psutil.cpu_freq().min if psutil.cpu_freq() else None,
                    "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percentage": memory.percent
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "free_gb": round(swap.free / (1024**3), 2),
                    "percentage": swap.percent
                }
            }
            
            # Performance Metrics
            cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
            
            report["performance"] = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "swap_usage_percent": swap.percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
                "process_count": len(psutil.pids())
            }
            
            # Network Information
            network_interfaces = {}
            for interface, addresses in psutil.net_if_addrs().items():
                interface_stats = psutil.net_if_stats().get(interface, None)
                network_interfaces[interface] = {
                    "addresses": [{"family": addr.family.name, "address": addr.address, "netmask": addr.netmask} for addr in addresses],
                    "is_up": interface_stats.isup if interface_stats else False,
                    "speed_mbps": interface_stats.speed if interface_stats else None
                }
            
            report["network"] = {
                "hostname": socket.gethostname(),
                "interfaces": network_interfaces
            }
            
            # Storage Information
            disk_partitions = psutil.disk_partitions()
            storage_info = {}
            
            for partition in disk_partitions:
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    storage_info[partition.device] = {
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total_gb": round(disk_usage.total / (1024**3), 2),
                        "used_gb": round(disk_usage.used / (1024**3), 2),
                        "free_gb": round(disk_usage.free / (1024**3), 2),
                        "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
                    }
                except PermissionError:
                    storage_info[partition.device] = {"error": "Permission denied"}
            
            report["storage"] = storage_info
            
            # Top Processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    pinfo = proc.info
                    pinfo['running_time'] = time.time() - pinfo['create_time']
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            report["processes"] = {
                "total_count": len(processes),
                "top_cpu": processes[:5]
            }
            
            # Environment
            report["environment"] = {
                "user": os.getenv('USER') or os.getenv('USERNAME'),
                "home": os.getenv('HOME') or os.getenv('USERPROFILE'),
                "shell": os.getenv('SHELL'),
                "path_entries": len(os.getenv('PATH', '').split(os.pathsep)),
                "environment_variables_count": len(os.environ)
            }
            
            return {
                "success": True,
                "report": report
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Report generation failed: {str(e)}"
            }

    @mcp.tool()
    def hardware_detection() -> Dict[str, Any]:
        """
        Rilevamento dettagliato dell'hardware del sistema.
        """
        try:
            hardware_info = {
                "detection_timestamp": datetime.now().isoformat(),
                "cpu": {},
                "memory": {},
                "storage": {},
                "sensors": {},
                "battery": {}
            }
            
            # CPU Information
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "architecture": platform.machine(),
                "processor_name": platform.processor()
            }
            
            # CPU Frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_info.update({
                    "base_frequency_mhz": cpu_freq.min,
                    "max_frequency_mhz": cpu_freq.max,
                    "current_frequency_mhz": cpu_freq.current
                })
            
            # CPU Features (Linux only)
            if platform.system() == "Linux":
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                        if 'flags' in cpuinfo:
                            flags_line = [line for line in cpuinfo.split('\n') if line.startswith('flags')][0]
                            cpu_features = flags_line.split(':')[1].strip().split()
                            cpu_info["features"] = cpu_features[:20]  # Limit output
                except:
                    pass
            
            hardware_info["cpu"] = cpu_info
            
            # Memory Information  
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            hardware_info["memory"] = {
                "ram": {
                    "total_bytes": memory.total,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_bytes": memory.available,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": memory.percent
                },
                "swap": {
                    "total_bytes": swap.total,
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_bytes": swap.used,
                    "used_gb": round(swap.used / (1024**3), 2),
                    "usage_percent": swap.percent
                }
            }
            
            # Storage Information
            disk_info = {}
            
            # Disk partitions
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.device] = {
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total_bytes": usage.total,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "free_bytes": usage.free,
                        "free_gb": round(usage.free / (1024**3), 2),
                        "usage_percent": round((usage.used / usage.total) * 100, 1)
                    }
                except PermissionError:
                    disk_info[partition.device] = {"error": "Permission denied"}
            
            # Disk I/O
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    disk_info["io_stats"] = {
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count,
                        "read_bytes": disk_io.read_bytes,
                        "write_bytes": disk_io.write_bytes,
                        "read_time": disk_io.read_time,
                        "write_time": disk_io.write_time
                    }
            except:
                pass
            
            hardware_info["storage"] = disk_info
            
            # Sensors (if available)
            sensors_info = {}
            try:
                # Temperature sensors
                temps = psutil.sensors_temperatures()
                if temps:
                    temp_summary = {}
                    for name, entries in temps.items():
                        temp_values = [entry.current for entry in entries if entry.current]
                        if temp_values:
                            temp_summary[name] = {
                                "current_avg": round(sum(temp_values) / len(temp_values), 1),
                                "current_max": round(max(temp_values), 1),
                                "sensor_count": len(temp_values)
                            }
                    sensors_info["temperatures"] = temp_summary
                
                # Fan sensors
                fans = psutil.sensors_fans()
                if fans:
                    fan_summary = {}
                    for name, entries in fans.items():
                        fan_speeds = [entry.current for entry in entries if entry.current]
                        if fan_speeds:
                            fan_summary[name] = {
                                "rpm_avg": round(sum(fan_speeds) / len(fan_speeds), 0),
                                "rpm_max": round(max(fan_speeds), 0),
                                "fan_count": len(fan_speeds)
                            }
                    sensors_info["fans"] = fan_summary
                    
            except:
                sensors_info["error"] = "Sensor data not available"
            
            hardware_info["sensors"] = sensors_info
            
            # Battery Information
            try:
                battery = psutil.sensors_battery()
                if battery:
                    hardware_info["battery"] = {
                        "present": True,
                        "percentage": battery.percent,
                        "power_plugged": battery.power_plugged,
                        "time_left_seconds": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
                else:
                    hardware_info["battery"] = {"present": False}
            except:
                hardware_info["battery"] = {"present": False, "error": "Battery info not available"}
            
            return {
                "success": True,
                "hardware": hardware_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Hardware detection failed: {str(e)}"
            }

    @mcp.tool()
    def environment_analysis() -> Dict[str, Any]:
        """
        Analisi completa dell'ambiente di sistema e variabili.
        """
        try:
            env_analysis = {
                "analysis_timestamp": datetime.now().isoformat(),
                "user_environment": {},
                "system_paths": {},
                "environment_variables": {},
                "development_tools": {},
                "security_context": {}
            }
            
            # User Environment
            env_analysis["user_environment"] = {
                "current_user": os.getenv('USER') or os.getenv('USERNAME'),
                "home_directory": os.getenv('HOME') or os.getenv('USERPROFILE'),
                "shell": os.getenv('SHELL'),
                "terminal": os.getenv('TERM'),
                "language": os.getenv('LANG'),
                "timezone": os.getenv('TZ'),
                "current_working_directory": os.getcwd()
            }
            
            # System Paths
            path_env = os.getenv('PATH', '')
            path_entries = path_env.split(os.pathsep) if path_env else []
            
            env_analysis["system_paths"] = {
                "path_entries_count": len(path_entries),
                "path_entries": path_entries[:20],  # Limit output
                "python_path": sys.path[:10],  # Limit output
                "library_path": os.getenv('LD_LIBRARY_PATH', '').split(':') if os.getenv('LD_LIBRARY_PATH') else []
            }
            
            # Environment Variables Analysis
            env_vars = dict(os.environ)
            sensitive_patterns = ['key', 'secret', 'password', 'token', 'api']
            
            sensitive_vars = []
            development_vars = []
            system_vars = []
            
            for var_name, var_value in env_vars.items():
                var_lower = var_name.lower()
                
                if any(pattern in var_lower for pattern in sensitive_patterns):
                    sensitive_vars.append(var_name)
                elif var_lower.startswith(('dev', 'debug', 'test')):
                    development_vars.append(var_name)
                elif var_lower.startswith(('system', 'os', 'proc')):
                    system_vars.append(var_name)
            
            env_analysis["environment_variables"] = {
                "total_count": len(env_vars),
                "sensitive_variables": sensitive_vars,
                "development_variables": development_vars,
                "system_variables": system_vars,
                "common_variables": {
                    "PATH": bool(os.getenv('PATH')),
                    "HOME": bool(os.getenv('HOME') or os.getenv('USERPROFILE')),
                    "PYTHONPATH": bool(os.getenv('PYTHONPATH')),
                    "EDITOR": os.getenv('EDITOR'),
                    "BROWSER": os.getenv('BROWSER')
                }
            }
            
            # Development Tools Detection
            dev_tools = {}
            
            # Check for common development tools in PATH
            tools_to_check = [
                'python', 'python3', 'pip', 'git', 'node', 'npm', 'yarn',
                'docker', 'kubectl', 'java', 'javac', 'gcc', 'make', 'cmake'
            ]
            
            for tool in tools_to_check:
                try:
                    result = subprocess.run(['which', tool] if platform.system() != 'Windows' else ['where', tool], 
                                          capture_output=True, text=True, timeout=2)
                    dev_tools[tool] = {
                        "available": result.returncode == 0,
                        "path": result.stdout.strip() if result.returncode == 0 else None
                    }
                except:
                    dev_tools[tool] = {"available": False}
            
            # Check Python packages
            try:
                import pkg_resources
                installed_packages = [str(d).split()[0] for d in pkg_resources.working_set]
                dev_tools["python_packages_count"] = len(installed_packages)
                dev_tools["common_packages"] = {
                    pkg: pkg in installed_packages 
                    for pkg in ['requests', 'numpy', 'pandas', 'flask', 'django', 'pytest']
                }
            except:
                dev_tools["python_packages"] = "Unable to detect"
            
            env_analysis["development_tools"] = dev_tools
            
            # Security Context
            security_info = {
                "effective_user_id": os.getuid() if hasattr(os, 'getuid') else None,
                "effective_group_id": os.getgid() if hasattr(os, 'getgid') else None,
                "is_root": os.getuid() == 0 if hasattr(os, 'getuid') else False,
                "umask": oct(os.umask(os.umask(0))) if hasattr(os, 'umask') else None,
                "process_id": os.getpid(),
                "parent_process_id": os.getppid() if hasattr(os, 'getppid') else None
            }
            
            # Check for security-related environment variables
            security_vars = [var for var in env_vars.keys() 
                           if any(sec in var.lower() for sec in ['sudo', 'priv', 'admin', 'root'])]
            security_info["security_related_vars"] = security_vars
            
            env_analysis["security_context"] = security_info
            
            return {
                "success": True,
                "environment": env_analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Environment analysis failed: {str(e)}"
            }

    @mcp.tool()
    def performance_monitoring(duration_seconds: int = 10) -> Dict[str, Any]:
        """
        Monitora le performance del sistema per un periodo specificato.
        
        Args:
            duration_seconds: Durata del monitoraggio in secondi (5-60)
        """
        try:
            duration_seconds = max(5, min(duration_seconds, 60))
            
            monitoring_result = {
                "monitoring_start": datetime.now().isoformat(),
                "duration_seconds": duration_seconds,
                "samples": [],
                "summary": {}
            }
            
            samples = []
            sample_interval = max(1, duration_seconds // 10)  # Max 10 samples
            
            for i in range(0, duration_seconds, sample_interval):
                sample_time = datetime.now()
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.5)
                
                # Memory usage
                memory = psutil.virtual_memory()
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                
                # Network I/O
                network_io = psutil.net_io_counters()
                
                # Process count
                process_count = len(psutil.pids())
                
                sample = {
                    "timestamp": sample_time.isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "process_count": process_count,
                    "disk_io": {
                        "read_bytes": disk_io.read_bytes if disk_io else 0,
                        "write_bytes": disk_io.write_bytes if disk_io else 0
                    } if disk_io else None,
                    "network_io": {
                        "bytes_sent": network_io.bytes_sent if network_io else 0,
                        "bytes_recv": network_io.bytes_recv if network_io else 0
                    } if network_io else None
                }
                
                samples.append(sample)
                
                if i < duration_seconds - sample_interval:
                    time.sleep(sample_interval)
            
            monitoring_result["samples"] = samples
            
            # Calculate summary statistics
            if samples:
                cpu_values = [s["cpu_percent"] for s in samples]
                memory_values = [s["memory_percent"] for s in samples]
                
                monitoring_result["summary"] = {
                    "cpu_usage": {
                        "average": round(sum(cpu_values) / len(cpu_values), 2),
                        "minimum": min(cpu_values),
                        "maximum": max(cpu_values),
                        "samples_count": len(cpu_values)
                    },
                    "memory_usage": {
                        "average": round(sum(memory_values) / len(memory_values), 2),
                        "minimum": min(memory_values),
                        "maximum": max(memory_values)
                    },
                    "process_count": {
                        "average": round(sum(s["process_count"] for s in samples) / len(samples), 0),
                        "minimum": min(s["process_count"] for s in samples),
                        "maximum": max(s["process_count"] for s in samples)
                    }
                }
                
                # Performance assessment
                avg_cpu = monitoring_result["summary"]["cpu_usage"]["average"]
                avg_memory = monitoring_result["summary"]["memory_usage"]["average"]
                
                performance_level = "Good"
                if avg_cpu > 80 or avg_memory > 90:
                    performance_level = "Poor"
                elif avg_cpu > 60 or avg_memory > 75:
                    performance_level = "Fair"
                
                monitoring_result["summary"]["performance_assessment"] = performance_level
            
            monitoring_result["monitoring_end"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "monitoring": monitoring_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Performance monitoring failed: {str(e)}"
            }

    @mcp.tool()
    def system_services_status() -> Dict[str, Any]:
        """
        Controlla lo stato dei servizi di sistema (quando possibile).
        """
        try:
            services_info = {
                "check_timestamp": datetime.now().isoformat(),
                "system_type": platform.system(),
                "services": {},
                "service_manager": None
            }
            
            system = platform.system()
            
            if system == "Linux":
                # Check for systemd
                try:
                    result = subprocess.run(['systemctl', '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        services_info["service_manager"] = "systemd"
                        
                        # Get list of services
                        result = subprocess.run(['systemctl', 'list-units', '--type=service', '--no-pager'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')[1:]  # Skip header
                            service_count = 0
                            active_count = 0
                            failed_count = 0
                            
                            for line in lines:
                                if '.service' in line:
                                    service_count += 1
                                    if 'active' in line:
                                        active_count += 1
                                    elif 'failed' in line:
                                        failed_count += 1
                            
                            services_info["services"] = {
                                "total_services": service_count,
                                "active_services": active_count,
                                "failed_services": failed_count,
                                "inactive_services": service_count - active_count - failed_count
                            }
                except:
                    services_info["service_manager"] = "unknown"
                    
            elif system == "Darwin":  # macOS
                services_info["service_manager"] = "launchd"
                try:
                    # Check launchctl
                    result = subprocess.run(['launchctl', 'list'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')[1:]  # Skip header
                        services_info["services"] = {
                            "total_services": len(lines),
                            "note": "Service details require elevated permissions"
                        }
                except:
                    pass
                    
            elif system == "Windows":
                services_info["service_manager"] = "Windows Service Manager"
                try:
                    # Use PowerShell to get service status
                    result = subprocess.run(['powershell', '-Command', 'Get-Service | Measure-Object'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        services_info["services"] = {
                            "note": "Service enumeration requires PowerShell access"
                        }
                except:
                    pass
            
            # General process information as fallback
            try:
                # Count processes that might be services/daemons
                daemon_processes = 0
                user_processes = 0
                
                for proc in psutil.process_iter(['pid', 'name', 'username']):
                    try:
                        if proc.info['username'] in ['root', 'SYSTEM', 'daemon']:
                            daemon_processes += 1
                        else:
                            user_processes += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                services_info["process_analysis"] = {
                    "system_processes": daemon_processes,
                    "user_processes": user_processes,
                    "total_processes": daemon_processes + user_processes
                }
                
            except Exception as e:
                services_info["process_analysis"] = {"error": str(e)}
            
            return {
                "success": True,
                "services": services_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Service status check failed: {str(e)}"
            }