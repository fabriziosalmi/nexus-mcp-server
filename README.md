# 🚀 Nexus MCP Server

**Nexus** è un server MCP (Model Context Protocol) avanzato, modulare e configurabile che funge da hub centrale per integrare una vasta gamma di strumenti personalizzati, rendendoli disponibili a un Large Language Model (LLM).

## 📊 Panoramica Tool e Funzioni

🛠️ **Tool Disponibili**: **34**  
⚙️ **Funzioni Totali**: **183**

## 📋 Tabella Completa Tool

| Tool | File | Funzioni | Descrizione |
|------|------|----------|-------------|
| Audio Processing | `audio_processing.py` | 6 | Elaborazione e analisi di file audio |
| Backup Tools | `backup_tools.py` | 5 | Gestione backup e archivi |
| Calculator | `calculator.py` | 2 | Operazioni matematiche di base |
| Cloud Tools | `cloud_tools.py` | 10 | Servizi e API per piattaforme cloud |
| Code Analysis Tools | `code_analysis_tools.py` | 4 | Analisi qualità e metriche del codice |
| Code Execution Tools | `code_execution_tools.py` | 6 | Ambienti sicuri per esecuzione codice |
| Code Generation Tools | `code_generation_tools.py` | 5 | Generazione template e strutture codice |
| Crypto Tools | `crypto_tools.py` | 3 | Funzioni crittografiche e hashing |
| Data Analysis | `data_analysis.py` | 5 | Elaborazione e analisi statistica dati |
| Database Tools | `database_tools.py` | 5 | Gestione database e query |
| Datetime Tools | `datetime_tools.py` | 4 | Manipolazione date e orari |
| Docker Tools | `docker_tools.py` | 6 | Gestione container Docker |
| Encoding Tools | `encoding_tools.py` | 6 | Codifica e decodifica dati |
| Environment Tools | `environment_tools.py` | 5 | Gestione variabili ambiente |
| File Converter | `file_converter.py` | 8 | Utilità conversione formati file |
| Filesystem Reader | `filesystem_reader.py` | 1 | Accesso sicuro al file system |
| Git Tools | `git_tools.py` | 5 | Gestione repository Git |
| Image Processing | `image_processing.py` | 6 | Manipolazione e analisi immagini |
| Log Analysis Tools | `log_analysis_tools.py` | 5 | Parsing e analisi file log |
| Network Security Tools | `network_security_tools.py` | 5 | Scansione sicurezza di rete |
| Network Tools | `network_tools.py` | 7 | Diagnostica e utilità di rete |
| PDF Tools | `pdf_tools.py` | 6 | Elaborazione documenti PDF |
| Performance Tools | `performance_tools.py` | 6 | Monitoraggio performance sistema |
| Process Management Tools | `process_management_tools.py` | 6 | Controllo e monitoraggio processi |
| QR Code Tools | `qr_code_tools.py` | 7 | Generazione e analisi QR code |
| Regex Tools | `regex_tools.py` | 8 | Utilità espressioni regolari |
| Security Tools | `security_tools.py` | 7 | Utilità sicurezza e crittografia |
| String Tools | `string_tools.py` | 5 | Funzioni manipolazione stringhe |
| System Info | `system_info.py` | 6 | Informazioni e monitoraggio sistema |
| Unit Converter | `unit_converter.py` | 6 | Utilità conversione unità misura |
| UUID Tools | `uuid_tools.py` | 6 | Generazione UUID e ID |
| Validator Tools | `validator_tools.py` | 5 | Funzioni validazione dati |
| Video Processing | `video_processing.py` | 5 | Elaborazione file video |
| Web Fetcher | `web_fetcher.py` | 1 | Recupero contenuti web |

## 🎯 Filosofia di Progettazione

- **🎭 Orchestrazione Centrale, Logica Distribuita**: Il server principale non contiene la logica di nessun tool, ma solo la responsabilità di caricarli e servirli
- **⚙️ Configurazione-Driven**: Attivazione/disattivazione dei tool tramite file `config.json` senza ricompilazione
- **🔒 Sicurezza First-Class**: Ogni tool implementa rigorosi controlli di sicurezza
- **📚 Auto-documentazione**: Codice completamente documentato per facilità di manutenzione

## 📦 Tool Disponibili

### 🧮 Calculator (`calculator.py`)
**Operazioni matematiche di base**
- `add(a, b)` - Addizione
- `multiply(a, b)` - Moltiplicazione

