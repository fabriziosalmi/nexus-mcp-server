# -*- coding: utf-8 -*-
# tools/web_fetcher.py
import logging
import httpx

# E' buona pratica definire un User-Agent per identificare le richieste del nostro server.
HEADERS = {"User-Agent": "NexusMCPServer/1.0"}

def register_tools(mcp):
    """Registra i tool per il recupero di contenuti web con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Web Fetcher")

    @mcp.tool()
    async def fetch_url_content(url: str) -> str:
        """
        Recupera il contenuto testuale (HTML) da un dato URL.

        Args:
            url: L'URL completo da cui scaricare il contenuto (es. 'https://www.google.com').
        """
        logging.info(f"Tentativo di fetch dall'URL: {url}")
        try:
            async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status() # Lancia un'eccezione per status code 4xx o 5xx
                
                # Limita la dimensione del contenuto per evitare di sovraccaricare il contesto dell'LLM
                content = response.text
                max_length = 4000
                if len(content) > max_length:
                    content = content[:max_length] + "\n... [contenuto troncato] ..."
                
                return f"--- Contenuto da {url} ---\n{content}"
        except httpx.RequestError as e:
            return f"ERRORE DI RETE: Impossibile raggiungere l'URL '{url}'. Dettagli: {e}"
        except httpx.HTTPStatusError as e:
            return f"ERRORE HTTP: Il server ha risposto con lo status {e.response.status_code} per l'URL '{url}'."
        except Exception as e:
            logging.error(f"[WebFetcher] Errore imprevisto durante il fetch di '{url}': {e}")
            return f"ERRORE: Si è verificato un problema tecnico imprevisto durante il fetch dell'URL."