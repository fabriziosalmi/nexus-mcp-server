# -*- coding: utf-8 -*-
# tools/docker_tools.py
import subprocess
import json
import re
import logging
import time
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

def register_tools(mcp):
    """Registra i tool Docker avanzati con l'istanza del server MCP."""
    logging.info("🐳 Registrazione tool-set: Docker Management Tools")

    @mcp.tool()
    def check_docker_status() -> Dict[str, Any]:
        """
        Controlla lo stato di Docker e fornisce informazioni di base.
        """
        try:
            # Controlla se Docker è installato e in esecuzione
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return {
                    "docker_available": False,
                    "error": "Docker not installed or not accessible"
                }
            
            docker_version = result.stdout.strip()
            
            # Controlla il daemon Docker
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
            daemon_running = result.returncode == 0
            
            info = {}
            if daemon_running:
                # Estrae informazioni base
                for line in result.stdout.split('\n'):
                    if 'Containers:' in line:
                        info['containers'] = line.split(':')[1].strip()
                    elif 'Images:' in line:
                        info['images'] = line.split(':')[1].strip()
                    elif 'Server Version:' in line:
                        info['server_version'] = line.split(':')[1].strip()
            
            return {
                "docker_available": True,
                "daemon_running": daemon_running,
                "version": docker_version,
                "info": info if daemon_running else "Daemon not running"
            }
        except subprocess.TimeoutExpired:
            return {
                "docker_available": False,
                "error": "Docker command timed out"
            }
        except FileNotFoundError:
            return {
                "docker_available": False,
                "error": "Docker command not found"
            }
        except Exception as e:
            return {
                "docker_available": False,
                "error": str(e)
            }

    @mcp.tool()
    def list_docker_containers(status: str = "all") -> Dict[str, Any]:
        """
        Lista i container Docker.
        
        Args:
            status: Filtro per stato (all, running, stopped, exited)
        """
        try:
            # Controlla se Docker è disponibile
            cmd = ['docker', 'ps']
            if status == "all":
                cmd.append('-a')
            elif status == "stopped":
                cmd.extend(['--filter', 'status=exited'])
            elif status == "running":
                pass  # Default behavior
            
            result = subprocess.run(cmd + ['--format', 'json'], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Failed to list containers"
                }
            
            containers = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            container = json.loads(line)
                            containers.append({
                                "id": container.get("ID", "")[:12],
                                "image": container.get("Image", ""),
                                "command": container.get("Command", ""),
                                "created": container.get("CreatedAt", ""),
                                "status": container.get("Status", ""),
                                "ports": container.get("Ports", ""),
                                "names": container.get("Names", "")
                            })
                        except json.JSONDecodeError:
                            continue
            
            return {
                "success": True,
                "containers": containers,
                "count": len(containers),
                "filter": status
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def list_docker_images() -> Dict[str, Any]:
        """
        Lista le immagini Docker disponibili.
        """
        try:
            result = subprocess.run(['docker', 'images', '--format', 'json'], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Failed to list images"
                }
            
            images = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            image = json.loads(line)
                            images.append({
                                "repository": image.get("Repository", ""),
                                "tag": image.get("Tag", ""),
                                "image_id": image.get("ID", "")[:12],
                                "created": image.get("CreatedAt", ""),
                                "size": image.get("Size", "")
                            })
                        except json.JSONDecodeError:
                            continue
            
            total_size = 0
            for image in images:
                size_str = image.get("size", "0B")
                # Conversione approssimativa della dimensione
                if "GB" in size_str:
                    total_size += float(re.findall(r'[\d.]+', size_str)[0]) * 1024
                elif "MB" in size_str:
                    total_size += float(re.findall(r'[\d.]+', size_str)[0])
            
            return {
                "success": True,
                "images": images,
                "count": len(images),
                "estimated_total_size_mb": round(total_size, 2)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def validate_dockerfile(dockerfile_content: str) -> Dict[str, Any]:
        """
        Valida un Dockerfile e fornisce suggerimenti di ottimizzazione.
        
        Args:
            dockerfile_content: Il contenuto del Dockerfile da validare
        """
        try:
            lines = dockerfile_content.strip().split('\n')
            issues = []
            suggestions = []
            commands = {}
            
            # Analizza ogni linea
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Estrae il comando
                command = line.split()[0].upper() if line.split() else ""
                commands[command] = commands.get(command, 0) + 1
                
                # Controlli specifici
                if command == "FROM":
                    if ":latest" in line:
                        suggestions.append(f"Line {i}: Avoid using :latest tag, specify exact version")
                    if line.count("FROM") > 1:
                        suggestions.append(f"Line {i}: Consider multi-stage builds for optimization")
                
                elif command == "RUN":
                    if "apt-get update" in line and "apt-get install" not in line:
                        issues.append(f"Line {i}: apt-get update without install in same RUN")
                    if line.count("&&") > 3:
                        suggestions.append(f"Line {i}: Consider breaking long RUN commands")
                    if "sudo" in line:
                        issues.append(f"Line {i}: Avoid using sudo in containers")
                
                elif command == "COPY" or command == "ADD":
                    if "*" in line or "." in line:
                        suggestions.append(f"Line {i}: Be specific with COPY/ADD paths to avoid cache invalidation")
                
                elif command == "USER":
                    if "root" in line:
                        issues.append(f"Line {i}: Running as root is not recommended")
                
                elif command == "EXPOSE":
                    # Valida porte
                    ports = re.findall(r'\b\d+\b', line)
                    for port in ports:
                        if int(port) < 1 or int(port) > 65535:
                            issues.append(f"Line {i}: Invalid port number {port}")
            
            # Controlli generali
            if "FROM" not in commands:
                issues.append("Missing FROM instruction")
            
            if commands.get("RUN", 0) > 10:
                suggestions.append("Too many RUN instructions, consider combining them")
            
            if "WORKDIR" not in commands:
                suggestions.append("Consider adding WORKDIR instruction")
            
            if "USER" not in commands:
                suggestions.append("Consider adding USER instruction for security")
            
            # Score di qualità
            score = 100
            score -= len(issues) * 10
            score -= len(suggestions) * 3
            score = max(0, score)
            
            quality_rating = (
                "Excellent" if score >= 90 else
                "Good" if score >= 70 else
                "Fair" if score >= 50 else
                "Poor"
            )
            
            return {
                "valid": len(issues) == 0,
                "quality_score": score,
                "quality_rating": quality_rating,
                "total_lines": len(lines),
                "command_usage": commands,
                "issues": issues,
                "suggestions": suggestions,
                "issue_count": len(issues),
                "suggestion_count": len(suggestions)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_docker_compose(services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera un file docker-compose.yml basato su specifiche servizi.
        
        Args:
            services: Lista di servizi con le loro configurazioni
        """
        try:
            compose_config = {
                "version": "3.8",
                "services": {}
            }
            
            for service in services:
                service_name = service.get("name", "app")
                service_config = {}
                
                # Configurazioni base
                if "image" in service:
                    service_config["image"] = service["image"]
                elif "build" in service:
                    service_config["build"] = service["build"]
                
                # Porte
                if "ports" in service:
                    service_config["ports"] = service["ports"]
                
                # Variabili d'ambiente
                if "environment" in service:
                    service_config["environment"] = service["environment"]
                
                # Volumi
                if "volumes" in service:
                    service_config["volumes"] = service["volumes"]
                
                # Dipendenze
                if "depends_on" in service:
                    service_config["depends_on"] = service["depends_on"]
                
                # Restart policy
                service_config["restart"] = service.get("restart", "unless-stopped")
                
                compose_config["services"][service_name] = service_config
            
            # Genera YAML (simplified)
            yaml_content = f"version: '{compose_config['version']}'\n\nservices:\n"
            
            for service_name, config in compose_config["services"].items():
                yaml_content += f"  {service_name}:\n"
                for key, value in config.items():
                    if isinstance(value, list):
                        yaml_content += f"    {key}:\n"
                        for item in value:
                            yaml_content += f"      - {item}\n"
                    elif isinstance(value, dict):
                        yaml_content += f"    {key}:\n"
                        for k, v in value.items():
                            yaml_content += f"      {k}: {v}\n"
                    else:
                        yaml_content += f"    {key}: {value}\n"
                yaml_content += "\n"
            
            return {
                "success": True,
                "docker_compose_yml": yaml_content,
                "services_count": len(services),
                "version": compose_config["version"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def docker_security_scan(image_name: str) -> Dict[str, Any]:
        """
        Esegue una scansione di sicurezza di base su un'immagine Docker.
        
        Args:
            image_name: Nome dell'immagine da scansionare
        """
        try:
            security_issues = []
            recommendations = []
            
            # Ispeziona l'immagine
            result = subprocess.run(['docker', 'inspect', image_name], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Cannot inspect image {image_name}"
                }
            
            image_info = json.loads(result.stdout)[0]
            config = image_info.get("Config", {})
            
            # Controlli di sicurezza
            user = config.get("User", "")
            if not user or user == "root" or user == "0":
                security_issues.append("Running as root user")
                recommendations.append("Set a non-root user with USER instruction")
            
            # Controlla porte esposte
            exposed_ports = config.get("ExposedPorts", {})
            for port in exposed_ports.keys():
                port_num = int(port.split('/')[0])
                if port_num < 1024:
                    security_issues.append(f"Privileged port {port_num} exposed")
                    recommendations.append("Consider using non-privileged ports (>1024)")
            
            # Controlla variabili d'ambiente
            env_vars = config.get("Env", [])
            for env_var in env_vars:
                if any(keyword in env_var.upper() for keyword in ["PASSWORD", "SECRET", "KEY", "TOKEN"]):
                    security_issues.append("Potential secrets in environment variables")
                    recommendations.append("Use Docker secrets or external secret management")
                    break
            
            # Controlla dimensione immagine
            size = image_info.get("Size", 0)
            size_mb = size / (1024 * 1024)
            if size_mb > 1000:  # > 1GB
                recommendations.append("Large image size - consider using Alpine or distroless base images")
            
            # Score di sicurezza
            security_score = 100 - len(security_issues) * 20
            security_score = max(0, security_score)
            
            security_rating = (
                "Excellent" if security_score >= 90 else
                "Good" if security_score >= 70 else
                "Fair" if security_score >= 50 else
                "Poor"
            )
            
            return {
                "success": True,
                "image": image_name,
                "security_score": security_score,
                "security_rating": security_rating,
                "size_mb": round(size_mb, 2),
                "user": user or "root",
                "exposed_ports": list(exposed_ports.keys()),
                "security_issues": security_issues,
                "recommendations": recommendations,
                "issue_count": len(security_issues)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def manage_container(container_id: str, action: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gestisce operazioni su container Docker.
        
        Args:
            container_id: ID o nome del container
            action: Azione da eseguire (start, stop, restart, pause, unpause, remove, logs)
            options: Opzioni aggiuntive per l'azione
        """
        try:
            if not container_id:
                return {"success": False, "error": "Container ID/name is required"}
            
            options = options or {}
            
            if action == "start":
                cmd = ['docker', 'start', container_id]
                
            elif action == "stop":
                timeout = options.get("timeout", 10)
                cmd = ['docker', 'stop', '-t', str(timeout), container_id]
                
            elif action == "restart":
                timeout = options.get("timeout", 10)
                cmd = ['docker', 'restart', '-t', str(timeout), container_id]
                
            elif action == "pause":
                cmd = ['docker', 'pause', container_id]
                
            elif action == "unpause":
                cmd = ['docker', 'unpause', container_id]
                
            elif action == "remove":
                cmd = ['docker', 'rm']
                if options.get("force", False):
                    cmd.append('-f')
                if options.get("volumes", False):
                    cmd.append('-v')
                cmd.append(container_id)
                
            elif action == "logs":
                cmd = ['docker', 'logs']
                if options.get("follow", False):
                    cmd.append('-f')
                if options.get("tail"):
                    cmd.extend(['--tail', str(options["tail"])])
                if options.get("since"):
                    cmd.extend(['--since', options["since"]])
                cmd.append(container_id)
                
            else:
                return {"success": False, "error": f"Unsupported action: {action}"}
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or f"Failed to {action} container",
                    "container_id": container_id,
                    "action": action
                }
            
            # Per logs, restituisce l'output
            if action == "logs":
                return {
                    "success": True,
                    "container_id": container_id,
                    "action": action,
                    "logs": result.stdout,
                    "log_lines": len(result.stdout.split('\n')) if result.stdout else 0
                }
            
            # Per altre azioni, verifica lo stato
            container_status = _get_container_status(container_id)
            
            return {
                "success": True,
                "container_id": container_id,
                "action": action,
                "current_status": container_status,
                "output": result.stdout.strip() if result.stdout else None
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out for action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def build_docker_image(build_context: str, dockerfile_path: str = "Dockerfile",
                          image_name: str = "", build_args: Dict[str, str] = None,
                          no_cache: bool = False) -> Dict[str, Any]:
        """
        Costruisce un'immagine Docker.
        
        Args:
            build_context: Path del contesto di build
            dockerfile_path: Path del Dockerfile
            image_name: Nome e tag dell'immagine (es. myapp:v1.0)
            build_args: Argomenti di build
            no_cache: Se disabilitare la cache
        """
        try:
            if not os.path.exists(build_context):
                return {"success": False, "error": "Build context path does not exist"}
            
            dockerfile_full_path = os.path.join(build_context, dockerfile_path)
            if not os.path.exists(dockerfile_full_path):
                return {"success": False, "error": f"Dockerfile not found at {dockerfile_full_path}"}
            
            cmd = ['docker', 'build']
            
            if no_cache:
                cmd.append('--no-cache')
            
            if dockerfile_path != "Dockerfile":
                cmd.extend(['-f', dockerfile_path])
            
            if build_args:
                for key, value in build_args.items():
                    cmd.extend(['--build-arg', f'{key}={value}'])
            
            if image_name:
                cmd.extend(['-t', image_name])
            
            cmd.append(build_context)
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            build_time = time.time() - start_time
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Build failed",
                    "stderr": result.stderr,
                    "build_time_seconds": round(build_time, 2)
                }
            
            # Estrae informazioni dal build output
            build_output = result.stdout
            image_id = None
            
            # Cerca l'ID dell'immagine nell'output
            for line in build_output.split('\n'):
                if 'Successfully built' in line:
                    image_id = line.split()[-1]
                    break
            
            # Calcola dimensione se immagine creata con successo
            image_size = None
            if image_name:
                try:
                    size_result = subprocess.run(['docker', 'images', image_name, '--format', '{{.Size}}'], 
                                               capture_output=True, text=True, timeout=10)
                    if size_result.returncode == 0:
                        image_size = size_result.stdout.strip()
                except:
                    pass
            
            return {
                "success": True,
                "image_name": image_name,
                "image_id": image_id,
                "image_size": image_size,
                "build_time_seconds": round(build_time, 2),
                "build_context": build_context,
                "dockerfile": dockerfile_path,
                "build_output_lines": len(build_output.split('\n')),
                "no_cache_used": no_cache
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Build timed out (10 minutes limit)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def manage_docker_networks(action: str, network_name: str = "", 
                              network_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gestisce reti Docker.
        
        Args:
            action: Azione (list, create, remove, inspect, connect, disconnect)
            network_name: Nome della rete
            network_config: Configurazione per creazione rete
        """
        try:
            if action == "list":
                result = subprocess.run(['docker', 'network', 'ls', '--format', 'json'], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {"success": False, "error": "Failed to list networks"}
                
                networks = []
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        try:
                            network = json.loads(line)
                            networks.append({
                                "id": network.get("ID", "")[:12],
                                "name": network.get("Name", ""),
                                "driver": network.get("Driver", ""),
                                "scope": network.get("Scope", "")
                            })
                        except json.JSONDecodeError:
                            continue
                
                return {
                    "success": True,
                    "networks": networks,
                    "count": len(networks)
                }
            
            elif action == "create":
                if not network_name:
                    return {"success": False, "error": "Network name required for create action"}
                
                cmd = ['docker', 'network', 'create']
                
                if network_config:
                    if 'driver' in network_config:
                        cmd.extend(['--driver', network_config['driver']])
                    if 'subnet' in network_config:
                        cmd.extend(['--subnet', network_config['subnet']])
                    if 'gateway' in network_config:
                        cmd.extend(['--gateway', network_config['gateway']])
                
                cmd.append(network_name)
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "network_name": network_name,
                    "network_id": result.stdout.strip(),
                    "action": "created"
                }
            
            elif action == "remove":
                if not network_name:
                    return {"success": False, "error": "Network name required for remove action"}
                
                result = subprocess.run(['docker', 'network', 'rm', network_name], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "network_name": network_name,
                    "action": "removed"
                }
            
            elif action == "inspect":
                if not network_name:
                    return {"success": False, "error": "Network name required for inspect action"}
                
                result = subprocess.run(['docker', 'network', 'inspect', network_name], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                try:
                    network_info = json.loads(result.stdout)[0]
                    return {
                        "success": True,
                        "network_info": network_info,
                        "containers_connected": len(network_info.get("Containers", {}))
                    }
                except json.JSONDecodeError:
                    return {"success": False, "error": "Failed to parse network info"}
            
            else:
                return {"success": False, "error": f"Unsupported network action: {action}"}
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Network command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def manage_docker_volumes(action: str, volume_name: str = "", 
                             volume_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gestisce volumi Docker.
        
        Args:
            action: Azione (list, create, remove, inspect, prune)
            volume_name: Nome del volume
            volume_config: Configurazione per creazione volume
        """
        try:
            if action == "list":
                result = subprocess.run(['docker', 'volume', 'ls', '--format', 'json'], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {"success": False, "error": "Failed to list volumes"}
                
                volumes = []
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        try:
                            volume = json.loads(line)
                            volumes.append({
                                "name": volume.get("Name", ""),
                                "driver": volume.get("Driver", ""),
                                "mountpoint": volume.get("Mountpoint", "")
                            })
                        except json.JSONDecodeError:
                            continue
                
                return {
                    "success": True,
                    "volumes": volumes,
                    "count": len(volumes)
                }
            
            elif action == "create":
                if not volume_name:
                    return {"success": False, "error": "Volume name required for create action"}
                
                cmd = ['docker', 'volume', 'create']
                
                if volume_config:
                    if 'driver' in volume_config:
                        cmd.extend(['--driver', volume_config['driver']])
                    if 'options' in volume_config:
                        for key, value in volume_config['options'].items():
                            cmd.extend(['--opt', f'{key}={value}'])
                
                cmd.append(volume_name)
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "volume_name": volume_name,
                    "action": "created"
                }
            
            elif action == "remove":
                if not volume_name:
                    return {"success": False, "error": "Volume name required for remove action"}
                
                result = subprocess.run(['docker', 'volume', 'rm', volume_name], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                return {
                    "success": True,
                    "volume_name": volume_name,
                    "action": "removed"
                }
            
            elif action == "prune":
                result = subprocess.run(['docker', 'volume', 'prune', '-f'], 
                                      capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}
                
                # Estrae informazioni dal output
                space_reclaimed = "0B"
                for line in result.stdout.split('\n'):
                    if "Total reclaimed space" in line:
                        space_reclaimed = line.split(':')[-1].strip()
                        break
                
                return {
                    "success": True,
                    "action": "pruned",
                    "space_reclaimed": space_reclaimed
                }
            
            else:
                return {"success": False, "error": f"Unsupported volume action: {action}"}
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Volume command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def run_container(image: str, container_name: str = "", 
                     run_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Avvia un nuovo container Docker.
        
        Args:
            image: Nome dell'immagine
            container_name: Nome del container (opzionale)
            run_config: Configurazione di esecuzione
        """
        try:
            cmd = ['docker', 'run']
            
            run_config = run_config or {}
            
            # Modalità detached di default
            if run_config.get('detached', True):
                cmd.append('-d')
            
            # Nome container
            if container_name:
                cmd.extend(['--name', container_name])
            
            # Porte
            if 'ports' in run_config:
                for port_mapping in run_config['ports']:
                    cmd.extend(['-p', port_mapping])
            
            # Variabili ambiente
            if 'environment' in run_config:
                for env_var in run_config['environment']:
                    cmd.extend(['-e', env_var])
            
            # Volumi
            if 'volumes' in run_config:
                for volume_mapping in run_config['volumes']:
                    cmd.extend(['-v', volume_mapping])
            
            # Rete
            if 'network' in run_config:
                cmd.extend(['--network', run_config['network']])
            
            # Restart policy
            if 'restart' in run_config:
                cmd.extend(['--restart', run_config['restart']])
            
            # Rimozione automatica
            if run_config.get('remove', False):
                cmd.append('--rm')
            
            # Comando personalizzato
            cmd.append(image)
            if 'command' in run_config:
                if isinstance(run_config['command'], list):
                    cmd.extend(run_config['command'])
                else:
                    cmd.extend(run_config['command'].split())
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip(),
                    "command": ' '.join(cmd)
                }
            
            container_id = result.stdout.strip()
            
            # Ottieni informazioni container se creato con successo
            container_info = None
            if container_id:
                try:
                    inspect_result = subprocess.run(['docker', 'inspect', container_id], 
                                                  capture_output=True, text=True, timeout=10)
                    if inspect_result.returncode == 0:
                        container_data = json.loads(inspect_result.stdout)[0]
                        container_info = {
                            "id": container_id[:12],
                            "name": container_data.get("Name", "").lstrip('/'),
                            "status": container_data.get("State", {}).get("Status", ""),
                            "created": container_data.get("Created", ""),
                            "image": container_data.get("Config", {}).get("Image", "")
                        }
                except:
                    pass
            
            return {
                "success": True,
                "container_id": container_id[:12] if container_id else None,
                "container_name": container_name,
                "image": image,
                "container_info": container_info,
                "run_config": run_config
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Container run command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def monitor_container_resources(container_id: str, duration: int = 10) -> Dict[str, Any]:
        """
        Monitora le risorse utilizzate da un container.
        
        Args:
            container_id: ID o nome del container
            duration: Durata del monitoraggio in secondi (max 60)
        """
        try:
            if duration > 60:
                duration = 60
                
            # Verifica che il container esista ed è in esecuzione
            status = _get_container_status(container_id)
            if not status or "running" not in status.lower():
                return {"success": False, "error": "Container not found or not running"}
            
            # Raccoglie statistiche per la durata specificata
            stats_samples = []
            
            for i in range(min(duration, 10)):  # Max 10 campioni
                result = subprocess.run(['docker', 'stats', '--no-stream', '--format', 
                                       'json', container_id], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    break
                
                try:
                    stats = json.loads(result.stdout.strip())
                    
                    # Estrae valori numerici
                    cpu_percent = float(stats.get("CPUPerc", "0%").rstrip('%'))
                    mem_usage = stats.get("MemUsage", "0B / 0B")
                    mem_percent = float(stats.get("MemPerc", "0%").rstrip('%'))
                    net_io = stats.get("NetIO", "0B / 0B")
                    block_io = stats.get("BlockIO", "0B / 0B")
                    
                    stats_samples.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "cpu_percent": cpu_percent,
                        "memory_usage": mem_usage,
                        "memory_percent": mem_percent,
                        "network_io": net_io,
                        "block_io": block_io
                    })
                    
                except (json.JSONDecodeError, ValueError):
                    continue
                
                if i < duration - 1:
                    time.sleep(1)
            
            if not stats_samples:
                return {"success": False, "error": "Could not collect resource statistics"}
            
            # Calcola statistiche aggregate
            cpu_values = [s["cpu_percent"] for s in stats_samples]
            mem_values = [s["memory_percent"] for s in stats_samples]
            
            return {
                "success": True,
                "container_id": container_id,
                "monitoring_duration": len(stats_samples),
                "samples": stats_samples,
                "aggregated_stats": {
                    "cpu_avg": round(sum(cpu_values) / len(cpu_values), 2),
                    "cpu_max": max(cpu_values),
                    "cpu_min": min(cpu_values),
                    "memory_avg": round(sum(mem_values) / len(mem_values), 2),
                    "memory_max": max(mem_values),
                    "memory_min": min(mem_values)
                },
                "recommendations": _generate_resource_recommendations(cpu_values, mem_values)
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Resource monitoring timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def cleanup_docker_resources(cleanup_type: str = "all", 
                                force: bool = False) -> Dict[str, Any]:
        """
        Pulisce risorse Docker inutilizzate.
        
        Args:
            cleanup_type: Tipo pulizia (all, containers, images, volumes, networks)
            force: Forza la pulizia senza conferma
        """
        try:
            cleanup_results = {}
            
            if cleanup_type in ["all", "containers"]:
                # Pulisce container fermati
                cmd = ['docker', 'container', 'prune']
                if force:
                    cmd.append('-f')
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                cleanup_results["containers"] = {
                    "success": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip() if result.returncode != 0 else None
                }
            
            if cleanup_type in ["all", "images"]:
                # Pulisce immagini dangling
                cmd = ['docker', 'image', 'prune']
                if force:
                    cmd.append('-f')
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                cleanup_results["images"] = {
                    "success": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip() if result.returncode != 0 else None
                }
            
            if cleanup_type in ["all", "volumes"]:
                # Pulisce volumi inutilizzati
                cmd = ['docker', 'volume', 'prune']
                if force:
                    cmd.append('-f')
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                cleanup_results["volumes"] = {
                    "success": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip() if result.returncode != 0 else None
                }
            
            if cleanup_type in ["all", "networks"]:
                # Pulisce reti inutilizzate
                cmd = ['docker', 'network', 'prune']
                if force:
                    cmd.append('-f')
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                cleanup_results["networks"] = {
                    "success": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip() if result.returncode != 0 else None
                }
            
            # Calcola spazio totale recuperato
            total_space_reclaimed = "0B"
            for category, result in cleanup_results.items():
                if result["success"] and result["output"]:
                    for line in result["output"].split('\n'):
                        if "Total reclaimed space" in line:
                            space = line.split(':')[-1].strip()
                            if space != "0B":
                                total_space_reclaimed = space
                            break
            
            successful_cleanups = sum(1 for r in cleanup_results.values() if r["success"])
            
            return {
                "success": successful_cleanups > 0,
                "cleanup_type": cleanup_type,
                "results": cleanup_results,
                "successful_cleanups": successful_cleanups,
                "total_space_reclaimed": total_space_reclaimed,
                "force_used": force
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Cleanup operation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Enhanced helper functions
    def _get_container_status(container_id: str) -> Optional[str]:
        """Ottiene lo stato di un container."""
        try:
            result = subprocess.run(['docker', 'inspect', '--format', '{{.State.Status}}', container_id],
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None

    def _generate_resource_recommendations(cpu_values: List[float], mem_values: List[float]) -> List[str]:
        """Genera raccomandazioni basate sull'uso delle risorse."""
        recommendations = []
        
        avg_cpu = sum(cpu_values) / len(cpu_values)
        avg_mem = sum(mem_values) / len(mem_values)
        max_cpu = max(cpu_values)
        max_mem = max(mem_values)
        
        if avg_cpu > 80:
            recommendations.append("High CPU usage - consider allocating more CPU or optimizing application")
        elif avg_cpu < 10:
            recommendations.append("Low CPU usage - consider reducing CPU allocation")
        
        if avg_mem > 80:
            recommendations.append("High memory usage - consider increasing memory limit or optimizing application")
        elif avg_mem < 20:
            recommendations.append("Low memory usage - consider reducing memory allocation")
        
        if max_cpu > 95:
            recommendations.append("CPU peaks detected - monitor for performance bottlenecks")
        
        if max_mem > 95:
            recommendations.append("Memory peaks detected - risk of OOM kills")
        
        return recommendations