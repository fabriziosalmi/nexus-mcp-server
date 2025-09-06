# 🚀 Nexus MCP Server - Guida al Deployment

Questa guida completa ti mostrerà come deployare e utilizzare il server Nexus MCP con Docker, VSCode/Copilot e Claude Code.

## 📋 Indice

- [Prerequisiti](#prerequisiti)
- [Deployment Rapido](#deployment-rapido)
- [Configurazione Docker](#configurazione-docker)
- [Integrazione VSCode/Copilot](#integrazione-vscodecopilot)
- [Integrazione Claude Code](#integrazione-claude-code)
- [Monitoraggio e Debug](#monitoraggio-e-debug)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisiti

### Sistemi Supportati
- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 9+
- **macOS**: 10.15+
- **Windows**: Windows 10+ (con WSL2)

### Software Necessario
```bash
# Docker & Docker Compose
docker --version    # >= 20.10
docker-compose --version  # >= 1.29 (o docker compose plugin)

# Python (per sviluppo locale)
python3 --version   # >= 3.8

# Git (per clonare il repository)
git --version
```

### Installazione Rapida Prerequisites

#### macOS (con Homebrew)
```bash
# Installa Docker Desktop
brew install --cask docker

# Avvia Docker Desktop
open -a Docker

# Verifica installazione
docker run hello-world
```

#### Ubuntu/Debian
```bash
# Installa Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installa Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Riavvia per applicare i gruppi
newgrp docker
```

## 🚀 Deployment Rapido

### Metodo 1: Script Automatico (Raccomandato)

```bash
# Clona il repository
git clone <repository-url> nexus-mcp-server
cd nexus-mcp-server

# Deployment completo (locale + Docker)
./scripts/deploy.sh full

# Oppure deployment specifico:
./scripts/deploy.sh local    # Solo ambiente locale
./scripts/deploy.sh docker   # Solo Docker
./scripts/deploy.sh compose  # Docker Compose
```

### Metodo 2: Deployment Manuale

#### A. Setup Locale
```bash
# Crea ambiente virtuale
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -r requirements.txt

# Test rapido
python client.py add '{"a": 10, "b": 5}'
```

#### B. Docker Build
```bash
# Build immagine
docker build -t nexus-mcp-server:latest .

# Test Docker
docker run --rm -i nexus-mcp-server:latest python -c "print('OK')"
```

#### C. Docker Compose
```bash
# Avvia tutti i servizi
docker-compose up -d

# Verifica status
docker-compose ps

# Logs
docker-compose logs -f nexus-mcp
```

## 🐳 Configurazione Docker

### Dockerfile Features
- **Base Image**: Python 3.12 slim per performance ottimali
- **Security**: Utente non-root `nexus`
- **Multi-stage**: Build ottimizzato per dimensioni ridotte
- **Health Check**: Monitoraggio automatico salute container

### Environment Variables
```bash
# Nel container o docker-compose.yml
PYTHONUNBUFFERED=1          # Output Python non bufferizzato
MCP_SERVER_NAME=NexusServer # Nome server personalizzabile
LOG_LEVEL=INFO              # Livello di logging (DEBUG, INFO, WARNING, ERROR)
```

### Volume Mapping
```yaml
volumes:
  - ./safe_files:/app/safe_files:rw     # Directory sicura file
  - ./config.json:/app/config.json:ro  # Configurazione server
  - ./logs:/app/logs:rw                 # Log persistenti (opzionale)
```

### Networking
```yaml
# Per accesso MCP standard
network_mode: "host"

# Per networking personalizzato
networks:
  - nexus-network
```

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 512M      # Limite memoria
      cpus: '0.5'       # Limite CPU (50%)
    reservations:
      memory: 256M      # Memoria garantita
      cpus: '0.25'      # CPU garantita
```

## 🔧 Integrazione VSCode/Copilot

### Installazione Extension MCP

1. **Installa MCP Extension** per VSCode (quando disponibile)
2. **Configura Settings JSON**:

```json
// .vscode/settings.json
{
  "mcp.servers": {
    "nexus-local": {
      "command": "python",
      "args": ["multi_server.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "LOG_LEVEL": "INFO"
      }
    },
    "nexus-docker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--network=host",
        "-v", "${workspaceFolder}/safe_files:/app/safe_files:rw",
        "-v", "${workspaceFolder}/config.json:/app/config.json:ro",
        "nexus-mcp-server:latest"
      ]
    }
  },
  "mcp.defaultServer": "nexus-local"
}
```

### Utilizzo in VSCode

1. **Apertura Server MCP**:
   - Ctrl/Cmd + Shift + P
   - "MCP: Connect to Server"
   - Seleziona "nexus-local" o "nexus-docker"

2. **Utilizzo Tool**:
   ```
   Copilot Chat: @mcp generate_uuid4 {}
   Copilot Chat: @mcp validate_email {"email": "test@example.com"}
   Copilot Chat: @mcp string_case_convert {"text": "Hello World", "case_type": "snake"}
   ```

### Configurazione Copilot

```json
// settings.json - Configurazione Copilot
{
  "github.copilot.chat.experimental.mcp.enabled": true,
  "github.copilot.chat.experimental.mcp.servers": ["nexus-local"]
}
```

## 🤖 Integrazione Claude Code

### Setup Configurazione

1. **Copia il file di configurazione**:
```bash
# Copia la configurazione base
cp mcp-configs/claude-code-config.json ~/.config/claude-code/mcp-servers.json

# O personalizza il percorso
vim mcp-configs/claude-code-config.json
# Sostituisci "/path/to/nexus-mcp-server" con il percorso reale
```

2. **Configurazione Claude Code** (`~/.config/claude-code/mcp-servers.json`):
```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["multi_server.py"],
      "cwd": "/percorso/assoluto/a/nexus-mcp-server",
      "env": {
        "PYTHONPATH": "/percorso/assoluto/a/nexus-mcp-server",
        "MCP_SERVER_NAME": "NexusServer",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Utilizzo con Claude Code

```bash
# Avvia Claude Code con il server MCP
claude-code --mcp-server nexus

# Oppure usa direttamente i tool
claude-code "Genera un UUID v4" --tool generate_uuid4
claude-code "Valida questa email: test@example.com" --tool validate_email
claude-code "Converti 'Hello World' in snake_case" --tool string_case_convert
```

### Esempi Pratici Claude Code

```bash
# Hash generation
claude-code "Genera hash SHA256 per 'password123'" \
  --tool generate_hash \
  --args '{"text": "password123", "algorithm": "sha256"}'

# Date operations
claude-code "Che timestamp Unix è adesso?" \
  --tool current_timestamp

# System info
claude-code "Mostra informazioni del sistema" \
  --tool system_overview

# String manipulation
claude-code "Pulisci questa stringa: '  Hello   World!  '" \
  --tool string_clean \
  --args '{"text": "  Hello   World!  ", "operation": "normalize_spaces"}'
```

## 📊 Monitoraggio e Debug

### Logging Configuration

```python
# multi_server.py - Configurazione logging
import logging

# Livelli disponibili
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}

# Configurazione custom
logging.basicConfig(
    level=LOG_LEVELS.get(os.getenv('LOG_LEVEL', 'INFO')),
    format='[%(asctime)s] [%(levelname)-8s] --- %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('logs/nexus.log')  # Se directory logs esiste
    ]
)
```

### Docker Logs

```bash
# Logs in tempo reale
docker-compose logs -f nexus-mcp

# Logs con timestamp
docker-compose logs -t nexus-mcp

# Ultimi N logs
docker-compose logs --tail=100 nexus-mcp

# Logs di un container specifico
docker logs -f nexus-mcp-server
```

### Health Monitoring

```bash
# Status servizi Docker Compose
docker-compose ps

# Health check manuale
docker exec nexus-mcp-server python -c "
import sys
try:
    import importlib
    for module in ['calculator', 'crypto_tools', 'datetime_tools']:
        importlib.import_module(f'tools.{module}')
    print('All modules OK')
    sys.exit(0)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"

# Test funzionalità specifica
docker exec nexus-mcp-server python client.py system_overview '{}'
```

### Performance Monitoring

```bash
# Resource usage
docker stats nexus-mcp-server

# Processi all'interno del container
docker exec nexus-mcp-server ps aux

# Memory usage dettagliato
docker exec nexus-mcp-server python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"
```

## 🔍 Troubleshooting

### Problemi Comuni e Soluzioni

#### 1. Container non si avvia
```bash
# Controllo errori build
docker build -t nexus-mcp-server:latest . --no-cache

# Controllo configurazione
docker-compose config

# Verifica permessi directory
ls -la safe_files/
chmod 755 safe_files/
```

#### 2. Tool non funzionano
```bash
# Verifica configurazione
cat config.json

# Test singolo tool
docker exec nexus-mcp-server python client.py add '{"a": 1, "b": 1}'

# Verifica dipendenze
docker exec nexus-mcp-server pip list
```

#### 3. Problemi di encoding
```bash
# Verifica encoding file
file -bi tools/*.py

# Forza encoding UTF-8
export PYTHONIOENCODING=utf-8
```

#### 4. Problemi VSCode/Claude Code
```bash
# Verifica path assoluti nelle configurazioni
realpath /path/to/nexus-mcp-server

# Test comando diretto
python multi_server.py

# Verifica environment variables
env | grep PYTHON
```

### Debug Mode

```bash
# Abilita debug completo
export LOG_LEVEL=DEBUG
python multi_server.py

# Debug Docker
docker run -it --rm nexus-mcp-server:latest bash

# Debug con client
python client.py --help
```

### Reset Completo

```bash
# Reset ambiente locale
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Reset Docker
docker-compose down -v
docker rmi nexus-mcp-server:latest
docker system prune -a
./scripts/deploy.sh docker
```

## 🚀 Deployment Produzione

### Best Practices

1. **Security**:
```bash
# Usa utente non-root
USER nexus

# Limita resource container
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

2. **Monitoring**:
```yaml
# Aggiungi healthcheck
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
```

3. **Backup**:
```bash
# Backup configurazioni e dati
tar -czf nexus-backup-$(date +%Y%m%d).tar.gz \
  config.json safe_files/ mcp-configs/
```

4. **Updates**:
```bash
# Update sicuro
docker-compose pull
docker-compose up -d --no-deps nexus-mcp
```

## 📞 Supporto

- **Issues**: Apri una issue su GitHub
- **Documentation**: Consulta README.md principale  
- **Logs**: Includi sempre i log quando riporti problemi
- **Configuration**: Condividi la configurazione (mascherando dati sensibili)

---

**Nexus MCP Server** - *Il tuo hub MCP definitivo per VSCode, Copilot e Claude Code* 🚀