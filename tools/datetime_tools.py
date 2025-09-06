# -*- coding: utf-8 -*-
# tools/datetime_tools.py
import datetime
import time
import logging
from dateutil import parser as dateparser, tz

def register_tools(mcp):
    """Registra i tool di data e ora con l'istanza del server MCP."""
    logging.info("📝 Registrazione tool-set: DateTime Tools")

    @mcp.tool()
    def current_timestamp() -> str:
        """
        Restituisce il timestamp corrente in vari formati.
        """
        now = datetime.datetime.now()
        utc_now = datetime.datetime.utcnow()
        
        return f"""Timestamp corrente:
- ISO 8601: {now.isoformat()}
- UTC ISO: {utc_now.isoformat()}Z
- Unix timestamp: {int(time.time())}
- Formato leggibile: {now.strftime('%d/%m/%Y %H:%M:%S')}
- UTC leggibile: {utc_now.strftime('%d/%m/%Y %H:%M:%S')} UTC"""

    @mcp.tool()
    def unix_to_date(timestamp: int) -> str:
        """
        Converte un timestamp Unix in data leggibile.

        Args:
            timestamp: Il timestamp Unix da convertire.
        """
        try:
            dt = datetime.datetime.fromtimestamp(timestamp)
            utc_dt = datetime.datetime.utcfromtimestamp(timestamp)
            
            return f"""Conversione timestamp {timestamp}:
- Locale: {dt.strftime('%d/%m/%Y %H:%M:%S')}
- UTC: {utc_dt.strftime('%d/%m/%Y %H:%M:%S')} UTC
- ISO 8601: {dt.isoformat()}"""
        except (ValueError, OverflowError) as e:
            return f"ERRORE: Timestamp non valido - {str(e)}"

    @mcp.tool()
    def date_to_unix(date_string: str) -> str:
        """
        Converte una data in timestamp Unix.

        Args:
            date_string: La data da convertire (es. "2024-12-25 15:30:00" o "25/12/2024").
        """
        try:
            dt = dateparser.parse(date_string)
            if dt is None:
                return "ERRORE: Formato data non riconosciuto"
            
            timestamp = int(dt.timestamp())
            
            return f"""Conversione "{date_string}":
- Unix timestamp: {timestamp}
- Data interpretata: {dt.strftime('%d/%m/%Y %H:%M:%S')}
- ISO 8601: {dt.isoformat()}"""
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def date_math(start_date: str, operation: str, amount: int, unit: str) -> str:
        """
        Esegue operazioni matematiche sulle date.

        Args:
            start_date: La data di partenza (es. "2024-01-15").
            operation: L'operazione da eseguire ("add" o "subtract").
            amount: La quantita' da aggiungere/sottrarre.
            unit: L'unita' di tempo ("days", "weeks", "months", "years", "hours", "minutes").
        """
        try:
            dt = dateparser.parse(start_date)
            if dt is None:
                return "ERRORE: Formato data di partenza non riconosciuto"
            
            if operation not in ["add", "subtract"]:
                return "ERRORE: Operazione deve essere 'add' o 'subtract'"
            
            if unit == "days":
                delta = datetime.timedelta(days=amount)
            elif unit == "weeks":
                delta = datetime.timedelta(weeks=amount)
            elif unit == "hours":
                delta = datetime.timedelta(hours=amount)
            elif unit == "minutes":
                delta = datetime.timedelta(minutes=amount)
            elif unit in ["months", "years"]:
                # Calcolo approssimativo per mesi e anni
                days_per_unit = 30 if unit == "months" else 365
                delta = datetime.timedelta(days=amount * days_per_unit)
            else:
                return "ERRORE: Unita' non supportata. Usa: days, weeks, months, years, hours, minutes"
            
            if operation == "add":
                result_dt = dt + delta
            else:
                result_dt = dt - delta
            
            return f"""Calcolo data:
- Data iniziale: {dt.strftime('%d/%m/%Y %H:%M:%S')}
- Operazione: {operation} {amount} {unit}
- Risultato: {result_dt.strftime('%d/%m/%Y %H:%M:%S')}
- ISO 8601: {result_dt.isoformat()}"""
        except Exception as e:
            return f"ERRORE: {str(e)}"