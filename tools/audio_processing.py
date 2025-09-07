# -*- coding: utf-8 -*-
# tools/audio_processing.py
import base64
import io
import logging
import wave
import json
from typing import Dict, List, Optional, Any, Tuple
import struct
import math

def register_tools(mcp):
    """Registra i tool di elaborazione audio con l'istanza del server MCP."""
    logging.info("🎵 Registrazione tool-set: Audio Processing Tools")

    @mcp.tool()
    def analyze_audio_metadata(audio_base64: str) -> Dict[str, Any]:
        """
        Analizza metadata di un file audio da base64.
        
        Args:
            audio_base64: File audio codificato in base64
        """
        try:
            # Decodifica base64
            audio_data = base64.b64decode(audio_base64)
            
            # Prova a leggere come WAV
            try:
                audio_io = io.BytesIO(audio_data)
                with wave.open(audio_io, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    duration = frames / sample_rate if sample_rate > 0 else 0
                    
                    return {
                        "format": "WAV",
                        "duration_seconds": round(duration, 2),
                        "sample_rate": sample_rate,
                        "channels": channels,
                        "sample_width_bytes": sample_width,
                        "bit_depth": sample_width * 8,
                        "total_frames": frames,
                        "file_size_kb": round(len(audio_data) / 1024, 2),
                        "bitrate_kbps": round((len(audio_data) * 8) / (duration * 1000), 2) if duration > 0 else 0,
                        "channel_layout": "Mono" if channels == 1 else "Stereo" if channels == 2 else f"{channels} channels"
                    }
            except wave.Error:
                pass
            
            # Analisi generica per altri formati
            file_size_kb = len(audio_data) / 1024
            
            # Prova a riconoscere formato dai primi bytes (magic numbers)
            format_detected = "Sconosciuto"
            if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
                format_detected = "WAV"
            elif audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
                format_detected = "MP3"
            elif audio_data[:4] == b'fLaC':
                format_detected = "FLAC"
            elif audio_data[:4] == b'OggS':
                format_detected = "OGG"
            
            return {
                "format": format_detected,
                "file_size_kb": round(file_size_kb, 2),
                "analysis_method": "basic_header_analysis",
                "note": "Analisi limitata - per analisi completa usare formati WAV non compressi"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_sine_wave(frequency: float, duration: float, sample_rate: int = 44100, amplitude: float = 0.5) -> Dict[str, Any]:
        """
        Genera un'onda sinusoidale.
        
        Args:
            frequency: Frequenza in Hz
            duration: Durata in secondi
            sample_rate: Frequenza di campionamento (default: 44100)
            amplitude: Ampiezza (0.0-1.0, default: 0.5)
        """
        try:
            import math
            
            # Limiti di sicurezza
            duration = min(duration, 10.0)  # Max 10 secondi
            frequency = max(20, min(frequency, 20000))  # 20Hz - 20kHz
            amplitude = max(0.0, min(amplitude, 1.0))  # 0-100%
            
            # Genera campioni
            num_samples = int(sample_rate * duration)
            samples = []
            
            for i in range(num_samples):
                t = i / sample_rate
                sample = amplitude * math.sin(2 * math.pi * frequency * t)
                # Converte a 16-bit signed integer
                sample_int = int(sample * 32767)
                samples.append(sample_int)
            
            # Crea file WAV
            output_buffer = io.BytesIO()
            with wave.open(output_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Converti campioni a bytes
                for sample in samples:
                    wav_file.writeframes(struct.pack('<h', sample))
            
            # Converti a base64
            audio_base64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            return {
                "audio_base64": audio_base64,
                "properties": {
                    "frequency_hz": frequency,
                    "duration_seconds": duration,
                    "sample_rate": sample_rate,
                    "amplitude": amplitude,
                    "samples_generated": num_samples,
                    "file_size_kb": round(len(output_buffer.getvalue()) / 1024, 2)
                },
                "format": "WAV",
                "channels": 1,
                "bit_depth": 16
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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
    
    # Funzioni di supporto (definite nel contesto del registro)
    def _classify_pitch(self, pitch_hz):
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
    
    def _classify_audio_content(self, zcr, silence_percentage, pitch):
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