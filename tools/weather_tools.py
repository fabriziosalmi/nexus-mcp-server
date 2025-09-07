# -*- coding: utf-8 -*-
# tools/weather_tools.py
import logging
import requests
import json
from datetime import datetime

def register_tools(mcp):
    """Registra i tool meteorologici con l'istanza del server MCP."""
    logging.info("🌦️ Registrazione tool-set: Weather Tools")

    @mcp.tool()
    def get_weather_info(city: str, country_code: str = "", units: str = "metric") -> str:
        """
        Ottiene informazioni meteorologiche per una città (richiede API key OpenWeatherMap).
        
        Args:
            city: Nome della città
            country_code: Codice paese ISO (opzionale, es. "IT", "US")
            units: Unità di misura (metric, imperial, kelvin)
        """
        try:
            # Per demo, restituisce dati simulati
            mock_data = {
                "city": city,
                "country": country_code or "N/A",
                "temperature": "22°C" if units == "metric" else "72°F",
                "humidity": "65%",
                "conditions": "Parzialmente nuvoloso",
                "wind_speed": "15 km/h" if units == "metric" else "9 mph",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return f"""🌦️ Meteo per {city}:
Temperatura: {mock_data['temperature']}
Condizioni: {mock_data['conditions']}
Umidità: {mock_data['humidity']}
Vento: {mock_data['wind_speed']}
Aggiornamento: {mock_data['timestamp']}

Nota: Dati simulati - configurare API key OpenWeatherMap per dati reali"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def parse_weather_data(weather_json: str) -> str:
        """
        Analizza e formatta dati meteorologici in formato JSON.
        
        Args:
            weather_json: Dati meteorologici in formato JSON
        """
        try:
            data = json.loads(weather_json)
            
            # Estrae informazioni comuni dai dati meteo
            result = "📊 Analisi dati meteorologici:\n"
            
            if 'main' in data:
                temp = data['main'].get('temp', 'N/A')
                humidity = data['main'].get('humidity', 'N/A')
                pressure = data['main'].get('pressure', 'N/A')
                result += f"Temperatura: {temp}°\n"
                result += f"Umidità: {humidity}%\n"
                result += f"Pressione: {pressure} hPa\n"
            
            if 'weather' in data and data['weather']:
                condition = data['weather'][0].get('description', 'N/A')
                result += f"Condizioni: {condition}\n"
            
            if 'wind' in data:
                wind_speed = data['wind'].get('speed', 'N/A')
                result += f"Vento: {wind_speed} m/s\n"
            
            return result
            
        except json.JSONDecodeError:
            return "ERRORE: JSON non valido"
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def weather_alert_formatter(temperature: float, humidity: float, wind_speed: float) -> str:
        """
        Genera avvisi meteorologici basati su soglie.
        
        Args:
            temperature: Temperatura in gradi Celsius
            humidity: Umidità percentuale
            wind_speed: Velocità del vento in km/h
        """
        try:
            alerts = []
            
            if temperature > 35:
                alerts.append("🔥 ALLERTA CALDO: Temperatura molto elevata")
            elif temperature < -10:
                alerts.append("🧊 ALLERTA FREDDO: Temperatura molto bassa")
            
            if humidity > 80:
                alerts.append("💧 ALTA UMIDITÀ: Possibile disagio")
            elif humidity < 20:
                alerts.append("🏜️ BASSA UMIDITÀ: Aria molto secca")
            
            if wind_speed > 60:
                alerts.append("💨 VENTO FORTE: Attenzione alle raffiche")
            
            if not alerts:
                return "✅ Condizioni meteorologiche normali"
            
            return "⚠️ AVVISI METEO:\n" + "\n".join(alerts)
            
        except Exception as e:
            return f"ERRORE: {str(e)}"