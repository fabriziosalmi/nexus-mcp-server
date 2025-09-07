# -*- coding: utf-8 -*-
# tools/docker_tools.py
import subprocess
import json
import re
import logging
from typing import Dict, List, Any, Optional

def register_tools(mcp):
    """Registra i tool Docker con l'istanza del server MCP."""
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