### 📁 Filesystem Reader (`filesystem_reader.py`) 
**Lettura sicura di file con sandbox**
- `read_safe_file(filename)` - Legge file dalla directory sandbox `safe_files/`
- ✅ **Protezione contro path traversal**
- ✅ **Validazione percorsi**

### 🌐 Web Fetcher (`web_fetcher.py`)
**Recupero contenuti web**
- `fetch_url_content(url)` - Scarica contenuto HTML da URL
- ✅ **Timeout configurabile**
- ✅ **Limitazione dimensioni**
- ✅ **Gestione redirect**

### 🔐 Crypto Tools (`crypto_tools.py`)
**Strumenti crittografici e hashing**
- `generate_hash(text, algorithm)` - Hash SHA256, SHA1, MD5, SHA512
- `generate_hmac(message, secret_key, algorithm)` - HMAC per autenticazione
- `generate_random_token(length, encoding)` - Token sicuri (hex/base64/urlsafe)

### 🔤 Encoding Tools (`encoding_tools.py`)
**Codifica e decodifica dati**
- `base64_encode(text)` / `base64_decode(encoded_text)` - Codifica Base64
- `url_encode(text)` / `url_decode(encoded_text)` - URL encoding/decoding
- `html_escape(text)` - Escape caratteri HTML
- `json_format(json_string, indent)` - Formattazione e validazione JSON

### 📅 DateTime Tools (`datetime_tools.py`)
**Manipolazione date e timestamp**
- `current_timestamp()` - Timestamp corrente in vari formati
- `unix_to_date(timestamp)` - Converte Unix timestamp in data
- `date_to_unix(date_string)` - Converte data in Unix timestamp  
- `date_math(start_date, operation, amount, unit)` - Operazioni matematiche su date

### 🆔 UUID Tools (`uuid_tools.py`)
**Generazione identificatori unici**
- `generate_uuid4()` / `generate_uuid1()` - UUID versioni 1 e 4
- `generate_multiple_uuids(count, version)` - Generazione multipla UUID
- `generate_short_id(length, use_uppercase)` - ID brevi alfanumerici
- `generate_nanoid(length, alphabet)` - Nano ID personalizzabili
- `uuid_info(uuid_string)` - Analisi e informazioni UUID

### 📝 String Tools (`string_tools.py`)
**Manipolazione avanzata stringhe**
- `string_case_convert(text, case_type)` - Conversioni case (camel, snake, kebab, etc.)
- `string_stats(text)` - Statistiche dettagliate stringa
- `string_clean(text, operation)` - Pulizia e normalizzazione testo
- `string_wrap(text, width, break_long_words)` - Word wrapping
- `string_find_replace(text, find, replace, case_sensitive)` - Trova e sostituisci

### ✅ Validator Tools (`validator_tools.py`)
**Validazione dati e formati**
- `validate_email(email)` - Validazione indirizzi email
- `validate_url(url)` - Validazione e analisi URL
- `validate_ip_address(ip)` - Validazione IP (IPv4/IPv6)
- `validate_phone(phone, country_code)` - Validazione numeri telefono
- `validate_credit_card(card_number)` - Validazione carte credito (algoritmo Luhn)

### 💻 System Info (`system_info.py`)
**Informazioni sistema e monitoraggio**
- `system_overview()` - Panoramica completa sistema
- `memory_usage()` - Utilizzo RAM e SWAP
- `cpu_info()` - Informazioni CPU e utilizzo
- `disk_usage(path)` - Utilizzo spazio disco
- `network_info()` - Informazioni interfacce di rete
- `running_processes(limit)` - Top processi per utilizzo CPU

### 🌐 Network Tools (`network_tools.py`)
**Strumenti diagnostici di rete**
- `ping_host(host, count)` - Ping verso host specificato
- `dns_lookup(hostname, record_type)` - Lookup DNS (A, AAAA, MX, NS, TXT)
- `port_scan(host, ports)` - Scansione porte specifiche
- `traceroute(host, max_hops)` - Traceroute verso destinazione
- `whois_lookup(domain)` - Informazioni whois dominio
- `check_website_status(url, timeout)` - Status e performance sito web
- `get_public_ip()` - IP pubblico corrente

### 🔒 Security Tools (`security_tools.py`)
**Strumenti sicurezza e crittografia**
- `generate_secure_password(length, include_symbols, exclude_ambiguous)` - Password sicure
- `password_strength_check(password)` - Analisi robustezza password
- `generate_api_key(length, format_type)` - Chiavi API sicure
- `hash_file_content(content, algorithms)` - Hash per verifica integrità
- `jwt_decode_header(jwt_token)` - Decodifica header JWT (senza verifica)
- `check_common_ports(host)` - Controllo porte comuni per sicurezza
- `ssl_certificate_check(domain, port)` - Verifica certificati SSL/TLS

