# Interfaccia di Configurazione Dinamica - Nexus MCP Server

Questa documentazione descrive l'interfaccia web per la gestione dinamica della configurazione del server Nexus MCP, che permette di abilitare/disabilitare i tool e monitorare il server in tempo reale senza necessità di riavvio.

## Caratteristiche Principali

### 🔧 Dashboard dei Tool
- **Visualizzazione di tutti i tool disponibili**: Scansiona automaticamente la cartella `tools/` per trovare tutti i file .py
- **Checkbox per abilitazione/disabilitazione**: Interfaccia intuitiva per selezionare i tool
- **Descrizioni automatiche**: Estrae le descrizioni dai commenti nei file dei tool
- **Controlli rapidi**: Pulsanti "Seleziona Tutti" e "Deseleziona Tutti"

### 📊 Visualizzatore di Metriche
- **Metriche in tempo reale**: Tool abilitati, tool disponibili, sessioni attive
- **Aggiornamento automatico**: Le metriche si aggiornano ogni 5 secondi
- **Integrazione Prometheus**: Utilizza il sistema di monitoring esistente

### 📋 Streamer di Log in Tempo Reale
- **Server-Sent Events (SSE)**: Stream continuo dei log del server
- **Filtri per livello**: Visualizzazione colorata per INFO, WARNING, ERROR
- **Auto-scroll**: Scorre automaticamente per mostrare i log più recenti
- **Buffer limitato**: Mantiene solo le ultime 100 righe in memoria

### ⚡ Hot Reload
- **Configurazione dinamica**: Applica modifiche senza riavviare il server
- **Salvataggio automatico**: Aggiorna il file `config.json` automaticamente
- **Feedback immediato**: Notifiche di successo/errore
- **Zero downtime**: Il server continua a funzionare durante il reload

## Avvio del Server UI

### Modalità Standalone
```bash
# Avvia il server UI su porta 8888
python ui_server.py

# Il server sarà disponibile su http://localhost:8888
```

### Parametri di Configurazione
- **Host**: `0.0.0.0` (accetta connessioni da tutti gli indirizzi)
- **Porta**: `8888`
- **Log Level**: `INFO`
- **Timeout**: Configurabile per operazioni lunghe

## Endpoint API

### Gestione Tool
- `GET /api/tools/available` - Lista tutti i tool disponibili con stato
- `POST /api/tools/configure` - Aggiorna configurazione tool e ricarica server

### Metriche e Monitoring
- `GET /api/metrics/current` - Metriche correnti del server
- `GET /api/logs/stream` - Stream SSE dei log in tempo reale
- `GET /api/logs/recent?limit=50` - Ultimi N log entries

### Health Check
- `GET /health` - Stato del server UI
- `GET /` - Dashboard principale (HTML)

## Architettura Tecnica

### Frontend
- **HTML5 + CSS3 + JavaScript Vanilla**: Nessuna dipendenza frontend
- **Responsive Design**: Funziona su desktop e mobile
- **Real-time Updates**: WebSocket-like tramite Server-Sent Events
- **Progressive Enhancement**: Funziona anche senza JavaScript

### Backend
- **FastAPI**: Framework web moderno e performante
- **Async/Await**: Gestione asincrona per SSE e operazioni I/O
- **Pydantic Models**: Validazione automatica dei dati
- **In-Memory Logging**: Buffer circolare per catturare i log

### Integrazione con Nexus
- **Importazione diretta**: Utilizza `multi_server.py` e `monitoring.py`
- **Configurazione condivisa**: Legge e scrive lo stesso `config.json`
- **Hot Reload**: Ricrea istanze FastMCP senza interruzioni

## Sicurezza e Prestazioni

### Sicurezza
- **Sandbox Mode**: Accesso limitato solo ai file di configurazione
- **Input Validation**: Validazione di tutti i parametri di input
- **Error Handling**: Gestione robusta degli errori
- **Log Sanitization**: Filtraggio di informazioni sensibili

### Prestazioni
- **Async Streams**: Stream non bloccanti per log e metriche
- **Memory Management**: Buffer limitato per evitare memory leak
- **Efficient Polling**: Controllo periodico ottimizzato
- **Caching**: Cache intelligente per ridurre I/O

## Workflow di Utilizzo

### 1. Accesso alla Dashboard
```
http://localhost:8888/
```

### 2. Gestione Tool
1. Visualizza tutti i tool disponibili nel pannello sinistro
2. Seleziona/deseleziona i tool desiderati tramite checkbox
3. Usa i pulsanti "Seleziona Tutti" o "Deseleziona Tutti" per operazioni rapide
4. Clicca "Applica Modifiche" per salvare la configurazione

