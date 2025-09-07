# -*- coding: utf-8 -*-
# tools/audio_processing.py
import base64
import io
import logging
import wave
import json
import os
from typing import Dict, List, Optional, Any, Tuple, Union
import struct
import math
import tempfile
from datetime import datetime, timezone

# Utility functions for audio processing
def _classify_pitch(pitch_hz: float) -> str:
    """Classifica il pitch in base alla frequenza."""
    if pitch_hz < 100:
        return "Basso"
    elif pitch_hz < 300:
        return "Medio-basso"
    elif pitch_hz < 600:
        return "Medio"
    elif pitch_hz < 1000:
        return "Medio-alto"
    else:
        return "Alto"

def _classify_audio_content(zcr: float, silence_percentage: float, pitch: Optional[float]) -> str:
    """Classifica il contenuto audio in base alle caratteristiche."""
    if silence_percentage > 80:
        return "Silenzio/Rumore di fondo"
    elif zcr > 0.1:
        return "Rumore/Percussioni"
    elif pitch and 80 < pitch < 1000:
        return "Voce/Strumento melodico"
    elif zcr < 0.05:
        return "Tono puro/Sinusoidale"
    else:
        return "Audio complesso/Musica"

def _validate_audio_params(sample_rate: int, duration: float, amplitude: float) -> Dict[str, Any]:
    """Valida parametri audio e applica limiti di sicurezza."""
    errors = []
    
    if sample_rate not in [8000, 11025, 16000, 22050, 44100, 48000, 96000]:
        sample_rate = 44100
        errors.append("Sample rate corretto a 44100 Hz")
    
    if duration > 30.0:
        duration = 30.0
        errors.append("Durata limitata a 30 secondi")
    elif duration <= 0:
        duration = 1.0
        errors.append("Durata corretta a 1 secondo")
    
    if amplitude > 1.0:
        amplitude = 1.0
        errors.append("Ampiezza limitata a 1.0")
    elif amplitude < 0.0:
        amplitude = 0.1
        errors.append("Ampiezza corretta a 0.1")
    
    return {
        "sample_rate": sample_rate,
        "duration": duration,
        "amplitude": amplitude,
        "warnings": errors
    }

def _detect_audio_format(data: bytes) -> str:
    """Rileva il formato audio dai magic numbers."""
    if len(data) < 12:
        return "Troppo piccolo"
    
    # WAV
    if data[:4] == b'RIFF' and data[8:12] == b'WAVE':
        return "WAV"
    # MP3
    elif data[:3] == b'ID3' or (data[0] == 0xFF and (data[1] & 0xF0) == 0xF0):
        return "MP3"
    # FLAC
    elif data[:4] == b'fLaC':
        return "FLAC"
    # OGG
    elif data[:4] == b'OggS':
        return "OGG/Vorbis"
    # M4A/AAC
    elif data[4:8] == b'ftyp' and (b'M4A ' in data[:20] or b'mp41' in data[:20]):
        return "M4A/AAC"
    # AIFF
    elif data[:4] == b'FORM' and data[8:12] == b'AIFF':
        return "AIFF"
    else:
        return "Sconosciuto"

