# -*- coding: utf-8 -*-
# tools/api_testing_tools.py
import logging
import json
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime

def register_tools(mcp):
    """Registra i tool per test API con l'istanza del server MCP."""
    logging.info("🚀 Registrazione tool-set: API Testing Tools")

    @mcp.tool()
    def build_http_request(method: str, url: str, headers: str = "", body: str = "", auth_type: str = "none") -> str:
        """
        Costruisce una richiesta HTTP completa per test API.
        
        Args:
            method: Metodo HTTP (GET, POST, PUT, DELETE, PATCH)
            url: URL dell'endpoint
            headers: Headers in formato JSON o "key:value,key2:value2"
            body: Body della richiesta (JSON, form-data, etc.)
            auth_type: Tipo di autenticazione (none, bearer, basic, api_key)
        """
        try:
            # Valida metodo HTTP
            valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
            method = method.upper()
            if method not in valid_methods:
                return f"ERRORE: Metodo '{method}' non valido. Usa: {', '.join(valid_methods)}"
            
            # Valida URL
            if not url.startswith(('http://', 'https://')):
                return "ERRORE: URL deve iniziare con http:// o https://"
            
            # Parse headers
            headers_dict = {}
            if headers:
                try:
                    # Prova JSON prima
                    headers_dict = json.loads(headers)
                except:
                    # Fallback al formato semplice
                    for header in headers.split(','):
                        if ':' in header:
                            key, value = header.split(':', 1)
                            headers_dict[key.strip()] = value.strip()
            
            # Aggiunge headers di default
            if method in ['POST', 'PUT', 'PATCH'] and body and 'Content-Type' not in headers_dict:
                try:
                    json.loads(body)
                    headers_dict['Content-Type'] = 'application/json'
                except:
                    headers_dict['Content-Type'] = 'application/x-www-form-urlencoded'
            
            # Gestisce autenticazione
            auth_examples = {
                'bearer': 'Authorization: Bearer YOUR_TOKEN_HERE',
                'basic': 'Authorization: Basic dXNlcjpwYXNzd29yZA==',
                'api_key': 'X-API-Key: YOUR_API_KEY_HERE'
            }
            
            if auth_type != 'none' and auth_type in auth_examples:
                auth_header = auth_examples[auth_type]
                key, value = auth_header.split(': ', 1)
                headers_dict[key] = value
            
            # Costruisce la richiesta
            request_parts = [f"{method} {urlparse(url).path or '/'} HTTP/1.1"]
            request_parts.append(f"Host: {urlparse(url).netloc}")
            
            for key, value in headers_dict.items():
                request_parts.append(f"{key}: {value}")
            
            if body:
                request_parts.append(f"Content-Length: {len(body)}")
                request_parts.append("")  # Linea vuota prima del body
                request_parts.append(body)
            else:
                request_parts.append("")  # Linea vuota finale
            
            raw_request = "\r\n".join(request_parts)
            
            # Genera esempi per diversi client
            curl_cmd = f"curl -X {method}"
            for key, value in headers_dict.items():
                curl_cmd += f" -H '{key}: {value}'"
            if body:
                curl_cmd += f" -d '{body}'"
            curl_cmd += f" '{url}'"
            
            # Python requests
            python_code = f"""import requests

response = requests.{method.lower()}(
    '{url}',"""
            
            if headers_dict:
                python_code += f"\n    headers={json.dumps(headers_dict, indent=4)},"
            if body:
                if headers_dict.get('Content-Type') == 'application/json':
                    python_code += f"\n    json={body},"
                else:
                    python_code += f"\n    data='{body}',"
            
            python_code += "\n)\nprint(response.status_code)\nprint(response.text)"
            
            return f"""🚀 RICHIESTA HTTP COSTRUITA
Metodo: {method}
URL: {url}
Headers: {len(headers_dict)}
Body: {'Sì' if body else 'No'} ({len(body)} caratteri)
Auth: {auth_type}

RAW HTTP REQUEST:
{raw_request}

CURL COMMAND:
{curl_cmd}

PYTHON REQUESTS:
{python_code}"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def validate_api_response(response_body: str, expected_status: int, expected_schema: str = "") -> str:
        """
        Valida una risposta API contro schemi e aspettative.
        
        Args:
            response_body: Body della risposta
            expected_status: Codice di stato atteso
            expected_schema: Schema JSON atteso (opzionale)
        """
        try:
            # Simula analisi della risposta
            response_size = len(response_body)
            
            # Prova a parsare come JSON
            is_json = False
            json_data = None
            try:
                json_data = json.loads(response_body)
                is_json = True
            except:
                pass
            
            # Analisi contenuto
            content_analysis = []
            
            if is_json:
                content_analysis.append("✅ JSON valido")
                
                # Analizza struttura JSON
                def analyze_json_structure(obj, path=""):
                    info = []
                    if isinstance(obj, dict):
                        info.append(f"Oggetto con {len(obj)} chiavi" + (f" a {path}" if path else ""))
                        for key in list(obj.keys())[:5]:  # Prime 5 chiavi
                            info.extend(analyze_json_structure(obj[key], f"{path}.{key}" if path else key))
                    elif isinstance(obj, list):
                        info.append(f"Array di {len(obj)} elementi" + (f" a {path}" if path else ""))
                        if obj:  # Se non vuoto, analizza primo elemento
                            info.extend(analyze_json_structure(obj[0], f"{path}[0]" if path else "[0]"))
                    else:
                        type_name = type(obj).__name__
                        info.append(f"{path}: {type_name}")
                    return info[:10]  # Limita output
                
                structure_info = analyze_json_structure(json_data)
                content_analysis.extend(structure_info)
            else:
                content_analysis.append("❌ Non è JSON valido")
                
                # Verifica altri formati
                if response_body.strip().startswith('<'):
                    content_analysis.append("🔍 Sembra contenuto XML/HTML")
                elif '=' in response_body and '&' in response_body:
                    content_analysis.append("🔍 Sembra form-encoded")
                else:
                    content_analysis.append("🔍 Formato testo/sconosciuto")
            
            # Controlli di sicurezza
            security_checks = []
            
            # Verifica informazioni sensibili (basic check)
            sensitive_patterns = [
                (r'password', 'Password in chiaro'),
                (r'secret', 'Segreti esposti'),
                (r'token', 'Token esposti'),
                (r'api[_-]?key', 'API key esposte'),
                (r'\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}', 'Possibili numeri di carta di credito')
            ]
            
            for pattern, desc in sensitive_patterns:
                if re.search(pattern, response_body, re.IGNORECASE):
                    security_checks.append(f"⚠️ {desc}")
            
            if not security_checks:
                security_checks.append("✅ Nessuna informazione sensibile evidente")
            
            # Controllo status code
            status_analysis = []
            if 200 <= expected_status < 300:
                status_analysis.append(f"✅ Status {expected_status} - Successo")
            elif 300 <= expected_status < 400:
                status_analysis.append(f"🔄 Status {expected_status} - Redirection")
            elif 400 <= expected_status < 500:
                status_analysis.append(f"⚠️ Status {expected_status} - Client Error")
            elif expected_status >= 500:
                status_analysis.append(f"❌ Status {expected_status} - Server Error")
            else:
                status_analysis.append(f"❓ Status {expected_status} - Non standard")
            
            # Validazione schema (se fornito)
            schema_validation = []
            if expected_schema and is_json:
                try:
                    expected_structure = json.loads(expected_schema)
                    # Semplice confronto strutturale
                    def compare_structure(actual, expected, path=""):
                        issues = []
                        if isinstance(expected, dict):
                            if not isinstance(actual, dict):
                                issues.append(f"❌ {path}: atteso oggetto, trovato {type(actual).__name__}")
                            else:
                                for key in expected.keys():
                                    if key not in actual:
                                        issues.append(f"❌ {path}.{key}: chiave mancante")
                                    else:
                                        issues.extend(compare_structure(actual[key], expected[key], f"{path}.{key}"))
                        elif isinstance(expected, list):
                            if not isinstance(actual, list):
                                issues.append(f"❌ {path}: atteso array, trovato {type(actual).__name__}")
                        return issues[:5]  # Limita a 5 errori
                    
                    schema_issues = compare_structure(json_data, expected_structure)
                    if schema_issues:
                        schema_validation.extend(schema_issues)
                    else:
                        schema_validation.append("✅ Schema corrisponde")
                        
                except json.JSONDecodeError:
                    schema_validation.append("❌ Schema atteso non è JSON valido")
            
            result = f"""🔍 VALIDAZIONE RISPOSTA API
