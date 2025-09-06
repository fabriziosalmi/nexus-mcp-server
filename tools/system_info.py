# -*- coding: utf-8 -*-
# tools/system_info.py
import platform
import sys
import os
import psutil
import socket
import logging
from datetime import datetime

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