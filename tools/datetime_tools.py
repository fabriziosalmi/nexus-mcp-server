# -*- coding: utf-8 -*-
# tools/datetime_tools.py
import datetime
import time
import logging
import calendar
import re
from typing import Dict, List, Any, Optional, Tuple
from dateutil import parser as dateparser, tz, relativedelta, rrule
import pytz

def register_tools(mcp):
    """Registra i tool di data e ora avanzati con l'istanza del server MCP."""
    logging.info("📅 Registrazione tool-set: DateTime Tools")

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

    @mcp.tool()
    def convert_timezone(date_string: str, from_timezone: str, to_timezone: str) -> Dict[str, Any]:
        """
        Converte una data da un fuso orario all'altro.
        
        Args:
            date_string: Data da convertire
            from_timezone: Fuso orario sorgente (es. "UTC", "Europe/Rome", "America/New_York")
            to_timezone: Fuso orario destinazione
        """
        try:
            # Parse della data
            dt = dateparser.parse(date_string)
            if dt is None:
                return {"success": False, "error": "Formato data non riconosciuto"}
            
            # Ottieni timezone objects
            try:
                from_tz = pytz.timezone(from_timezone)
                to_tz = pytz.timezone(to_timezone)
            except pytz.exceptions.UnknownTimeZoneError as e:
                return {"success": False, "error": f"Fuso orario non valido: {str(e)}"}
            
            # Se la data non ha timezone info, assumiamo sia nel fuso sorgente
            if dt.tzinfo is None:
                dt = from_tz.localize(dt)
            else:
                dt = dt.astimezone(from_tz)
            
            # Converti al fuso destinazione
            converted_dt = dt.astimezone(to_tz)
            
            # Calcola differenza UTC offset
            from_offset = dt.strftime('%z')
            to_offset = converted_dt.strftime('%z')
            
            return {
                "success": True,
                "original_date": date_string,
                "from_timezone": from_timezone,
                "to_timezone": to_timezone,
                "original_datetime": dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "converted_datetime": converted_dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "original_iso": dt.isoformat(),
                "converted_iso": converted_dt.isoformat(),
                "utc_offset_from": from_offset,
                "utc_offset_to": to_offset,
                "time_difference": str(converted_dt - dt.replace(tzinfo=None))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_world_times(reference_time: str = "", timezones: List[str] = None) -> Dict[str, Any]:
        """
        Mostra l'ora corrente in diversi fusi orari del mondo.
        
        Args:
            reference_time: Ora di riferimento (vuoto per ora corrente)
            timezones: Lista fusi orari specifici (vuoto per principali città)
        """
        try:
            # Usa ora corrente se non specificata
            if reference_time:
                base_dt = dateparser.parse(reference_time)
                if base_dt is None:
                    return {"success": False, "error": "Formato ora di riferimento non valido"}
                if base_dt.tzinfo is None:
                    base_dt = pytz.UTC.localize(base_dt)
            else:
                base_dt = datetime.datetime.now(pytz.UTC)
            
            # Fusi orari predefiniti se non specificati
            if not timezones:
                timezones = [
                    "UTC", "Europe/London", "Europe/Rome", "Europe/Paris",
                    "America/New_York", "America/Los_Angeles", "America/Chicago",
                    "Asia/Tokyo", "Asia/Shanghai", "Asia/Dubai", "Asia/Kolkata",
                    "Australia/Sydney", "Pacific/Auckland"
                ]
            
            world_times = []
            
            for tz_name in timezones:
                try:
                    tz_obj = pytz.timezone(tz_name)
                    local_time = base_dt.astimezone(tz_obj)
                    
                    world_times.append({
                        "timezone": tz_name,
                        "local_time": local_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "iso_format": local_time.isoformat(),
                        "utc_offset": local_time.strftime('%z'),
                        "timezone_abbr": local_time.strftime('%Z'),
                        "is_dst": bool(local_time.dst())
                    })
                except pytz.exceptions.UnknownTimeZoneError:
                    world_times.append({
                        "timezone": tz_name,
                        "error": "Fuso orario non valido"
                    })
            
            return {
                "success": True,
                "reference_time": base_dt.isoformat(),
                "reference_timezone": "UTC",
                "world_times": world_times,
                "total_timezones": len(timezones)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def calculate_duration(start_date: str, end_date: str, 
                          include_weekends: bool = True,
                          exclude_holidays: bool = False) -> Dict[str, Any]:
        """
        Calcola la durata tra due date con varie opzioni.
        
        Args:
            start_date: Data iniziale
            end_date: Data finale
            include_weekends: Se includere weekend nel calcolo
            exclude_holidays: Se escludere giorni festivi (basic holidays)
        """
        try:
            start_dt = dateparser.parse(start_date)
            end_dt = dateparser.parse(end_date)
            
            if start_dt is None or end_dt is None:
                return {"success": False, "error": "Formato data non valido"}
            
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, start_dt  # Scambia se necessario
            
            # Calcolo durata totale
            total_duration = end_dt - start_dt
            total_days = total_duration.days
            total_seconds = total_duration.total_seconds()
            
            # Calcolo giorni lavorativi
            business_days = 0
            weekend_days = 0
            holidays = []
            
            current_date = start_dt.date()
            end_date_only = end_dt.date()
            
            # Basic holidays (New Year, Christmas)
            basic_holidays = set()
            for year in range(start_dt.year, end_dt.year + 1):
                basic_holidays.add(datetime.date(year, 1, 1))   # New Year
                basic_holidays.add(datetime.date(year, 12, 25)) # Christmas
            
            while current_date <= end_date_only:
                is_weekend = current_date.weekday() >= 5  # Saturday=5, Sunday=6
                is_holiday = exclude_holidays and current_date in basic_holidays
                
                if is_weekend:
                    weekend_days += 1
                if is_holiday:
                    holidays.append(current_date.isoformat())
                
                if include_weekends or not is_weekend:
                    if not (exclude_holidays and is_holiday):
                        business_days += 1
                
                current_date += datetime.timedelta(days=1)
            
            # Calcoli aggiuntivi
            weeks = total_days // 7
            remaining_days = total_days % 7
            
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            return {
                "success": True,
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "duration": {
                    "total_days": total_days,
                    "weeks": weeks,
                    "remaining_days": remaining_days,
                    "business_days": business_days,
                    "weekend_days": weekend_days,
                    "total_hours": hours,
                    "total_minutes": int(total_seconds // 60),
                    "total_seconds": int(total_seconds)
                },
                "detailed_breakdown": {
                    "years": total_days // 365,
                    "months": total_days // 30,
                    "weeks": weeks,
                    "days": remaining_days,
                    "hours": hours % 24,
                    "minutes": minutes,
                    "seconds": seconds
                },
                "holidays_excluded": holidays if exclude_holidays else [],
                "options": {
                    "include_weekends": include_weekends,
                    "exclude_holidays": exclude_holidays
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def format_date_multiple(date_string: str, formats: List[str] = None, 
                           locale: str = "en") -> Dict[str, Any]:
        """
        Formatta una data in diversi formati.
        
        Args:
            date_string: Data da formattare
            formats: Lista formati personalizzati (opzionale)
            locale: Locale per i nomi (en, it, fr, es, de)
        """
        try:
            dt = dateparser.parse(date_string)
            if dt is None:
                return {"success": False, "error": "Formato data non valido"}
            
            # Formati predefiniti se non specificati
            if not formats:
                formats = [
                    '%Y-%m-%d',           # 2024-01-15
                    '%d/%m/%Y',           # 15/01/2024
                    '%m/%d/%Y',           # 01/15/2024
                    '%B %d, %Y',          # January 15, 2024
                    '%d %B %Y',           # 15 January 2024
                    '%A, %B %d, %Y',      # Monday, January 15, 2024
                    '%Y-%m-%d %H:%M:%S',  # 2024-01-15 14:30:00
                    '%d/%m/%Y %H:%M',     # 15/01/2024 14:30
                    '%Y%m%d',             # 20240115
                    '%Y-W%U-%w',          # Week format
                ]
            
            formatted_dates = {}
            
            for fmt in formats:
                try:
                    formatted_dates[fmt] = dt.strftime(fmt)
                except ValueError as e:
                    formatted_dates[fmt] = f"Error: {str(e)}"
            
            # Formati speciali
            special_formats = {
                "iso_8601": dt.isoformat(),
                "rfc_2822": dt.strftime('%a, %d %b %Y %H:%M:%S'),
                "unix_timestamp": int(dt.timestamp()),
                "excel_serial": (dt - datetime.datetime(1900, 1, 1)).days + 2,
                "julian_day": dt.toordinal() + 1721425.5,
                "week_number": dt.isocalendar()[1],
                "day_of_year": dt.timetuple().tm_yday,
                "quarter": (dt.month - 1) // 3 + 1
            }
            
            # Informazioni aggiuntive
            date_info = {
                "weekday_number": dt.weekday(),  # 0=Monday
                "weekday_name": dt.strftime('%A'),
                "month_name": dt.strftime('%B'),
                "is_weekend": dt.weekday() >= 5,
                "is_leap_year": calendar.isleap(dt.year),
                "days_in_month": calendar.monthrange(dt.year, dt.month)[1]
            }
            
            return {
                "success": True,
                "original_date": date_string,
                "parsed_date": dt.isoformat(),
                "formatted_dates": formatted_dates,
                "special_formats": special_formats,
                "date_info": date_info,
                "locale": locale
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_recurring_dates(start_date: str, pattern: str, count: int = 10,
                               end_date: str = "") -> Dict[str, Any]:
        """
        Genera date ricorrenti basate su un pattern.
        
        Args:
            start_date: Data iniziale
            pattern: Pattern ricorrenza (daily, weekly, monthly, yearly, custom)
            count: Numero di occorrenze da generare
            end_date: Data finale (opzionale)
        """
        try:
            start_dt = dateparser.parse(start_date)
            if start_dt is None:
                return {"success": False, "error": "Data iniziale non valida"}
            
            end_dt = None
            if end_date:
                end_dt = dateparser.parse(end_date)
                if end_dt is None:
                    return {"success": False, "error": "Data finale non valida"}
            
            if count < 1 or count > 100:
                return {"success": False, "error": "Count deve essere tra 1 e 100"}
            
            recurring_dates = []
            
            if pattern == "daily":
                rule = rrule.rrule(rrule.DAILY, dtstart=start_dt, count=count, until=end_dt)
            elif pattern == "weekly":
                rule = rrule.rrule(rrule.WEEKLY, dtstart=start_dt, count=count, until=end_dt)
            elif pattern == "monthly":
                rule = rrule.rrule(rrule.MONTHLY, dtstart=start_dt, count=count, until=end_dt)
            elif pattern == "yearly":
                rule = rrule.rrule(rrule.YEARLY, dtstart=start_dt, count=count, until=end_dt)
            elif pattern == "weekdays":
                # Solo giorni feriali (Mon-Fri)
                rule = rrule.rrule(rrule.DAILY, byweekday=(0,1,2,3,4), dtstart=start_dt, count=count, until=end_dt)
            elif pattern == "weekends":
                # Solo weekend (Sat-Sun)
                rule = rrule.rrule(rrule.DAILY, byweekday=(5,6), dtstart=start_dt, count=count, until=end_dt)
            else:
                return {"success": False, "error": f"Pattern '{pattern}' non supportato"}
            
            for dt in rule:
                recurring_dates.append({
                    "date": dt.strftime('%Y-%m-%d'),
                    "datetime": dt.strftime('%Y-%m-%d %H:%M:%S'),
                    "iso_format": dt.isoformat(),
                    "weekday": dt.strftime('%A'),
                    "unix_timestamp": int(dt.timestamp())
                })
            
            # Calcola intervalli
            if len(recurring_dates) > 1:
                first_interval = recurring_dates[1]["unix_timestamp"] - recurring_dates[0]["unix_timestamp"]
                interval_days = first_interval // 86400
            else:
                interval_days = 0
            
            return {
                "success": True,
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat() if end_dt else None,
                "pattern": pattern,
                "requested_count": count,
                "generated_count": len(recurring_dates),
                "interval_days": interval_days,
                "recurring_dates": recurring_dates,
                "summary": {
                    "first_date": recurring_dates[0]["date"] if recurring_dates else None,
                    "last_date": recurring_dates[-1]["date"] if recurring_dates else None,
                    "total_span_days": (dateparser.parse(recurring_dates[-1]["date"]) - start_dt).days if recurring_dates else 0
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_calendar_info(year: int, month: int = None) -> Dict[str, Any]:
        """
        Ottiene informazioni dettagliate su calendario per anno/mese.
        
        Args:
            year: Anno (1-9999)
            month: Mese (1-12, opzionale per info annuale)
        """
        try:
            if year < 1 or year > 9999:
                return {"success": False, "error": "Anno deve essere tra 1 e 9999"}
            
            if month is not None and (month < 1 or month > 12):
                return {"success": False, "error": "Mese deve essere tra 1 e 12"}
            
            result = {
                "success": True,
                "year": year,
                "is_leap_year": calendar.isleap(year)
            }
            
            if month is not None:
                # Informazioni mensili
                first_weekday, days_in_month = calendar.monthrange(year, month)
                
                # Crea calendario del mese
                cal = calendar.monthcalendar(year, month)
                
                # Prima e ultima data del mese
                first_date = datetime.date(year, month, 1)
                last_date = datetime.date(year, month, days_in_month)
                
                # Conta weekend e giorni lavorativi
                weekends = 0
                weekdays = 0
                
                for day in range(1, days_in_month + 1):
                    date_obj = datetime.date(year, month, day)
                    if date_obj.weekday() >= 5:
                        weekends += 1
                    else:
                        weekdays += 1
                
                result.update({
                    "month": month,
                    "month_name": calendar.month_name[month],
                    "days_in_month": days_in_month,
                    "first_weekday": first_weekday,  # 0=Monday
                    "first_weekday_name": calendar.day_name[first_weekday],
                    "weekdays_count": weekdays,
                    "weekends_count": weekends,
                    "first_date": first_date.isoformat(),
                    "last_date": last_date.isoformat(),
                    "calendar_matrix": cal,
                    "week_numbers": [datetime.date(year, month, max(week)).isocalendar()[1] 
                                   for week in cal if any(day != 0 for day in week)]
                })
            else:
                # Informazioni annuali
                total_days = 366 if calendar.isleap(year) else 365
                
                # Prima e ultima data dell'anno
                first_date = datetime.date(year, 1, 1)
                last_date = datetime.date(year, 12, 31)
                
                # Informazioni per ogni mese
                months_info = []
                total_weekdays = 0
                total_weekends = 0
                
                for m in range(1, 13):
                    _, days_in_m = calendar.monthrange(year, m)
                    month_weekdays = 0
                    month_weekends = 0
                    
                    for day in range(1, days_in_m + 1):
                        date_obj = datetime.date(year, m, day)
                        if date_obj.weekday() >= 5:
                            month_weekends += 1
                            total_weekends += 1
                        else:
                            month_weekdays += 1
                            total_weekdays += 1
                    
                    months_info.append({
                        "month": m,
                        "name": calendar.month_name[m],
                        "days": days_in_m,
                        "weekdays": month_weekdays,
                        "weekends": month_weekends
                    })
                
                result.update({
                    "total_days": total_days,
                    "total_weekdays": total_weekdays,
                    "total_weekends": total_weekends,
                    "first_date": first_date.isoformat(),
                    "last_date": last_date.isoformat(),
                    "first_weekday": first_date.weekday(),
                    "last_weekday": last_date.weekday(),
                    "months_info": months_info
                })
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def validate_and_parse_date(date_input: str, expected_format: str = "", 
                               strict_mode: bool = False) -> Dict[str, Any]:
        """
        Valida e parsa una data con opzioni avanzate.
        
        Args:
            date_input: Stringa data da validare
            expected_format: Formato atteso (opzionale)
            strict_mode: Se usare parsing rigoroso
        """
        try:
            result = {
                "success": False,
                "input": date_input,
                "expected_format": expected_format,
                "strict_mode": strict_mode
            }
            
            # Tentativo parsing con formato specifico
            if expected_format:
                try:
                    dt = datetime.datetime.strptime(date_input, expected_format)
                    result.update({
                        "success": True,
                        "parsed_date": dt.isoformat(),
                        "format_matched": True,
                        "parsing_method": "strptime"
                    })
                    return result
                except ValueError:
                    if strict_mode:
                        result["error"] = f"Data non corrisponde al formato atteso: {expected_format}"
                        return result
            
            # Tentativo parsing con dateutil
            try:
                dt = dateparser.parse(date_input, fuzzy=not strict_mode)
                if dt is None:
                    result["error"] = "Impossibile parsare la data"
                    return result
                
                # Validazioni aggiuntive
                validation_issues = []
                
                # Controlla date future irrealistiche
                now = datetime.datetime.now()
                if dt.year > now.year + 100:
                    validation_issues.append("Data nel futuro oltre 100 anni")
                
                # Controlla date storiche irrealistiche
                if dt.year < 1900:
                    validation_issues.append("Data antecedente al 1900")
                
                # Controlla 29 febbraio in anni non bisestili
                if dt.month == 2 and dt.day == 29 and not calendar.isleap(dt.year):
                    validation_issues.append("29 febbraio in anno non bisestile")
                
                # Analizza componenti della data
                components = {
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "second": dt.second,
                    "microsecond": dt.microsecond
                }
                
                # Determina precisione
                if date_input.count(':') >= 2:
                    precision = "seconds"
                elif date_input.count(':') >= 1:
                    precision = "minutes"
                elif any(char in date_input for char in ['H', 'h', ':']):
                    precision = "hours"
                else:
                    precision = "days"
                
                result.update({
                    "success": True,
                    "parsed_date": dt.isoformat(),
                    "format_matched": expected_format and not validation_issues,
                    "parsing_method": "dateutil",
                    "precision": precision,
                    "components": components,
                    "validation_issues": validation_issues,
                    "weekday": dt.strftime('%A'),
                    "is_weekend": dt.weekday() >= 5,
                    "timezone_aware": dt.tzinfo is not None
                })
                
                return result
                
            except Exception as parse_error:
                result["error"] = f"Errore parsing: {str(parse_error)}"
                return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def calculate_age_and_milestones(birth_date: str, reference_date: str = "") -> Dict[str, Any]:
        """
        Calcola età e milestone importanti.
        
        Args:
            birth_date: Data di nascita
            reference_date: Data di riferimento (vuoto per oggi)
        """
        try:
            birth_dt = dateparser.parse(birth_date)
            if birth_dt is None:
                return {"success": False, "error": "Data di nascita non valida"}
            
            if reference_date:
                ref_dt = dateparser.parse(reference_date)
                if ref_dt is None:
                    return {"success": False, "error": "Data di riferimento non valida"}
            else:
                ref_dt = datetime.datetime.now()
            
            if birth_dt > ref_dt:
                return {"success": False, "error": "Data di nascita nel futuro"}
            
            # Calcola età esatta
            age_delta = relativedelta.relativedelta(ref_dt, birth_dt)
            
            # Prossimo compleanno
            next_birthday = datetime.date(ref_dt.year, birth_dt.month, birth_dt.day)
            if next_birthday <= ref_dt.date():
                next_birthday = datetime.date(ref_dt.year + 1, birth_dt.month, birth_dt.day)
            
            days_to_birthday = (next_birthday - ref_dt.date()).days
            
            # Milestone importanti
            milestones = []
            
            # Età milestone
            age_milestones = [18, 21, 30, 40, 50, 65, 70, 80, 90, 100]
            for milestone_age in age_milestones:
                milestone_date = birth_dt + relativedelta.relativedelta(years=milestone_age)
                if milestone_date <= ref_dt:
                    milestones.append({
                        "age": milestone_age,
                        "date": milestone_date.strftime('%Y-%m-%d'),
                        "achieved": True,
                        "years_ago": age_delta.years - milestone_age
                    })
                else:
                    milestones.append({
                        "age": milestone_age,
                        "date": milestone_date.strftime('%Y-%m-%d'),
                        "achieved": False,
                        "years_until": milestone_age - age_delta.years
                    })
            
            # Calcoli aggiuntivi
            total_days_lived = (ref_dt.date() - birth_dt.date()).days
            total_hours_lived = total_days_lived * 24
            total_minutes_lived = total_hours_lived * 60
            
            return {
                "success": True,
                "birth_date": birth_dt.strftime('%Y-%m-%d'),
                "reference_date": ref_dt.strftime('%Y-%m-%d'),
                "exact_age": {
                    "years": age_delta.years,
                    "months": age_delta.months,
                    "days": age_delta.days
                },
                "age_in_different_units": {
                    "total_days": total_days_lived,
                    "total_weeks": total_days_lived // 7,
                    "total_months": age_delta.years * 12 + age_delta.months,
                    "total_hours": total_hours_lived,
                    "total_minutes": total_minutes_lived
                },
                "next_birthday": {
                    "date": next_birthday.strftime('%Y-%m-%d'),
                    "days_until": days_to_birthday,
                    "weekday": next_birthday.strftime('%A'),
                    "turning_age": age_delta.years + 1
                },
                "milestones": milestones,
                "life_statistics": {
                    "birth_weekday": birth_dt.strftime('%A'),
                    "zodiac_sign": _get_zodiac_sign(birth_dt.month, birth_dt.day),
                    "generation": _get_generation(birth_dt.year)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions
    def _get_zodiac_sign(month: int, day: int) -> str:
        """Determina segno zodiacale."""
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "Aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "Taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "Gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "Cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "Leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "Virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "Libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "Scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "Sagittarius"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "Capricorn"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "Aquarius"
        else:
            return "Pisces"

    def _get_generation(year: int) -> str:
        """Determina generazione di appartenenza."""
        if year >= 2010:
            return "Generation Alpha"
        elif year >= 1997:
            return "Generation Z"
        elif year >= 1981:
            return "Millennials"
        elif year >= 1965:
            return "Generation X"
        elif year >= 1946:
            return "Baby Boomers"
        else:
            return "Silent Generation"