### 🛡️ Network Security Tools (`network_security_tools.py`)
**Strumenti avanzati di sicurezza di rete**
- `ip_threat_intelligence(ip_address)` - Analisi threat intelligence per indirizzi IP
- `scan_security_headers(url, follow_redirects)` - Scansione header di sicurezza HTTP
- `discover_subdomains(domain, wordlist_size)` - Scoperta sottodomini per security assessment
- `grab_service_banner(host, port, timeout)` - Estrazione banner servizi per fingerprinting
- `analyze_certificate_chain(domain, port)` - Analisi approfondita catena certificati SSL

### ⚡ Performance Tools (`performance_tools.py`)
**Monitoraggio e benchmark performance**
- `benchmark_function_performance(code, iterations)` - Benchmark codice Python
- `monitor_system_performance(duration_seconds)` - Monitoraggio sistema real-time
- `analyze_memory_usage()` - Analisi dettagliata memoria
- `disk_performance_test(test_size_mb)` - Test velocità disco
- `network_latency_test(hosts)` - Test latenza rete
- `cpu_stress_test(duration_seconds)` - Stress test CPU

### 📊 Data Analysis Tools (`data_analysis.py`)
**Analisi e elaborazione dati**
- `analyze_csv_data(csv_content, delimiter)` - Analisi statistiche CSV
- `analyze_json_structure(json_content)` - Analisi struttura JSON
- `statistical_analysis(numbers)` - Statistiche descrittive complete
- `text_analysis(text)` - Analisi linguistica e sentiment
- `correlation_analysis(dataset1, dataset2)` - Correlazione tra dataset

### 🖼️ Image Processing Tools (`image_processing.py`)
**Elaborazione e analisi immagini**
- `analyze_image_metadata(image_base64)` - Metadata ed EXIF
- `resize_image(image_base64, width, height, maintain_aspect)` - Ridimensionamento
- `convert_image_format(image_base64, target_format)` - Conversione formato
- `apply_image_filters(image_base64, filters)` - Filtri (blur, sharpen, sepia, etc.)
- `create_thumbnail(image_base64, size, quality)` - Generazione thumbnail
- `extract_dominant_colors(image_base64, num_colors)` - Palette colori dominanti

### 🎵 Audio Processing Tools (`audio_processing.py`)
**Elaborazione e analisi audio**
- `analyze_audio_metadata(audio_base64)` - Metadata audio WAV
- `generate_sine_wave(frequency, duration, sample_rate, amplitude)` - Generazione onde sinusoidali
- `analyze_audio_spectrum(audio_base64, fft_size)` - Analisi spettro di frequenza
- `adjust_audio_volume(audio_base64, volume_factor)` - Regolazione volume
- `convert_audio_format(audio_base64, target_format, quality)` - Conversione formato
- `extract_audio_features(audio_base64)` - Estrazione caratteristiche audio

### 🎬 Video Processing Tools (`video_processing.py`)
**Elaborazione e analisi video**
- `analyze_video_metadata(video_base64)` - Metadata e formato video
- `create_video_thumbnail_placeholder(width, height, color, text)` - Placeholder thumbnail
- `analyze_video_structure(video_base64)` - Struttura MP4 (atom/box analysis)
- `estimate_video_properties(video_base64)` - Stima proprietà da euristica
- `create_video_info_summary(video_base64)` - Riassunto completo informazioni

### 🔄 Unit Converter Tools (`unit_converter.py`)
**Conversioni unità di misura**
- `convert_length(value, from_unit, to_unit)` - Conversioni lunghezza (mm, cm, m, km, in, ft, yd, mi)
- `convert_weight(value, from_unit, to_unit)` - Conversioni peso (mg, g, kg, t, oz, lb, st)
- `convert_temperature(value, from_unit, to_unit)` - Conversioni temperatura (C, F, K, R)
- `convert_volume(value, from_unit, to_unit)` - Conversioni volume (ml, l, gal, qt, pt, cup, floz)
- `convert_area(value, from_unit, to_unit)` - Conversioni area (mm2, cm2, m2, km2, in2, ft2, yd2, ac, ha)
- `list_available_units()` - Elenca tutte le unità disponibili per categoria

