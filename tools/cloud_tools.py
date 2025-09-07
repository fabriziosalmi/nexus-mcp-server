# -*- coding: utf-8 -*-
# tools/cloud_tools.py
import json
import logging
import httpx
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

def register_tools(mcp):
    """Registra i cloud tools con l'istanza del server MCP."""
    logging.info("☁️ Registrazione tool-set: Cloud Platform Tools")

    @mcp.tool()
    async def aws_service_status(service: str = "all", region: str = "us-east-1") -> str:
        """
        Verifica lo stato dei servizi AWS usando la AWS Service Health Dashboard.
        
        Args:
            service: Nome del servizio AWS da controllare (default: "all")
            region: Regione AWS da controllare (default: "us-east-1")
        """
        try:
            # Simulazione controllo status AWS (API pubblica limitata)
            common_services = ["ec2", "s3", "lambda", "rds", "vpc", "cloudfront", "route53"]
            
            if service == "all":
                result = f"=== AWS Service Status - Region: {region} ===\n"
                for svc in common_services:
                    result += f"✅ {svc.upper()}: Operational\n"
                result += "\nNote: This is a simulated status check. For real-time status, visit https://status.aws.amazon.com/"
                return result
            else:
                return f"✅ AWS {service.upper()} - Region {region}: Operational\n\nNote: This is a simulated status check."
        except Exception as e:
            return f"❌ Error checking AWS service status: {str(e)}"

    @mcp.tool()
    async def azure_service_status(service: str = "all", region: str = "East US") -> str:
        """
        Verifica lo stato dei servizi Azure.
        
        Args:
            service: Nome del servizio Azure da controllare (default: "all")
            region: Regione Azure da controllare (default: "East US")
        """
        try:
            common_services = ["compute", "storage", "networking", "databases", "app-services", "functions"]
            
            if service == "all":
                result = f"=== Azure Service Status - Region: {region} ===\n"
                for svc in common_services:
                    result += f"✅ {svc.replace('-', ' ').title()}: Available\n"
                result += "\nNote: This is a simulated status check. For real-time status, visit https://status.azure.com/"
                return result
            else:
                return f"✅ Azure {service.title()} - Region {region}: Available\n\nNote: This is a simulated status check."
        except Exception as e:
            return f"❌ Error checking Azure service status: {str(e)}"

    @mcp.tool()
    async def gcp_service_status(service: str = "all", region: str = "us-central1") -> str:
        """
        Verifica lo stato dei servizi Google Cloud Platform.
        
        Args:
            service: Nome del servizio GCP da controllare (default: "all")
            region: Regione GCP da controllare (default: "us-central1")
        """
        try:
            common_services = ["compute-engine", "cloud-storage", "cloud-functions", "cloud-sql", "kubernetes-engine", "app-engine"]
            
            if service == "all":
                result = f"=== GCP Service Status - Region: {region} ===\n"
                for svc in common_services:
                    result += f"✅ {svc.replace('-', ' ').title()}: Available\n"
                result += "\nNote: This is a simulated status check. For real-time status, visit https://status.cloud.google.com/"
                return result
            else:
                return f"✅ GCP {service.title()} - Region {region}: Available\n\nNote: This is a simulated status check."
        except Exception as e:
            return f"❌ Error checking GCP service status: {str(e)}"

    @mcp.tool()
    async def cloudflare_dns_lookup(domain: str, record_type: str = "A") -> str:
        """
        Esegue una query DNS usando i server Cloudflare.
        
        Args:
            domain: Il dominio da interrogare
            record_type: Tipo di record DNS (A, AAAA, MX, TXT, CNAME)
        """
        try:
            # Usa l'API DNS-over-HTTPS di Cloudflare
            url = f"https://cloudflare-dns.com/dns-query"
            headers = {"Accept": "application/dns-json"}
            params = {"name": domain, "type": record_type}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("Status") != 0:
                    return f"❌ DNS query failed for {domain} (Type: {record_type})"
                
                result = f"=== Cloudflare DNS Lookup ===\n"
                result += f"Domain: {domain}\n"
                result += f"Record Type: {record_type}\n"
                result += f"Status: {'✅ Success' if data.get('Status') == 0 else '❌ Failed'}\n\n"
                
                if "Answer" in data:
                    result += "Records found:\n"
                    for answer in data["Answer"]:
                        result += f"  {answer.get('name', domain)} -> {answer.get('data', 'N/A')}\n"
                else:
                    result += "No records found.\n"
                
                return result
        except Exception as e:
            return f"❌ Error performing DNS lookup: {str(e)}"

    @mcp.tool()
    async def digitalocean_status_check() -> str:
        """
        Verifica lo stato dei servizi DigitalOcean.
        """
        try:
            # Controlla la pagina di status pubblica di DigitalOcean
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://status.digitalocean.com/api/v2/status.json")
                response.raise_for_status()
                data = response.json()
                
                result = "=== DigitalOcean Status ===\n"
                status = data.get("status", {})
                result += f"Overall Status: {status.get('description', 'Unknown')}\n"
                result += f"Indicator: {status.get('indicator', 'Unknown')}\n"
                
                return result
        except Exception as e:
            return f"❌ Error checking DigitalOcean status: {str(e)}\n\nFallback info: Check https://status.digitalocean.com/ for current status"

    @mcp.tool()
    def cloud_cost_calculator(service_type: str, usage_hours: float, instance_type: str = "medium") -> str:
        """
        Calcola una stima dei costi per servizi cloud comuni.
        
        Args:
            service_type: Tipo di servizio (compute, storage, database, bandwidth)
            usage_hours: Ore di utilizzo nel mese
            instance_type: Tipo di istanza (small, medium, large, xlarge)
        """
        try:
            # Prezzi approssimativi per scopo educativo
            pricing = {
                "compute": {
                    "small": 0.02,   # $/hour
                    "medium": 0.05,
                    "large": 0.10,
                    "xlarge": 0.20
                },
                "storage": {
                    "small": 0.10,   # $/GB/month
                    "medium": 0.08,
                    "large": 0.06,
                    "xlarge": 0.04
                },
                "database": {
                    "small": 0.08,   # $/hour
                    "medium": 0.15,
                    "large": 0.30,
                    "xlarge": 0.60
                },
                "bandwidth": {
                    "small": 0.09,   # $/GB
                    "medium": 0.085,
                    "large": 0.08,
                    "xlarge": 0.075
                }
            }
            
            if service_type not in pricing:
                return f"❌ Service type '{service_type}' not supported. Available: {', '.join(pricing.keys())}"
            
            if instance_type not in pricing[service_type]:
                return f"❌ Instance type '{instance_type}' not supported for {service_type}. Available: {', '.join(pricing[service_type].keys())}"
            
            rate = pricing[service_type][instance_type]
            
            if service_type == "storage":
                cost = rate * usage_hours  # treating usage_hours as GB for storage
                unit = "GB"
            elif service_type == "bandwidth":
                cost = rate * usage_hours  # treating usage_hours as GB for bandwidth
                unit = "GB"
            else:
                cost = rate * usage_hours
                unit = "hours"
            
            result = f"=== Cloud Cost Estimate ===\n"
            result += f"Service Type: {service_type.title()}\n"
            result += f"Instance Type: {instance_type.title()}\n"
            result += f"Usage: {usage_hours} {unit}\n"
            result += f"Rate: ${rate:.3f} per {unit}\n"
            result += f"Estimated Cost: ${cost:.2f}\n\n"
            result += "⚠️ This is an approximate estimate for educational purposes.\n"
            result += "Actual costs may vary significantly between providers and regions."
            
            return result
        except Exception as e:
            return f"❌ Error calculating cloud costs: {str(e)}"

    @mcp.tool()
    async def cloud_health_checker(endpoints: List[str]) -> str:
        """
        Controlla la salute di endpoints cloud comuni.
        
        Args:
            endpoints: Lista di URL/endpoint da controllare
        """
        try:
            result = "=== Cloud Health Check ===\n\n"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint in endpoints:
                    try:
                        import time
                        start_time = time.time()
                        response = await client.get(endpoint)
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # milliseconds
                        
                        status = "✅ Healthy" if response.status_code < 400 else f"❌ Error ({response.status_code})"
                        result += f"{endpoint}\n"
                        result += f"  Status: {status}\n"
                        result += f"  Response Time: {response_time:.2f}ms\n"
                        result += f"  Status Code: {response.status_code}\n\n"
                        
                    except Exception as e:
                        result += f"{endpoint}\n"
                        result += f"  Status: ❌ Failed\n"
                        result += f"  Error: {str(e)}\n\n"
            
            return result
        except Exception as e:
            return f"❌ Error performing health checks: {str(e)}"

    @mcp.tool()
    def cloud_security_scanner(config_text: str, cloud_provider: str = "aws") -> str:
        """
        Scansiona configurazioni cloud per problemi di sicurezza comuni.
        
        Args:
            config_text: Testo della configurazione (JSON/YAML)
            cloud_provider: Provider cloud (aws, azure, gcp)
        """
        try:
            issues = []
            suggestions = []
            
            # Controlli di sicurezza generici
            if "password" in config_text.lower() and ("123" in config_text or "password" in config_text.lower()):
                issues.append("⚠️ Weak password detected in configuration")
                suggestions.append("Use strong, randomly generated passwords")
            
            if "0.0.0.0/0" in config_text:
                issues.append("🔴 Open security group detected (0.0.0.0/0)")
                suggestions.append("Restrict access to specific IP ranges")
            
            if re.search(r'"?\d+\.\d+\.\d+\.\d+"?', config_text):
                issues.append("ℹ️ Hardcoded IP addresses found")
                suggestions.append("Consider using variables or dynamic references")
            
            if "http://" in config_text and "https://" in config_text:
                issues.append("⚠️ Mixed HTTP/HTTPS usage detected")
                suggestions.append("Use HTTPS only for security")
            
            # Controlli specifici per provider
            if cloud_provider == "aws":
                if '"Action": "*"' in config_text or "'Action': '*'" in config_text:
                    issues.append("🔴 Overly permissive IAM policy (Action: *)")
                    suggestions.append("Follow least privilege principle for IAM policies")
            
            result = f"=== Cloud Security Scan ({cloud_provider.upper()}) ===\n\n"
            
            if issues:
                result += "🔍 Issues Found:\n"
                for issue in issues:
                    result += f"  {issue}\n"
                result += "\n💡 Recommendations:\n"
                for suggestion in suggestions:
                    result += f"  • {suggestion}\n"
            else:
                result += "✅ No obvious security issues detected.\n"
                result += "Note: This is a basic scan. Perform thorough security reviews for production systems.\n"
            
            return result
        except Exception as e:
            return f"❌ Error scanning configuration: {str(e)}"

    @mcp.tool()
    def multi_cloud_resource_tracker(resources: List[Dict[str, str]]) -> str:
        """
        Traccia risorse su più provider cloud.
        
        Args:
            resources: Lista di risorse nel formato [{"provider": "aws", "type": "ec2", "name": "web-server", "region": "us-east-1"}]
        """
        try:
            result = "=== Multi-Cloud Resource Tracker ===\n\n"
            
            # Raggruppa per provider
            by_provider = {}
            for resource in resources:
                provider = resource.get("provider", "unknown")
                if provider not in by_provider:
                    by_provider[provider] = []
                by_provider[provider].append(resource)
            
            total_resources = len(resources)
            result += f"Total Resources: {total_resources}\n"
            result += f"Providers: {len(by_provider)}\n\n"
            
            for provider, provider_resources in by_provider.items():
                result += f"--- {provider.upper()} ({len(provider_resources)} resources) ---\n"
                
                # Raggruppa per tipo
                by_type = {}
                for resource in provider_resources:
                    res_type = resource.get("type", "unknown")
                    if res_type not in by_type:
                        by_type[res_type] = []
                    by_type[res_type].append(resource)
                
                for res_type, type_resources in by_type.items():
                    result += f"  {res_type.upper()}: {len(type_resources)}\n"
                    for resource in type_resources:
                        name = resource.get("name", "unnamed")
                        region = resource.get("region", "unknown")
                        result += f"    • {name} ({region})\n"
                
                result += "\n"
            
            return result
        except Exception as e:
            return f"❌ Error tracking resources: {str(e)}"

    @mcp.tool()
    def cloud_config_validator(config_text: str, config_type: str = "json") -> str:
        """
        Valida file di configurazione cloud comuni.
        
        Args:
            config_text: Contenuto del file di configurazione
            config_type: Tipo di configurazione (json, yaml, terraform, cloudformation)
        """
        try:
            result = f"=== Cloud Config Validator ({config_type.upper()}) ===\n\n"
            issues = []
            warnings = []
            
            # Validazione JSON
            if config_type.lower() == "json":
                try:
                    json.loads(config_text)
                    result += "✅ Valid JSON syntax\n"
                except json.JSONDecodeError as e:
                    issues.append(f"Invalid JSON syntax: {str(e)}")
            
            # Controlli generali
            if len(config_text.strip()) == 0:
                issues.append("Configuration is empty")
            
            if len(config_text) > 100000:  # 100KB
                warnings.append("Configuration file is very large (>100KB)")
            
            # Controlli specifici per tipo
            if config_type.lower() == "terraform":
                if "resource " not in config_text:
                    warnings.append("No Terraform resources found")
                if "provider " not in config_text:
                    warnings.append("No Terraform provider configuration found")
            
            if config_type.lower() == "cloudformation":
                if "Resources:" not in config_text and '"Resources"' not in config_text:
                    warnings.append("No CloudFormation resources section found")
            
            # Controlli di sicurezza
            sensitive_patterns = [
                (r'password\s*[:=]\s*["\']?\w+', "Possible hardcoded password"),
                (r'secret\s*[:=]\s*["\']?\w+', "Possible hardcoded secret"),
                (r'key\s*[:=]\s*["\']?[A-Za-z0-9+/]{20,}', "Possible hardcoded API key")
            ]
            
            for pattern, warning in sensitive_patterns:
                if re.search(pattern, config_text, re.IGNORECASE):
                    warnings.append(warning)
            
            # Risultati
            if issues:
                result += "\n🔴 Issues:\n"
                for issue in issues:
                    result += f"  • {issue}\n"
            
            if warnings:
                result += "\n⚠️ Warnings:\n"
                for warning in warnings:
                    result += f"  • {warning}\n"
            
            if not issues and not warnings:
                result += "✅ Configuration appears valid with no obvious issues.\n"
            
            result += f"\nConfiguration size: {len(config_text)} characters\n"
            result += f"Lines: {config_text.count(chr(10)) + 1}\n"
            
            return result
        except Exception as e:
            return f"❌ Error validating configuration: {str(e)}"