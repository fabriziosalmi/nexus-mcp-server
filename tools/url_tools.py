# -*- coding: utf-8 -*-
# tools/url_tools.py
import logging
import re
import urllib.parse
import hashlib
import base64
from typing import Dict, Any

def register_tools(mcp):
    """Registra i tool per la gestione URL con l'istanza del server MCP."""
    logging.info("🔗 Registrazione tool-set: URL Tools")

    @mcp.tool()
    def validate_url(url: str) -> str:
        """
        Valida e analizza un URL.
        
        Args:
            url: URL da validare
        """
        try:
            # Pattern per validazione URL base
            url_pattern = re.compile(
                r'^https?://'  # http:// o https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
                r'(?::\d+)?'  # porta opzionale
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            is_valid = bool(url_pattern.match(url))
            
            if is_valid:
                parsed = urllib.parse.urlparse(url)
                return f"""✅ URL VALIDO
Schema: {parsed.scheme}
Dominio: {parsed.netloc}
Percorso: {parsed.path or '/'}
Query: {parsed.query or 'Nessuna'}
Frammento: {parsed.fragment or 'Nessuno'}"""
            else:
                return "❌ URL NON VALIDO - Formato non corretto"
                
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def url_shortener_simulator(url: str, custom_alias: str = "") -> str:
        """
        Simula un servizio di accorciamento URL.
        
        Args:
            url: URL da accorciare
            custom_alias: Alias personalizzato (opzionale)
        """
        try:
            # Valida l'URL
            if not url.startswith(('http://', 'https://')):
                return "ERRORE: URL deve iniziare con http:// o https://"
            
            # Genera un hash dell'URL per l'alias
            if custom_alias:
                short_id = custom_alias[:10]  # Limita lunghezza
            else:
                hash_obj = hashlib.md5(url.encode())
                short_id = base64.urlsafe_b64encode(hash_obj.digest())[:8].decode()
            
            short_url = f"https://short.ly/{short_id}"
            
            return f"""🔗 URL ACCORCIATO
URL originale: {url}
URL corto: {short_url}
Alias: {short_id}
Caratteri salvati: {len(url) - len(short_url)}

Nota: Questo è un simulatore - non genera URL realmente funzionanti"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def extract_domain_info(url: str) -> str:
        """
        Estrae informazioni dettagliate sul dominio di un URL.
        
        Args:
            url: URL da analizzare
        """
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            # Rimuove www. se presente
            clean_domain = domain.replace('www.', '')
            
            # Estrae TLD
            domain_parts = clean_domain.split('.')
            tld = domain_parts[-1] if len(domain_parts) > 1 else "N/A"
            subdomain = '.'.join(domain_parts[:-2]) if len(domain_parts) > 2 else "N/A"
            main_domain = domain_parts[-2] if len(domain_parts) > 1 else clean_domain
            
            # Verifica porta
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            return f"""🌐 INFORMAZIONI DOMINIO
Dominio completo: {domain}
Dominio principale: {main_domain}
TLD: {tld}
Sottodominio: {subdomain}
Porta: {port}
Schema: {parsed.scheme}
È HTTPS: {'✅' if parsed.scheme == 'https' else '❌'}
Lunghezza dominio: {len(clean_domain)} caratteri"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def build_query_url(base_url: str, params: str) -> str:
        """
        Costruisce un URL con parametri query.
        
        Args:
            base_url: URL base
            params: Parametri in formato "key1=value1,key2=value2" o JSON
        """
        try:
            # Prova a parsare come JSON
            import json
            try:
                param_dict = json.loads(params)
            except:
                # Fallback al formato semplice
                param_dict = {}
                for param in params.split(','):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        param_dict[key.strip()] = value.strip()
            
            # Costruisce l'URL con i parametri
            query_string = urllib.parse.urlencode(param_dict)
            separator = '&' if '?' in base_url else '?'
            full_url = f"{base_url}{separator}{query_string}"
            
            return f"""🔧 URL COSTRUITO
URL base: {base_url}
Parametri: {len(param_dict)} parametri
URL finale: {full_url}
Lunghezza query: {len(query_string)} caratteri"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"