### 📱 QR Code Tools (`qr_code_tools.py`)
**Generazione e analisi QR code**
- `generate_qr_code(text, size, border, error_correction)` - Genera QR code da testo
- `generate_qr_code_url(url, size)` - Genera QR code per URL
- `generate_qr_code_wifi(ssid, password, security, hidden)` - QR code configurazione WiFi
- `generate_qr_code_contact(name, phone, email, organization)` - QR code contatto vCard
- `generate_qr_code_sms(phone, message)` - QR code per SMS
- `analyze_qr_content(content)` - Analizza tipo e contenuto QR code
- `qr_code_formats_info()` - Informazioni formati QR supportati

### 🔍 Regex Tools (`regex_tools.py`)
**Strumenti espressioni regolari**
- `regex_test(pattern, text, flags)` - Testa pattern regex su testo
- `regex_match_details(pattern, text, flags)` - Dettagli corrispondenze con posizioni
- `regex_replace(pattern, text, replacement, flags, count)` - Sostituisce con regex
- `regex_split(pattern, text, flags, maxsplit)` - Divide testo con regex
- `regex_validate_pattern(pattern)` - Valida e analizza pattern regex
- `regex_common_patterns()` - Libreria pattern regex comuni
- `regex_extract_emails(text)` - Estrae indirizzi email da testo
- `regex_extract_urls(text)` - Estrae URL da testo

### 🔄 File Converter Tools (`file_converter.py`)
**Conversioni formato file**
- `csv_to_json(csv_content, delimiter, has_header)` - Converte CSV in JSON
- `json_to_csv(json_content, delimiter, include_header)` - Converte JSON in CSV
- `json_to_xml(json_content, root_name)` - Converte JSON in XML
- `xml_to_json(xml_content)` - Converte XML in JSON
- `txt_to_json_lines(text_content, line_key)` - Converte testo in JSON righe
- `json_lines_to_txt(json_content, line_field)` - Converte JSON in testo
- `detect_file_format(content)` - Rileva automaticamente formato file
- `conversion_help()` - Guida completa conversioni disponibili

### 📄 PDF Tools (`pdf_tools.py`)
**Strumenti elaborazione PDF**
- `analyze_pdf_metadata(pdf_base64)` - Analizza metadata e struttura PDF
- `create_simple_pdf_info(title, author, subject, pages)` - Genera informazioni PDF
- `pdf_text_extraction_guide()` - Guida estrazione testo da PDF
- `validate_pdf_structure(pdf_base64)` - Valida struttura PDF
- `pdf_security_check(pdf_base64)` - Controlla impostazioni sicurezza PDF
- `pdf_tools_info()` - Documentazione completa strumenti PDF

### ☁️ Cloud Platform Tools (`cloud_tools.py`)
**Strumenti per servizi cloud e multi-cloud**
- `aws_service_status(service, region)` - Verifica stato servizi AWS
- `azure_service_status(service, region)` - Verifica stato servizi Azure
- `gcp_service_status(service, region)` - Verifica stato servizi Google Cloud
- `cloudflare_dns_lookup(domain, record_type)` - Query DNS tramite Cloudflare
- `digitalocean_status_check()` - Verifica stato servizi DigitalOcean
- `cloud_cost_calculator(service_type, usage_hours, instance_type)` - Calcolo costi cloud
- `cloud_health_checker(endpoints)` - Controllo salute endpoint cloud
- `cloud_security_scanner(config_text, cloud_provider)` - Scansione sicurezza configurazioni
- `multi_cloud_resource_tracker(resources)` - Tracciamento risorse multi-cloud
- `cloud_config_validator(config_text, config_type)` - Validazione file configurazione cloud

## 🏗️ Struttura del Progetto

