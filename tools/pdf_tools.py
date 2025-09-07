# -*- coding: utf-8 -*-
# tools/pdf_tools.py
import logging
import base64
import io

def register_tools(mcp):
    """Registra i tool per PDF con l'istanza del server MCP."""
    logging.info("📄 Registrazione tool-set: PDF Tools")

    @mcp.tool()
    def analyze_pdf_metadata(pdf_base64: str) -> str:
        """
        Analizza i metadati di un file PDF.

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
            
            # Analisi base del PDF (senza librerie esterne)
            # In un ambiente reale, useresti PyPDF2 o simili
            
            result = "=== ANALISI METADATI PDF ===\n"
            result += f"Dimensione file: {len(pdf_data)} bytes\n"
            
            # Converti in stringa per analisi testuale
            try:
                # Cerca pattern PDF
                pdf_str = pdf_data.decode('latin1', errors='ignore')
                
                # Verifica header PDF
                if pdf_str.startswith('%PDF-'):
                    version_line = pdf_str.split('\n')[0]
                    result += f"Header PDF: {version_line}\n"
                    
                    # Estrai versione
                    if '%PDF-' in version_line:
                        version = version_line.split('%PDF-')[1].split()[0]
                        result += f"Versione PDF: {version}\n"
                else:
                    return "ERRORE: File non riconosciuto come PDF valido"
                
                # Cerca informazioni di base
                page_count = pdf_str.count('/Type/Page')
                if page_count > 0:
                    result += f"Pagine stimate: {page_count}\n"
                
                # Cerca metadati comuni
                metadata_fields = {
                    '/Title': 'Titolo',
                    '/Author': 'Autore',
                    '/Subject': 'Oggetto',
                    '/Creator': 'Creatore',
                    '/Producer': 'Produttore',
                    '/CreationDate': 'Data creazione',
                    '/ModDate': 'Data modifica'
                }
                
                found_metadata = False
                for field, label in metadata_fields.items():
                    if field in pdf_str:
                        found_metadata = True
                        # Tentativo di estrazione valore (molto basilare)
                        start = pdf_str.find(field)
                        if start != -1:
                            result += f"{label}: Presente\n"
                
                if not found_metadata:
                    result += "Metadati: Nessun metadato rilevato\n"
                
                # Cerca presenza di immagini
                if '/Image' in pdf_str or '/XObject' in pdf_str:
                    result += "Immagini: Probabilmente presenti\n"
                
                # Cerca presenza di font
                font_count = pdf_str.count('/Font')
                if font_count > 0:
                    result += f"Font rilevati: {font_count}\n"
                
                # Cerca bookmarks/outline
                if '/Outlines' in pdf_str:
                    result += "Bookmarks: Presenti\n"
                
                # Cerca form fields
                if '/AcroForm' in pdf_str:
                    result += "Campi modulo: Presenti\n"
                
                # Stima della sicurezza
                if '/Encrypt' in pdf_str:
                    result += "Sicurezza: PDF crittografato/protetto\n"
                
                result += "\nNOTA: Analisi semplificata - per metadati completi usa una libreria PDF dedicata."
                
            except Exception as e:
                result += f"Errore nell'analisi: {str(e)}\n"
                result += "NOTA: File PDF binario - analisi limitata senza librerie specializzate."
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

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