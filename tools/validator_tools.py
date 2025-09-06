# -*- coding: utf-8 -*-
# tools/validator_tools.py
import re
import ipaddress
import urllib.parse
import logging

def register_tools(mcp):
    """Registra i tool di validazione con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Data Validation Tools")

    @mcp.tool()
    def validate_email(email: str) -> str:
        """
        Valida un indirizzo email.

        Args:
            email: L'indirizzo email da validare.
        """
        if not email:
            return "ERRORE: Email vuota"
        
        # Pattern RFC 5322 semplificato
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = re.match(pattern, email) is not None
        
        result = f"Email: {email}\n"
        result += f"Valida: {'✅ SI' if is_valid else '❌ NO'}"
        
        if is_valid:
            local, domain = email.split('@')
            result += f"\nParte locale: {local}\nDominio: {domain}"
        
        return result

    @mcp.tool()
    def validate_url(url: str) -> str:
        """
        Valida e analizza un URL.

        Args:
            url: L'URL da validare.
        """
        if not url:
            return "ERRORE: URL vuoto"
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            is_valid = all([parsed.scheme, parsed.netloc])
            
            result = f"URL: {url}\n"
            result += f"Valido: {'✅ SI' if is_valid else '❌ NO'}"
            
            if is_valid:
                result += f"\nSchema: {parsed.scheme}"
                result += f"\nDominio: {parsed.netloc}"
                if parsed.path:
                    result += f"\nPercorso: {parsed.path}"
                if parsed.query:
                    result += f"\nQuery: {parsed.query}"
                if parsed.fragment:
                    result += f"\nFragment: {parsed.fragment}"
            
            return result
        except Exception as e:
            return f"ERRORE: URL non valido - {str(e)}"

    @mcp.tool()
    def validate_ip_address(ip: str) -> str:
        """
        Valida un indirizzo IP (IPv4 o IPv6).

        Args:
            ip: L'indirizzo IP da validare.
        """
        if not ip:
            return "ERRORE: IP vuoto"
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            result = f"IP: {ip}\n"
            result += f"Valido: ✅ SI\n"
            result += f"Versione: IPv{ip_obj.version}\n"
            result += f"Privato: {'SI' if ip_obj.is_private else 'NO'}\n"
            result += f"Loopback: {'SI' if ip_obj.is_loopback else 'NO'}\n"
            result += f"Multicast: {'SI' if ip_obj.is_multicast else 'NO'}"
            
            if ip_obj.version == 4:
                result += f"\nClasse: {_get_ipv4_class(str(ip_obj))}"
            
            return result
        except ValueError:
            return f"IP: {ip}\nValido: ❌ NO\nMotivo: Formato non valido"

    @mcp.tool()
    def validate_phone(phone: str, country_code: str = "IT") -> str:
        """
        Valida un numero di telefono (validazione base).

        Args:
            phone: Il numero di telefono da validare.
            country_code: Il codice paese (IT, US, UK, etc.).
        """
        if not phone:
            return "ERRORE: Numero vuoto"
        
        # Rimuovi spazi, trattini e parentesi
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        patterns = {
            "IT": r'^\+?39[0-9]{8,10}$|^[0-9]{8,10}$',
            "US": r'^\+?1[0-9]{10}$|^[0-9]{10}$',
            "UK": r'^\+?44[0-9]{10}$|^[0-9]{10,11}$',
            "DE": r'^\+?49[0-9]{10,11}$|^[0-9]{10,11}$',
            "FR": r'^\+?33[0-9]{9}$|^[0-9]{10}$'
        }
        
        pattern = patterns.get(country_code.upper(), r'^[\+]?[0-9]{7,15}$')
        is_valid = re.match(pattern, clean_phone) is not None
        
        result = f"Telefono: {phone}\n"
        result += f"Pulito: {clean_phone}\n"
        result += f"Paese: {country_code.upper()}\n"
        result += f"Valido: {'✅ SI' if is_valid else '❌ NO'}"
        
        return result

    @mcp.tool()
    def validate_credit_card(card_number: str) -> str:
        """
        Valida un numero di carta di credito usando l'algoritmo di Luhn.

        Args:
            card_number: Il numero di carta di credito da validare.
        """
        if not card_number:
            return "ERRORE: Numero carta vuoto"
        
        # Rimuovi spazi e trattini
        clean_number = re.sub(r'[\s\-]', '', card_number)
        
        # Controlla se contiene solo numeri
        if not clean_number.isdigit():
            return f"Carta: {card_number}\nValida: ❌ NO\nMotivo: Contiene caratteri non numerici"
        
        # Controlla lunghezza
        if len(clean_number) < 13 or len(clean_number) > 19:
            return f"Carta: {card_number}\nValida: ❌ NO\nMotivo: Lunghezza non valida"
        
        # Algoritmo di Luhn
        def luhn_check(number):
            digits = [int(d) for d in number]
            for i in range(len(digits) - 2, -1, -2):
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] -= 9
            return sum(digits) % 10 == 0
        
        is_valid = luhn_check(clean_number)
        
        # Identifica il tipo di carta
        card_type = "Sconosciuto"
        if clean_number.startswith('4'):
            card_type = "Visa"
        elif clean_number.startswith('5') or clean_number.startswith('2'):
            card_type = "Mastercard"
        elif clean_number.startswith('3'):
            card_type = "American Express"
        
        result = f"Carta: {card_number}\n"
        result += f"Numero pulito: {clean_number}\n"
        result += f"Tipo: {card_type}\n"
        result += f"Lunghezza: {len(clean_number)} cifre\n"
        result += f"Valida (Luhn): {'✅ SI' if is_valid else '❌ NO'}"
        
        return result

def _get_ipv4_class(ip):
    """Determina la classe di un indirizzo IPv4."""
    first_octet = int(ip.split('.')[0])
    if 1 <= first_octet <= 126:
        return "A"
    elif 128 <= first_octet <= 191:
        return "B"
    elif 192 <= first_octet <= 223:
        return "C"
    elif 224 <= first_octet <= 239:
        return "D (Multicast)"
    elif 240 <= first_octet <= 255:
        return "E (Riservata)"
    else:
        return "Sconosciuta"