```
nexus-mcp-server/
├── .venv/                      # Ambiente virtuale Python
├── multi_server.py             # 🎯 Orchestratore principale
├── config.json                 # ⚙️ Configurazione tool
├── requirements.txt            # 📦 Dipendenze Python
├── client.py                   # 🧪 Client di test
├── README.md                   # 📖 Questa documentazione
├── safe_files/                 # 🔒 Directory sandbox sicura
│   └── esempio.txt
└── tools/                      # 🛠️ Moduli tool
    ├── __init__.py
    ├── calculator.py           # 🧮 Tool matematici
    ├── filesystem_reader.py    # 📁 Lettore file sicuro
    ├── web_fetcher.py          # 🌐 Recupero contenuti web
    ├── crypto_tools.py         # 🔐 Strumenti crittografici
    ├── encoding_tools.py       # 🔤 Codifica/decodifica
    ├── datetime_tools.py       # 📅 Manipolazione date
    ├── uuid_tools.py           # 🆔 Generazione UUID/ID
    ├── string_tools.py         # 📝 Manipolazione stringhe
    ├── validator_tools.py      # ✅ Validazione dati
    ├── system_info.py          # 💻 Informazioni sistema
    ├── network_tools.py        # 🌐 Strumenti diagnostici rete
    ├── security_tools.py       # 🔒 Strumenti sicurezza
    ├── network_security_tools.py # 🛡️ Strumenti sicurezza di rete
    ├── performance_tools.py    # ⚡ Monitoraggio performance
    ├── data_analysis.py        # 📊 Analisi dati
    ├── image_processing.py     # 🖼️ Elaborazione immagini
    ├── audio_processing.py     # 🎵 Elaborazione audio
    ├── video_processing.py     # 🎬 Elaborazione video
    ├── unit_converter.py       # 🔄 Conversioni unità misura
    ├── qr_code_tools.py        # 📱 Generazione QR code
    ├── regex_tools.py          # 🔍 Strumenti regex
    ├── file_converter.py       # 🔄 Conversioni formato file
    ├── pdf_tools.py            # 📄 Strumenti PDF
    └── cloud_tools.py          # ☁️ Strumenti cloud platform
```

## 🚀 Quick Start

### Deployment Automatico (Raccomandato)

```bash
# Clona il progetto
git clone <repository-url> nexus-mcp-server
cd nexus-mcp-server

# Deployment completo con script automatico
./scripts/deploy.sh full

# Oppure deployment specifico:
./scripts/deploy.sh local    # Solo ambiente locale
./scripts/deploy.sh docker   # Solo Docker
./scripts/deploy.sh compose  # Docker Compose
```

### 1. Setup Ambiente Locale

```bash
# Crea ambiente virtuale
python -m venv .venv

# Attiva ambiente virtuale
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Docker Setup

```bash
# Build immagine Docker
docker build -t nexus-mcp-server:latest .

# Avvia con Docker Compose
docker-compose up -d nexus-mcp

# Test container
docker run --rm -i nexus-mcp-server:latest python -c "print('OK')"
```

### 3. Utilizzo

```bash
# Locale
python client.py <nome_tool> '<argomenti_json>'

# Docker
docker run --rm -i -v "./safe_files:/app/safe_files:rw" nexus-mcp-server:latest python client.py <tool> '<args>'
```

### 3. Esempi di Utilizzo

```bash
# Calculator
python client.py add '{"a": 42, "b": 8}'
python client.py multiply '{"a": 7, "b": 6}'

# Crypto Tools
python client.py generate_hash '{"text": "Hello World", "algorithm": "sha256"}'
python client.py generate_random_token '{"length": 16, "encoding": "hex"}'

# String Tools  
python client.py string_case_convert '{"text": "Hello World", "case_type": "snake"}'
python client.py string_stats '{"text": "The quick brown fox jumps over the lazy dog"}'

# DateTime Tools
python client.py current_timestamp '{}'
python client.py date_to_unix '{"date_string": "2024-12-25 15:30:00"}'

# UUID Tools
python client.py generate_uuid4 '{}'
python client.py generate_nanoid '{"length": 12, "alphabet": "lowercase"}'

# Encoding Tools
python client.py base64_encode '{"text": "Hello, Nexus!"}'
python client.py json_format '{"json_string": "{\\"name\\":\\"test\\",\\"value\\":123}"}'

# Validator Tools
python client.py validate_email '{"email": "user@example.com"}'
python client.py validate_url '{"url": "https://www.example.com/path?query=1"}'

# System Info
python client.py system_overview '{}'
python client.py memory_usage '{}'
python client.py running_processes '{"limit": 5}'

# Filesystem Reader
python client.py read_safe_file '{"filename": "esempio.txt"}'

# Web Fetcher  
python client.py fetch_url_content '{"url": "https://httpbin.org/json"}'

# Network Tools
python client.py ping_host '{"host": "8.8.8.8", "count": 4}'
python client.py dns_lookup '{"hostname": "example.com", "record_type": "A"}'
python client.py check_website_status '{"url": "https://www.example.com"}'
python client.py get_public_ip '{}'

# Security Tools
python client.py generate_secure_password '{"length": 16, "include_symbols": true}'
python client.py password_strength_check '{"password": "MyPassword123!"}'
python client.py generate_api_key '{"length": 32, "format_type": "hex"}'

