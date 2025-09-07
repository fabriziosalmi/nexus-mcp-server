# -*- coding: utf-8 -*-
# tools/filesystem_reader.py
import logging
from pathlib import Path

# --- ZONA DI SICUREZZA ---
# Definiamo una directory "sandbox" da cui è permesso leggere i file.
# Qualsiasi tentativo di leggere file al di fuori di questa cartella verrà bloccato.
SAFE_DIRECTORY = Path.cwd() / "safe_files"

def _setup_safe_zone():
    """
    Funzione di utility interna per creare la directory sicura e un file di esempio
    se non esistono già, rendendo il tool immediatamente testabile.
    """
    if not SAFE_DIRECTORY.exists():
        logging.info(f"Prima esecuzione: creo la directory sandbox in: {SAFE_DIRECTORY}")
        SAFE_DIRECTORY.mkdir()
    
    example_file = SAFE_DIRECTORY / "esempio.txt"
    if not example_file.exists():
        example_file.write_text("Questo è un file di esempio che può essere letto in sicurezza dal server Nexus.", encoding="utf-8")

def register_tools(mcp):
    """Registra i tool per la lettura sicura di file con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: Lettore File System (Sandbox)")
    _setup_safe_zone()
    
    @mcp.tool()
    def read_safe_file(filename: str) -> str:
        """
        Legge il contenuto di un file dalla directory sicura 'safe_files'.
        L'uso di percorsi relativi come '../' o percorsi assoluti è bloccato.

        Args:
            filename: Il nome del file da leggere (es. 'esempio.txt').
        """
        try:
            # VALIDAZIONE DI SICUREZZA 1: Rifiuta nomi di file sospetti.
            if ".." in filename or "/" in filename or "\\" in filename:
                return "ERRORE DI SICUREZZA: Il nome del file contiene caratteri non validi per la navigazione."

            target_file = SAFE_DIRECTORY / filename
            
            # VALIDAZIONE DI SICUREZZA 2: Verifica che il percorso assoluto del file richiesto
            # sia effettivamente un figlio della nostra directory sicura. È la difesa più forte.
            if not target_file.resolve().is_relative_to(SAFE_DIRECTORY.resolve()):
                return "ERRORE DI SICUREZZA: Tentativo di accesso a un file al di fuori della directory sandbox."

            if not target_file.is_file():
                return f"ERRORE: Il file '{filename}' non è stato trovato nella directory sicura."

            content = target_file.read_text(encoding="utf-8")
            return f"--- Contenuto di '{filename}' ---\n{content}"
        
        except Exception as e:
            logging.error(f"[FileSystemReader] Errore imprevisto durante la lettura di '{filename}': {e}")
            return f"ERRORE: Si è verificato un problema tecnico durante la lettura del file."