Dimensioni: {response_size:,} caratteri
Status atteso: {expected_status}
Formato: {'JSON' if is_json else 'Non-JSON'}

ANALISI CONTENUTO:
""" + '\n'.join(content_analysis)
            
            result += "\n\nSTATUS CODE:\n" + '\n'.join(status_analysis)
            
            if schema_validation:
                result += "\n\nVALIDAZIONE SCHEMA:\n" + '\n'.join(schema_validation)
            
            result += "\n\nCONTROLLI SICUREZZA:\n" + '\n'.join(security_checks)
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_api_test_suite(base_url: str, endpoints: str, auth_method: str = "none") -> str:
        """
        Genera una suite di test per API REST.
        
        Args:
            base_url: URL base dell'API
            endpoints: Lista endpoint in formato JSON [{"path": "/users", "method": "GET"}, ...]
            auth_method: Metodo di autenticazione (none, bearer, api_key)
        """
        try:
            # Parse endpoints
            try:
                endpoint_list = json.loads(endpoints)
            except json.JSONDecodeError:
                return "ERRORE: endpoints deve essere un JSON array valido"
            
            if not isinstance(endpoint_list, list):
                return "ERRORE: endpoints deve essere un array"
            
            # Genera test per ogni endpoint
            test_cases = []
            
            auth_header = ""
            if auth_method == "bearer":
                auth_header = "-H 'Authorization: Bearer YOUR_TOKEN'"
            elif auth_method == "api_key":
                auth_header = "-H 'X-API-Key: YOUR_API_KEY'"
            
            for i, endpoint in enumerate(endpoint_list, 1):
                if not isinstance(endpoint, dict) or 'path' not in endpoint or 'method' not in endpoint:
                    continue
                
                path = endpoint['path']
                method = endpoint['method'].upper()
                full_url = urljoin(base_url, path)
                
                # Test di base
                basic_test = f"""# Test {i}: {method} {path}