def register_tools(mcp):
    """Registra i tool di elaborazione audio con l'istanza del server MCP."""
    logging.info("🎵 Registrazione tool-set: Audio Processing Tools")

    @mcp.tool()
    def analyze_audio_metadata(audio_base64: str) -> Dict[str, Any]:
        """
        Analizza metadata dettagliati di un file audio da base64.
        
        Args:
            audio_base64: File audio codificato in base64
        """
        try:
            # Decodifica base64
            audio_data = base64.b64decode(audio_base64)
            file_size_kb = len(audio_data) / 1024
            
            # Rileva formato
            format_detected = _detect_audio_format(audio_data)
            
            result = {
                "format": format_detected,
                "file_size_kb": round(file_size_kb, 2),
                "file_size_mb": round(file_size_kb / 1024, 2),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Analisi WAV dettagliata
            if format_detected == "WAV":
                try:
                    audio_io = io.BytesIO(audio_data)
                    with wave.open(audio_io, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        sample_width = wav_file.getsampwidth()
                        duration = frames / sample_rate if sample_rate > 0 else 0
                        
                        # Calcola bitrate effettivo
                        bits_per_sample = sample_width * 8
                        bitrate_bps = sample_rate * channels * bits_per_sample
                        
                        result.update({
                            "audio_properties": {
                                "duration_seconds": round(duration, 3),
                                "duration_formatted": f"{int(duration//60):02d}:{int(duration%60):02d}",
                                "sample_rate": sample_rate,
                                "channels": channels,
                                "sample_width_bytes": sample_width,
                                "bit_depth": bits_per_sample,
                                "total_frames": frames,
                                "bitrate_kbps": round(bitrate_bps / 1000, 1),
                                "channel_layout": self._get_channel_layout(channels)
                            },
                            "file_metrics": {
                                "compression_ratio": "Nessuna (WAV non compresso)",
                                "data_rate_mbps": round((len(audio_data) * 8) / (duration * 1_000_000), 2) if duration > 0 else 0,
                                "samples_per_channel": frames,
                                "total_samples": frames * channels
                            },
                            "quality_assessment": self._assess_audio_quality(sample_rate, bits_per_sample, duration)
                        })
                except wave.Error as e:
                    result["error"] = f"Errore lettura WAV: {str(e)}"
            
            else:
                # Analisi generica per altri formati
                result.update({
                    "note": "Analisi limitata per questo formato",
                    "recommendation": "Converti in WAV per analisi dettagliata",
                    "estimated_properties": self._estimate_audio_properties(audio_data, format_detected)
                })
            
            return result
            
        except Exception as e:
            logging.error(f"Errore in analyze_audio_metadata: {e}")
            return {"success": False, "error": str(e)}

    def _get_channel_layout(self, channels: int) -> str:
        """Determina il layout dei canali."""
        layouts = {
            1: "Mono",
            2: "Stereo",
            3: "2.1 Surround",
            4: "Quadraphonic",
            5: "5.0 Surround",
            6: "5.1 Surround",
            7: "6.1 Surround",
            8: "7.1 Surround"
        }
        return layouts.get(channels, f"{channels} canali")

    def _assess_audio_quality(self, sample_rate: int, bit_depth: int, duration: float) -> Dict[str, str]:
        """Valuta la qualità audio."""
        quality_score = 0
        
        # Sample rate scoring
        if sample_rate >= 48000:
            quality_score += 3
            sr_quality = "Eccellente"
        elif sample_rate >= 44100:
            quality_score += 2
            sr_quality = "Buona"
        elif sample_rate >= 22050:
            quality_score += 1
            sr_quality = "Accettabile"
        else:
            sr_quality = "Bassa"
        
        # Bit depth scoring
        if bit_depth >= 24:
            quality_score += 3
            bd_quality = "Professionale"
        elif bit_depth >= 16:
            quality_score += 2
            bd_quality = "CD Quality"
        else:
            bd_quality = "Bassa"
        
        # Overall assessment
        if quality_score >= 5:
            overall = "Eccellente (Hi-Fi)"
        elif quality_score >= 4:
            overall = "Buona (Standard)"
        elif quality_score >= 2:
            overall = "Accettabile"
        else:
            overall = "Bassa qualità"
        
        return {
            "overall": overall,
            "sample_rate_quality": sr_quality,
            "bit_depth_quality": bd_quality,
            "recommendations": self._get_quality_recommendations(sample_rate, bit_depth)
        }

    def _get_quality_recommendations(self, sample_rate: int, bit_depth: int) -> List[str]:
        """Fornisce raccomandazioni per migliorare la qualità."""
        recommendations = []
        
        if sample_rate < 44100:
            recommendations.append("Considera upsampling a 44.1kHz o superiore")
        if bit_depth < 16:
            recommendations.append("Aumenta la profondità di bit ad almeno 16-bit")
        if sample_rate == 44100 and bit_depth == 16:
            recommendations.append("Qualità CD standard - adeguata per la maggior parte degli usi")
        if sample_rate >= 48000 and bit_depth >= 24:
            recommendations.append("Qualità professionale - ideale per produzione audio")
        
        return recommendations

    def _estimate_audio_properties(self, audio_data: bytes, format_type: str) -> Dict[str, Any]:
        """Stima proprietà audio per formati non WAV."""
        estimates = {"method": "heuristic_estimation"}
        
        # Stime basate su dimensioni tipiche per formato
        if format_type == "MP3":
            # MP3 tipicamente 128-320 kbps
            estimated_bitrate = 128  # kbps conservative estimate
            estimated_duration = (len(audio_data) * 8) / (estimated_bitrate * 1000)
            estimates.update({
                "estimated_duration_seconds": round(estimated_duration, 1),
                "estimated_bitrate_kbps": estimated_bitrate,
                "compression": "Lossy (MP3)"
            })
        elif format_type == "FLAC":
            estimates.update({
                "compression": "Lossless",
                "typical_compression_ratio": "50-60%"
            })
        
        return estimates

    @mcp.tool()
    def generate_advanced_waveform(waveform_type: str, frequency: float, duration: float, 
                                 sample_rate: int = 44100, amplitude: float = 0.5,
                                 modulation_freq: float = 0, fade_in: float = 0, 
                                 fade_out: float = 0) -> Dict[str, Any]:
        """
        Genera forme d'onda avanzate con modulazione e fade.
        
        Args:
            waveform_type: Tipo di onda ('sine', 'square', 'triangle', 'sawtooth', 'noise')
            frequency: Frequenza principale in Hz
            duration: Durata in secondi
            sample_rate: Frequenza di campionamento
            amplitude: Ampiezza (0.0-1.0)
            modulation_freq: Frequenza di modulazione AM (0 = nessuna)
            fade_in: Durata fade in in secondi
            fade_out: Durata fade out in secondi
        """
        try:
            # Validazione parametri
            validation = _validate_audio_params(sample_rate, duration, amplitude)
            sample_rate = validation["sample_rate"]
            duration = validation["duration"]
            amplitude = validation["amplitude"]
            
            # Limiti aggiuntivi
            frequency = max(20, min(frequency, sample_rate // 2))
            modulation_freq = max(0, min(modulation_freq, 50))
            fade_in = max(0, min(fade_in, duration / 2))
            fade_out = max(0, min(fade_out, duration / 2))
            
            # Genera campioni
            num_samples = int(sample_rate * duration)
            samples = []
            
            for i in range(num_samples):
                t = i / sample_rate
                
                # Genera forma d'onda base
                if waveform_type == "sine":
                    sample = math.sin(2 * math.pi * frequency * t)
                elif waveform_type == "square":
                    sample = 1 if math.sin(2 * math.pi * frequency * t) >= 0 else -1
                elif waveform_type == "triangle":
                    phase = (frequency * t) % 1
                    sample = 4 * abs(phase - 0.5) - 1
                elif waveform_type == "sawtooth":
                    phase = (frequency * t) % 1
                    sample = 2 * phase - 1
                elif waveform_type == "noise":
                    import random
                    sample = random.uniform(-1, 1)
                else:
                    sample = math.sin(2 * math.pi * frequency * t)  # Default to sine
                
                # Modulazione di ampiezza
                if modulation_freq > 0:
                    modulation = 0.5 * (1 + math.sin(2 * math.pi * modulation_freq * t))
                    sample *= modulation
                
                # Applicazione fade
                fade_factor = 1.0
                if fade_in > 0 and t < fade_in:
                    fade_factor *= t / fade_in
                if fade_out > 0 and t > (duration - fade_out):
                    fade_factor *= (duration - t) / fade_out
                
                sample *= amplitude * fade_factor
                
                # Converte a 16-bit signed integer
                sample_int = max(-32767, min(32767, int(sample * 32767)))
                samples.append(sample_int)
            
            # Crea file WAV
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                for sample in samples:
                    wav_file.writeframes(struct.pack('<h', sample))
            
            audio_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "audio_base64": audio_base64,
                "generation_parameters": {
                    "waveform_type": waveform_type,
                    "frequency_hz": frequency,
                    "duration_seconds": duration,
                    "sample_rate": sample_rate,
                    "amplitude": amplitude,
                    "modulation_frequency_hz": modulation_freq,
                    "fade_in_seconds": fade_in,
                    "fade_out_seconds": fade_out
                },
                "audio_properties": {
                    "samples_generated": num_samples,
                    "file_size_kb": round(len(output_buffer.getvalue()) / 1024, 2),
                    "bit_depth": 16,
                    "channels": 1
                },
                "validation_warnings": validation.get("warnings", [])
            }
            
        except Exception as e:
            logging.error(f"Errore in generate_advanced_waveform: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def analyze_audio_spectrum(audio_base64: str, fft_size: int = 1024) -> Dict[str, Any]:
        """
        Analizza spettro di frequenza di un audio WAV.
        
        Args:
            audio_base64: Audio WAV codificato in base64
            fft_size: Dimensione FFT (default: 1024)
        """
        try:
            import cmath
            
            # Decodifica base64
            audio_data = base64.b64decode(audio_base64)
            audio_io = io.BytesIO(audio_data)
            
            # Leggi WAV
            with wave.open(audio_io, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                raw_audio = wav_file.readframes(frames)
            
            # Converte byte a campioni
            if wav_file.getsampwidth() == 2:  # 16-bit
                samples = struct.unpack(f'<{frames * channels}h', raw_audio)
            else:
                return {"success": False, "error": "Solo audio 16-bit supportato"}
            
            # Usa solo il primo canale se stereo
            if channels > 1:
                samples = samples[::channels]
            
            # Limita numero di campioni per performance
            max_samples = min(len(samples), fft_size * 10)
            samples = samples[:max_samples]
            
            # FFT semplice (implementazione base)
            def simple_fft(x):
                N = len(x)
                if N <= 1:
                    return x
                
                # Per semplicità, usiamo solo potenze di 2
                if N & (N-1) != 0:
                    # Riempi con zeri fino alla prossima potenza di 2
                    next_pow2 = 1 << (N - 1).bit_length()
                    x = x + [0] * (next_pow2 - N)
                    N = next_pow2
                
                # Ricorsione semplificata per piccole dimensioni
                if N <= 64:  # Limite per evitare troppa ricorsione
                    result = []
                    for k in range(N):
                        sum_val = 0
                        for n in range(N):
                            angle = -2 * cmath.pi * k * n / N
                            sum_val += x[n] * cmath.exp(1j * angle)
                        result.append(sum_val)
                    return result
                else:
                    return x  # Fallback per dimensioni grandi
            
            # Analizza in finestre
            window_size = min(fft_size, len(samples))
            window_data = samples[:window_size]
            
            # Applica finestra di Hanning semplificata
            for i in range(len(window_data)):
                hanning = 0.5 * (1 - math.cos(2 * math.pi * i / (len(window_data) - 1)))
                window_data[i] *= hanning
            
            # Esegui FFT
            fft_result = simple_fft(window_data)
            
            # Calcola magnitudini
            magnitudes = [abs(x) for x in fft_result[:len(fft_result)//2]]
            
            # Trova frequenze dominanti
            max_magnitude = max(magnitudes) if magnitudes else 0
            dominant_frequencies = []
            
            for i, magnitude in enumerate(magnitudes):
                if magnitude > max_magnitude * 0.1:  # Solo componenti significative
                    freq = i * sample_rate / len(window_data)
                    if freq < sample_rate / 2:  # Nyquist limit
                        dominant_frequencies.append({
                            "frequency_hz": round(freq, 2),
                            "magnitude": round(magnitude, 2),
                            "relative_strength": round(magnitude / max_magnitude, 3)
                        })
            
            # Ordina per magnitude
            dominant_frequencies.sort(key=lambda x: x['magnitude'], reverse=True)
            
            # Analisi delle frequenze
            def classify_frequency(freq):
                if freq < 60:
                    return "Sub-bass"
                elif freq < 250:
                    return "Bass"
                elif freq < 500:
                    return "Low midrange"
                elif freq < 2000:
                    return "Midrange"
                elif freq < 4000:
                    return "Upper midrange"
                elif freq < 6000:
                    return "Presence"
                else:
                    return "Brilliance"
            
            frequency_bands = {}
            for freq_info in dominant_frequencies[:10]:
                band = classify_frequency(freq_info["frequency_hz"])
                if band not in frequency_bands:
                    frequency_bands[band] = []
                frequency_bands[band].append(freq_info)
            
            return {
                "spectrum_analysis": {
                    "dominant_frequencies": dominant_frequencies[:10],
                    "frequency_bands": frequency_bands,
                    "analysis_window_size": window_size,
                    "sample_rate": sample_rate,
                    "frequency_resolution": round(sample_rate / window_size, 2)
                },
                "audio_properties": {
                    "total_samples_analyzed": len(samples),
                    "channels": channels,
                    "duration_analyzed": round(len(samples) / sample_rate, 2)
                }
            }
            
        except wave.Error:
            return {
                "success": False,
                "error": "Formato audio non supportato - utilizzare WAV"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def adjust_audio_volume(audio_base64: str, volume_factor: float) -> Dict[str, Any]:
        """
        Modifica volume di un file audio WAV.
        
        Args:
            audio_base64: Audio WAV codificato in base64
            volume_factor: Fattore di volume (0.5 = dimezza, 2.0 = raddoppia)
        """
        try:
            # Limiti di sicurezza
            volume_factor = max(0.0, min(volume_factor, 5.0))  # 0x - 5x volume
            
            # Decodifica base64
            audio_data = base64.b64decode(audio_base64)
            audio_io = io.BytesIO(audio_data)
            
            # Leggi WAV
            with wave.open(audio_io, 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.getnframes()
                raw_audio = wav_file.readframes(frames)
            
            # Converte byte a campioni
            if params.sampwidth == 2:  # 16-bit
                samples = list(struct.unpack(f'<{frames * params.nchannels}h', raw_audio))
            else:
                return {"success": False, "error": "Solo audio 16-bit supportato"}
            
            # Applica fattore volume
            max_value = 32767
            min_value = -32768
            clipped_samples = 0
            
            for i in range(len(samples)):
                samples[i] = int(samples[i] * volume_factor)
                
                # Clipping protection
                if samples[i] > max_value:
                    samples[i] = max_value
                    clipped_samples += 1
                elif samples[i] < min_value:
                    samples[i] = min_value
                    clipped_samples += 1
            
            # Crea nuovo file WAV
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setparams(params)
                
                # Converti campioni a bytes
                audio_bytes = struct.pack(f'<{len(samples)}h', *samples)
                wav_file.writeframes(audio_bytes)
            
            # Converti a base64
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            clipping_percentage = (clipped_samples / len(samples)) * 100
            
            return {
                "audio_base64": output_base64,
                "volume_adjustment": {
                    "original_volume_factor": 1.0,
                    "new_volume_factor": volume_factor,
                    "volume_change_db": round(20 * math.log10(volume_factor), 2) if volume_factor > 0 else -float('inf'),
                    "clipped_samples": clipped_samples,
                    "clipping_percentage": round(clipping_percentage, 2)
                },
                "audio_properties": {
                    "sample_rate": params.framerate,
                    "channels": params.nchannels,
                    "duration_seconds": round(frames / params.framerate, 2),
                    "bit_depth": params.sampwidth * 8
                },
                "quality_warning": "Clipping detected - audio quality may be degraded" if clipping_percentage > 1 else None
            }
            
        except wave.Error:
            return {
                "success": False,
                "error": "Formato audio non supportato - utilizzare WAV"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def convert_audio_format(audio_base64: str, target_format: str, quality: int = 192) -> Dict[str, Any]:
        """
        Converte formato audio (limitato a operazioni base su WAV).
        
        Args:
            audio_base64: Audio codificato in base64
            target_format: Formato target (solo 'wav' supportato nativamente)
            quality: Qualità di conversione (non utilizzata per WAV)
        """
        try:
            # Per questa implementazione base, supportiamo solo operazioni WAV
            target_format = target_format.lower()
            
            if target_format != 'wav':
                return {
                    "success": False,
                    "error": "Solo conversioni WAV supportate in questa versione. Per altri formati servono librerie aggiuntive (ffmpeg, pydub)",
                    "supported_formats": ["wav"]
                }
            
            # Decodifica base64
            audio_data = base64.b64decode(audio_base64)
            original_size_kb = len(audio_data) / 1024
            
            # Verifica che sia WAV valido
            audio_io = io.BytesIO(audio_data)
            with wave.open(audio_io, 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.getnframes()
            
            # Per WAV, restituiamo il file originale
            return {
                "converted_audio_base64": audio_base64,
                "conversion_info": {
                    "source_format": "WAV",
                    "target_format": "WAV",
                    "original_size_kb": round(original_size_kb, 2),
                    "converted_size_kb": round(original_size_kb, 2),
                    "compression_ratio": 0,
                    "quality_setting": quality
                },
                "audio_properties": {
                    "sample_rate": params.framerate,
                    "channels": params.nchannels,
                    "bit_depth": params.sampwidth * 8,
                    "duration_seconds": round(frames / params.framerate, 2)
                },
                "note": "File WAV mantenuto nel formato originale"
            }
            
        except wave.Error:
            return {
                "success": False,
                "error": "File audio non valido o formato non supportato"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def extract_audio_features(audio_base64: str) -> Dict[str, Any]:
        """
        Estrae caratteristiche audio da un file WAV.
        
        Args:
            audio_base64: Audio WAV codificato in base64
        """
        try:
            # Decodifica base64
            audio_data = base64.b64decode(audio_base64)
            audio_io = io.BytesIO(audio_data)
            
            # Leggi WAV
            with wave.open(audio_io, 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.getnframes()
                raw_audio = wav_file.readframes(frames)
            
            # Converte byte a campioni
            if params.sampwidth == 2:  # 16-bit
                samples = struct.unpack(f'<{frames * params.nchannels}h', raw_audio)
            else:
                return {"success": False, "error": "Solo audio 16-bit supportato"}
            
            # Usa solo primo canale se stereo
            if params.nchannels > 1:
                samples = samples[::params.nchannels]
            
            # Calcola caratteristiche temporali
            duration = frames / params.framerate
            max_amplitude = max(abs(s) for s in samples) if samples else 0
            rms = math.sqrt(sum(s**2 for s in samples) / len(samples)) if samples else 0
            
            # Zero crossing rate (indica periodicità/rumore)
            zero_crossings = sum(1 for i in range(1, len(samples)) 
                               if (samples[i] >= 0) != (samples[i-1] >= 0))
            zcr = zero_crossings / len(samples) if samples else 0
            
            # Energy e power
            energy = sum(s**2 for s in samples)
            avg_power = energy / len(samples) if samples else 0
            
            # Analisi distribuzione ampiezze
            amplitude_histogram = {}
            for sample in samples[::100]:  # Campiona per performance
                bucket = int(abs(sample) // 3277)  # 10% buckets
                amplitude_histogram[bucket] = amplitude_histogram.get(bucket, 0) + 1
            
            # Calcola statistiche temporali
            silence_threshold = max_amplitude * 0.01  # 1% del massimo
            silence_samples = sum(1 for s in samples if abs(s) < silence_threshold)
            silence_percentage = (silence_samples / len(samples)) * 100 if samples else 0
            
            # Stima pitch dominante (metodo autocorrelazione semplificato)
            def estimate_pitch(samples, sample_rate, min_freq=50, max_freq=800):
                # Limita campioni per performance
                samples = samples[:sample_rate]  # Max 1 secondo
                
                max_correlation = 0
                best_period = 0
                
                min_period = int(sample_rate / max_freq)
                max_period = int(sample_rate / min_freq)
                
                for period in range(min_period, min(max_period, len(samples)//2)):
                    correlation = sum(samples[i] * samples[i + period] 
                                   for i in range(len(samples) - period))
                    
                    if correlation > max_correlation:
                        max_correlation = correlation
                        best_period = period
                
                return sample_rate / best_period if best_period > 0 else 0
            
            estimated_pitch = estimate_pitch(list(samples), params.framerate)
            
            return {
                "temporal_features": {
                    "duration_seconds": round(duration, 2),
                    "max_amplitude": max_amplitude,
                    "rms_amplitude": round(rms, 2),
                    "dynamic_range": round(max_amplitude / (rms + 1), 2),
                    "zero_crossing_rate": round(zcr, 4),
                    "silence_percentage": round(silence_percentage, 2)
                },
                "spectral_features": {
                    "estimated_pitch_hz": round(estimated_pitch, 2) if estimated_pitch > 0 else None,
                    "pitch_classification": self._classify_pitch(estimated_pitch) if estimated_pitch > 0 else "Non determinato"
                },
                "energy_features": {
                    "total_energy": energy,
                    "average_power": round(avg_power, 2),
                    "peak_to_average_ratio": round(max_amplitude / (rms + 1), 2)
                },
                "audio_classification": {
                    "likely_content": self._classify_audio_content(zcr, silence_percentage, estimated_pitch),
                    "audio_quality": "Alta" if max_amplitude > 20000 and silence_percentage < 50 else "Media"
                },
                "technical_info": {
                    "sample_rate": params.framerate,
                    "channels": params.nchannels,
                    "bit_depth": params.sampwidth * 8,
                    "total_samples": len(samples)
                }
            }
            
        except wave.Error:
            return {
                "success": False,
                "error": "Formato audio non supportato - utilizzare WAV"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    def trim_audio(audio_base64: str, start_time: float, end_time: float) -> Dict[str, Any]:
        """
        Taglia un segmento da un file audio WAV.
        
        Args:
            audio_base64: Audio WAV codificato in base64
            start_time: Tempo di inizio in secondi
            end_time: Tempo di fine in secondi
        """
        try:
            audio_data = base64.b64decode(audio_base64)
            audio_io = io.BytesIO(audio_data)
            
            with wave.open(audio_io, 'rb') as wav_file:
                params = wav_file.getparams()
                total_frames = wav_file.getnframes()
                total_duration = total_frames / params.framerate
                
                # Validazione tempi
                start_time = max(0, min(start_time, total_duration))
                end_time = max(start_time + 0.1, min(end_time, total_duration))
                
                # Calcola frame di inizio e fine
                start_frame = int(start_time * params.framerate)
                end_frame = int(end_time * params.framerate)
                
                # Leggi solo la porzione necessaria
                wav_file.setpos(start_frame)
                frames_to_read = end_frame - start_frame
                raw_audio = wav_file.readframes(frames_to_read)
            
            # Crea nuovo file WAV
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setparams(params)
                wav_file.writeframes(raw_audio)
            
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "trimmed_audio_base64": output_base64,
                "trim_info": {
                    "original_duration": round(total_duration, 2),
                    "start_time": start_time,
                    "end_time": end_time,
                    "trimmed_duration": round(end_time - start_time, 2),
                    "frames_extracted": frames_to_read,
                    "size_reduction_percent": round((1 - len(output_buffer.getvalue()) / len(audio_data)) * 100, 1)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def concatenate_audio(audio_files_base64: List[str], crossfade_duration: float = 0) -> Dict[str, Any]:
        """
        Concatena multipli file audio WAV.
        
        Args:
            audio_files_base64: Lista di file audio WAV in base64
            crossfade_duration: Durata crossfade tra file in secondi
        """
        try:
            if not audio_files_base64:
                return {"success": False, "error": "Nessun file audio fornito"}
            
            if len(audio_files_base64) > 10:
                return {"success": False, "error": "Massimo 10 file supportati"}
            
            all_samples = []
            common_params = None
            file_durations = []
            
            # Processa ogni file
            for i, audio_base64 in enumerate(audio_files_base64):
                audio_data = base64.b64decode(audio_base64)
                audio_io = io.BytesIO(audio_data)
                
                with wave.open(audio_io, 'rb') as wav_file:
                    params = wav_file.getparams()
                    
                    # Verifica compatibilità parametri
                    if common_params is None:
                        common_params = params
                    elif (params.framerate != common_params.framerate or 
                          params.nchannels != common_params.nchannels or
                          params.sampwidth != common_params.sampwidth):
                        return {
                            "success": False, 
                            "error": f"File {i+1} ha parametri incompatibili con il primo file"
                        }
                    
                    # Leggi campioni
                    raw_audio = wav_file.readframes(wav_file.getnframes())
                    if params.sampwidth == 2:
                        samples = struct.unpack(f'<{len(raw_audio)//2}h', raw_audio)
                        all_samples.extend(samples)
                        file_durations.append(len(samples) / params.nchannels / params.framerate)
                    else:
                        return {"success": False, "error": "Solo audio 16-bit supportato"}
            
            # Applica crossfade se richiesto
            if crossfade_duration > 0 and len(audio_files_base64) > 1:
                all_samples = self._apply_crossfade(all_samples, file_durations, 
                                                  crossfade_duration, common_params)
            
            # Crea file concatenato
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setparams(common_params)
                audio_bytes = struct.pack(f'<{len(all_samples)}h', *all_samples)
                wav_file.writeframes(audio_bytes)
            
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            total_duration = len(all_samples) / common_params.nchannels / common_params.framerate
            
            return {
                "concatenated_audio_base64": output_base64,
                "concatenation_info": {
                    "input_files_count": len(audio_files_base64),
                    "individual_durations": [round(d, 2) for d in file_durations],
                    "total_duration": round(total_duration, 2),
                    "crossfade_applied": crossfade_duration > 0,
                    "crossfade_duration": crossfade_duration,
                    "final_file_size_kb": round(len(output_buffer.getvalue()) / 1024, 2)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _apply_crossfade(self, samples: List[int], durations: List[float], 
                        fade_duration: float, params) -> List[int]:
        """Applica crossfade tra segmenti audio."""
        # Implementazione semplificata del crossfade
        fade_samples = int(fade_duration * params.framerate * params.nchannels)
        
        # Per semplicità, applichiamo solo fade out/in sui bordi
        result_samples = list(samples)
        
        # Calcola posizioni dei file
        current_pos = 0
        for i, duration in enumerate(durations[:-1]):  # Tutti tranne l'ultimo
            file_samples = int(duration * params.framerate * params.nchannels)
            
            # Fade out del file corrente
            fade_start = current_pos + file_samples - fade_samples
            for j in range(fade_samples):
                if fade_start + j < len(result_samples):
                    fade_factor = 1.0 - (j / fade_samples)
                    result_samples[fade_start + j] = int(result_samples[fade_start + j] * fade_factor)
            
            current_pos += file_samples
        
        return result_samples

    @mcp.tool()
    def detect_audio_features_advanced(audio_base64: str) -> Dict[str, Any]:
        """
        Rilevamento avanzato di caratteristiche audio con analisi dettagliata.
        
        Args:
            audio_base64: Audio WAV codificato in base64
        """
        try:
            audio_data = base64.b64decode(audio_base64)
            audio_io = io.BytesIO(audio_data)
            
            with wave.open(audio_io, 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.getnframes()
                raw_audio = wav_file.readframes(frames)
            
            if params.sampwidth != 2:
                return {"success": False, "error": "Solo audio 16-bit supportato"}
            
            samples = struct.unpack(f'<{frames * params.nchannels}h', raw_audio)
            
            # Usa solo primo canale se stereo
            if params.nchannels > 1:
                samples = samples[::params.nchannels]
            
            duration = frames / params.framerate
            
            # Analisi avanzata delle caratteristiche
            features = {
                "basic_properties": self._extract_basic_features(samples, params),
                "spectral_features": self._extract_spectral_features(samples, params.framerate),
                "temporal_features": self._extract_temporal_features(samples, params.framerate),
                "perceptual_features": self._extract_perceptual_features(samples, params.framerate),
                "quality_metrics": self._extract_quality_metrics(samples, params)
            }
            
            return {
                "audio_features": features,
                "analysis_metadata": {
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "samples_analyzed": len(samples),
                    "analysis_duration_seconds": round(duration, 2),
                    "sample_rate": params.framerate
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_basic_features(self, samples: List[int], params) -> Dict[str, Any]:
        """Estrae caratteristiche audio di base."""
        max_amp = max(abs(s) for s in samples) if samples else 0
        rms = math.sqrt(sum(s**2 for s in samples) / len(samples)) if samples else 0
        
        return {
            "max_amplitude": max_amp,
            "rms_amplitude": round(rms, 2),
            "dynamic_range_db": round(20 * math.log10(max_amp / (rms + 1)), 2),
            "peak_to_rms_ratio": round(max_amp / (rms + 1), 2),
            "amplitude_distribution": self._analyze_amplitude_distribution(samples)
        }

    def _extract_spectral_features(self, samples: List[int], sample_rate: int) -> Dict[str, Any]:
        """Estrae caratteristiche spettrali."""
        # Analisi spettrale semplificata
        spectral_centroid = self._calculate_spectral_centroid(samples, sample_rate)
        dominant_freq = self._find_dominant_frequency(samples, sample_rate)
        
        return {
            "spectral_centroid_hz": round(spectral_centroid, 2),
            "dominant_frequency_hz": round(dominant_freq, 2),
            "frequency_classification": _classify_pitch(dominant_freq),
            "bandwidth_estimate": self._estimate_bandwidth(samples, sample_rate)
        }

    def _extract_temporal_features(self, samples: List[int], sample_rate: int) -> Dict[str, Any]:
        """Estrae caratteristiche temporali."""
        zcr = self._calculate_zero_crossing_rate(samples)
        onset_times = self._detect_onsets(samples, sample_rate)
        
        return {
            "zero_crossing_rate": round(zcr, 4),
            "onset_detection": {
                "onset_times": onset_times[:10],  # Prime 10 per brevità
                "onset_count": len(onset_times),
                "average_onset_interval": round(sum(onset_times[i+1] - onset_times[i] 
                                                  for i in range(len(onset_times)-1)) / max(1, len(onset_times)-1), 2) if len(onset_times) > 1 else 0
            }
        }

    def _extract_perceptual_features(self, samples: List[int], sample_rate: int) -> Dict[str, Any]:
        """Estrae caratteristiche percettive."""
        loudness = self._calculate_loudness(samples)
        brightness = self._calculate_brightness(samples, sample_rate)
        
        return {
            "perceived_loudness": loudness,
            "brightness_metric": brightness,
            "content_classification": _classify_audio_content(
                self._calculate_zero_crossing_rate(samples),
                self._calculate_silence_percentage(samples),
                self._find_dominant_frequency(samples, sample_rate)
            )
        }

    def _extract_quality_metrics(self, samples: List[int], params) -> Dict[str, Any]:
        """Estrae metriche di qualità audio."""
        snr = self._estimate_snr(samples)
        thd = self._estimate_thd(samples, params.framerate)
        
        return {
            "estimated_snr_db": round(snr, 2),
            "estimated_thd_percent": round(thd * 100, 2),
            "quality_score": self._calculate_quality_score(snr, thd, params),
            "clipping_detection": self._detect_clipping(samples)
        }

    # Helper methods for advanced analysis
    def _calculate_spectral_centroid(self, samples: List[int], sample_rate: int) -> float:
        """Calcola il centroide spettrale."""
        # Implementazione semplificata
        freqs = []
        mags = []
        
        # FFT semplificata per frequenze principali
        for i in range(1, min(100, len(samples)//2)):
            freq = i * sample_rate / len(samples)
            if freq < sample_rate / 2:
                mag = abs(sum(samples[j] * math.cos(2 * math.pi * i * j / len(samples)) 
                            for j in range(0, len(samples), len(samples)//100)))
                freqs.append(freq)
                mags.append(mag)
        
        if not mags:
            return 0
        
        weighted_sum = sum(f * m for f, m in zip(freqs, mags))
        magnitude_sum = sum(mags)
        
        return weighted_sum / magnitude_sum if magnitude_sum > 0 else 0

    def _find_dominant_frequency(self, samples: List[int], sample_rate: int) -> float:
        """Trova la frequenza dominante tramite autocorrelazione."""
        if len(samples) < 100:
            return 0
        
        # Autocorrelazione semplificata
        max_correlation = 0
        best_period = 0
        
        min_period = sample_rate // 800  # Max 800 Hz
        max_period = sample_rate // 50   # Min 50 Hz
        
        test_samples = samples[:min(sample_rate, len(samples))]
        
        for period in range(min_period, min(max_period, len(test_samples)//2)):
            correlation = sum(test_samples[i] * test_samples[i + period] 
                            for i in range(len(test_samples) - period))
            
            if correlation > max_correlation:
                max_correlation = correlation
                best_period = period
        
        return sample_rate / best_period if best_period > 0 else 0

    def _calculate_zero_crossing_rate(self, samples: List[int]) -> float:
        """Calcola il tasso di attraversamento dello zero."""
        if len(samples) < 2:
            return 0
        
        zero_crossings = sum(1 for i in range(1, len(samples)) 
                           if (samples[i] >= 0) != (samples[i-1] >= 0))
        return zero_crossings / len(samples)

    def _calculate_silence_percentage(self, samples: List[int]) -> float:
        """Calcola la percentuale di silenzio."""
        if not samples:
            return 100
        
        max_amp = max(abs(s) for s in samples)
        threshold = max_amp * 0.01  # 1% del massimo
        
        silence_samples = sum(1 for s in samples if abs(s) < threshold)
        return (silence_samples / len(samples)) * 100

    # ...existing methods continue with enhanced implementations...
    
    # ...existing code...