# Network Security Tools
python client.py ip_threat_intelligence '{"ip_address": "8.8.8.8"}'
python client.py scan_security_headers '{"url": "https://example.com"}'
python client.py discover_subdomains '{"domain": "example.com", "wordlist_size": "small"}'
python client.py grab_service_banner '{"host": "example.com", "port": 80}'
python client.py analyze_certificate_chain '{"domain": "example.com", "port": 443"}'

# Performance Tools
python client.py benchmark_function_performance '{"code": "sum(range(1000))", "iterations": 1000}'
python client.py monitor_system_performance '{"duration_seconds": 5}'
python client.py analyze_memory_usage '{}'

# Data Analysis Tools
python client.py statistical_analysis '{"numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}'
python client.py text_analysis '{"text": "This is a sample text for analysis."}'

# Unit Converter Tools
python client.py convert_length '{"value": 100, "from_unit": "cm", "to_unit": "m"}'
python client.py convert_temperature '{"value": 100, "from_unit": "C", "to_unit": "F"}'
python client.py convert_weight '{"value": 1000, "from_unit": "g", "to_unit": "kg"}'
python client.py list_available_units '{}'

# QR Code Tools
python client.py generate_qr_code '{"text": "Hello World", "size": 200}'
python client.py generate_qr_code_url '{"url": "https://github.com", "size": 250}'
python client.py generate_qr_code_wifi '{"ssid": "MyWiFi", "password": "password123", "security": "WPA"}'
python client.py analyze_qr_content '{"content": "https://www.example.com"}'

# Regex Tools
python client.py regex_test '{"pattern": "[0-9]+", "text": "Ho 25 anni e 30 euro"}'
python client.py regex_replace '{"pattern": "[0-9]+", "text": "Ho 25 anni", "replacement": "XXX"}'
python client.py regex_extract_emails '{"text": "Contatta mario@example.com o lucia@test.it"}'
python client.py regex_common_patterns '{}'

# File Converter Tools
python client.py csv_to_json '{"csv_content": "name,age\\nMario,30\\nLucia,25", "delimiter": ","}'
python client.py json_to_csv '{"json_content": "[{\\"name\\": \\"Mario\\", \\"age\\": 30}]"}'
python client.py detect_file_format '{"content": "{\\"test\\": \\"json\\"}"}'
python client.py conversion_help '{}'

# PDF Tools
python client.py pdf_text_extraction_guide '{}'
python client.py pdf_tools_info '{}'

# Cloud Platform Tools
python client.py aws_service_status '{"service": "all", "region": "us-east-1"}'
python client.py azure_service_status '{"service": "compute", "region": "East US"}'
python client.py gcp_service_status '{"service": "all", "region": "us-central1"}'
python client.py cloudflare_dns_lookup '{"domain": "example.com", "record_type": "A"}'
python client.py digitalocean_status_check '{}'
python client.py cloud_cost_calculator '{"service_type": "compute", "usage_hours": 730, "instance_type": "medium"}'
python client.py cloud_health_checker '{"endpoints": ["https://api.example.com", "https://status.example.com"]}'
python client.py cloud_security_scanner '{"config_text": "{\\"Action\\": \\"*\\", \\"Resource\\": \\"*\\"}", "cloud_provider": "aws"}'
python client.py multi_cloud_resource_tracker '{"resources": [{"provider": "aws", "type": "ec2", "name": "web-server", "region": "us-east-1"}]}'
python client.py cloud_config_validator '{"config_text": "{\\"AWSTemplateFormatVersion\\": \\"2010-09-09\\"}", "config_type": "json"}'
```

## 🔌 Integrazione VSCode con Docker/Docker Compose

### Prerequisiti

- **VSCode** con estensione **Continue** o **Claude Code** installata
- **Docker** installato e funzionante
- **Docker Compose** (opzionale, per deployment orchestrato)

### 📋 Setup VSCode - Versione Docker

#### 1. Build dell'immagine Docker

```bash
# Assicurati di essere nella directory del progetto
cd nexus-mcp-server

# Build dell'immagine
docker build -t nexus-mcp-server:latest .

# Verifica che l'immagine sia stata creata
docker images | grep nexus-mcp-server
```

#### 2. Configurazione VSCode

Crea o modifica il file di configurazione MCP in VSCode (solitamente in `%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json` su Windows o `~/.vscode/settings.json`):

```json
{
  "mcpServers": {
    "nexus-docker": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--network=host",
        "-v", "./safe_files:/app/safe_files:rw",
        "-v", "./config.json:/app/config.json:ro",
        "nexus-mcp-server:latest"
      ],
      "env": {
        "MCP_SERVER_NAME": "NexusServer-Docker"
      }
    }
  }
}
```

#### 3. Test della configurazione

```bash
# Test rapido del container
docker run --rm -i \
  -v "$(pwd)/safe_files:/app/safe_files:rw" \
  -v "$(pwd)/config.json:/app/config.json:ro" \
  nexus-mcp-server:latest \
  python client.py system_overview '{}'
