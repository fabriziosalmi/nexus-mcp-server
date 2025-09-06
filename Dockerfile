# Nexus MCP Server - Dockerfile
FROM python:3.12-slim

# Metadata del container
LABEL maintainer="Nexus MCP Server"
LABEL description="Advanced, modular and configurable MCP server"
LABEL version="2.0.0"

# Imposta variabili di ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crea utente non-root per sicurezza
RUN groupadd -r nexus && useradd -r -g nexus -m nexus

# Installa dipendenze di sistema necessarie
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Imposta directory di lavoro
WORKDIR /app

# Copia requirements prima per sfruttare la cache Docker
COPY requirements.txt .

# Installa dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Crea directory per i file sicuri se non esiste
RUN mkdir -p safe_files

# Cambia ownership alla directory dell'app
RUN chown -R nexus:nexus /app

# Switcha all'utente non-root
USER nexus

# Espone la porta per comunicazioni HTTP
EXPOSE 9999

# Copia e configura entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

# Definisce il punto di ingresso
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando di default (può essere sovrascritto)
CMD []

# Health check per verificare che il container sia funzionante
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"