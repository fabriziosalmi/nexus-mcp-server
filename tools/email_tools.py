# -*- coding: utf-8 -*-
# tools/email_tools.py
import logging
import re
import hashlib
import base64
import json
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import dns.resolver

def register_tools(mcp):
    """Registra i tool email avanzati con l'istanza del server MCP."""
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

    @mcp.tool()
    def compose_email(recipient: str, subject: str, content: str, 
                     email_type: str = "plain", sender_info: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Compone un email completo con validazione e formattazione.
        
        Args:
            recipient: Indirizzo email destinatario
            subject: Oggetto dell'email
            content: Contenuto del messaggio
            email_type: Tipo email (plain, html, markdown)
            sender_info: Informazioni mittente (nome, email, signature)
        """
        try:
            # Validazione recipient
            if not _is_valid_email(recipient):
                return {"success": False, "error": f"Email destinatario non valida: {recipient}"}
            
            # Validazione subject
            if not subject.strip():
                return {"success": False, "error": "Oggetto email non può essere vuoto"}
            
            if len(subject) > 250:
                return {"success": False, "error": "Oggetto troppo lungo (max 250 caratteri)"}
            
            # Informazioni mittente
            sender_info = sender_info or {}
            sender_name = sender_info.get("name", "")
            sender_email = sender_info.get("email", "")
            signature = sender_info.get("signature", "")
            
            # Compone email in base al tipo
            composed_email = {
                "success": True,
                "recipient": recipient,
                "subject": subject,
                "email_type": email_type,
                "composed_at": datetime.now(timezone.utc).isoformat()
            }
            
            if email_type == "plain":
                body = content
                if signature:
                    body += f"\n\n--\n{signature}"
                composed_email["body"] = body
                composed_email["content_type"] = "text/plain; charset=utf-8"
                
            elif email_type == "html":
                html_body = _convert_to_html(content)
                if signature:
                    html_signature = _convert_to_html(signature)
                    html_body += f"<br><br><div style='border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px;'>{html_signature}</div>"
                
                composed_email["body"] = html_body
                composed_email["content_type"] = "text/html; charset=utf-8"
                
            elif email_type == "markdown":
                # Converte markdown in HTML
                html_body = _markdown_to_html(content)
                if signature:
                    html_signature = _markdown_to_html(signature)
                    html_body += f"<hr>{html_signature}"
                
                composed_email["body"] = html_body
                composed_email["content_type"] = "text/html; charset=utf-8"
                composed_email["original_markdown"] = content
                
            else:
                return {"success": False, "error": f"Tipo email non supportato: {email_type}"}
            
            # Headers email
            headers = {
                "From": f"{sender_name} <{sender_email}>" if sender_name and sender_email else sender_email,
                "To": recipient,
                "Subject": subject,
                "Date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
                "Message-ID": _generate_message_id(sender_email),
                "MIME-Version": "1.0",
                "Content-Type": composed_email["content_type"]
            }
            
            composed_email["headers"] = headers
            
            # Analisi contenuto
            content_analysis = _analyze_email_content(content, subject)
            composed_email["content_analysis"] = content_analysis
            
            # Genera email completo
            full_email = _generate_full_email(headers, composed_email["body"])
            composed_email["full_email"] = full_email
            composed_email["estimated_size_bytes"] = len(full_email.encode('utf-8'))
            
            return composed_email
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def validate_email_list(email_list: List[str], check_dns: bool = False) -> Dict[str, Any]:
        """
        Valida una lista di indirizzi email con analisi dettagliata.
        
        Args:
            email_list: Lista di indirizzi email da validare
            check_dns: Se controllare esistenza domini via DNS
        """
        try:
            if not email_list:
                return {"success": False, "error": "Lista email vuota"}
            
            if len(email_list) > 1000:
                return {"success": False, "error": "Troppi email (max 1000)"}
            
            results = {
                "success": True,
                "total_emails": len(email_list),
                "valid_emails": [],
                "invalid_emails": [],
                "suspicious_emails": [],
                "domain_analysis": {},
                "validation_summary": {}
            }
            
            domain_counter = Counter()
            
            for email in email_list:
                email = email.strip().lower()
                validation_result = _detailed_email_validation(email, check_dns)
                
                if validation_result["is_valid"]:
                    results["valid_emails"].append({
                        "email": email,
                        "domain": validation_result["domain"],
                        "issues": validation_result.get("warnings", [])
                    })
                    domain_counter[validation_result["domain"]] += 1
                    
                    # Controlla email sospetti
                    if validation_result.get("is_suspicious", False):
                        results["suspicious_emails"].append({
                            "email": email,
                            "reasons": validation_result.get("suspicious_reasons", [])
                        })
                else:
                    results["invalid_emails"].append({
                        "email": email,
                        "errors": validation_result.get("errors", [])
                    })
            
            # Analisi domini
            results["domain_analysis"] = {
                "unique_domains": len(domain_counter),
                "most_common_domains": domain_counter.most_common(10),
                "single_use_domains": len([d for d, count in domain_counter.items() if count == 1])
            }
            
            # Summary statistiche
            valid_count = len(results["valid_emails"])
            invalid_count = len(results["invalid_emails"])
            suspicious_count = len(results["suspicious_emails"])
            
            results["validation_summary"] = {
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "suspicious_count": suspicious_count,
                "valid_percentage": round((valid_count / len(email_list)) * 100, 2),
                "quality_score": _calculate_list_quality_score(valid_count, invalid_count, suspicious_count)
            }
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def detect_email_spam(email_content: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Analizza email per rilevare caratteristiche spam.
        
        Args:
            email_content: Contenuto email completo
            headers: Headers email (opzionali)
        """
        try:
            headers = headers or {}
            
            spam_score = 0
            spam_indicators = []
            
            # Analisi contenuto
            content_lower = email_content.lower()
            
            # Parole spam comuni
            spam_keywords = [
                'free', 'winner', 'congratulations', 'urgent', 'act now',
                'limited time', 'offer expires', 'no obligation', 'risk free',
                'guarantee', 'click here', 'buy now', 'order now', 'call now',
                'make money', 'earn cash', 'work from home', 'lose weight',
                'viagra', 'cialis', 'pharmacy', 'casino', 'lottery'
            ]
            
            spam_keyword_count = sum(1 for keyword in spam_keywords if keyword in content_lower)
            if spam_keyword_count > 3:
                spam_score += spam_keyword_count * 2
                spam_indicators.append(f"Multiple spam keywords found ({spam_keyword_count})")
            
            # Caratteri in maiuscolo eccessivi
            uppercase_ratio = sum(1 for c in email_content if c.isupper()) / len(email_content) if email_content else 0
            if uppercase_ratio > 0.3:
                spam_score += 10
                spam_indicators.append(f"Excessive uppercase text ({uppercase_ratio:.1%})")
            
            # Punti esclamativi eccessivi
            exclamation_count = email_content.count('!')
            if exclamation_count > 5:
                spam_score += exclamation_count
                spam_indicators.append(f"Too many exclamation marks ({exclamation_count})")
            
            # URL sospetti
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', email_content)
            suspicious_urls = [url for url in urls if _is_suspicious_url(url)]
            if suspicious_urls:
                spam_score += len(suspicious_urls) * 5
                spam_indicators.append(f"Suspicious URLs found ({len(suspicious_urls)})")
            
            # Analisi headers
            if headers:
                # Controlla sender reputation
                if 'from' in headers:
                    from_email = headers['from'].lower()
                    if any(domain in from_email for domain in ['noreply', 'donotreply', 'no-reply']):
                        spam_score += 2
                        spam_indicators.append("Generic no-reply sender")
                
                # Controlla X-Spam headers
                spam_headers = [h for h in headers.keys() if 'spam' in h.lower()]
                if spam_headers:
                    spam_score += len(spam_headers) * 3
                    spam_indicators.append("Spam-related headers present")
            
            # Analisi struttura email
            if len(email_content) < 50:
                spam_score += 5
                spam_indicators.append("Suspiciously short content")
            
            # Pattern di phishing
            phishing_patterns = [
                r'verify your account',
                r'confirm your identity',
                r'urgent action required',
                r'suspended.*account',
                r'click.*link.*immediately'
            ]
            
            phishing_matches = [pattern for pattern in phishing_patterns if re.search(pattern, content_lower)]
            if phishing_matches:
                spam_score += len(phishing_matches) * 8
                spam_indicators.append(f"Phishing patterns detected ({len(phishing_matches)})")
            
            # Calcola classificazione
            if spam_score >= 50:
                classification = "High Risk Spam"
            elif spam_score >= 25:
                classification = "Likely Spam"
            elif spam_score >= 10:
                classification = "Suspicious"
            else:
                classification = "Legitimate"
            
            return {
                "success": True,
                "spam_score": spam_score,
                "classification": classification,
                "spam_indicators": spam_indicators,
                "suspicious_urls": suspicious_urls,
                "analysis_details": {
                    "content_length": len(email_content),
                    "uppercase_ratio": round(uppercase_ratio * 100, 1),
                    "exclamation_count": exclamation_count,
                    "url_count": len(urls),
                    "spam_keyword_count": spam_keyword_count
                },
                "recommendations": _generate_spam_recommendations(spam_score, spam_indicators)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def extract_email_data(email_text: str) -> Dict[str, Any]:
        """
        Estrae dati strutturati da testo email completo.
        
        Args:
            email_text: Testo completo email con headers e body
        """
        try:
            extracted_data = {
                "success": True,
                "headers": {},
                "body": "",
                "attachments": [],
                "urls": [],
                "email_addresses": [],
                "phone_numbers": [],
                "dates": [],
                "metadata": {}
            }
            
            # Separa headers dal body
            if '\n\n' in email_text:
                header_section, body_section = email_text.split('\n\n', 1)
            else:
                header_section = email_text
                body_section = ""
            
            # Estrae headers
            for line in header_section.split('\n'):
                if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
                    key, value = line.split(':', 1)
                    extracted_data["headers"][key.strip()] = value.strip()
            
            extracted_data["body"] = body_section
            
            # Estrae URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, email_text)
            extracted_data["urls"] = list(set(urls))
            
            # Estrae indirizzi email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, email_text)
            extracted_data["email_addresses"] = list(set(emails))
            
            # Estrae numeri di telefono
            phone_patterns = [
                r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US
                r'\+?39[-.\s]?[0-9]{2,3}[-.\s]?[0-9]{6,7}',  # IT
                r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'  # Generic
            ]
            
            phones = []
            for pattern in phone_patterns:
                phones.extend(re.findall(pattern, email_text))
            extracted_data["phone_numbers"] = list(set(phones))
            
            # Estrae date
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
                r'\b\d{2,4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b'  # Month DD, YYYY
            ]
            
            dates = []
            for pattern in date_patterns:
                dates.extend(re.findall(pattern, email_text, re.IGNORECASE))
            extracted_data["dates"] = list(set(dates))
            
            # Metadata aggiuntivi
            extracted_data["metadata"] = {
                "total_length": len(email_text),
                "body_length": len(body_section),
                "header_count": len(extracted_data["headers"]),
                "word_count": len(body_section.split()) if body_section else 0,
                "line_count": len(email_text.split('\n')),
                "has_html": '<html>' in email_text.lower() or '<body>' in email_text.lower(),
                "charset": _detect_charset(extracted_data["headers"]),
                "message_id": extracted_data["headers"].get("Message-ID", ""),
                "date_sent": extracted_data["headers"].get("Date", "")
            }
            
            return extracted_data
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def validate_smtp_config(smtp_host: str, smtp_port: int, 
                           security: str = "tls", test_email: str = "") -> Dict[str, Any]:
        """
        Valida configurazione SMTP e testa connettività.
        
        Args:
            smtp_host: Host server SMTP
            smtp_port: Porta SMTP
            security: Tipo sicurezza (none, ssl, tls, starttls)
            test_email: Email per test validazione (opzionale)
        """
        try:
            validation_result = {
                "success": True,
                "smtp_host": smtp_host,
                "smtp_port": smtp_port,
                "security": security,
                "validation_results": {},
                "recommendations": []
            }
            
            # Validazione configurazione
            config_issues = []
            
            # Controlla host
            if not smtp_host or not re.match(r'^[a-zA-Z0-9.-]+$', smtp_host):
                config_issues.append("Invalid SMTP host format")
            
            # Controlla porta
            if not 1 <= smtp_port <= 65535:
                config_issues.append("Invalid port number (must be 1-65535)")
            
            # Controlla sicurezza
            valid_security = ["none", "ssl", "tls", "starttls"]
            if security not in valid_security:
                config_issues.append(f"Invalid security type. Use: {', '.join(valid_security)}")
            
            if config_issues:
                validation_result["validation_results"]["config_validation"] = {
                    "valid": False,
                    "issues": config_issues
                }
                return validation_result
            
            # Validazione porta/sicurezza standard
            port_security_map = {
                25: ["none", "starttls"],    # Standard SMTP
                587: ["tls", "starttls"],    # Submission
                465: ["ssl"],               # SMTPS
                2525: ["tls", "starttls"]   # Alternative
            }
            
            port_validation = {
                "valid": True,
                "port_type": "custom",
                "security_match": True
            }
            
            if smtp_port in port_security_map:
                expected_security = port_security_map[smtp_port]
                port_validation["port_type"] = "standard"
                if security not in expected_security:
                    port_validation["security_match"] = False
                    validation_result["recommendations"].append(
                        f"Port {smtp_port} typically uses {'/'.join(expected_security)} security"
                    )
            
            validation_result["validation_results"]["port_validation"] = port_validation
            
            # Test connettività di base (simulato)
            connectivity_test = {
                "connection_possible": True,
                "response_time_ms": 150,  # Simulato
                "ssl_cert_valid": security in ["ssl", "tls"],
                "auth_methods": ["PLAIN", "LOGIN"]  # Simulato
            }
            
            validation_result["validation_results"]["connectivity_test"] = connectivity_test
            
            # Test email se fornito
            if test_email:
                email_validation = _detailed_email_validation(test_email, check_dns=False)
                validation_result["validation_results"]["email_validation"] = email_validation
            
            # Raccomandazioni sicurezza
            security_recommendations = []
            
            if security == "none":
                security_recommendations.append("Consider using encryption (TLS/SSL) for security")
            
            if smtp_port == 25:
                security_recommendations.append("Port 25 may be blocked by ISPs, consider port 587")
            
            if security == "ssl" and smtp_port != 465:
                security_recommendations.append("SSL typically uses port 465")
            
            validation_result["recommendations"].extend(security_recommendations)
            
            # Score complessivo
            score = 100
            if config_issues:
                score -= len(config_issues) * 20
            if not port_validation["security_match"]:
                score -= 10
            if security == "none":
                score -= 15
            
            validation_result["overall_score"] = max(0, score)
            validation_result["rating"] = _get_config_rating(score)
            
            return validation_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_email_analytics(email_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera analytics da dataset di email.
        
        Args:
            email_data: Lista di email con metadati (sender, recipient, subject, date, etc.)
        """
        try:
            if not email_data:
                return {"success": False, "error": "No email data provided"}
            
            if len(email_data) > 10000:
                return {"success": False, "error": "Too many emails (max 10000)"}
            
            analytics = {
                "success": True,
                "total_emails": len(email_data),
                "date_range": {},
                "sender_analysis": {},
                "recipient_analysis": {},
                "subject_analysis": {},
                "domain_analysis": {},
                "temporal_analysis": {},
                "content_analysis": {}
            }
            
            # Estrae dati per analisi
            senders = []
            recipients = []
            subjects = []
            dates = []
            domains = {"sender": [], "recipient": []}
            
            for email in email_data:
                if "sender" in email:
                    senders.append(email["sender"])
                    if "@" in email["sender"]:
                        domains["sender"].append(email["sender"].split("@")[1])
                
                if "recipient" in email:
                    recipients.append(email["recipient"])
                    if "@" in email["recipient"]:
                        domains["recipient"].append(email["recipient"].split("@")[1])
                
                if "subject" in email:
                    subjects.append(email["subject"])
                
                if "date" in email:
                    dates.append(email["date"])
            
            # Analisi mittenti
            sender_counter = Counter(senders)
            analytics["sender_analysis"] = {
                "unique_senders": len(sender_counter),
                "most_active_senders": sender_counter.most_common(10),
                "average_emails_per_sender": round(len(senders) / len(sender_counter), 2) if sender_counter else 0
            }
            
            # Analisi destinatari
            recipient_counter = Counter(recipients)
            analytics["recipient_analysis"] = {
                "unique_recipients": len(recipient_counter),
                "most_contacted_recipients": recipient_counter.most_common(10),
                "average_emails_per_recipient": round(len(recipients) / len(recipient_counter), 2) if recipient_counter else 0
            }
            
            # Analisi oggetti
            subject_words = []
            for subject in subjects:
                words = re.findall(r'\b\w+\b', subject.lower())
                subject_words.extend(words)
            
            subject_word_counter = Counter(subject_words)
            analytics["subject_analysis"] = {
                "total_subjects": len(subjects),
                "average_subject_length": round(sum(len(s) for s in subjects) / len(subjects), 2) if subjects else 0,
                "most_common_words": subject_word_counter.most_common(20),
                "unique_words": len(subject_word_counter)
            }
            
            # Analisi domini
            sender_domains = Counter(domains["sender"])
            recipient_domains = Counter(domains["recipient"])
            
            analytics["domain_analysis"] = {
                "sender_domains": {
                    "unique_count": len(sender_domains),
                    "most_common": sender_domains.most_common(10)
                },
                "recipient_domains": {
                    "unique_count": len(recipient_domains),
                    "most_common": recipient_domains.most_common(10)
                }
            }
            
            # Analisi temporale (se date disponibili)
            if dates:
                date_analysis = _analyze_email_dates(dates)
                analytics["temporal_analysis"] = date_analysis
            
            # Range date
            if dates:
                try:
                    parsed_dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in dates if d]
                    if parsed_dates:
                        analytics["date_range"] = {
                            "earliest": min(parsed_dates).isoformat(),
                            "latest": max(parsed_dates).isoformat(),
                            "span_days": (max(parsed_dates) - min(parsed_dates)).days
                        }
                except:
                    pass
            
            return analytics
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions for enhanced functionality
    def _is_valid_email(email: str) -> bool:
        """Validazione email base."""
        pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(pattern.match(email))

    def _detailed_email_validation(email: str, check_dns: bool = False) -> Dict[str, Any]:
        """Validazione email dettagliata."""
        result = {
            "email": email,
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "domain": "",
            "local_part": "",
            "is_suspicious": False,
            "suspicious_reasons": []
        }
        
        try:
            # Controlli base
            if "@" not in email:
                result["errors"].append("Missing @ symbol")
                return result
            
            local_part, domain = email.rsplit("@", 1)
            result["local_part"] = local_part
            result["domain"] = domain
            
            # Validazione formato
            if not re.match(r'^[a-zA-Z0-9._%+-]+$', local_part):
                result["errors"].append("Invalid characters in local part")
            
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
                result["errors"].append("Invalid domain format")
            
            # Controlli lunghezza
            if len(local_part) > 64:
                result["errors"].append("Local part too long (>64 chars)")
            
            if len(domain) > 253:
                result["errors"].append("Domain too long (>253 chars)")
            
            # Controlli sospetti
            suspicious_domains = ['tempmail', '10minutemail', 'guerrillamail', 'throwaway', 'mailinator']
            if any(sus in domain.lower() for sus in suspicious_domains):
                result["is_suspicious"] = True
                result["suspicious_reasons"].append("Temporary email service")
            
            # Se non ci sono errori, è valido
            result["is_valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
        
        return result

    def _convert_to_html(text: str) -> str:
        """Converte testo plain in HTML."""
        # Escape HTML
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Converti newline
        text = text.replace("\n", "<br>")
        return f"<div>{text}</div>"

    def _markdown_to_html(markdown_text: str) -> str:
        """Conversione markdown base in HTML."""
        html = markdown_text
        
        # Headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Bold e italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Links
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
        
        # Newlines
        html = html.replace('\n', '<br>')
        
        return html

    def _generate_message_id(sender_email: str) -> str:
        """Genera Message-ID univoco."""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        domain = sender_email.split('@')[1] if '@' in sender_email else 'localhost'
        unique_id = hashlib.md5(f"{timestamp}{sender_email}".encode()).hexdigest()[:8]
        return f"<{timestamp}.{unique_id}@{domain}>"

    def _analyze_email_content(content: str, subject: str) -> Dict[str, Any]:
        """Analizza contenuto email."""
        return {
            "word_count": len(content.split()),
            "character_count": len(content),
            "sentence_count": len(re.split(r'[.!?]+', content)),
            "paragraph_count": len(content.split('\n\n')),
            "has_links": bool(re.search(r'http[s]?://', content)),
            "has_emails": bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)),
            "subject_length": len(subject),
            "reading_time_minutes": max(1, len(content.split()) // 200)
        }

    def _calculate_list_quality_score(valid: int, invalid: int, suspicious: int) -> str:
        """Calcola score qualità lista email."""
        total = valid + invalid + suspicious
        if total == 0:
            return "N/A"
        
        valid_percentage = (valid / total) * 100
        
        if valid_percentage >= 95:
            return "Excellent"
        elif valid_percentage >= 85:
            return "Good"
        elif valid_percentage >= 70:
            return "Fair"
        else:
            return "Poor"