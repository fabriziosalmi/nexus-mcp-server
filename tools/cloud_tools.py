# -*- coding: utf-8 -*-
# tools/cloud_tools.py
import json
import logging
import httpx
import re
import base64
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta
import ipaddress
import socket

def register_tools(mcp):
    """Registra i cloud tools avanzati con l'istanza del server MCP."""
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

    @mcp.tool()
    async def enhanced_service_status_monitor(providers: List[str] = None, detailed: bool = True) -> Dict[str, Any]:
        """
        Monitora lo stato dei servizi cloud in tempo reale con API ufficiali.
        
        Args:
            providers: Lista provider da monitorare (aws, azure, gcp, cloudflare, digitalocean)
            detailed: Include dettagli per regione e servizio specifico
        """
        try:
            if providers is None:
                providers = ["aws", "azure", "gcp", "cloudflare", "digitalocean"]
            
            results = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "providers": {},
                "summary": {"total_providers": len(providers), "healthy": 0, "degraded": 0, "down": 0}
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                for provider in providers:
                    try:
                        provider_status = await self._check_provider_status(client, provider, detailed)
                        results["providers"][provider] = provider_status
                        
                        # Update summary
                        if provider_status["overall_status"] == "operational":
                            results["summary"]["healthy"] += 1
                        elif provider_status["overall_status"] == "degraded":
                            results["summary"]["degraded"] += 1
                        else:
                            results["summary"]["down"] += 1
                            
                    except Exception as e:
                        results["providers"][provider] = {
                            "status": "error",
                            "error": str(e),
                            "last_checked": datetime.now(timezone.utc).isoformat()
                        }
                        results["summary"]["down"] += 1
            
            return {
                "success": True,
                "monitoring_results": results,
                "health_score": (results["summary"]["healthy"] / len(providers)) * 100
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _check_provider_status(self, client: httpx.AsyncClient, provider: str, detailed: bool) -> Dict[str, Any]:
        """Controlla lo status di un provider specifico."""
        status_urls = {
            "digitalocean": "https://status.digitalocean.com/api/v2/status.json",
            "github": "https://www.githubstatus.com/api/v2/status.json",
            "cloudflare": "https://www.cloudflarestatus.com/api/v2/status.json"
        }
        
        if provider in status_urls:
            try:
                response = await client.get(status_urls[provider])
                response.raise_for_status()
                data = response.json()
                
                status_info = data.get("status", {})
                return {
                    "overall_status": "operational" if status_info.get("indicator") == "none" else "degraded",
                    "description": status_info.get("description", "Unknown"),
                    "indicator": status_info.get("indicator", "unknown"),
                    "last_updated": data.get("page", {}).get("updated_at"),
                    "url": status_urls[provider].replace("/api/v2/status.json", ""),
                    "components": await self._get_component_status(client, provider) if detailed else None
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            # Fallback per provider senza API pubblica
            return await self._simulate_provider_status(provider, detailed)

    async def _simulate_provider_status(self, provider: str, detailed: bool) -> Dict[str, Any]:
        """Simula status per provider senza API pubblica accessibile."""
        service_lists = {
            "aws": ["EC2", "S3", "Lambda", "RDS", "CloudFront", "Route53", "VPC"],
            "azure": ["Virtual Machines", "Storage", "App Service", "SQL Database", "Functions"],
            "gcp": ["Compute Engine", "Cloud Storage", "Cloud Functions", "Cloud SQL", "Kubernetes Engine"]
        }
        
        services = service_lists.get(provider, ["Service 1", "Service 2", "Service 3"])
        
        return {
            "overall_status": "operational",
            "description": f"{provider.upper()} services are operational",
            "indicator": "none",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "note": "Simulated status - check official status page for real-time information",
            "official_url": f"https://status.{provider}.com" if provider != "gcp" else "https://status.cloud.google.com",
            "services": {service: "operational" for service in services} if detailed else None
        }

    @mcp.tool()
    async def advanced_dns_analyzer(domain: str, comprehensive: bool = True) -> Dict[str, Any]:
        """
        Analisi DNS completa con multiple query e controlli di sicurezza.
        
        Args:
            domain: Dominio da analizzare
            comprehensive: Esegue analisi completa di tutti i record
        """
        try:
            results = {
                "domain": domain,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "records": {},
                "security_analysis": {},
                "performance_metrics": {}
            }
            
            record_types = ["A", "AAAA", "MX", "TXT", "CNAME", "NS", "SOA"]
            if comprehensive:
                record_types.extend(["SRV", "PTR", "CAA"])
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # DNS over HTTPS queries
                for record_type in record_types:
                    try:
                        start_time = datetime.now()
                        response = await client.get(
                            "https://cloudflare-dns.com/dns-query",
                            headers={"Accept": "application/dns-json"},
                            params={"name": domain, "type": record_type}
                        )
                        end_time = datetime.now()
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("Answer"):
                                results["records"][record_type] = [
                                    {
                                        "data": answer.get("data"),
                                        "ttl": answer.get("TTL"),
                                        "type": answer.get("type")
                                    }
                                    for answer in data["Answer"]
                                ]
                                
                        # Metriche performance
                        query_time = (end_time - start_time).total_seconds() * 1000
                        if "query_times" not in results["performance_metrics"]:
                            results["performance_metrics"]["query_times"] = {}
                        results["performance_metrics"]["query_times"][record_type] = f"{query_time:.2f}ms"
                        
                    except Exception as e:
                        results["records"][record_type] = {"error": str(e)}
                
                # Analisi sicurezza DNS
                results["security_analysis"] = await self._analyze_dns_security(domain, results["records"])
                
                # Controlli aggiuntivi
                results["domain_validation"] = self._validate_domain_structure(domain)
                results["nameserver_analysis"] = await self._analyze_nameservers(client, domain)
                
            return {"success": True, "analysis": results}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _analyze_dns_security(self, domain: str, records: Dict) -> Dict[str, Any]:
        """Analizza aspetti di sicurezza DNS."""
        security_issues = []
        recommendations = []
        
        # Controlla SPF
        txt_records = records.get("TXT", {})
        has_spf = False
        if isinstance(txt_records, list):
            for record in txt_records:
                if record.get("data", "").startswith("v=spf1"):
                    has_spf = True
                    break
        
        if not has_spf:
            security_issues.append("No SPF record found")
            recommendations.append("Add SPF record to prevent email spoofing")
        
        # Controlla DMARC
        has_dmarc = False
        if isinstance(txt_records, list):
            for record in txt_records:
                if record.get("data", "").startswith("v=DMARC1"):
                    has_dmarc = True
                    break
        
        if not has_dmarc:
            security_issues.append("No DMARC record found")
            recommendations.append("Implement DMARC for email authentication")
        
        # Controlla CAA
        caa_records = records.get("CAA", {})
        if not caa_records or isinstance(caa_records, dict) and "error" in caa_records:
            security_issues.append("No CAA records found")
            recommendations.append("Add CAA records to control certificate issuance")
        
        return {
            "security_score": max(0, 100 - len(security_issues) * 25),
            "issues": security_issues,
            "recommendations": recommendations,
            "has_email_security": has_spf and has_dmarc
        }

    def _validate_domain_structure(self, domain: str) -> Dict[str, Any]:
        """Valida la struttura del dominio."""
        issues = []
        
        if len(domain) > 253:
            issues.append("Domain name too long (>253 characters)")
        
        if domain.startswith("-") or domain.endswith("-"):
            issues.append("Domain cannot start or end with hyphen")
        
        if ".." in domain:
            issues.append("Domain contains consecutive dots")
        
        # Controlla TLD validity
        parts = domain.split(".")
        if len(parts) < 2:
            issues.append("Invalid domain structure")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "subdomain_count": len(parts) - 2,
            "tld": parts[-1] if parts else None
        }

    @mcp.tool()
    def cloud_cost_optimizer(current_usage: Dict[str, Any], optimization_target: str = "cost") -> Dict[str, Any]:
        """
        Analizza e ottimizza i costi cloud con raccomandazioni specifiche.
        
        Args:
            current_usage: Utilizzo attuale {provider, services: [{type, size, hours, region}]}
            optimization_target: Target di ottimizzazione (cost, performance, balanced)
        """
        try:
            results = {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "optimization_target": optimization_target,
                "current_costs": {},
                "optimizations": [],
                "potential_savings": 0,
                "recommendations": []
            }
            
            # Calcola costi attuali
            total_current_cost = 0
            
            for service in current_usage.get("services", []):
                service_cost = self._calculate_service_cost(service)
                total_current_cost += service_cost["total_cost"]
                
                results["current_costs"][f"{service['type']}_{service.get('size', 'unknown')}"] = service_cost
                
                # Trova ottimizzazioni
                optimizations = self._find_cost_optimizations(service, optimization_target)
                results["optimizations"].extend(optimizations)
            
            results["current_total_cost"] = total_current_cost
            
            # Calcola risparmi potenziali
            potential_savings = sum(opt["monthly_savings"] for opt in results["optimizations"])
            results["potential_savings"] = potential_savings
            results["savings_percentage"] = (potential_savings / total_current_cost * 100) if total_current_cost > 0 else 0
            
            # Raccomandazioni generali
            results["recommendations"] = self._generate_cost_recommendations(current_usage, results["optimizations"])
            
            return {"success": True, "optimization_analysis": results}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_service_cost(self, service: Dict[str, Any]) -> Dict[str, float]:
        """Calcola il costo di un servizio specifico."""
        # Prezzi approssimativi aggiornati per 2024
        pricing_matrix = {
            "compute": {
                "t2.micro": 0.0116, "t2.small": 0.023, "t2.medium": 0.046,
                "t3.small": 0.021, "t3.medium": 0.042, "t3.large": 0.083,
                "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384
            },
            "storage": {
                "gp2": 0.10, "gp3": 0.08, "io1": 0.125, "io2": 0.125,
                "standard": 0.045, "ia": 0.025, "glacier": 0.004
            },
            "database": {
                "db.t3.micro": 0.017, "db.t3.small": 0.034, "db.t3.medium": 0.068,
                "db.r5.large": 0.24, "db.r5.xlarge": 0.48
            },
            "bandwidth": {"outbound": 0.09, "inbound": 0.0, "cloudfront": 0.085}
        }
        
        service_type = service.get("type", "compute")
        size = service.get("size", "t2.micro")
        hours = service.get("hours", 730)  # Default: full month
        
        hourly_rate = pricing_matrix.get(service_type, {}).get(size, 0.05)
        
        if service_type == "storage":
            # Storage is typically priced per GB-month
            gb_usage = service.get("gb", 100)
            total_cost = hourly_rate * gb_usage
        else:
            total_cost = hourly_rate * hours
        
        return {
            "hourly_rate": hourly_rate,
            "usage_hours": hours,
            "total_cost": total_cost,
            "service_type": service_type,
            "size": size
        }

    def _find_cost_optimizations(self, service: Dict[str, Any], target: str) -> List[Dict[str, Any]]:
        """Trova ottimizzazioni per un servizio specifico."""
        optimizations = []
        service_type = service.get("type", "compute")
        current_size = service.get("size", "t2.micro")
        utilization = service.get("utilization", 70)  # Default 70%
        
        # Ottimizzazione per sottoutilizzo
        if utilization < 50 and service_type == "compute":
            # Suggerisci downsize
            downsized_options = {
                "t3.medium": "t3.small",
                "t3.large": "t3.medium",
                "m5.xlarge": "m5.large"
            }
            
            if current_size in downsized_options:
                new_size = downsized_options[current_size]
                current_cost = self._calculate_service_cost(service)["total_cost"]
                
                optimized_service = service.copy()
                optimized_service["size"] = new_size
                new_cost = self._calculate_service_cost(optimized_service)["total_cost"]
                
                savings = current_cost - new_cost
                
                optimizations.append({
                    "type": "downsize",
                    "description": f"Downsize {current_size} to {new_size}",
                    "reason": f"Low utilization ({utilization}%)",
                    "monthly_savings": savings,
                    "confidence": "high" if utilization < 30 else "medium"
                })
        
        # Ottimizzazione Reserved Instances
        if service_type == "compute" and service.get("hours", 730) > 500:
            ri_discount = 0.30  # 30% discount for 1-year RI
            current_cost = self._calculate_service_cost(service)["total_cost"]
            savings = current_cost * ri_discount
            
            optimizations.append({
                "type": "reserved_instance",
                "description": "Purchase 1-year Reserved Instance",
                "reason": "High usage hours justify RI purchase",
                "monthly_savings": savings,
                "confidence": "high"
            })
        
        # Ottimizzazione storage
        if service_type == "storage" and current_size == "gp2":
            gp3_service = service.copy()
            gp3_service["size"] = "gp3"
            current_cost = self._calculate_service_cost(service)["total_cost"]
            new_cost = self._calculate_service_cost(gp3_service)["total_cost"]
            savings = current_cost - new_cost
            
            if savings > 0:
                optimizations.append({
                    "type": "storage_upgrade",
                    "description": "Migrate from gp2 to gp3",
                    "reason": "Better performance at lower cost",
                    "monthly_savings": savings,
                    "confidence": "high"
                })
        
        return optimizations

    def _generate_cost_recommendations(self, usage: Dict[str, Any], optimizations: List[Dict[str, Any]]) -> List[str]:
        """Genera raccomandazioni generali di ottimizzazione."""
        recommendations = []
        
        if len(optimizations) > 3:
            recommendations.append("Multiple optimization opportunities found - prioritize by confidence level")
        
        if any(opt["type"] == "reserved_instance" for opt in optimizations):
            recommendations.append("Consider Reserved Instances for predictable workloads")
        
        if any(opt["type"] == "downsize" for opt in optimizations):
            recommendations.append("Monitor resource utilization regularly to identify underused instances")
        
        recommendations.extend([
            "Implement auto-scaling to match demand",
            "Use spot instances for fault-tolerant workloads",
            "Review and cleanup unused resources monthly",
            "Consider multi-cloud strategies for cost optimization"
        ])
        
        return recommendations

    @mcp.tool()
    def infrastructure_security_audit(config: Dict[str, Any], compliance_framework: str = "general") -> Dict[str, Any]:
        """
        Audit di sicurezza completo per infrastrutture cloud.
        
        Args:
            config: Configurazione infrastruttura da auditare
            compliance_framework: Framework di compliance (general, pci-dss, hipaa, sox, gdpr)
        """
        try:
            audit_results = {
                "audit_timestamp": datetime.now(timezone.utc).isoformat(),
                "compliance_framework": compliance_framework,
                "security_score": 0,
                "findings": {
                    "critical": [],
                    "high": [],
                    "medium": [],
                    "low": [],
                    "info": []
                },
                "compliance_status": {},
                "remediation_plan": []
            }
            
            # Controlli di sicurezza generali
            self._audit_network_security(config, audit_results)
            self._audit_access_controls(config, audit_results)
            self._audit_encryption(config, audit_results)
            self._audit_logging_monitoring(config, audit_results)
            
            # Controlli specifici per compliance
            if compliance_framework != "general":
                self._audit_compliance_specific(config, audit_results, compliance_framework)
            
            # Calcola security score
            finding_weights = {"critical": -25, "high": -15, "medium": -10, "low": -5, "info": 0}
            total_deductions = sum(
                len(findings) * weight 
                for severity, findings in audit_results["findings"].items()
                for weight_severity, weight in finding_weights.items()
                if severity == weight_severity
            )
            
            audit_results["security_score"] = max(0, 100 + total_deductions)
            
            # Piano di remediation prioritizzato
            audit_results["remediation_plan"] = self._create_remediation_plan(audit_results["findings"])
            
            return {"success": True, "security_audit": audit_results}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _audit_network_security(self, config: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Audit della sicurezza di rete."""
        # Controlla security groups aperti
        security_groups = config.get("security_groups", [])
        for sg in security_groups:
            rules = sg.get("rules", [])
            for rule in rules:
                if rule.get("cidr") == "0.0.0.0/0" and rule.get("port") != 80 and rule.get("port") != 443:
                    results["findings"]["critical"].append({
                        "type": "open_security_group",
                        "description": f"Security group allows all traffic on port {rule.get('port')}",
                        "resource": sg.get("name", "unknown"),
                        "recommendation": "Restrict access to specific IP ranges"
                    })
        
        # Controlla VPC configuration
        vpcs = config.get("vpcs", [])
        for vpc in vpcs:
            if not vpc.get("flow_logs_enabled", False):
                results["findings"]["medium"].append({
                    "type": "missing_flow_logs",
                    "description": "VPC Flow Logs not enabled",
                    "resource": vpc.get("name", "unknown"),
                    "recommendation": "Enable VPC Flow Logs for network monitoring"
                })

    def _audit_access_controls(self, config: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Audit dei controlli di accesso."""
        # Controlla IAM policies
        iam_policies = config.get("iam_policies", [])
        for policy in iam_policies:
            statements = policy.get("statements", [])
            for statement in statements:
                if statement.get("action") == "*" and statement.get("resource") == "*":
                    results["findings"]["critical"].append({
                        "type": "overprivileged_policy",
                        "description": "IAM policy grants full access to all resources",
                        "resource": policy.get("name", "unknown"),
                        "recommendation": "Apply principle of least privilege"
                    })
        
        # Controlla MFA
        users = config.get("users", [])
        for user in users:
            if not user.get("mfa_enabled", False):
                results["findings"]["high"].append({
                    "type": "missing_mfa",
                    "description": "User does not have MFA enabled",
                    "resource": user.get("username", "unknown"),
                    "recommendation": "Enable MFA for all users"
                })

    def _audit_encryption(self, config: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Audit della crittografia."""
        # Controlla encryption at rest
        storage_volumes = config.get("storage_volumes", [])
        for volume in storage_volumes:
            if not volume.get("encrypted", False):
                results["findings"]["high"].append({
                    "type": "unencrypted_storage",
                    "description": "Storage volume is not encrypted",
                    "resource": volume.get("name", "unknown"),
                    "recommendation": "Enable encryption at rest"
                })
        
        # Controlla SSL/TLS
        load_balancers = config.get("load_balancers", [])
        for lb in load_balancers:
            listeners = lb.get("listeners", [])
            for listener in listeners:
                if listener.get("protocol") == "HTTP":
                    results["findings"]["medium"].append({
                        "type": "unencrypted_traffic",
                        "description": "Load balancer accepts HTTP traffic",
                        "resource": lb.get("name", "unknown"),
                        "recommendation": "Redirect HTTP to HTTPS"
                    })

    def _audit_logging_monitoring(self, config: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Audit di logging e monitoring."""
        monitoring_config = config.get("monitoring", {})
        
        if not monitoring_config.get("cloudtrail_enabled", False):
            results["findings"]["high"].append({
                "type": "missing_audit_logs",
                "description": "CloudTrail audit logging not enabled",
                "resource": "account",
                "recommendation": "Enable CloudTrail for audit logging"
            })
        
        if not monitoring_config.get("alerts_configured", False):
            results["findings"]["medium"].append({
                "type": "missing_alerts",
                "description": "Security alerts not configured",
                "resource": "monitoring",
                "recommendation": "Configure security event alerts"
            })

    def _audit_compliance_specific(self, config: Dict[str, Any], results: Dict[str, Any], framework: str) -> None:
        """Audit specifico per framework di compliance."""
        compliance_checks = {
            "pci-dss": [
                ("network_segmentation", "PCI-DSS requires network segmentation"),
                ("encryption_key_management", "PCI-DSS requires proper key management"),
                ("access_logging", "PCI-DSS requires comprehensive access logging")
            ],
            "hipaa": [
                ("data_encryption", "HIPAA requires encryption of PHI"),
                ("access_controls", "HIPAA requires role-based access controls"),
                ("audit_logging", "HIPAA requires audit logging")
            ],
            "gdpr": [
                ("data_retention", "GDPR requires data retention policies"),
                ("data_encryption", "GDPR requires encryption of personal data"),
                ("access_rights", "GDPR requires data subject access rights")
            ]
        }
        
        if framework in compliance_checks:
            for check_id, description in compliance_checks[framework]:
                # Simplified compliance check
                results["compliance_status"][check_id] = {
                    "status": "needs_review",
                    "description": description,
                    "framework": framework
                }

    def _create_remediation_plan(self, findings: Dict[str, List]) -> List[Dict[str, Any]]:
        """Crea un piano di remediation prioritizzato."""
        plan = []
        
        # Priorità: Critical > High > Medium > Low
        for severity in ["critical", "high", "medium", "low"]:
            for finding in findings.get(severity, []):
                priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
                
                plan.append({
                    "priority": priority_map[severity],
                    "severity": severity,
                    "issue": finding.get("description"),
                    "resource": finding.get("resource"),
                    "action": finding.get("recommendation"),
                    "estimated_effort": self._estimate_remediation_effort(finding.get("type"))
                })
        
        return sorted(plan, key=lambda x: x["priority"])

    def _estimate_remediation_effort(self, finding_type: str) -> str:
        """Stima lo sforzo per la remediation."""
        effort_map = {
            "open_security_group": "Low (1-2 hours)",
            "missing_mfa": "Medium (4-8 hours)",
            "overprivileged_policy": "High (1-2 days)",
            "unencrypted_storage": "Medium (4-8 hours)",
            "missing_audit_logs": "High (1-2 days)"
        }
        return effort_map.get(finding_type, "Medium (4-8 hours)")

    @mcp.tool()
    async def cloud_performance_monitor(endpoints: List[str], metrics: List[str] = None) -> Dict[str, Any]:
        """
        Monitoraggio avanzato delle performance cloud con metriche dettagliate.
        
        Args:
            endpoints: Lista di endpoint da monitorare
            metrics: Metriche da raccogliere (latency, availability, throughput, dns_timing)
        """
        try:
            if metrics is None:
                metrics = ["latency", "availability", "dns_timing"]
            
            results = {
                "monitoring_timestamp": datetime.now(timezone.utc).isoformat(),
                "endpoints": {},
                "summary": {
                    "total_endpoints": len(endpoints),
                    "healthy_endpoints": 0,
                    "average_response_time": 0,
                    "overall_availability": 0
                }
            }
            
            total_response_time = 0
            healthy_count = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in endpoints:
                    endpoint_results = await self._monitor_endpoint_performance(client, endpoint, metrics)
                    results["endpoints"][endpoint] = endpoint_results
                    
                    if endpoint_results.get("status") == "healthy":
                        healthy_count += 1
                    
                    response_time = endpoint_results.get("response_time_ms", 0)
                    if response_time > 0:
                        total_response_time += response_time
            
            # Calcola metriche summary
            results["summary"]["healthy_endpoints"] = healthy_count
            results["summary"]["average_response_time"] = total_response_time / len(endpoints) if endpoints else 0
            results["summary"]["overall_availability"] = (healthy_count / len(endpoints)) * 100 if endpoints else 0
            
            # Performance recommendations
            results["recommendations"] = self._generate_performance_recommendations(results["endpoints"])
            
            return {"success": True, "performance_monitoring": results}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _monitor_endpoint_performance(self, client: httpx.AsyncClient, endpoint: str, metrics: List[str]) -> Dict[str, Any]:
        """Monitora le performance di un singolo endpoint."""
        results = {
            "endpoint": endpoint,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # DNS timing
            if "dns_timing" in metrics:
                dns_start = datetime.now()
                try:
                    parsed_url = urlparse(endpoint)
                    hostname = parsed_url.hostname
                    if hostname:
                        socket.gethostbyname(hostname)
                    dns_end = datetime.now()
                    results["dns_resolution_ms"] = (dns_end - dns_start).total_seconds() * 1000
                except Exception as e:
                    results["dns_error"] = str(e)
            
            # HTTP request timing
            if "latency" in metrics or "availability" in metrics:
                start_time = datetime.now()
                response = await client.get(endpoint, follow_redirects=True)
                end_time = datetime.now()
                
                response_time_ms = (end_time - start_time).total_seconds() * 1000
                results["response_time_ms"] = response_time_ms
                results["status_code"] = response.status_code
                results["status"] = "healthy" if response.status_code < 400 else "unhealthy"
                
                # Response headers analysis
                results["response_headers"] = dict(response.headers)
                results["content_length"] = len(response.content)
                
                # Security headers check
                security_headers = ["strict-transport-security", "x-frame-options", "x-content-type-options"]
                missing_headers = [h for h in security_headers if h not in response.headers]
                if missing_headers:
                    results["missing_security_headers"] = missing_headers
            
            # Throughput calculation (simplified)
            if "throughput" in metrics:
                content_size_kb = results.get("content_length", 0) / 1024
                response_time_s = results.get("response_time_ms", 1) / 1000
                results["throughput_kbps"] = content_size_kb / response_time_s if response_time_s > 0 else 0
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        
        return results

    def _generate_performance_recommendations(self, endpoints_data: Dict[str, Any]) -> List[str]:
        """Genera raccomandazioni per migliorare le performance."""
        recommendations = []
        
        # Analizza response times
        response_times = [
            data.get("response_time_ms", 0) 
            for data in endpoints_data.values() 
            if data.get("response_time_ms")
        ]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            
            if avg_response_time > 2000:
                recommendations.append("High average response time detected - consider CDN implementation")
            elif avg_response_time > 1000:
                recommendations.append("Response times could be improved - review server optimization")
        
        # Controlla missing security headers
        endpoints_with_missing_headers = [
            endpoint for endpoint, data in endpoints_data.items()
            if data.get("missing_security_headers")
        ]
        
        if endpoints_with_missing_headers:
            recommendations.append("Security headers missing on some endpoints - review security configuration")
        
        # DNS performance
        dns_times = [
            data.get("dns_resolution_ms", 0)
            for data in endpoints_data.values()
            if data.get("dns_resolution_ms")
        ]
        
        if dns_times and sum(dns_times) / len(dns_times) > 100:
            recommendations.append("Slow DNS resolution detected - consider DNS optimization")
        
        return recommendations

    @mcp.tool()
    def multi_cloud_migration_planner(current_setup: Dict[str, Any], target_provider: str, 
                                     migration_type: str = "lift_and_shift") -> Dict[str, Any]:
        """
        Pianifica migrazione multi-cloud con analisi di costi e compatibilità.
        
        Args:
            current_setup: Setup attuale con provider e risorse
            target_provider: Provider di destinazione (aws, azure, gcp)
            migration_type: Tipo migrazione (lift_and_shift, re_architect, hybrid)
        """
        try:
            migration_plan = {
                "migration_timestamp": datetime.now(timezone.utc).isoformat(),
                "source_provider": current_setup.get("provider"),
                "target_provider": target_provider,
                "migration_type": migration_type,
                "resource_mapping": {},
                "estimated_costs": {},
                "migration_phases": [],
                "risks_and_mitigations": [],
                "timeline_estimate": ""
            }
            
            # Mapping delle risorse
            migration_plan["resource_mapping"] = self._map_resources_across_providers(
                current_setup.get("resources", []), target_provider
            )
            
            # Stima dei costi
            migration_plan["estimated_costs"] = self._estimate_migration_costs(
                current_setup, target_provider, migration_type
            )
            
            # Piano di migrazione per fasi
            migration_plan["migration_phases"] = self._create_migration_phases(
                current_setup.get("resources", []), migration_type
            )
            
            # Analisi rischi
            migration_plan["risks_and_mitigations"] = self._analyze_migration_risks(
                current_setup, target_provider, migration_type
            )
            
            # Stima timeline
            migration_plan["timeline_estimate"] = self._estimate_migration_timeline(
                len(current_setup.get("resources", [])), migration_type
            )
            
            return {"success": True, "migration_plan": migration_plan}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _map_resources_across_providers(self, resources: List[Dict], target_provider: str) -> Dict[str, Any]:
        """Mappa le risorse tra provider cloud."""
        resource_mapping = {
            "aws_to_azure": {
                "ec2": "virtual_machines",
                "s3": "blob_storage", 
                "rds": "sql_database",
                "lambda": "functions",
                "vpc": "virtual_network"
            },
            "aws_to_gcp": {
                "ec2": "compute_engine",
                "s3": "cloud_storage",
                "rds": "cloud_sql", 
                "lambda": "cloud_functions",
                "vpc": "vpc_network"
            },
            "azure_to_aws": {
                "virtual_machines": "ec2",
                "blob_storage": "s3",
                "sql_database": "rds",
                "functions": "lambda"
            }
        }
        
        source_provider = "aws"  # Simplified - would detect from current_setup
        mapping_key = f"{source_provider}_to_{target_provider}"
        mapping = resource_mapping.get(mapping_key, {})
        
        mapped_resources = {}
        for resource in resources:
            resource_type = resource.get("type")
            target_type = mapping.get(resource_type, resource_type)
            
            mapped_resources[resource.get("name", "unknown")] = {
                "source_type": resource_type,
                "target_type": target_type,
                "compatibility": "high" if target_type != resource_type else "direct",
                "migration_complexity": self._assess_migration_complexity(resource_type, target_type)
            }
        
        return mapped_resources

    def _estimate_migration_costs(self, current_setup: Dict, target_provider: str, migration_type: str) -> Dict[str, float]:
        """Stima i costi di migrazione."""
        base_costs = {
            "assessment_and_planning": 5000,
            "data_transfer": 1000,  # Per TB
            "downtime_cost": 2000,  # Per ora
            "testing_and_validation": 3000,
            "training": 2000
        }
        
        # Fattori moltiplicativi basati sul tipo di migrazione
        complexity_multipliers = {
            "lift_and_shift": 1.0,
            "re_architect": 2.5,
            "hybrid": 1.8
        }
        
        multiplier = complexity_multipliers.get(migration_type, 1.0)
        resource_count = len(current_setup.get("resources", []))
        
        estimated_costs = {}
        for cost_type, base_cost in base_costs.items():
            estimated_costs[cost_type] = base_cost * multiplier * (1 + resource_count * 0.1)
        
        estimated_costs["total_estimated_cost"] = sum(estimated_costs.values())
        
        return estimated_costs

    def _create_migration_phases(self, resources: List[Dict], migration_type: str) -> List[Dict[str, Any]]:
        """Crea le fasi di migrazione."""
        phases = [
            {
                "phase": 1,
                "name": "Assessment and Planning",
                "duration_weeks": 2,
                "activities": [
                    "Inventory current resources",
                    "Assess dependencies",
                    "Create migration plan",
                    "Set up target environment"
                ]
            },
            {
                "phase": 2,
                "name": "Preparation",
                "duration_weeks": 3,
                "activities": [
                    "Set up networking",
                    "Configure security",
                    "Create backup strategies",
                    "Test migration tools"
                ]
            },
            {
                "phase": 3,
                "name": "Migration Execution",
                "duration_weeks": 4 if migration_type == "re_architect" else 2,
                "activities": [
                    "Migrate non-critical workloads",
                    "Migrate critical workloads",
                    "Data synchronization",
                    "Switch over"
                ]
            },
            {
                "phase": 4,
                "name": "Validation and Optimization",
                "duration_weeks": 2,
                "activities": [
                    "Performance testing",
                    "Security validation",
                    "Cost optimization",
                    "Documentation update"
                ]
            }
        ]
        
        return phases

    def _analyze_migration_risks(self, current_setup: Dict, target_provider: str, migration_type: str) -> List[Dict[str, str]]:
        """Analizza i rischi della migrazione."""
        risks = [
            {
                "risk": "Data Loss",
                "probability": "Medium",
                "impact": "High",
                "mitigation": "Comprehensive backup and testing strategy"
            },
            {
                "risk": "Extended Downtime",
                "probability": "Medium" if migration_type == "lift_and_shift" else "High",
                "impact": "High",
                "mitigation": "Phased migration with rollback procedures"
            },
            {
                "risk": "Cost Overrun",
                "probability": "High",
                "impact": "Medium",
                "mitigation": "Detailed cost monitoring and budget controls"
            },
            {
                "risk": "Performance Degradation",
                "probability": "Low" if migration_type == "re_architect" else "Medium",
                "impact": "Medium",
                "mitigation": "Thorough performance testing and optimization"
            }
        ]
        
        return risks

    def _estimate_migration_timeline(self, resource_count: int, migration_type: str) -> str:
        """Stima la timeline di migrazione."""
        base_weeks = {
            "lift_and_shift": 8,
            "re_architect": 16,
            "hybrid": 12
        }
        
        base = base_weeks.get(migration_type, 8)
        additional_weeks = resource_count // 10  # 1 settimana extra ogni 10 risorse
        
        total_weeks = base + additional_weeks
        
        return f"{total_weeks} weeks ({total_weeks // 4} months)"

    def _assess_migration_complexity(self, source_type: str, target_type: str) -> str:
        """Valuta la complessità di migrazione per un tipo di risorsa."""
        if source_type == target_type:
            return "low"
        
        complex_migrations = {
            ("rds", "cloud_sql"): "medium",
            ("lambda", "cloud_functions"): "low",
            ("ec2", "compute_engine"): "medium"
        }
        
        return complex_migrations.get((source_type, target_type), "medium")