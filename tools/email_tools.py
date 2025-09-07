# -*- coding: utf-8 -*-
# tools/email_tools.py
import logging
import re
import hashlib
from datetime import datetime

def register_tools(mcp):
    """Registra i tool email con l'istanza del server MCP."""
    logging.info("📧 Registrazione tool-set: Email Tools")

    @mcp.tool()
    def validate_email_advanced(email: str) -> str:
        """
        Valida un indirizzo email con controlli avanzati.
        
        Args:
            email: Indirizzo email da validare
        """
        try:
            # Pattern RFC compliant (semplificato)
            email_pattern = re.compile(
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            )
            
            # Controlli di base
            is_valid_format = bool(email_pattern.match(email))
            
            if not is_valid_format:
                return "❌ EMAIL NON VALIDO - Formato non corretto"
            
            # Divide email in parti
            local_part, domain = email.split('@')
            
            # Analisi della parte locale
            local_issues = []
            if len(local_part) > 64:
                local_issues.append("Parte locale troppo lunga (>64 caratteri)")
            if local_part.startswith('.') or local_part.endswith('.'):
                local_issues.append("Non può iniziare o finire con un punto")
            if '..' in local_part:
                local_issues.append("Non può contenere punti consecutivi")
            
            # Analisi del dominio
            domain_issues = []
            if len(domain) > 253:
                domain_issues.append("Dominio troppo lungo (>253 caratteri)")
            
            domain_parts = domain.split('.')
            if any(len(part) > 63 for part in domain_parts):
                domain_issues.append("Parte del dominio troppo lunga (>63 caratteri)")
            
            # Domini comuni sospetti
            suspicious_domains = ['tempmail', '10minutemail', 'guerrillamail', 'throwaway']
            is_suspicious = any(sus in domain.lower() for sus in suspicious_domains)
            
            # TLD comuni
            common_tlds = ['com', 'org', 'net', 'edu', 'gov', 'it', 'co.uk', 'de', 'fr']
            tld = domain.split('.')[-1].lower()
            is_common_tld = tld in common_tlds
            
            result = f"""✅ EMAIL VALIDO
Email: {email}
Parte locale: {local_part} ({len(local_part)} caratteri)
Dominio: {domain} ({len(domain)} caratteri)
TLD: {tld} {'(comune)' if is_common_tld else '(raro)'}
Possibile temporaneo: {'⚠️ Sì' if is_suspicious else '✅ No'}"""
            
            if local_issues:
                result += f"\n\n⚠️ Problemi parte locale:\n" + '\n'.join(f"- {issue}" for issue in local_issues)
            
            if domain_issues:
                result += f"\n\n⚠️ Problemi dominio:\n" + '\n'.join(f"- {issue}" for issue in domain_issues)
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_email_template(template_type: str, sender_name: str, recipient_name: str = "", subject: str = "") -> str:
        """
        Genera template email per diversi scopi.
        
        Args:
            template_type: Tipo di template (welcome, follow_up, newsletter, reminder, thank_you)
            sender_name: Nome del mittente
            recipient_name: Nome del destinatario (opzionale)
            subject: Oggetto personalizzato (opzionale)
        """
        try:
            recipient = recipient_name or "[Nome Destinatario]"
            
            templates = {
                'welcome': {
                    'subject': subject or f"Benvenuto/a in {sender_name}!",
                    'body': f"""Caro/a {recipient},

Benvenuto/a nella famiglia {sender_name}! Siamo entusiasti di averti con noi.

In questo messaggio troverai:
- Informazioni su come iniziare
- Risorse utili per sfruttare al meglio i nostri servizi
- Contatti per assistenza

Se hai domande, non esitare a contattarci.

Cordiali saluti,
Il team {sender_name}"""
                },
                'follow_up': {
                    'subject': subject or "Follow-up: La tua esperienza con noi",
                    'body': f"""Caro/a {recipient},

Spero che tu stia bene. Volevo fare il punto sulla tua esperienza con {sender_name}.

Ci piacerebbe sapere:
- Come ti stai trovando con i nostri servizi?
- Hai suggerimenti per migliorare?
- C'è qualcosa che possiamo fare per te?

La tua opinione è molto importante per noi.

Cordiali saluti,
{sender_name}"""
                },
                'newsletter': {
                    'subject': subject or f"Newsletter {sender_name} - {datetime.now().strftime('%B %Y')}",
                    'body': f"""Caro/a {recipient},

Ecco le novità di questo mese da {sender_name}:

📈 AGGIORNAMENTI PRODOTTO
- [Inserire novità principali]
- [Miglioramenti e nuove funzionalità]

📊 IN EVIDENZA
- [Contenuto interessante per gli utenti]
- [Casi di successo o statistiche]

🎯 PROSSIMI EVENTI
- [Eventi, webinar, o iniziative]

Continua a seguirci per rimanere aggiornato!

Il team {sender_name}"""
                },
                'reminder': {
                    'subject': subject or "Promemoria importante",
                    'body': f"""Caro/a {recipient},

Questo è un gentile promemoria riguardo a:
[INSERIRE DETTAGLI SPECIFICI]

Dettagli:
- Data: [DATA]
- Ora: [ORA]
- Luogo/Link: [INFORMAZIONI]

Se hai domande, contattaci pure.

Cordiali saluti,
{sender_name}"""
                },
                'thank_you': {
                    'subject': subject or "Grazie!",
                    'body': f"""Caro/a {recipient},

Volevo ringraziarti personalmente per [MOTIVO SPECIFICO].

Il tuo [supporto/acquisto/feedback/partecipazione] significa molto per noi e ci aiuta a crescere e migliorare continuamente.

Speriamo di poterti servire ancora in futuro.

Con gratitudine,
{sender_name}"""
                }
            }
            
            if template_type not in templates:
                available = ', '.join(templates.keys())
                return f"ERRORE: Template '{template_type}' non disponibile. Disponibili: {available}"
            
            template = templates[template_type]
            
            return f"""📧 TEMPLATE EMAIL GENERATO

Oggetto: {template['subject']}

{template['body']}

---
Template tipo: {template_type}
Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def parse_email_header(email_text: str) -> str:
        """
        Estrae e analizza le informazioni dall'header di un'email.
        
        Args:
            email_text: Testo completo dell'email con header
        """
        try:
            lines = email_text.split('\n')
            headers = {}
            
            # Estrae header principali
            header_patterns = {
                'From': r'^From:\s*(.+)',
                'To': r'^To:\s*(.+)',
                'Subject': r'^Subject:\s*(.+)',
                'Date': r'^Date:\s*(.+)',
                'Message-ID': r'^Message-ID:\s*(.+)',
                'Reply-To': r'^Reply-To:\s*(.+)',
                'Return-Path': r'^Return-Path:\s*(.+)',
                'X-Mailer': r'^X-Mailer:\s*(.+)',
                'Content-Type': r'^Content-Type:\s*(.+)'
            }
            
            for line in lines:
                if line.strip() == '':  # Fine header
                    break
                    
                for header_name, pattern in header_patterns.items():
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        headers[header_name] = match.group(1).strip()
            
            if not headers:
                return "❌ Nessun header email valido trovato"
            
            result = "📨 ANALISI HEADER EMAIL\n\n"
            
            # Informazioni principali
            if 'From' in headers:
                result += f"Mittente: {headers['From']}\n"
            if 'To' in headers:
                result += f"Destinatario: {headers['To']}\n"
            if 'Subject' in headers:
                result += f"Oggetto: {headers['Subject']}\n"
            if 'Date' in headers:
                result += f"Data: {headers['Date']}\n"
            
            result += "\n📋 HEADER TECNICI:\n"
            
            # Informazioni tecniche
            for header, value in headers.items():
                if header not in ['From', 'To', 'Subject', 'Date']:
                    result += f"{header}: {value[:100]}{'...' if len(value) > 100 else ''}\n"
            
            # Analisi sicurezza di base
            result += "\n🔍 ANALISI SICUREZZA:\n"
            
            security_checks = []
            if 'Return-Path' in headers and 'From' in headers:
                from_domain = headers['From'].split('@')[-1] if '@' in headers['From'] else ''
                return_domain = headers['Return-Path'].split('@')[-1] if '@' in headers['Return-Path'] else ''
                if from_domain != return_domain and from_domain and return_domain:
                    security_checks.append("⚠️ Dominio From diverso da Return-Path")
            
            if not security_checks:
                security_checks.append("✅ Nessun problema di sicurezza evidente")
            
            result += '\n'.join(security_checks)
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_email_signature(name: str, title: str, company: str, phone: str = "", email: str = "", website: str = "") -> str:
        """
        Genera una firma email professionale.
        
        Args:
            name: Nome completo
            title: Titolo/Posizione
            company: Nome azienda
            phone: Numero di telefono (opzionale)
            email: Email (opzionale)
            website: Sito web (opzionale)
        """
        try:
            # Template firma base
            signature = f"""{name}
{title}
{company}"""
            
            # Aggiunge contatti se forniti
            contacts = []
            if phone:
                contacts.append(f"📞 {phone}")
            if email:
                contacts.append(f"📧 {email}")
            if website:
                website_clean = website.replace('http://', '').replace('https://', '')
                contacts.append(f"🌐 {website_clean}")
            
            if contacts:
                signature += "\n\n" + " | ".join(contacts)
            
            # Versione HTML
            html_signature = f"""<div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
<strong>{name}</strong><br>
<em>{title}</em><br>
{company}"""
            
            if contacts:
                html_signature += "<br><br>"
                html_contacts = []
                if phone:
                    html_contacts.append(f'📞 <a href="tel:{phone.replace(" ", "")}">{phone}</a>')
                if email:
                    html_contacts.append(f'📧 <a href="mailto:{email}">{email}</a>')
                if website:
                    website_clean = website.replace('http://', '').replace('https://', '')
                    full_website = website if website.startswith('http') else f'https://{website}'
                    html_contacts.append(f'🌐 <a href="{full_website}">{website_clean}</a>')
                
                html_signature += " | ".join(html_contacts)
            
            html_signature += "</div>"
            
            return f"""📝 FIRMA EMAIL GENERATA

VERSIONE TESTO:
{signature}

VERSIONE HTML:
{html_signature}

---
Caratteri totali (testo): {len(signature)}
Generata il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"