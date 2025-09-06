# 🚀 Nexus MCP Server

**Nexus** è un server MCP (Model Context Protocol) avanzato, modulare e configurabile che funge da hub centrale per integrare una vasta gamma di strumenti personalizzati, rendendoli disponibili a un Large Language Model (LLM).

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
    └── system_info.py          # 💻 Informazioni sistema
```

## 🚀 Quick Start

### 1. Setup Ambiente

```bash
# Clona/scarica il progetto
cd nexus-mcp-server

# Crea ambiente virtuale
python -m venv .venv

# Attiva ambiente virtuale
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Avvia il Server

```bash
# Il server si avvia automaticamente tramite client
python client.py <nome_tool> '<argomenti_json>'
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
    "uuid_tools"
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

## 🔄 Changelog

### v2.0.0 (Corrente)
- ➕ Aggiunti 7 nuovi tool (Crypto, Encoding, DateTime, UUID, String, Validator, System)
- 🔧 Migliorata configurazione tool
- 📚 Documentazione completa
- 🧪 Test estesi

### v1.0.0
- 🚀 Release iniziale
- 🧮 Calculator tool
- 📁 Filesystem reader tool  
- 🌐 Web fetcher tool
- ⚙️ Sistema configurazione dinamica

---

**Nexus MCP Server** - *Il tuo hub centrale per tool MCP* 🚀