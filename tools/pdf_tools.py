# -*- coding: utf-8 -*-
# tools/pdf_tools.py
import logging
import base64
import io
import json
import hashlib
from datetime import datetime

def register_tools(mcp):
    """Registra i tool per PDF con l'istanza del server MCP."""
    logging.info("📄 Registrazione tool-set: PDF Tools")

    @mcp.tool()
    def analyze_pdf_metadata(pdf_base64: str) -> str:
        """
        Analizza i metadati di un file PDF con controlli avanzati.

        Args:
            pdf_base64: Il file PDF codificato in base64.
        """
        try:
            if not pdf_base64.strip():
                return "ERRORE: Il contenuto PDF base64 non può essere vuoto"
            
            # Decodifica base64
            try:
                pdf_data = base64.b64decode(pdf_base64)
            except Exception as e:
                return f"ERRORE: Decodifica base64 fallita: {str(e)}"
            
            # Controllo dimensione minima
            if len(pdf_data) < 50:
                return "ERRORE: File troppo piccolo per essere un PDF valido"
            
            result = "=== ANALISI METADATI PDF AVANZATA ===\n"
            result += f"Dimensione file: {len(pdf_data):,} bytes ({len(pdf_data)/1024:.1f} KB)\n"
            
            # Hash del file per identificazione
            file_hash = hashlib.md5(pdf_data).hexdigest()
            result += f"Hash MD5: {file_hash}\n"
            
            # Converti in stringa per analisi testuale
            try:
                pdf_str = pdf_data.decode('latin1', errors='ignore')
                
                # Verifica header PDF con versione estesa
                if pdf_str.startswith('%PDF-'):
                    version_line = pdf_str.split('\n')[0]
                    result += f"Header PDF: {version_line.strip()}\n"
                    
                    if '%PDF-' in version_line:
                        version = version_line.split('%PDF-')[1].split()[0]
                        result += f"Versione PDF: {version}\n"
                        
                        # Interpretazione versione
                        version_info = {
                            '1.0': 'PDF 1.0 (1993) - Versione base',
                            '1.1': 'PDF 1.1 (1996) - Link esterni',
                            '1.2': 'PDF 1.2 (1996) - Compressione oggetti',
                            '1.3': 'PDF 1.3 (2000) - Firma digitale',
                            '1.4': 'PDF 1.4 (2001) - Trasparenza',
                            '1.5': 'PDF 1.5 (2003) - Layer oggetti',
                            '1.6': 'PDF 1.6 (2005) - AES crittografia',
                            '1.7': 'PDF 1.7 (2006) - Standard ISO',
                            '2.0': 'PDF 2.0 (2017) - Standard moderno'
                        }
                        if version in version_info:
                            result += f"Info versione: {version_info[version]}\n"
                else:
                    return "ERRORE: File non riconosciuto come PDF valido"
                
                # Analisi struttura avanzata
                obj_count = pdf_str.count(' obj')
                result += f"Oggetti PDF: {obj_count}\n"
                
                # Conta pagine con metodi multipli
                page_patterns = [
                    pdf_str.count('/Type/Page'),
                    pdf_str.count('/Type /Page'),
                    pdf_str.count('<<\n/Type/Page'),
                    pdf_str.count('<< /Type /Page')
                ]
                page_count = max(page_patterns) if page_patterns else 0
                result += f"Pagine rilevate: {page_count}\n"
                
                # Analisi metadati estesa
                metadata_fields = {
                    '/Title': 'Titolo',
                    '/Author': 'Autore', 
                    '/Subject': 'Oggetto',
                    '/Creator': 'Creatore',
                    '/Producer': 'Produttore',
                    '/CreationDate': 'Data creazione',
                    '/ModDate': 'Data modifica',
                    '/Keywords': 'Parole chiave',
                    '/Trapped': 'Trapping info'
                }
                
                result += "\n--- METADATI RILEVATI ---\n"
                found_metadata = False
                for field, label in metadata_fields.items():
                    if field in pdf_str:
                        found_metadata = True
                        # Tentativo di estrazione valore migliorato
                        try:
                            start_idx = pdf_str.find(field)
                            if start_idx != -1:
                                # Cerca il valore tra parentesi o dopo /
                                substr = pdf_str[start_idx:start_idx+200]
                                if '(' in substr and ')' in substr:
                                    value_start = substr.find('(') + 1
                                    value_end = substr.find(')', value_start)
                                    if value_end > value_start:
                                        value = substr[value_start:value_end]
                                        result += f"{label}: {value[:50]}\n"
                                    else:
                                        result += f"{label}: Presente\n"
                                else:
                                    result += f"{label}: Presente\n"
                        except:
                            result += f"{label}: Presente\n"
                
                if not found_metadata:
                    result += "Nessun metadato standard rilevato\n"
                
                # Analisi contenuto avanzata
                result += "\n--- ANALISI CONTENUTO ---\n"
                
                # Analisi immagini
                image_patterns = ['/Image', '/XObject', '/DCTDecode', '/JPXDecode']
                image_indicators = sum(1 for pattern in image_patterns if pattern in pdf_str)
                if image_indicators > 0:
                    result += f"Immagini: Probabilmente presenti ({image_indicators} indicatori)\n"
                
                # Analisi font
                font_count = pdf_str.count('/Font')
                font_types = []
                if '/Type1' in pdf_str: font_types.append('Type1')
                if '/TrueType' in pdf_str: font_types.append('TrueType') 
                if '/CIDFont' in pdf_str: font_types.append('CID')
                if '/Type0' in pdf_str: font_types.append('Composite')
                
                result += f"Font rilevati: {font_count}\n"
                if font_types:
                    result += f"Tipi font: {', '.join(font_types)}\n"
                
                # Analisi funzionalità
                result += "\n--- FUNZIONALITÀ ---\n"
                
                if '/Outlines' in pdf_str:
                    result += "Bookmarks/Segnalibri: Presenti\n"
                
                if '/AcroForm' in pdf_str:
                    result += "Campi modulo: Presenti\n"
                    if '/Sig' in pdf_str:
                        result += "Campi firma: Presenti\n"
                
                if '/Annot' in pdf_str:
                    result += "Annotazioni: Presenti\n"
                
                if '/JavaScript' in pdf_str or '/JS' in pdf_str:
                    result += "JavaScript: Presente (attenzione sicurezza)\n"
                
                if '/EmbeddedFile' in pdf_str:
                    result += "File allegati: Presenti\n"
                
                # Analisi sicurezza
                result += "\n--- SICUREZZA ---\n"
                if '/Encrypt' in pdf_str:
                    result += "Crittografia: PDF protetto\n"
                    if '/P ' in pdf_str:
                        result += "Permessi: Restrizioni attive\n"
                else:
                    result += "Crittografia: Non protetto\n"
                
                # Stima qualità
                result += "\n--- VALUTAZIONE QUALITÀ ---\n"
                quality_score = 0
                
                if page_count > 0: quality_score += 1
                if found_metadata: quality_score += 1  
                if obj_count > 5: quality_score += 1
                if font_count > 0: quality_score += 1
                if '/Outlines' in pdf_str: quality_score += 1
                
                result += f"Punteggio qualità: {quality_score}/5\n"
                
                if quality_score >= 4:
                    result += "Valutazione: PDF ben strutturato\n"
                elif quality_score >= 2:
                    result += "Valutazione: PDF standard\n"
                else:
                    result += "Valutazione: PDF semplice/limitato\n"
                
            except Exception as e:
                result += f"Errore nell'analisi approfondita: {str(e)}\n"
                result += "NOTA: File PDF binario - analisi limitata senza librerie specializzate."
            
            result += f"\n--- INFO ELABORAZIONE ---\n"
            result += f"Timestamp analisi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result += "Tool: Nexus MCP Server PDF Analyzer v2.0\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE CRITICO: {str(e)}"

    @mcp.tool()
    def create_simple_pdf_info(title: str, author: str = "", subject: str = "", pages: int = 1) -> str:
        """
        Crea informazioni per un PDF semplice (simulazione).

        Args:
            title: Titolo del documento.
            author: Autore del documento.
            subject: Oggetto/soggetto del documento.
            pages: Numero di pagine.
        """
        try:
            if not title.strip():
                return "ERRORE: Il titolo non può essere vuoto"
            
            if pages < 1 or pages > 10000:
                return "ERRORE: Il numero di pagine deve essere tra 1 e 10000"
            
            # Simula la creazione di un PDF (in realtà genera solo le info)
            result = "=== INFORMAZIONI PDF SIMULATO ===\n"
            result += f"Titolo: {title}\n"
            result += f"Autore: {author if author else 'Non specificato'}\n"
            result += f"Oggetto: {subject if subject else 'Non specificato'}\n"
            result += f"Pagine: {pages}\n"
            result += f"Versione PDF: 1.4\n"
            result += f"Dimensione stimata: {pages * 50} KB\n"
            result += f"Data creazione: [TIMESTAMP_CORRENTE]\n"
            result += f"Produttore: Nexus MCP Server PDF Tools\n\n"
            
            # Struttura PDF base (esempio)
            result += "STRUTTURA PDF BASE:\n"
            result += "%PDF-1.4\n"
            result += "1 0 obj\n"
            result += "<<\n"
            result += f"/Title ({title})\n"
            if author:
                result += f"/Author ({author})\n"
            if subject:
                result += f"/Subject ({subject})\n"
            result += "/Producer (Nexus MCP Server)\n"
            result += ">>\n"
            result += "endobj\n\n"
            
            result += f"% ... {pages} pagine di contenuto ...\n\n"
            result += "NOTA: Questo è un esempio di struttura PDF - per creare PDF reali usa librerie come reportlab."
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def pdf_text_extraction_guide() -> str:
        """
        Fornisce una guida per l'estrazione di testo da PDF.
        """
        try:
            guide = """=== GUIDA ESTRAZIONE TESTO PDF ===

📚 METODOLOGIE DISPONIBILI:

1. 🐍 PyPDF2/PyPDF4
   - Libreria Python popolare
   - Buona per PDF testuali semplici
   - Limitata con PDF complessi
   
   Esempio:
   ```python
   import PyPDF2
   with open('file.pdf', 'rb') as file:
       reader = PyPDF2.PdfReader(file)
       text = ""
       for page in reader.pages:
           text += page.extract_text()
   ```

2. 📖 pdfplumber
   - Estrazione testo più accurata
   - Preserva layout e formattazione
   - Migliore gestione tabelle
   
   Esempio:
   ```python
   import pdfplumber
   with pdfplumber.open('file.pdf') as pdf:
       for page in pdf.pages:
           text = page.extract_text()
   ```

3. ⚡ pdfminer
   - Analisi dettagliata layout
   - Controllo completo estrazione
   - Più complesso da usare
   
4. 🔧 pymupdf (fitz)
   - Veloce e potente
   - Supporta molti formati
   - Estrazione immagini inclusa

📊 TIPI DI PDF:

✅ PDF Testuali:
- Testo selezionabile
- Estrazione diretta possibile
- Metodi software funzionano bene

❌ PDF Scansionati (Immagini):
- Testo non selezionabile
- Richiedono OCR (Optical Character Recognition)
- Usa tesseract o servizi cloud

🔧 TOOLS OCR:

1. Tesseract (Open Source)
   ```bash
   pip install pytesseract
   apt-get install tesseract-ocr
   ```

2. Cloud Services:
   - Google Cloud Vision API
   - AWS Textract
   - Azure Computer Vision

📋 PROBLEMI COMUNI:

1. Caratteri Speciali:
   - Encoding issues
   - Font embedded problems
   - Soluzioni: prova diverse librerie

2. Layout Complesso:
   - Colonne multiple
   - Tabelle complesse
   - Soluzioni: pdfplumber o layout analysis

3. PDF Protetti:
   - Password required
   - Restrictions on text extraction
   - Check permissions first

💡 BEST PRACTICES:

1. Testa con campioni piccoli
2. Verifica qualità estrazione
3. Gestisci encoding UTF-8
4. Considera preprocessing
5. Valida output per accuratezza

🛠️ IMPLEMENTAZIONE SUGGERITA:

```python
def extract_pdf_text(pdf_path):
    methods = ['pdfplumber', 'PyPDF2', 'pymupdf']
    
    for method in methods:
        try:
            if method == 'pdfplumber':
                # Prova pdfplumber
                pass
            elif method == 'PyPDF2':
                # Fallback a PyPDF2
                pass
            # etc...
        except:
            continue
    
    return "Estrazione fallita"
```

⚠️ LIMITAZIONI NEXUS:
- Implementazione attuale semplificata
- Per produzione: aggiungi librerie PDF
- Considera ambiente sandbox"""

            return guide
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def validate_pdf_structure(pdf_base64: str) -> str:
        """
        Valida la struttura base di un file PDF.

        Args:
            pdf_base64: Il file PDF codificato in base64.
        """
        try:
            if not pdf_base64.strip():
                return "ERRORE: Il contenuto PDF base64 non può essere vuoto"
            
            # Decodifica base64
            try:
                pdf_data = base64.b64decode(pdf_base64)
            except Exception as e:
                return f"ERRORE: Decodifica base64 fallita: {str(e)}"
            
            result = "=== VALIDAZIONE STRUTTURA PDF ===\n"
            
            # Test 1: Dimensione minima
            if len(pdf_data) < 100:
                result += "❌ FALLITO: File troppo piccolo per essere un PDF valido\n"
                return result
            
            result += f"✅ Dimensione: {len(pdf_data)} bytes (OK)\n"
            
            # Test 2: Header PDF
            header = pdf_data[:10].decode('latin1', errors='ignore')
            if header.startswith('%PDF-'):
                version = header[5:8]
                result += f"✅ Header: {header.strip()} (OK)\n"
                result += f"✅ Versione: {version} (OK)\n"
            else:
                result += "❌ FALLITO: Header PDF non trovato\n"
                return result
            
            # Test 3: Footer PDF
            footer = pdf_data[-50:].decode('latin1', errors='ignore')
            if '%%EOF' in footer:
                result += "✅ Footer: %%EOF trovato (OK)\n"
            else:
                result += "⚠️ ATTENZIONE: Footer %%EOF non trovato\n"
            
            # Test 4: Oggetti PDF
            pdf_str = pdf_data.decode('latin1', errors='ignore')
            obj_count = pdf_str.count(' obj')
            if obj_count > 0:
                result += f"✅ Oggetti PDF: {obj_count} trovati (OK)\n"
            else:
                result += "❌ FALLITO: Nessun oggetto PDF trovato\n"
            
            # Test 5: Cross-reference table
            if 'xref' in pdf_str:
                result += "✅ Tabella xref: Trovata (OK)\n"
            else:
                result += "⚠️ ATTENZIONE: Tabella xref non trovata\n"
            
            # Test 6: Catalog root
            if '/Type/Catalog' in pdf_str:
                result += "✅ Catalog root: Trovato (OK)\n"
            else:
                result += "⚠️ ATTENZIONE: Catalog root non trovato\n"
            
            # Test 7: Pages object
            if '/Type/Pages' in pdf_str:
                result += "✅ Oggetto Pages: Trovato (OK)\n"
            else:
                result += "⚠️ ATTENZIONE: Oggetto Pages non trovato\n"
            
            # Riassunto
            result += "\n=== RIASSUNTO VALIDAZIONE ===\n"
            
            # Conta i test passati
            passed_tests = result.count('✅')
            warning_tests = result.count('⚠️')
            failed_tests = result.count('❌')
            
            result += f"Test passati: {passed_tests}\n"
            result += f"Warning: {warning_tests}\n"
            result += f"Test falliti: {failed_tests}\n"
            
            if failed_tests == 0:
                if warning_tests == 0:
                    result += "🎉 RISULTATO: PDF strutturalmente valido\n"
                else:
                    result += "✅ RISULTATO: PDF probabilmente valido (con warning)\n"
            else:
                result += "❌ RISULTATO: PDF potenzialmente corrotto o non valido\n"
            
            result += "\nNOTA: Validazione semplificata - per controlli completi usa tool PDF specializzati."
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def pdf_security_check(pdf_base64: str) -> str:
        """
        Controlla le impostazioni di sicurezza di un PDF.

        Args:
            pdf_base64: Il file PDF codificato in base64.
        """
        try:
            if not pdf_base64.strip():
                return "ERRORE: Il contenuto PDF base64 non può essere vuoto"
            
            # Decodifica base64
            try:
                pdf_data = base64.b64decode(pdf_base64)
            except Exception as e:
                return f"ERRORE: Decodifica base64 fallita: {str(e)}"
            
            result = "=== CONTROLLO SICUREZZA PDF ===\n"
            
            # Converti in stringa per analisi
            pdf_str = pdf_data.decode('latin1', errors='ignore')
            
            # Controlla crittografia
            if '/Encrypt' in pdf_str:
                result += "🔒 CRITTOGRAFIA: PDF protetto da password\n"
                
                # Cerca informazioni sui permessi
                if '/P ' in pdf_str:
                    result += "🔐 PERMESSI: Restrizioni sui permessi rilevate\n"
                
                # Cerca livello di crittografia
                if '/V ' in pdf_str:
                    result += "📊 VERSIONE CRITTOGRAFIA: Specificata nel documento\n"
                
                if '/R ' in pdf_str:
                    result += "🔢 REVISIONE CRITTOGRAFIA: Specificata nel documento\n"
                
            else:
                result += "🔓 CRITTOGRAFIA: PDF non protetto\n"
            
            # Controlla signature
            if '/Sig' in pdf_str or '/Signature' in pdf_str:
                result += "✍️ FIRMA DIGITALE: Potenzialmente presente\n"
            else:
                result += "📝 FIRMA DIGITALE: Non rilevata\n"
            
            # Controlla JavaScript
            if '/JavaScript' in pdf_str or '/JS' in pdf_str:
                result += "⚠️ JAVASCRIPT: Codice JavaScript rilevato\n"
                result += "   ATTENZIONE: Potenziale rischio sicurezza\n"
            else:
                result += "✅ JAVASCRIPT: Nessun JavaScript rilevato\n"
            
            # Controlla form fields
            if '/AcroForm' in pdf_str:
                result += "📝 CAMPI MODULO: Presenti (interattività rilevata)\n"
            else:
                result += "📄 CAMPI MODULO: Non presenti\n"
            
            # Controlla embedded files
            if '/EmbeddedFile' in pdf_str or '/FileAttachment' in pdf_str:
                result += "📎 FILE ALLEGATI: Potenzialmente presenti\n"
                result += "   ATTENZIONE: Verifica contenuto allegati\n"
            else:
                result += "📄 FILE ALLEGATI: Non rilevati\n"
            
            # Controlla URI/link esterni
            if '/URI' in pdf_str or 'http' in pdf_str.lower():
                result += "🔗 LINK ESTERNI: Potenzialmente presenti\n"
                result += "   INFO: PDF potrebbe contenere link web\n"
            else:
                result += "📋 LINK ESTERNI: Non rilevati\n"
            
            # Raccomandazioni sicurezza
            result += "\n=== RACCOMANDAZIONI SICUREZZA ===\n"
            
            security_score = 0
            
            if '/Encrypt' not in pdf_str:
                result += "⚠️ Considera crittografia per dati sensibili\n"
            else:
                security_score += 2
            
            if '/JavaScript' in pdf_str or '/JS' in pdf_str:
                result += "⚠️ Disabilita JavaScript nel visualizzatore PDF\n"
                security_score -= 1
            else:
                security_score += 1
            
            if '/EmbeddedFile' in pdf_str:
                result += "⚠️ Scansiona file allegati con antivirus\n"
                security_score -= 1
            else:
                security_score += 1
            
            result += "\n=== PUNTEGGIO SICUREZZA ===\n"
            result += f"Punteggio: {security_score}/4\n"
            
            if security_score >= 3:
                result += "✅ LIVELLO: Buono\n"
            elif security_score >= 1:
                result += "⚠️ LIVELLO: Medio - Attenzione necessaria\n"
            else:
                result += "❌ LIVELLO: Basso - Revisione richiesta\n"
            
            result += "\nNOTA: Analisi semplificata - per controlli completi usa tool di sicurezza PDF specializzati."
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def pdf_tools_info() -> str:
        """
        Fornisce informazioni complete sui tool PDF disponibili.
        """
        try:
            info = """=== INFORMAZIONI PDF TOOLS ===

📄 FUNZIONALITÀ DISPONIBILI:

1. 🔍 analyze_pdf_metadata()
   - Analizza metadati PDF base
   - Rileva versione e struttura
   - Conta pagine approssimativamente
   - Identifica presenza di elementi (font, immagini, etc.)

2. 📝 create_simple_pdf_info()
   - Simula creazione info PDF
   - Genera struttura PDF base
   - Mostra metadati essenziali
   - Stima dimensioni file

3. 📚 pdf_text_extraction_guide()
   - Guida completa estrazione testo
   - Confronta librerie disponibili
   - Suggerimenti OCR per PDF scansionati
   - Best practices implementazione

4. ✅ validate_pdf_structure()
   - Valida struttura PDF base
   - Controlla header e footer
   - Verifica oggetti essenziali
   - Punteggio validazione

5. 🔒 pdf_security_check()
   - Analizza sicurezza PDF
   - Rileva crittografia e permessi
   - Identifica JavaScript e allegati
   - Punteggio sicurezza e raccomandazioni

📋 LIMITAZIONI ATTUALI:

❌ Non supportato (richiede librerie):
- Estrazione testo completa
- Manipolazione pagine
- Conversione formati
- OCR automatico
- Firma digitale
- Crittografia/decrittografia

⚙️ PER IMPLEMENTAZIONE COMPLETA:

Installa librerie PDF:
```bash
pip install PyPDF2 pdfplumber pymupdf
pip install pytesseract  # Per OCR
```

Esempio implementazione:
```python
import PyPDF2
import pdfplumber

def full_pdf_analysis(pdf_path):
    # Estrazione testo
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    
    # Metadati
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        metadata = reader.metadata
        
    return text, metadata
```

🎯 CASI D'USO TIPICI:

1. Validazione PDF prima elaborazione
2. Controllo sicurezza documenti ricevuti
3. Analisi metadati per catalogazione
4. Guida implementazione estrazione testo
5. Diagnostica problemi PDF

💡 SUGGERIMENTI:

- Usa tools Nexus per analisi preliminare
- Per produzione: aggiungi librerie complete
- Testa sempre su campioni prima di batch processing
- Considera ambiente sandbox per PDF sconosciuti
- Backup sempre file originali prima modifiche

🔄 INTEGRAZIONE:

I tool PDF si integrano con:
- file_converter per conversioni
- crypto_tools per hash documenti
- validator_tools per controlli formato
- system_info per monitoring processing"""

            return info
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def compare_pdf_files(pdf1_base64: str, pdf2_base64: str) -> str:
        """
        Confronta due file PDF per trovare differenze strutturali.

        Args:
            pdf1_base64: Primo file PDF codificato in base64.
            pdf2_base64: Secondo file PDF codificato in base64.
        """
        try:
            if not pdf1_base64.strip() or not pdf2_base64.strip():
                return "ERRORE: Entrambi i file PDF devono essere forniti"
            
            # Decodifica entrambi i file
            try:
                pdf1_data = base64.b64decode(pdf1_base64)
                pdf2_data = base64.b64decode(pdf2_base64)
            except Exception as e:
                return f"ERRORE: Decodifica base64 fallita: {str(e)}"
            
            result = "=== CONFRONTO PDF FILES ===\n"
            
            # Confronto dimensioni
            size1, size2 = len(pdf1_data), len(pdf2_data)
            result += f"Dimensione PDF1: {size1:,} bytes\n"
            result += f"Dimensione PDF2: {size2:,} bytes\n"
            result += f"Differenza: {abs(size1-size2):,} bytes ({((abs(size1-size2)/max(size1,size2))*100):.1f}%)\n"
            
            # Hash comparison per identità
            hash1 = hashlib.md5(pdf1_data).hexdigest()
            hash2 = hashlib.md5(pdf2_data).hexdigest()
            result += f"\nHash PDF1: {hash1}\n"
            result += f"Hash PDF2: {hash2}\n"
            
            if hash1 == hash2:
                result += "🎯 RISULTATO: File identici (stesso hash)\n"
                return result
            
            result += "📋 RISULTATO: File diversi - analisi differenze...\n"
            
            # Analisi strutturale
            try:
                pdf1_str = pdf1_data.decode('latin1', errors='ignore')
                pdf2_str = pdf2_data.decode('latin1', errors='ignore')
                
                # Confronto versioni PDF
                version1 = version2 = "Non rilevata"
                if pdf1_str.startswith('%PDF-'):
                    version1 = pdf1_str.split('\n')[0].split('%PDF-')[1].split()[0]
                if pdf2_str.startswith('%PDF-'):
                    version2 = pdf2_str.split('\n')[0].split('%PDF-')[1].split()[0]
                
                result += f"\n--- CONFRONTO VERSIONI ---\n"
                result += f"Versione PDF1: {version1}\n"
                result += f"Versione PDF2: {version2}\n"
                if version1 != version2:
                    result += "⚠️ Versioni diverse rilevate\n"
                
                # Confronto struttura
                elements = {
                    'Oggetti': ' obj',
                    'Pagine': '/Type/Page',
                    'Font': '/Font',
                    'Immagini': '/Image',
                    'Bookmarks': '/Outlines',
                    'Moduli': '/AcroForm',
                    'Annotazioni': '/Annot',
                    'JavaScript': '/JavaScript'
                }
                
                result += f"\n--- CONFRONTO ELEMENTI ---\n"
                for element, pattern in elements.items():
                    count1 = pdf1_str.count(pattern)
                    count2 = pdf2_str.count(pattern)
                    diff = abs(count1 - count2)
                    
                    result += f"{element}: PDF1={count1}, PDF2={count2}"
                    if diff > 0:
                        result += f" (diff: {diff})"
                    result += "\n"
                
                # Confronto metadati
                metadata_fields = ['/Title', '/Author', '/Subject', '/Creator', '/Producer']
                result += f"\n--- CONFRONTO METADATI ---\n"
                
                for field in metadata_fields:
                    in_pdf1 = field in pdf1_str
                    in_pdf2 = field in pdf2_str
                    
                    if in_pdf1 and in_pdf2:
                        result += f"{field}: Presente in entrambi\n"
                    elif in_pdf1:
                        result += f"{field}: Solo in PDF1\n"
                    elif in_pdf2:
                        result += f"{field}: Solo in PDF2\n"
                
                # Confronto sicurezza
                result += f"\n--- CONFRONTO SICUREZZA ---\n"
                encrypt1 = '/Encrypt' in pdf1_str
                encrypt2 = '/Encrypt' in pdf2_str
                
                result += f"Crittografia PDF1: {'Sì' if encrypt1 else 'No'}\n"
                result += f"Crittografia PDF2: {'Sì' if encrypt2 else 'No'}\n"
                
                if encrypt1 != encrypt2:
                    result += "⚠️ Differenze nelle impostazioni di sicurezza\n"
                
                # Similarità generale
                common_chars = sum(1 for c1, c2 in zip(pdf1_str, pdf2_str) if c1 == c2)
                max_len = max(len(pdf1_str), len(pdf2_str))
                similarity = (common_chars / max_len) * 100 if max_len > 0 else 0
                
                result += f"\n--- ANALISI SIMILARITÀ ---\n"
                result += f"Similarità caratteri: {similarity:.1f}%\n"
                
                if similarity > 90:
                    result += "🔍 Valutazione: File molto simili (possibili versioni)\n"
                elif similarity > 70:
                    result += "📊 Valutazione: File moderatamente simili\n"
                elif similarity > 30:
                    result += "📋 Valutazione: File parzialmente simili\n"
                else:
                    result += "🆕 Valutazione: File molto diversi\n"
                
            except Exception as e:
                result += f"Errore nell'analisi comparativa: {str(e)}\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def detect_pdf_issues(pdf_base64: str) -> str:
        """
        Rileva potenziali problemi e anomalie in un file PDF.

        Args:
            pdf_base64: Il file PDF codificato in base64.
        """
        try:
            if not pdf_base64.strip():
                return "ERRORE: Il contenuto PDF base64 non può essere vuoto"
            
            try:
                pdf_data = base64.b64decode(pdf_base64)
            except Exception as e:
                return f"ERRORE: Decodifica base64 fallita: {str(e)}"
            
            result = "=== DIAGNOSI PROBLEMI PDF ===\n"
            issues_found = []
            warnings = []
            
            # Test dimensione
            file_size = len(pdf_data)
            result += f"Dimensione file: {file_size:,} bytes\n"
            
            if file_size < 100:
                issues_found.append("File troppo piccolo per PDF valido")
            elif file_size > 100 * 1024 * 1024:  # 100MB
                warnings.append("File molto grande (>100MB)")
            
            # Test struttura base
            try:
                pdf_str = pdf_data.decode('latin1', errors='ignore')
                
                # Test header
                if not pdf_str.startswith('%PDF-'):
                    issues_found.append("Header PDF mancante o corrotto")
                
                # Test footer
                if '%%EOF' not in pdf_str[-100:]:
                    warnings.append("Footer PDF (%%EOF) non trovato in posizione standard")
                
                # Test oggetti
                obj_count = pdf_str.count(' obj')
                if obj_count == 0:
                    issues_found.append("Nessun oggetto PDF trovato")
                elif obj_count > 10000:
                    warnings.append("Numero molto alto di oggetti (possibile complessità eccessiva)")
                
                # Test cross-reference
                if 'xref' not in pdf_str:
                    warnings.append("Tabella cross-reference non trovata")
                
                # Test catalog
                if '/Type/Catalog' not in pdf_str:
                    issues_found.append("Catalog root mancante")
                
                # Test pagine
                page_count = pdf_str.count('/Type/Page')
                if page_count == 0:
                    issues_found.append("Nessuna pagina rilevata")
                elif page_count > 1000:
                    warnings.append("Numero molto alto di pagine")
                
                # Test caratteri non validi
                null_bytes = pdf_data.count(b'\x00')
                if null_bytes > file_size * 0.1:  # >10% null bytes
                    warnings.append("Alto numero di byte null (possibile corruzione)")
                
                # Test sicurezza sospetta
                if '/JavaScript' in pdf_str:
                    warnings.append("JavaScript presente (potenziale rischio sicurezza)")
                
                if '/EmbeddedFile' in pdf_str:
                    warnings.append("File embedded presenti (verifica contenuto)")
                
                if '/URI' in pdf_str and 'javascript:' in pdf_str.lower():
                    issues_found.append("JavaScript URI rilevato (rischio sicurezza)")
                
                # Test encoding problems
                try:
                    pdf_data.decode('utf-8')
                except:
                    # Normal for PDF - binary content expected
                    pass
                
                # Test duplicazioni sospette
                repeated_patterns = []
                test_patterns = ['obj', 'endobj', 'stream', 'endstream']
                for pattern in test_patterns:
                    count = pdf_str.count(pattern)
                    if pattern in ['obj', 'endobj'] and count > 0:
                        if pdf_str.count('obj') != pdf_str.count('endobj'):
                            issues_found.append("Mismatch tra obj/endobj")
                    elif pattern in ['stream', 'endstream'] and count > 0:
                        if pdf_str.count('stream') != pdf_str.count('endstream'):
                            warnings.append("Mismatch tra stream/endstream")
                
                # Test metadati mancanti
                essential_metadata = ['/Title', '/Creator', '/Producer']
                missing_metadata = [m for m in essential_metadata if m not in pdf_str]
                if len(missing_metadata) == len(essential_metadata):
                    warnings.append("Tutti i metadati essenziali mancanti")
                
            except Exception as e:
                issues_found.append(f"Errore nell'analisi strutturale: {str(e)}")
            
            # Riepilogo risultati
            result += f"\n--- RIEPILOGO DIAGNOSI ---\n"
            result += f"Problemi critici: {len(issues_found)}\n"
            result += f"Avvertimenti: {len(warnings)}\n"
            
            if issues_found:
                result += f"\n🚨 PROBLEMI CRITICI:\n"
                for i, issue in enumerate(issues_found, 1):
                    result += f"{i}. {issue}\n"
            
            if warnings:
                result += f"\n⚠️ AVVERTIMENTI:\n"
                for i, warning in enumerate(warnings, 1):
                    result += f"{i}. {warning}\n"
            
            # Valutazione finale
            result += f"\n--- VALUTAZIONE FINALE ---\n"
            if not issues_found and not warnings:
                result += "✅ PDF sembra integro (nessun problema rilevato)\n"
            elif not issues_found:
                result += "⚠️ PDF probabilmente utilizzabile (solo avvertimenti)\n"
            else:
                result += "❌ PDF presenta problemi che potrebbero impedire l'uso\n"
            
            # Raccomandazioni
            result += f"\n--- RACCOMANDAZIONI ---\n"
            if issues_found:
                result += "• Considera riparazione/ricostruzione del PDF\n"
                result += "• Verifica integrità file originale\n"
            if warnings:
                result += "• Effettua backup prima di modifiche\n"
                result += "• Testa con diversi visualizzatori PDF\n"
            if not issues_found and not warnings:
                result += "• File sembra valido per l'elaborazione\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def batch_pdf_analysis(pdf_files_json: str) -> str:
        """
        Analizza multipli file PDF in batch e fornisce un report comparativo.

        Args:
            pdf_files_json: JSON con array di oggetti {name: string, data: base64_string}.
        """
        try:
            # Parse input JSON
            try:
                pdf_files = json.loads(pdf_files_json)
                if not isinstance(pdf_files, list):
                    return "ERRORE: Input deve essere un array JSON di file PDF"
            except json.JSONDecodeError as e:
                return f"ERRORE: JSON non valido: {str(e)}"
            
            if len(pdf_files) == 0:
                return "ERRORE: Nessun file PDF fornito"
            
            if len(pdf_files) > 10:
                return "ERRORE: Massimo 10 file per batch analysis"
            
            result = "=== ANALISI BATCH PDF ===\n"
            result += f"File da analizzare: {len(pdf_files)}\n"
            result += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Analisi individuale
            file_stats = []
            total_size = 0
            
            for i, pdf_file in enumerate(pdf_files, 1):
                if not isinstance(pdf_file, dict) or 'name' not in pdf_file or 'data' not in pdf_file:
                    result += f"File {i}: ERRORE - Formato non valido (richiesto: {{name, data}})\n"
                    continue
                
                name = pdf_file['name']
                data = pdf_file['data']
                
                result += f"--- FILE {i}: {name} ---\n"
                
                try:
                    # Decodifica e analisi base
                    pdf_data = base64.b64decode(data)
                    file_size = len(pdf_data)
                    total_size += file_size
                    
                    pdf_str = pdf_data.decode('latin1', errors='ignore')
                    
                    # Estrai statistiche
                    stats = {
                        'name': name,
                        'size': file_size,
                        'valid': pdf_str.startswith('%PDF-'),
                        'version': 'Unknown',
                        'pages': pdf_str.count('/Type/Page'),
                        'objects': pdf_str.count(' obj'),
                        'fonts': pdf_str.count('/Font'),
                        'images': pdf_str.count('/Image'),
                        'encrypted': '/Encrypt' in pdf_str,
                        'has_js': '/JavaScript' in pdf_str,
                        'has_forms': '/AcroForm' in pdf_str,
                        'hash': hashlib.md5(pdf_data).hexdigest()[:8]
                    }
                    
                    # Estrai versione
                    if stats['valid']:
                        try:
                            version_line = pdf_str.split('\n')[0]
                            if '%PDF-' in version_line:
                                stats['version'] = version_line.split('%PDF-')[1].split()[0]
                        except:
                            pass
                    
                    file_stats.append(stats)
                    
                    # Report individuale
                    result += f"Dimensione: {file_size:,} bytes\n"
                    result += f"Valido: {'✅' if stats['valid'] else '❌'}\n"
                    result += f"Versione: {stats['version']}\n"
                    result += f"Pagine: {stats['pages']}\n"
                    result += f"Oggetti: {stats['objects']}\n"
                    result += f"Font: {stats['fonts']}\n"
                    result += f"Immagini: {stats['images']}\n"
                    result += f"Crittografato: {'🔒' if stats['encrypted'] else '🔓'}\n"
                    
                    if stats['has_js']:
                        result += "⚠️ JavaScript presente\n"
                    if stats['has_forms']:
                        result += "📝 Moduli presenti\n"
                    
                    result += f"Hash: {stats['hash']}\n\n"
                    
                except Exception as e:
                    result += f"ERRORE nell'analisi: {str(e)}\n\n"
                    continue
            
            # Analisi comparativa
            valid_files = [f for f in file_stats if f['valid']]
            
            if valid_files:
                result += "=== ANALISI COMPARATIVA ===\n"
                result += f"File validi: {len(valid_files)}/{len(file_stats)}\n"
                result += f"Dimensione totale: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)\n"
                
                # Statistiche aggregate
                if len(valid_files) > 1:
                    sizes = [f['size'] for f in valid_files]
                    pages = [f['pages'] for f in valid_files]
                    
                    result += f"\n--- STATISTICHE DIMENSIONI ---\n"
                    result += f"Min: {min(sizes):,} bytes\n"
                    result += f"Max: {max(sizes):,} bytes\n"
                    result += f"Media: {sum(sizes)//len(sizes):,} bytes\n"
                    
                    result += f"\n--- STATISTICHE PAGINE ---\n"
                    result += f"Min: {min(pages)} pagine\n"
                    result += f"Max: {max(pages)} pagine\n"
                    result += f"Totale: {sum(pages)} pagine\n"
                    
                    # Versioni utilizzate
                    versions = [f['version'] for f in valid_files]
                    unique_versions = list(set(versions))
                    result += f"\n--- VERSIONI PDF ---\n"
                    for version in unique_versions:
                        count = versions.count(version)
                        result += f"PDF {version}: {count} file\n"
                    
                    # Caratteristiche speciali
                    encrypted_count = sum(1 for f in valid_files if f['encrypted'])
                    js_count = sum(1 for f in valid_files if f['has_js'])
                    forms_count = sum(1 for f in valid_files if f['has_forms'])
                    
                    result += f"\n--- CARATTERISTICHE SPECIALI ---\n"
                    result += f"File crittografati: {encrypted_count}\n"
                    result += f"File con JavaScript: {js_count}\n"
                    result += f"File con moduli: {forms_count}\n"
                    
                    # Check duplicati
                    hashes = [f['hash'] for f in valid_files]
                    unique_hashes = list(set(hashes))
                    if len(unique_hashes) < len(hashes):
                        result += f"\n⚠️ DUPLICATI RILEVATI: {len(hashes) - len(unique_hashes)} file duplicati\n"
                        
                        # Lista duplicati
                        for hash_val in unique_hashes:
                            files_with_hash = [f['name'] for f in valid_files if f['hash'] == hash_val]
                            if len(files_with_hash) > 1:
                                result += f"Hash {hash_val}: {', '.join(files_with_hash)}\n"
            
            # Raccomandazioni finali
            result += f"\n=== RACCOMANDAZIONI ===\n"
            
            invalid_count = len(file_stats) - len(valid_files)
            if invalid_count > 0:
                result += f"• {invalid_count} file non validi - verifica integrità\n"
            
            if any(f['has_js'] for f in valid_files):
                result += "• File con JavaScript rilevati - attenzione sicurezza\n"
            
            if any(f['encrypted'] for f in valid_files):
                result += "• File crittografati presenti - password richieste\n"
            
            large_files = [f for f in valid_files if f['size'] > 10*1024*1024]  # >10MB
            if large_files:
                result += f"• {len(large_files)} file molto grandi - considera ottimizzazione\n"
            
            if len(unique_hashes) < len(hashes):
                result += "• Duplicati rilevati - considera deduplicazione\n"
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"