```

### 🐳 Setup VSCode - Versione Docker Compose

#### 1. Avvio del servizio con Docker Compose

```bash
# Avvia il server in background
docker-compose up -d nexus-mcp

# Verifica che il container sia in esecuzione
docker-compose ps

# Visualizza i log (opzionale)
docker-compose logs -f nexus-mcp
```

#### 2. Configurazione VSCode per Docker Compose

```json
{
  "mcpServers": {
    "nexus-compose": {
      "command": "docker-compose",
      "args": ["exec", "-T", "nexus-mcp", "python", "multi_server.py"],
      "cwd": ".",
      "env": {
        "MCP_SERVER_NAME": "NexusServer-Compose"
      }
    }
  }
}
```

#### 3. Test con Docker Compose

```bash
# Test attraverso docker-compose
docker-compose exec nexus-mcp python client.py add '{"a": 42, "b": 8}'

# Test di più funzioni
docker-compose exec nexus-mcp python client.py system_overview '{}'
docker-compose exec nexus-mcp python client.py generate_uuid4 '{}'
```

### 📂 Configurazioni Pre-configurate

Il progetto include file di configurazione pronti all'uso nella directory `mcp-configs/`:

```bash
# Copia la configurazione VSCode nel tuo ambiente
cp mcp-configs/vscode-mcp.json ~/.vscode/mcp-servers.json

# Oppure per Continue/Claude Code
cp mcp-configs/claude-code-config.json %APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\
```

### 🔧 Configurazione Avanzata

#### Variabili d'ambiente personalizzate

```yaml
# docker-compose.override.yml
services:
  nexus-mcp:
    environment:
      - LOG_LEVEL=DEBUG
      - MCP_SERVER_NAME=NexusServer-Dev
      - CUSTOM_CONFIG_PATH=/app/config-dev.json
    volumes:
      - ./config-dev.json:/app/config-dev.json:ro
```

#### Configurazione di rete personalizzata

```yaml
# Per esporre il server su una porta specifica
services:
  nexus-mcp:
    ports:
      - "8080:9999"
    environment:
      - MCP_HTTP_PORT=9999
```

### 🧪 Testing e Verifica

#### 1. Test di connettività

```bash
# Test Docker diretto
docker run --rm nexus-mcp-server:latest python -c "print('✅ Container funzionante')"

# Test Docker Compose
docker-compose exec nexus-mcp python -c "print('✅ Compose funzionante')"
```

#### 2. Test funzionalità MCP

```bash
# Test tool matematici
docker-compose exec nexus-mcp python client.py add '{"a": 10, "b": 5}'

# Test tool di sicurezza
docker-compose exec nexus-mcp python client.py generate_secure_password '{"length": 16}'

# Test tool di sistema
docker-compose exec nexus-mcp python client.py memory_usage '{}'
```

#### 3. Verifica integrazione VSCode

1. Riavvia VSCode dopo aver configurato il server MCP
2. Apri la palette comandi (`Ctrl+Shift+P`)
3. Cerca "MCP" o "Continue" per verificare che il server sia riconosciuto
4. Testa una richiesta semplice come "Calcola 5 + 3 usando Nexus"

### 🚨 Troubleshooting

#### Problema: Container non si avvia

```bash
# Verifica i log
docker-compose logs nexus-mcp

# Verifica che le dipendenze siano installate
docker run --rm nexus-mcp-server:latest pip list
```

#### Problema: VSCode non riconosce il server

```bash
# Verifica la sintassi del file di configurazione
jq . < ~/.vscode/mcp-servers.json

# Verifica che Docker sia raggiungibile
docker --version
docker-compose --version
```

#### Problema: Errori di permessi sui volumi

```bash
# Verifica permessi directory safe_files
ls -la safe_files/

# Correggi permessi se necessario
chmod 755 safe_files/
```

#### Problema: Timeout di connessione

```bash
# Aumenta timeout nel docker-compose.yml
services:
  nexus-mcp:
    healthcheck:
      timeout: 30s
      interval: 60s
```

### 📊 Monitoraggio e Performance

#### Utilizzo risorse

```bash
# Monitora utilizzo risorse
docker stats nexus-mcp-server