### 3. Monitoring
1. Osserva le metriche nel pannello destro (aggiornamento automatico)
2. Monitora i log in tempo reale nel pannello inferiore
3. Verifica il successo delle operazioni tramite notifiche

### 4. Troubleshooting
1. Controlla i log per eventuali errori durante il reload
2. Verifica le metriche per confermare i cambiamenti
3. Usa gli endpoint API per debug programmatico

## Personalizzazione

### Temi e Stili
Il CSS è modulare e può essere facilmente personalizzato:
- **Colori**: Modifica le variabili CSS per i colori principali
- **Layout**: Grid responsive configurabile
- **Animazioni**: Transizioni CSS personalizzabili

### Estensioni
L'architettura permette facilmente di aggiungere:
- **Nuove metriche**: Estendi il sistema di monitoring
- **Filtri log**: Aggiungi filtri per modulo/livello
- **Gestione utenti**: Sistema di autenticazione
- **Backup configurazioni**: Versioning delle configurazioni

## Integrazione con Docker

### Dockerfile
```dockerfile
# Il server UI è incluso nell'immagine principale
EXPOSE 8888
CMD ["python", "ui_server.py"]
```

### Docker Compose
```yaml
services:
  nexus-ui:
    build: .
    ports:
      - "8888:8888"
    volumes:
      - ./config.json:/app/config.json
    environment:
      - UI_HOST=0.0.0.0
      - UI_PORT=8888
```

## Esempi di Utilizzo

### Configurazione via API
```bash
# Abilita solo tool essenziali
curl -X POST http://localhost:8888/api/tools/configure \
  -H "Content-Type: application/json" \
  -d '{"enabled_tools": ["calculator", "system_info", "crypto_tools"]}'

# Ottieni metriche correnti
curl http://localhost:8888/api/metrics/current

# Stream log in tempo reale
curl -N http://localhost:8888/api/logs/stream
```

### Automazione
```python
import requests
import json

# Client Python per gestione automatica
class NexusUIClient:
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url
    
    def get_available_tools(self):
        return requests.get(f"{self.base_url}/api/tools/available").json()
    
    def configure_tools(self, tool_names):
        return requests.post(
            f"{self.base_url}/api/tools/configure",
            json={"enabled_tools": tool_names}
        ).json()
    
    def get_metrics(self):
        return requests.get(f"{self.base_url}/api/metrics/current").json()

# Esempio d'uso
client = NexusUIClient()
tools = client.get_available_tools()
print(f"Tool disponibili: {len(tools)}")

# Abilita solo tool di base
basic_tools = ["calculator", "system_info", "string_tools"]
result = client.configure_tools(basic_tools)
print(f"Configurazione applicata: {result['status']}")
```

## Troubleshooting

### Problemi Comuni

**Server non si avvia**
- Verifica che la porta 8888 non sia occupata
- Controlla i permessi di lettura/scrittura su `config.json`
- Verifica che tutte le dipendenze siano installate

**Hot reload non funziona**
- Controlla i log per errori durante il reload
- Verifica che il file `config.json` sia scrivibile
- Assicurati che i tool selezionati esistano nella cartella `tools/`

**Log streaming non funziona**
- Verifica che il browser supporti Server-Sent Events
- Controlla la console JavaScript per errori
- Testa l'endpoint `/api/logs/stream` direttamente

### Debug
```bash
# Attiva logging verbose
export LOG_LEVEL=DEBUG
python ui_server.py

# Test endpoint manualmente
curl -v http://localhost:8888/health
curl -v http://localhost:8888/api/tools/available
curl -v http://localhost:8888/api/metrics/current
```

## Roadmap Future

### Funzionalità Pianificate
- **Autenticazione**: Sistema di login/logout
- **Multi-tenancy**: Gestione configurazioni multiple
- **Backup automatico**: Versioning delle configurazioni
- **Statistiche avanzate**: Grafici e trend delle metriche
- **Plugin system**: Estensioni per funzionalità custom
- **Mobile app**: App nativa per gestione remota

### Miglioramenti Tecnici
- **WebSocket**: Migrazione da SSE a WebSocket per comunicazione bidirezionale
- **Database**: Storage persistente per configurazioni e log
- **Clustering**: Supporto per multiple istanze server
- **CDN**: Ottimizzazione asset statici
- **Service Worker**: Funzionalità offline

---

**Nota**: Questa interfaccia è progettata per essere user-friendly ma potente, permettendo sia agli utenti tecnici che non tecnici di gestire efficacemente la configurazione del server Nexus MCP.