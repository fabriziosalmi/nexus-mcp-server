# -*- coding: utf-8 -*-
# tools/network_tools.py
import subprocess
import socket
import requests
import json
import logging
import time
import threading
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import ipaddress
import urllib.parse
import concurrent.futures

def register_tools(mcp):
    """Registra i tool di rete avanzati con l'istanza del server MCP."""
    logging.info("🌐 Registrazione tool-set: Network Tools")

    @mcp.tool()
    def ping_host(host: str, count: int = 4) -> Dict[str, Any]:
        """
        Esegue un ping verso un host specificato.
        
        Args:
            host: L'hostname o IP da pingare
            count: Numero di ping da inviare (default: 4)
        """
        try:
            result = subprocess.run(
                ['ping', '-c', str(count), host], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return {
                "host": host,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "packets_sent": count
            }
        except subprocess.TimeoutExpired:
            return {
                "host": host,
                "success": False,
                "error": "Timeout durante ping",
                "packets_sent": count
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e),
                "packets_sent": count
            }

    @mcp.tool()
    def dns_lookup(hostname: str, record_type: str = "A") -> Dict[str, Any]:
        """
        Esegue una lookup DNS per un hostname.
        
        Args:
            hostname: Il nome dell'host da risolvere
            record_type: Tipo di record DNS (A, AAAA, MX, NS, TXT)
        """
        try:
            import dns.resolver
            
            resolver = dns.resolver.Resolver()
            answers = resolver.resolve(hostname, record_type)
            
            results = []
            for answer in answers:
                results.append(str(answer))
            
            return {
                "hostname": hostname,
                "record_type": record_type,
                "success": True,
                "results": results,
                "count": len(results)
            }
        except ImportError:
            # Fallback usando socket per record A
            if record_type == "A":
                try:
                    ip = socket.gethostbyname(hostname)
                    return {
                        "hostname": hostname,
                        "record_type": record_type,
                        "success": True,
                        "results": [ip],
                        "count": 1
                    }
                except socket.gaierror as e:
                    return {
                        "hostname": hostname,
                        "record_type": record_type,
                        "success": False,
                        "error": str(e)
                    }
            else:
                return {
                    "hostname": hostname,
                    "record_type": record_type,
                    "success": False,
                    "error": "dnspython non installato - solo record A supportati"
                }
        except Exception as e:
            return {
                "hostname": hostname,
                "record_type": record_type,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def port_scan(host: str, ports: List[int]) -> Dict[str, Any]:
        """
        Scansiona porte specifiche su un host.
        
        Args:
            host: L'hostname o IP da scansionare
            ports: Lista delle porte da controllare
        """
        try:
            open_ports = []
            closed_ports = []
            
            for port in ports[:20]:  # Limita a 20 porte per sicurezza
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                
                try:
                    result = sock.connect_ex((host, port))
                    if result == 0:
                        open_ports.append(port)
                    else:
                        closed_ports.append(port)
                except Exception:
                    closed_ports.append(port)
                finally:
                    sock.close()
            
            return {
                "host": host,
                "scanned_ports": ports[:20],
                "open_ports": open_ports,
                "closed_ports": closed_ports,
                "total_open": len(open_ports),
                "total_scanned": len(ports[:20])
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def traceroute(host: str, max_hops: int = 15) -> Dict[str, Any]:
        """
        Esegue un traceroute verso un host.
        
        Args:
            host: L'hostname o IP di destinazione
            max_hops: Numero massimo di hop (default: 15)
        """
        try:
            result = subprocess.run(
                ['traceroute', '-m', str(max_hops), host], 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            return {
                "host": host,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "max_hops": max_hops
            }
        except subprocess.TimeoutExpired:
            return {
                "host": host,
                "success": False,
                "error": "Timeout durante traceroute",
                "max_hops": max_hops
            }
        except FileNotFoundError:
            return {
                "host": host,
                "success": False,
                "error": "Comando traceroute non disponibile",
                "max_hops": max_hops
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e),
                "max_hops": max_hops
            }

    @mcp.tool()
    def whois_lookup(domain: str) -> Dict[str, Any]:
        """
        Esegue una lookup whois per un dominio.
        
        Args:
            domain: Il dominio da controllare
        """
        try:
            result = subprocess.run(
                ['whois', domain], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return {
                "domain": domain,
                "success": result.returncode == 0,
                "whois_data": result.stdout,
                "error": result.stderr if result.stderr else None
            }
        except subprocess.TimeoutExpired:
            return {
                "domain": domain,
                "success": False,
                "error": "Timeout durante whois lookup"
            }
        except FileNotFoundError:
            return {
                "domain": domain,
                "success": False,
                "error": "Comando whois non disponibile"
            }
        except Exception as e:
            return {
                "domain": domain,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def check_website_status(url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Controlla lo status di un sito web.
        
        Args:
            url: URL del sito da controllare
            timeout: Timeout in secondi (default: 10)
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content),
                "headers": dict(response.headers),
                "final_url": response.url if response.url != url else None
            }
        except requests.exceptions.Timeout:
            return {
                "url": url,
                "success": False,
                "error": "Timeout durante connessione",
                "timeout": timeout
            }
        except requests.exceptions.ConnectionError:
            return {
                "url": url,
                "success": False,
                "error": "Impossibile connettersi al server"
            }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def get_public_ip() -> Dict[str, Any]:
        """
        Ottiene l'indirizzo IP pubblico corrente.
        """
        try:
            # Prova diversi servizi
            services = [
                'https://api.ipify.org?format=json',
                'https://httpbin.org/ip',
                'https://api.ip.sb/ip'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        if 'ipify' in service:
                            data = response.json()
                            return {
                                "success": True,
                                "public_ip": data["ip"],
                                "service": service
                            }
                        elif 'httpbin' in service:
                            data = response.json()
                            return {
                                "success": True,
                                "public_ip": data["origin"],
                                "service": service
                            }
                        elif 'ip.sb' in service:
                            return {
                                "success": True,
                                "public_ip": response.text.strip(),
                                "service": service
                            }
                except:
                    continue
            
            return {
                "success": False,
                "error": "Nessun servizio IP disponibile"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def network_speed_test(test_type: str = "download", duration: int = 10, 
                          server_url: str = None) -> Dict[str, Any]:
        """
        Esegue test velocità di rete (download/upload).
        
        Args:
            test_type: Tipo test (download, upload, both)
            duration: Durata test in secondi (default: 10)
            server_url: URL server test personalizzato
        """
        try:
            if duration < 5 or duration > 60:
                return {"success": False, "error": "Duration must be between 5 and 60 seconds"}
            
            speed_results = {
                "test_type": test_type,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "results": {}
            }
            
            # Default test servers
            test_servers = {
                "download": server_url or "http://speedtest.ftp.otenet.gr/files/test100k.db",
                "upload": server_url or "https://httpbin.org/post"
            }
            
            if test_type in ["download", "both"]:
                download_result = _perform_download_test(test_servers["download"], duration)
                speed_results["results"]["download"] = download_result
            
            if test_type in ["upload", "both"]:
                upload_result = _perform_upload_test(test_servers["upload"], duration)
                speed_results["results"]["upload"] = upload_result
            
            # Network quality metrics
            if test_type == "both":
                quality_metrics = _measure_network_quality("8.8.8.8", samples=10)
                speed_results["network_quality"] = quality_metrics
            
            return speed_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def monitor_network_interfaces(duration: int = 30, interval: int = 5) -> Dict[str, Any]:
        """
        Monitora interfacce di rete e raccoglie statistiche.
        
        Args:
            duration: Durata monitoraggio in secondi (default: 30)
            interval: Intervallo campionamento in secondi (default: 5)
        """
        try:
            if duration < 10 or duration > 300:
                return {"success": False, "error": "Duration must be between 10 and 300 seconds"}
            
            monitoring_results = {
                "duration": duration,
                "interval": interval,
                "start_time": datetime.now().isoformat(),
                "interfaces": {},
                "statistics": {}
            }
            
            # Get initial network stats
            initial_stats = _get_network_interface_stats()
            
            # Monitor for specified duration
            samples = []
            for i in range(duration // interval):
                time.sleep(interval)
                current_stats = _get_network_interface_stats()
                
                # Calculate deltas
                sample = {
                    "timestamp": datetime.now().isoformat(),
                    "interfaces": {}
                }
                
                for interface, stats in current_stats.items():
                    if interface in initial_stats:
                        initial = initial_stats[interface]
                        sample["interfaces"][interface] = {
                            "bytes_sent_delta": stats.get("bytes_sent", 0) - initial.get("bytes_sent", 0),
                            "bytes_recv_delta": stats.get("bytes_recv", 0) - initial.get("bytes_recv", 0),
                            "packets_sent_delta": stats.get("packets_sent", 0) - initial.get("packets_sent", 0),
                            "packets_recv_delta": stats.get("packets_recv", 0) - initial.get("packets_recv", 0),
                            "errors_in": stats.get("errin", 0),
                            "errors_out": stats.get("errout", 0),
                            "drops_in": stats.get("dropin", 0),
                            "drops_out": stats.get("dropout", 0)
                        }
                
                samples.append(sample)
                initial_stats = current_stats  # Update for next iteration
            
            # Calculate aggregated statistics
            monitoring_results["samples"] = samples
            monitoring_results["statistics"] = _calculate_interface_statistics(samples)
            
            return monitoring_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def advanced_dns_analysis(domain: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analisi DNS avanzata con propagazione e performance.
        
        Args:
            domain: Dominio da analizzare
            analysis_type: Tipo analisi (basic, comprehensive, propagation)
        """
        try:
            dns_results = {
                "domain": domain,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "dns_records": {},
                "dns_servers": {},
                "propagation_check": {},
                "performance_metrics": {}
            }
            
            if analysis_type in ["basic", "comprehensive"]:
                # Enhanced DNS record lookup
                dns_records = _perform_comprehensive_dns_lookup(domain)
                dns_results["dns_records"] = dns_records
            
            if analysis_type in ["comprehensive", "propagation"]:
                # DNS propagation check across multiple servers
                propagation_results = _check_dns_propagation(domain)
                dns_results["propagation_check"] = propagation_results
                
                # DNS server performance testing
                dns_performance = _test_dns_server_performance(domain)
                dns_results["performance_metrics"] = dns_performance
            
            if analysis_type == "comprehensive":
                # DNS security analysis
                security_analysis = _analyze_dns_security(domain)
                dns_results["security_analysis"] = security_analysis
                
                # Historical DNS data (if available)
                historical_data = _get_dns_historical_data(domain)
                dns_results["historical_data"] = historical_data
            
            return dns_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def network_quality_assessment(target_hosts: List[str], test_duration: int = 60) -> Dict[str, Any]:
        """
        Valutazione qualità rete con metriche latenza, jitter, packet loss.
        
        Args:
            target_hosts: Lista host da testare
            test_duration: Durata test in secondi (default: 60)
        """
        try:
            if len(target_hosts) > 10:
                return {"success": False, "error": "Too many target hosts (max 10)"}
            
            quality_results = {
                "target_hosts": target_hosts,
                "test_duration": test_duration,
                "timestamp": datetime.now().isoformat(),
                "quality_metrics": {},
                "overall_assessment": {}
            }
            
            # Test each target host
            for host in target_hosts:
                host_metrics = _comprehensive_quality_test(host, test_duration)
                quality_results["quality_metrics"][host] = host_metrics
            
            # Calculate overall network quality assessment
            quality_results["overall_assessment"] = _calculate_overall_quality(
                quality_results["quality_metrics"]
            )
            
            return quality_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def ssl_tls_connection_test(hostname: str, port: int = 443, 
                               test_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Test connessione SSL/TLS con analisi dettagliata.
        
        Args:
            hostname: Hostname da testare
            port: Porta SSL/TLS (default: 443)
            test_type: Tipo test (basic, comprehensive, security)
        """
        try:
            ssl_results = {
                "hostname": hostname,
                "port": port,
                "test_type": test_type,
                "timestamp": datetime.now().isoformat(),
                "connection_test": {},
                "certificate_info": {},
                "security_analysis": {}
            }
            
            # Basic SSL connection test
            connection_result = _test_ssl_connection(hostname, port)
            ssl_results["connection_test"] = connection_result
            
            if test_type in ["comprehensive", "security"] and connection_result.get("success"):
                # Certificate analysis
                cert_info = _analyze_ssl_certificate(hostname, port)
                ssl_results["certificate_info"] = cert_info
            
            if test_type == "security":
                # SSL/TLS security assessment
                security_assessment = _assess_ssl_security(hostname, port)
                ssl_results["security_analysis"] = security_assessment
            
            if test_type in ["comprehensive", "security"]:
                # SSL/TLS performance metrics
                performance_metrics = _measure_ssl_performance(hostname, port)
                ssl_results["performance_metrics"] = performance_metrics
            
            return ssl_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def network_troubleshooting(target: str, issue_type: str = "connectivity") -> Dict[str, Any]:
        """
        Diagnosi e troubleshooting problemi di rete.
        
        Args:
            target: Target da diagnosticare (IP, hostname, URL)
            issue_type: Tipo problema (connectivity, performance, dns, ssl)
        """
        try:
            troubleshooting_results = {
                "target": target,
                "issue_type": issue_type,
                "timestamp": datetime.now().isoformat(),
                "diagnostic_tests": {},
                "findings": [],
                "recommendations": []
            }
            
            if issue_type in ["connectivity", "all"]:
                # Connectivity diagnostics
                connectivity_tests = _diagnose_connectivity(target)
                troubleshooting_results["diagnostic_tests"]["connectivity"] = connectivity_tests
                troubleshooting_results["findings"].extend(connectivity_tests.get("issues", []))
            
            if issue_type in ["performance", "all"]:
                # Performance diagnostics
                performance_tests = _diagnose_performance(target)
                troubleshooting_results["diagnostic_tests"]["performance"] = performance_tests
                troubleshooting_results["findings"].extend(performance_tests.get("issues", []))
            
            if issue_type in ["dns", "all"]:
                # DNS diagnostics
                dns_tests = _diagnose_dns_issues(target)
                troubleshooting_results["diagnostic_tests"]["dns"] = dns_tests
                troubleshooting_results["findings"].extend(dns_tests.get("issues", []))
            
            if issue_type in ["ssl", "all"]:
                # SSL/TLS diagnostics
                ssl_tests = _diagnose_ssl_issues(target)
                troubleshooting_results["diagnostic_tests"]["ssl"] = ssl_tests
                troubleshooting_results["findings"].extend(ssl_tests.get("issues", []))
            
            # Generate recommendations based on findings
            troubleshooting_results["recommendations"] = _generate_troubleshooting_recommendations(
                troubleshooting_results["findings"]
            )
            
            return troubleshooting_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_ip_geolocation(ip_address: str = None) -> Dict[str, Any]:
        """
        Ottiene informazioni geolocation e ASN per indirizzo IP.
        
        Args:
            ip_address: IP da analizzare (default: IP pubblico corrente)
        """
        try:
            if not ip_address:
                # Get current public IP
                public_ip_result = get_public_ip()
                if not public_ip_result.get("success"):
                    return {"success": False, "error": "Could not determine public IP"}
                ip_address = public_ip_result["public_ip"]
            
            # Validate IP address
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                return {"success": False, "error": "Invalid IP address format"}
            
            geo_results = {
                "ip_address": ip_address,
                "timestamp": datetime.now().isoformat(),
                "geolocation": {},
                "asn_info": {},
                "security_info": {}
            }
            
            # Get geolocation data
            geo_data = _get_ip_geolocation_data(ip_address)
            geo_results["geolocation"] = geo_data
            
            # Get ASN information
            asn_data = _get_asn_information(ip_address)
            geo_results["asn_info"] = asn_data
            
            # Basic security checks
            security_data = _check_ip_security(ip_address)
            geo_results["security_info"] = security_data
            
            return geo_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def batch_network_operations(operations: List[Dict[str, Any]], 
                                max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Esegue operazioni di rete in batch con processing parallelo.
        
        Args:
            operations: Lista operazioni da eseguire
            max_concurrent: Massimo operazioni concorrenti (default: 5)
        """
        try:
            if len(operations) > 50:
                return {"success": False, "error": "Too many operations (max 50)"}
            
            if max_concurrent > 10:
                max_concurrent = 10
            
            batch_results = {
                "total_operations": len(operations),
                "max_concurrent": max_concurrent,
                "start_time": datetime.now().isoformat(),
                "results": [],
                "summary": {}
            }
            
            # Execute operations in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_operation = {}
                
                for i, operation in enumerate(operations):
                    operation_type = operation.get("type")
                    operation_args = operation.get("args", {})
                    
                    future = executor.submit(_execute_network_operation, operation_type, operation_args)
                    future_to_operation[future] = {"index": i, "operation": operation}
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_operation):
                    operation_info = future_to_operation[future]
                    try:
                        result = future.result()
                        batch_results["results"].append({
                            "index": operation_info["index"],
                            "operation": operation_info["operation"],
                            "result": result,
                            "success": True
                        })
                    except Exception as e:
                        batch_results["results"].append({
                            "index": operation_info["index"],
                            "operation": operation_info["operation"],
                            "error": str(e),
                            "success": False
                        })
            
            # Calculate summary statistics
            successful_ops = sum(1 for r in batch_results["results"] if r["success"])
            batch_results["summary"] = {
                "successful_operations": successful_ops,
                "failed_operations": len(operations) - successful_ops,
                "success_rate": round((successful_ops / len(operations)) * 100, 2),
                "execution_time": (datetime.now() - datetime.fromisoformat(batch_results["start_time"])).total_seconds()
            }
            
            return batch_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Enhanced helper functions
    def _perform_download_test(url: str, duration: int) -> Dict[str, Any]:
        """Perform download speed test."""
        try:
            start_time = time.time()
            response = requests.get(url, stream=True, timeout=duration + 5)
            
            total_bytes = 0
            chunk_times = []
            
            for chunk in response.iter_content(chunk_size=8192):
                if time.time() - start_time >= duration:
                    break
                
                chunk_start = time.time()
                total_bytes += len(chunk)
                chunk_times.append(time.time() - chunk_start)
            
            elapsed_time = time.time() - start_time
            
            # Calculate speeds
            bytes_per_second = total_bytes / elapsed_time if elapsed_time > 0 else 0
            mbps = (bytes_per_second * 8) / (1024 * 1024)  # Convert to Mbps
            
            return {
                "success": True,
                "total_bytes": total_bytes,
                "elapsed_time": elapsed_time,
                "bytes_per_second": bytes_per_second,
                "mbps": round(mbps, 2),
                "average_chunk_time": statistics.mean(chunk_times) if chunk_times else 0
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _perform_upload_test(url: str, duration: int) -> Dict[str, Any]:
        """Perform upload speed test."""
        try:
            # Generate test data
            test_data = b'0' * 1024  # 1KB chunks
            
            start_time = time.time()
            total_bytes = 0
            upload_times = []
            
            while time.time() - start_time < duration:
                chunk_start = time.time()
                
                try:
                    response = requests.post(url, data=test_data, timeout=5)
                    if response.status_code == 200:
                        total_bytes += len(test_data)
                        upload_times.append(time.time() - chunk_start)
                except:
                    break
            
            elapsed_time = time.time() - start_time
            bytes_per_second = total_bytes / elapsed_time if elapsed_time > 0 else 0
            mbps = (bytes_per_second * 8) / (1024 * 1024)
            
            return {
                "success": True,
                "total_bytes": total_bytes,
                "elapsed_time": elapsed_time,
                "bytes_per_second": bytes_per_second,
                "mbps": round(mbps, 2),
                "average_upload_time": statistics.mean(upload_times) if upload_times else 0
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _measure_network_quality(target: str, samples: int = 10) -> Dict[str, Any]:
        """Measure network quality metrics."""
        try:
            latencies = []
            packet_loss = 0
            
            for i in range(samples):
                start_time = time.time()
                try:
                    # Simple TCP connection test
                    sock = socket.create_connection((target, 53), timeout=5)
                    sock.close()
                    latency = (time.time() - start_time) * 1000  # Convert to ms
                    latencies.append(latency)
                except:
                    packet_loss += 1
                
                time.sleep(0.1)  # Small delay between tests
            
            if latencies:
                avg_latency = statistics.mean(latencies)
                jitter = statistics.stdev(latencies) if len(latencies) > 1 else 0
            else:
                avg_latency = 0
                jitter = 0
            
            packet_loss_percent = (packet_loss / samples) * 100
            
            return {
                "average_latency_ms": round(avg_latency, 2),
                "jitter_ms": round(jitter, 2),
                "packet_loss_percent": round(packet_loss_percent, 2),
                "samples": samples,
                "successful_samples": len(latencies)
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_network_interface_stats() -> Dict[str, Any]:
        """Get network interface statistics."""
        try:
            import psutil
            
            interfaces = {}
            net_io = psutil.net_io_counters(pernic=True)
            
            for interface, stats in net_io.items():
                interfaces[interface] = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "packets_sent": stats.packets_sent,
                    "packets_recv": stats.packets_recv,
                    "errin": stats.errin,
                    "errout": stats.errout,
                    "dropin": stats.dropin,
                    "dropout": stats.dropout
                }
            
            return interfaces
        except ImportError:
            # Fallback to basic interface detection
            return {"error": "psutil not available - install for detailed interface statistics"}
        except Exception as e:
            return {"error": str(e)}

    def _comprehensive_quality_test(host: str, duration: int) -> Dict[str, Any]:
        """Comprehensive network quality test for a single host."""
        try:
            # Multiple quality measurements
            ping_results = []
            connection_results = []
            
            start_time = time.time()
            while time.time() - start_time < duration:
                # Ping test
                ping_start = time.time()
                try:
                    sock = socket.create_connection((host, 80), timeout=3)
                    sock.close()
                    ping_time = (time.time() - ping_start) * 1000
                    ping_results.append(ping_time)
                    connection_results.append(True)
                except:
                    connection_results.append(False)
                
                time.sleep(1)  # Wait between tests
            
            # Calculate metrics
            if ping_results:
                avg_latency = statistics.mean(ping_results)
                min_latency = min(ping_results)
                max_latency = max(ping_results)
                jitter = statistics.stdev(ping_results) if len(ping_results) > 1 else 0
            else:
                avg_latency = min_latency = max_latency = jitter = 0
            
            success_rate = (sum(connection_results) / len(connection_results)) * 100
            
            return {
                "host": host,
                "test_duration": duration,
                "average_latency_ms": round(avg_latency, 2),
                "min_latency_ms": round(min_latency, 2),
                "max_latency_ms": round(max_latency, 2),
                "jitter_ms": round(jitter, 2),
                "success_rate_percent": round(success_rate, 2),
                "total_tests": len(connection_results),
                "successful_tests": sum(connection_results)
            }
        except Exception as e:
            return {"host": host, "error": str(e)}

    def _execute_network_operation(operation_type: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single network operation."""
        try:
            if operation_type == "ping":
                return ping_host(args.get("host"), args.get("count", 4))
            elif operation_type == "dns_lookup":
                return dns_lookup(args.get("hostname"), args.get("record_type", "A"))
            elif operation_type == "port_scan":
                return port_scan(args.get("host"), args.get("ports", [80, 443]))
            elif operation_type == "website_status":
                return check_website_status(args.get("url"), args.get("timeout", 10))
            else:
                return {"success": False, "error": f"Unknown operation type: {operation_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}