curl -X {method} {auth_header} "{full_url}"
# Atteso: 200 per operazioni di successo"""
                
                # Test specifici per metodo
                if method == 'GET':
                    # Test con parametri
                    param_test = f"""# Test {i}b: {method} {path} con parametri
curl -X {method} {auth_header} "{full_url}?limit=10&offset=0"
# Atteso: 200 con dati paginati"""
                    basic_test += "\n\n" + param_test
                
                elif method == 'POST':
                    # Test con body
                    create_test = f"""# Test {i}b: {method} {path} con dati
curl -X {method} {auth_header} \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "Test", "email": "test@example.com"}}' \\
  "{full_url}"
# Atteso: 201 Created"""
                    basic_test += "\n\n" + create_test
                
                elif method == 'PUT':
                    # Test aggiornamento
                    update_test = f"""# Test {i}b: {method} {path} aggiornamento
curl -X {method} {auth_header} \\
  -H "Content-Type: application/json" \\
  -d '{{"id": 1, "name": "Updated"}}' \\
  "{full_url}/1"
# Atteso: 200 Updated"""
                    basic_test += "\n\n" + update_test
                
                elif method == 'DELETE':
                    # Test cancellazione
                    delete_test = f"""# Test {i}b: {method} {path} cancellazione
curl -X {method} {auth_header} "{full_url}/1"
# Atteso: 204 No Content o 200"""
                    basic_test += "\n\n" + delete_test
                
                test_cases.append(basic_test)
            
            # Test di errore comuni
            error_tests = f"""
# Test errori comuni
# 1. Endpoint inesistente
curl -X GET {auth_header} "{base_url}/nonexistent"
# Atteso: 404 Not Found

# 2. Metodo non supportato
curl -X PATCH {auth_header} "{base_url}/users"
# Atteso: 405 Method Not Allowed

# 3. Request malformata
curl -X POST {auth_header} \\
  -H "Content-Type: application/json" \\
  -d '{{invalid json}}' \\
  "{base_url}/users"
# Atteso: 400 Bad Request

# 4. Autenticazione mancante (se richiesta)
curl -X GET "{base_url}/users"
# Atteso: 401 Unauthorized
"""
            
            # Genera script Python per test automatici
            python_script = f"""#!/usr/bin/env python3
import requests
import json
import sys

BASE_URL = "{base_url}"
AUTH_HEADERS = {{}}

# Configura autenticazione
if "{auth_method}" == "bearer":
    AUTH_HEADERS["Authorization"] = "Bearer YOUR_TOKEN_HERE"
elif "{auth_method}" == "api_key":
    AUTH_HEADERS["X-API-Key"] = "YOUR_API_KEY_HERE"

def test_endpoint(method, path, data=None):
    url = f"{{BASE_URL}}{{path}}"
    try:
        response = requests.request(method, url, headers=AUTH_HEADERS, json=data)
        print(f"{{method}} {{path}}: {{response.status_code}} - {{response.reason}}")
        return response.status_code < 400
    except Exception as e:
        print(f"{{method}} {{path}}: ERROR - {{e}}")
        return False

# Test automatici
tests_passed = 0
total_tests = 0

# Test endpoint principali"""
            
            for endpoint in endpoint_list:
                if 'path' in endpoint and 'method' in endpoint:
                    path = endpoint['path']
                    method = endpoint['method'].upper()
                    python_script += f"""
total_tests += 1
if test_endpoint("{method}", "{path}"):
    tests_passed += 1"""
            
            python_script += f"""

print(f"\\nTest completati: {{tests_passed}}/{{total_tests}} passati")
if tests_passed == total_tests:
    print("✅ Tutti i test sono passati!")
    sys.exit(0)
else:
    print("❌ Alcuni test sono falliti")
    sys.exit(1)"""
            
            return f"""🧪 SUITE TEST API GENERATA
Base URL: {base_url}
Endpoints: {len(endpoint_list)}
Autenticazione: {auth_method}
Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COMANDI CURL:
{chr(10).join(test_cases)}

{error_tests}

SCRIPT PYTHON AUTOMATICO:
{python_script}

💡 SUGGERIMENTI:
1. Sostituisci YOUR_TOKEN/YOUR_API_KEY con valori reali
2. Esegui i test in sequenza per verificare dipendenze
3. Controlla sempre i codici di stato delle risposte
4. Testa sia scenari di successo che di errore"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def parse_api_documentation(api_spec: str, spec_format: str = "openapi") -> str:
        """
        Analizza documentazione API e estrae informazioni utili.
        
        Args:
            api_spec: Specifica API (JSON o YAML)
            spec_format: Formato della specifica (openapi, swagger, postman)
        """
        try:
            # Parse della specifica
            try:
                if api_spec.strip().startswith('{'):
                    spec_data = json.loads(api_spec)
                else:
                    # Prova YAML (simulato per semplicità)
                    import yaml
                    spec_data = yaml.safe_load(api_spec)
            except Exception as e:
                return f"ERRORE nel parsing della specifica: {str(e)}"
            
            result = f"📚 ANALISI DOCUMENTAZIONE API\nFormato: {spec_format}\n"
            
            if spec_format.lower() in ['openapi', 'swagger']:
                # Analizza OpenAPI/Swagger
                info = spec_data.get('info', {})
                result += f"""