# Verifica health check
docker inspect nexus-mcp-server | grep -A 10 -B 5 Health
```

#### Log analysis

```bash
# Log in tempo reale
docker-compose logs -f nexus-mcp

# Log con timestamp
docker-compose logs -t nexus-mcp

# Ultimi 100 log
docker-compose logs --tail=100 nexus-mcp
```

## ⚙️ Configurazione

### Abilitare/Disabilitare Tool

Modifica `config.json` per controllare quali tool sono attivi:

```json
{
  "comment": "Pannello di controllo per il server MCP Nexus",
  "enabled_tools": [
    "calculator",
    "crypto_tools",
    "string_tools",
    "uuid_tools",
    "network_tools",
    "security_tools",
    "network_security_tools",
    "performance_tools",
    "data_analysis",
    "image_processing",
    "audio_processing",
    "video_processing",
    "unit_converter",
    "qr_code_tools",
    "regex_tools",
    "file_converter",
    "pdf_tools",
    "cloud_tools"
  ]
}
```

**Riavvia il server per applicare le modifiche.**

### Aggiungere Nuovi Tool

1. Crea un nuovo file `.py` nella cartella `tools/`
2. Implementa la funzione `register_tools(mcp)`:

```python
# tools/my_tool.py
import logging

def register_tools(mcp):
    logging.info("📝 Registrazione tool-set: My Tool")

    @mcp.tool()
    def my_function(param: str) -> str:
        """Descrizione della funzione."""
        return f"Risultato: {param}"
```

3. Aggiungi `"my_tool"` alla lista `enabled_tools` in `config.json`

## 🔒 Sicurezza

### Filesystem Reader
- **Sandbox**: Accesso limitato alla directory `safe_files/`
- **Path Traversal Protection**: Blocca `../`, `/`, `\\`
- **Path Resolution**: Verifica che il file sia effettivamente nel sandbox

### Web Fetcher
- **Timeout**: Richieste limitate a 10 secondi
- **Content Size**: Limite 4000 caratteri per response
- **User-Agent**: Identificazione richieste server

### General
- **Input Validation**: Tutti i parametri vengono validati
- **Error Handling**: Gestione sicura degli errori senza leak
- **Logging**: Monitoraggio completo attività

## 📋 Requisiti Sistema

- **Python**: 3.8+
- **Sistema Operativo**: Linux, macOS, Windows
- **RAM**: Minimo 512MB
- **Dipendenze**: Vedere `requirements.txt`

### Dipendenze Principali

```
mcp[cli]>=1.13.1      # Model Context Protocol
httpx>=0.28.1         # HTTP client asincrono  
psutil>=7.0.0         # Informazioni sistema
python-dateutil>=2.9  # Parsing date avanzato
```

## 🧪 Testing

### Test Singolo Tool
```bash
python client.py <tool_name> '<json_args>'
```

### Test Completo Sistema
```bash
# Test matematica
python client.py add '{"a": 10, "b": 5}'

# Test sicurezza filesystem  
python client.py read_safe_file '{"filename": "../config.json"}'  # Dovrebbe fallire

# Test validatori
python client.py validate_email '{"email": "invalid.email"}'

# Test sistema
python client.py system_overview '{}'
```

## 🤝 Contribuire

### Aggiungere Nuovi Tool

1. **Fork** il repository
2. **Crea** un branch per il tuo tool: `git checkout -b feature/awesome-tool`
3. **Implementa** il tool seguendo le convenzioni esistenti
4. **Testa** completamente la funzionalità
5. **Documenta** nel README
6. **Crea** una Pull Request

### Linee Guida Tool

- ✅ **Sicurezza**: Valida tutti gli input
- ✅ **Documentazione**: Docstring complete
- ✅ **Error Handling**: Gestione robusta errori  
- ✅ **Logging**: Info per debugging
- ✅ **Encoding**: UTF-8 header nei file

## 📜 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi file `LICENSE` per dettagli.

## 🆘 Supporto

### Problemi Comuni

**Q: Il server non trova un tool abilitato**  
A: Verifica che il file `.py` esista in `tools/` e sia presente in `config.json`

**Q: Errori di encoding**  
A: Assicurati che tutti i file abbiano header `# -*- coding: utf-8 -*-`

**Q: Tool sistema non funziona**  
A: Verifica che `psutil` sia installato: `pip install psutil`

**Q: Timeout nelle richieste web**  
A: Il timeout è configurato a 10 secondi. Alcune risorse potrebbero essere lente.

### Debug

Abilita logging dettagliato modificando il livello in `multi_server.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

