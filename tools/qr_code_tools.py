# -*- coding: utf-8 -*-
# tools/qr_code_tools.py
import logging
import base64
import io

def register_tools(mcp):
    """Registra i tool per QR code con l'istanza del server MCP."""
    logging.info("📱 Registrazione tool-set: QR Code Tools")

    @mcp.tool()
    def generate_qr_code(text: str, size: int = 200, border: int = 4, error_correction: str = "M") -> str:
        """
        Genera un QR code da un testo.

        Args:
            text: Il testo da codificare nel QR code.
            size: Dimensione dell'immagine in pixel (default 200).
            border: Spessore del bordo (default 4).
            error_correction: Livello di correzione errori (L, M, Q, H).
        """
        try:
            # Simulazione di generazione QR code (senza dipendenze esterne)
            # In un ambiente reale, useresti qrcode library
            
            # Validazione parametri
            if not text.strip():
                return "ERRORE: Il testo non può essere vuoto"
            
            if size < 100 or size > 1000:
                return "ERRORE: La dimensione deve essere tra 100 e 1000 pixel"
            
            if border < 1 or border > 10:
                return "ERRORE: Il bordo deve essere tra 1 e 10"
            
            valid_error_levels = ["L", "M", "Q", "H"]
            if error_correction not in valid_error_levels:
                return f"ERRORE: Livello correzione errori deve essere uno di: {', '.join(valid_error_levels)}"
            
            # Simulazione di creazione QR code semplice
            # In un vero ambiente, qui genereresti l'immagine QR
            qr_data = {
                "text": text,
                "size": f"{size}x{size}",
                "border": border,
                "error_correction": error_correction,
                "format": "PNG"
            }
            
            return f"QR Code generato con successo!\nTesto: {text}\nDimensioni: {size}x{size}\nBordo: {border}\nCorrezione errori: {error_correction}\n\nNOTA: Implementazione semplificata - in produzione genererebbe un'immagine QR code reale."
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_qr_code_url(url: str, size: int = 200) -> str:
        """
        Genera un QR code per un URL.

        Args:
            url: L'URL da codificare.
            size: Dimensione dell'immagine in pixel (default 200).
        """
        try:
            # Validazione URL di base
            if not url.strip():
                return "ERRORE: L'URL non può essere vuoto"
            
            if not (url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://')):
                return "ERRORE: L'URL deve iniziare con http://, https:// o ftp://"
            
            return generate_qr_code(url, size, border=4, error_correction="M")
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_qr_code_wifi(ssid: str, password: str, security: str = "WPA", hidden: bool = False) -> str:
        """
        Genera un QR code per connessione WiFi.

        Args:
            ssid: Nome della rete WiFi.
            password: Password della rete WiFi.
            security: Tipo di sicurezza (WPA, WEP, nopass).
            hidden: Se la rete è nascosta (default False).
        """
        try:
            if not ssid.strip():
                return "ERRORE: Il nome della rete (SSID) non può essere vuoto"
            
            valid_security = ["WPA", "WEP", "nopass"]
            if security not in valid_security:
                return f"ERRORE: Tipo sicurezza deve essere uno di: {', '.join(valid_security)}"
            
            # Formato WiFi QR code standard
            wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};H:{'true' if hidden else 'false'};;"
            
            return generate_qr_code(wifi_string, size=250, border=4, error_correction="M")
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_qr_code_contact(name: str, phone: str = "", email: str = "", organization: str = "") -> str:
        """
        Genera un QR code per un contatto (vCard).

        Args:
            name: Nome del contatto.
            phone: Numero di telefono (opzionale).
            email: Indirizzo email (opzionale).
            organization: Organizzazione/azienda (opzionale).
        """
        try:
            if not name.strip():
                return "ERRORE: Il nome del contatto non può essere vuoto"
            
            # Formato vCard semplificato
            vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\n"
            
            if phone.strip():
                vcard += f"TEL:{phone}\n"
            
            if email.strip():
                vcard += f"EMAIL:{email}\n"
            
            if organization.strip():
                vcard += f"ORG:{organization}\n"
            
            vcard += "END:VCARD"
            
            return generate_qr_code(vcard, size=250, border=4, error_correction="M")
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_qr_code_sms(phone: str, message: str = "") -> str:
        """
        Genera un QR code per inviare un SMS.

        Args:
            phone: Numero di telefono destinatario.
            message: Messaggio da inviare (opzionale).
        """
        try:
            if not phone.strip():
                return "ERRORE: Il numero di telefono non può essere vuoto"
            
            # Formato SMS QR code
            sms_string = f"SMS:{phone}:{message}"
            
            return generate_qr_code(sms_string, size=200, border=4, error_correction="M")
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def analyze_qr_content(content: str) -> str:
        """
        Analizza il contenuto di un QR code e determina il tipo.

        Args:
            content: Il contenuto decodificato del QR code.
        """
        try:
            if not content.strip():
                return "ERRORE: Il contenuto non può essere vuoto"
            
            analysis = "=== ANALISI CONTENUTO QR CODE ===\n"
            analysis += f"Contenuto: {content}\n"
            analysis += f"Lunghezza: {len(content)} caratteri\n\n"
            
            # Analisi del tipo di contenuto
            if content.startswith('http://') or content.startswith('https://'):
                analysis += "Tipo: URL/Sito Web\n"
                analysis += f"Dominio: {content.split('/')[2] if len(content.split('/')) > 2 else 'N/A'}\n"
            elif content.startswith('WIFI:'):
                analysis += "Tipo: Configurazione WiFi\n"
                # Parsing dei parametri WiFi
                parts = content.replace('WIFI:', '').split(';')
                for part in parts:
                    if ':' in part and part:
                        key, value = part.split(':', 1)
                        if key == 'T':
                            analysis += f"Sicurezza: {value}\n"
                        elif key == 'S':
                            analysis += f"SSID: {value}\n"
                        elif key == 'H':
                            analysis += f"Rete nascosta: {value}\n"
            elif content.startswith('BEGIN:VCARD'):
                analysis += "Tipo: Contatto vCard\n"
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('FN:'):
                        analysis += f"Nome: {line[3:]}\n"
                    elif line.startswith('TEL:'):
                        analysis += f"Telefono: {line[4:]}\n"
                    elif line.startswith('EMAIL:'):
                        analysis += f"Email: {line[6:]}\n"
            elif content.startswith('SMS:'):
                analysis += "Tipo: SMS\n"
                parts = content[4:].split(':', 1)
                analysis += f"Numero: {parts[0]}\n"
                if len(parts) > 1:
                    analysis += f"Messaggio: {parts[1]}\n"
            elif content.startswith('mailto:'):
                analysis += "Tipo: Email\n"
                analysis += f"Destinatario: {content[7:]}\n"
            elif content.startswith('tel:'):
                analysis += "Tipo: Numero di telefono\n"
                analysis += f"Numero: {content[4:]}\n"
            else:
                analysis += "Tipo: Testo semplice\n"
                # Controlla se potrebbe essere un numero
                if content.replace(' ', '').replace('-', '').replace('+', '').isdigit():
                    analysis += "Possibile numero di telefono\n"
                # Controlla se potrebbe essere un email
                elif '@' in content and '.' in content:
                    analysis += "Possibile indirizzo email\n"
            
            return analysis
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def qr_code_formats_info() -> str:
        """
        Fornisce informazioni sui formati supportati per QR code.
        """
        try:
            info = """=== FORMATI QR CODE SUPPORTATI ===

📱 URL/Sito Web:
   Formato: https://esempio.com
   
📶 WiFi:
   Formato: WIFI:T:WPA;S:NomeRete;P:Password;H:false;;
   
👤 Contatto vCard:
   Formato: BEGIN:VCARD
            VERSION:3.0
            FN:Nome Cognome
            TEL:+39123456789
            EMAIL:email@esempio.com
            END:VCARD
   
💬 SMS:
   Formato: SMS:+39123456789:Messaggio
   
📧 Email:
   Formato: mailto:email@esempio.com
   
📞 Telefono:
   Formato: tel:+39123456789
   
📝 Testo semplice:
   Qualsiasi testo normale

=== LIVELLI CORREZIONE ERRORI ===
L (Low)    - ~7%  - Per ambienti puliti
M (Medium) - ~15% - Uso generale (default)
Q (Quartile) - ~25% - Per ambienti rumorosi
H (High)   - ~30% - Massima resistenza

=== LIMITI DIMENSIONI ===
Testo: Fino a ~4,296 caratteri alfanumerici
Numeri: Fino a ~7,089 cifre
Byte: Fino a ~2,953 bytes"""
            
            return info
            
        except Exception as e:
            return f"ERRORE: {str(e)}"