INFORMAZIONI GENERALI:
Titolo: {info.get('title', 'N/A')}
Versione: {info.get('version', 'N/A')}
Descrizione: {info.get('description', 'N/A')[:100]}

SERVER:"""
                
                servers = spec_data.get('servers', [])
                if servers:
                    for server in servers[:3]:  # Prime 3
                        result += f"\n- {server.get('url', 'N/A')}"
                else:
                    # Swagger 2.0
                    host = spec_data.get('host', 'N/A')
                    base_path = spec_data.get('basePath', '')
                    schemes = spec_data.get('schemes', ['https'])
                    result += f"\n- {schemes[0]}://{host}{base_path}"
                
                # Analizza endpoints
                paths = spec_data.get('paths', {})
                result += f"\n\nENDPOINTS ({len(paths)}):"
                
                endpoint_count = 0
                for path, methods in paths.items():
                    if endpoint_count >= 10:  # Limita output
                        result += f"\n... e altri {len(paths) - 10} endpoint"
                        break
                    
                    for method, details in methods.items():
                        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            summary = details.get('summary', details.get('operationId', ''))
                            result += f"\n{method.upper():6} {path:<30} {summary[:50]}"
                            endpoint_count += 1
                
                # Analizza componenti/modelli
                components = spec_data.get('components', {})
                schemas = components.get('schemas', spec_data.get('definitions', {}))
                if schemas:
                    result += f"\n\nMODELLI DATI ({len(schemas)}):"
                    for schema_name in list(schemas.keys())[:5]:
                        result += f"\n- {schema_name}"
                    if len(schemas) > 5:
                        result += f"\n... e altri {len(schemas) - 5} modelli"
                
                # Analizza autenticazione
                security = spec_data.get('security', [])
                if security:
                    result += f"\n\nAUTENTICAZIONE:"
                    for sec in security[:3]:
                        result += f"\n- {list(sec.keys())}"
            
            elif spec_format.lower() == 'postman':
                # Analizza collezione Postman
                info = spec_data.get('info', {})
                result += f"""
COLLEZIONE POSTMAN:
Nome: {info.get('name', 'N/A')}
ID: {info.get('_postman_id', 'N/A')[:8]}...
Schema: {info.get('schema', 'N/A')}

REQUEST:"""
                
                items = spec_data.get('item', [])
                for i, item in enumerate(items[:10], 1):
                    if 'request' in item:
                        req = item['request']
                        method = req.get('method', 'N/A')
                        url = req.get('url', {})
                        if isinstance(url, dict):
                            url_str = '/'.join(url.get('path', []))
                        else:
                            url_str = str(url)
                        
                        result += f"\n{i:2d}. {method:6} {url_str[:50]}"
                
                if len(items) > 10:
                    result += f"\n... e altre {len(items) - 10} request"
            
            else:
                result += f"\nFormato '{spec_format}' non ancora supportato completamente"
                result += f"\nChiavi trovate nella specifica: {list(spec_data.keys())[:10]}"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"