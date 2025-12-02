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

def _validate_audio_params(sample_rate: int, duration: float, amplitude: float) -> None:
    """Validate audio parameters and enforce security limits.
    
    Raises:
        ValueError: If any parameter is out of acceptable range
    """
    valid_sample_rates = [8000, 11025, 16000, 22050, 44100, 48000, 96000]
    
    if sample_rate not in valid_sample_rates:
        raise ValueError(
            f"Invalid sample rate: {sample_rate} Hz. "
            f"Must be one of: {', '.join(map(str, valid_sample_rates))} Hz"
        )
    
    if duration > 30.0:
        raise ValueError(
            f"Duration {duration}s exceeds maximum limit of 30.0 seconds. "
            f"Please reduce the duration."
        )
    
    if duration <= 0:
        raise ValueError(
            f"Invalid duration: {duration}s. Duration must be greater than 0."
        )
    
    if amplitude > 1.0:
        raise ValueError(
            f"Amplitude {amplitude} exceeds maximum limit of 1.0. "
            f"Please reduce the amplitude."
        )
    
    if amplitude < 0.0:
        raise ValueError(
            f"Invalid amplitude: {amplitude}. Amplitude must be non-negative."
        )

def _detect_audio_format(data: bytes) -> str:
    """Detect audio format from magic numbers."""
    if len(data) < 12:
        return "Too small"
    
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
        return "Unknown"

def register_tools(mcp):
    """Register audio processing tools with the MCP server instance."""
    logging.info("🎵 Registering tool-set: Audio Processing Tools")

    @mcp.tool()
    def analyze_audio_metadata(audio_base64: str) -> Dict[str, Any]:
        """
        Analyze detailed metadata of an audio file from base64.
        
        Args:
            audio_base64: Audio file encoded in base64
        """
        try:
            # Decode base64
            audio_data = base64.b64decode(audio_base64)
            file_size_kb = len(audio_data) / 1024
            
            # Detect format
            format_detected = _detect_audio_format(audio_data)
            
            result = {
                "format": format_detected,
                "file_size_kb": round(file_size_kb, 2),
                "file_size_mb": round(file_size_kb / 1024, 2),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Detailed WAV analysis
            if format_detected == "WAV":
                try:
                    audio_io = io.BytesIO(audio_data)
                    with wave.open(audio_io, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        sample_width = wav_file.getsampwidth()
                        duration = frames / sample_rate if sample_rate > 0 else 0
                        
                        # Calculate effective bitrate
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
                                "channel_layout": _get_channel_layout(channels)
                            },
                            "file_metrics": {
                                "compression_ratio": "None (uncompressed WAV)",
                                "data_rate_mbps": round((len(audio_data) * 8) / (duration * 1_000_000), 2) if duration > 0 else 0,
                                "samples_per_channel": frames,
                                "total_samples": frames * channels
                            },
                            "quality_assessment": _assess_audio_quality(sample_rate, bits_per_sample, duration)
                        })
                except wave.Error as e:
                    result["error"] = f"WAV reading error: {str(e)}"
            
            else:
                # Generic analysis for other formats
                result.update({
                    "note": "Limited analysis for this format",
                    "recommendation": "Convert to WAV for detailed analysis",
                    "estimated_properties": _estimate_audio_properties(audio_data, format_detected)
                })
            
            return result
            
        except Exception as e:
            logging.error(f"Error in analyze_audio_metadata: {e}")
            return {"success": False, "error": str(e)}

    def _get_channel_layout(channels: int) -> str:
        """Determine the channel layout."""
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

    def _assess_audio_quality(sample_rate: int, bit_depth: int, duration: float) -> Dict[str, str]:
        """Assess audio quality."""
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
            "recommendations": _get_quality_recommendations(sample_rate, bit_depth)
        }

    def _get_quality_recommendations(sample_rate: int, bit_depth: int) -> List[str]:
        """Provide recommendations to improve quality."""
        recommendations = []
        
        if sample_rate < 44100:
            recommendations.append("Consider upsampling to 44.1kHz or higher")
        if bit_depth < 16:
            recommendations.append("Increase bit depth to at least 16-bit")
        if sample_rate == 44100 and bit_depth == 16:
            recommendations.append("CD quality standard - adequate for most uses")
        if sample_rate >= 48000 and bit_depth >= 24:
            recommendations.append("Professional quality - ideal for audio production")
        
        return recommendations

    def _estimate_audio_properties(audio_data: bytes, format_type: str) -> Dict[str, Any]:
        """Estimate audio properties for non-WAV formats."""
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
        Generate advanced waveforms with modulation and fade.
        
        Args:
            waveform_type: Waveform type ('sine', 'square', 'triangle', 'sawtooth', 'noise')
            frequency: Main frequency in Hz
            duration: Duration in seconds
            sample_rate: Sampling rate
            amplitude: Amplitude (0.0-1.0)
            modulation_freq: AM modulation frequency (0 = none)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
        """
        try:
            # Parameter validation - will raise ValueError if params are invalid
            _validate_audio_params(sample_rate, duration, amplitude)
            
            # Additional limits for secondary parameters (these can be clamped)
            frequency = max(20, min(frequency, sample_rate // 2))
            modulation_freq = max(0, min(modulation_freq, 50))
            fade_in = max(0, min(fade_in, duration / 2))
            fade_out = max(0, min(fade_out, duration / 2))
            
            # Generate samples
            num_samples = int(sample_rate * duration)
            samples = []
            
            for i in range(num_samples):
                t = i / sample_rate
                
                # Generate base waveform
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
                
                # Amplitude modulation
                if modulation_freq > 0:
                    modulation = 0.5 * (1 + math.sin(2 * math.pi * modulation_freq * t))
                    sample *= modulation
                
                # Apply fade
                fade_factor = 1.0
                if fade_in > 0 and t < fade_in:
                    fade_factor *= t / fade_in
                if fade_out > 0 and t > (duration - fade_out):
                    fade_factor *= (duration - t) / fade_out
                
                sample *= amplitude * fade_factor
                
                # Convert to 16-bit signed integer
                sample_int = max(-32767, min(32767, int(sample * 32767)))
                samples.append(sample_int)
            
            # Create WAV file
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
                }
            }
            
        except Exception as e:
            logging.error(f"Error in generate_advanced_waveform: {e}")
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
        Adjust volume of a WAV audio file.
        
        Args:
            audio_base64: WAV audio encoded in base64
            volume_factor: Volume factor (0.5 = halve, 2.0 = double, max 5.0)
        """
        try:
            # Validate volume factor
            if volume_factor < 0.0:
                raise ValueError(f"Invalid volume_factor: {volume_factor}. Must be non-negative.")
            if volume_factor > 5.0:
                raise ValueError(
                    f"Volume factor {volume_factor} exceeds maximum limit of 5.0. "
                    f"Please reduce the volume factor."
                )
            
            # Decode base64
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
                    "pitch_classification": _classify_pitch(estimated_pitch) if estimated_pitch > 0 else "Not determined"
                },
                "energy_features": {
                    "total_energy": energy,
                    "average_power": round(avg_power, 2),
                    "peak_to_average_ratio": round(max_amplitude / (rms + 1), 2)
                },
                "audio_classification": {
                    "likely_content": _classify_audio_content(zcr, silence_percentage, estimated_pitch),
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
                
                # Validate time parameters
                if start_time < 0:
                    raise ValueError(f"Invalid start_time: {start_time}. Must be non-negative.")
                if start_time > total_duration:
                    raise ValueError(
                        f"Start time {start_time}s exceeds audio duration of {total_duration}s."
                    )
                if end_time <= start_time:
                    raise ValueError(
                        f"End time {end_time}s must be greater than start time {start_time}s."
                    )
                if end_time > total_duration:
                    raise ValueError(
                        f"End time {end_time}s exceeds audio duration of {total_duration}s."
                    )
                
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
                all_samples = _apply_crossfade(all_samples, file_durations, 
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

    def _apply_crossfade(samples: List[int], durations: List[float], 
                        fade_duration: float, params) -> List[int]:
        """Apply crossfade between audio segments."""
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
                "basic_properties": _extract_basic_features(samples, params),
                "spectral_features": _extract_spectral_features(samples, params.framerate),
                "temporal_features": _extract_temporal_features(samples, params.framerate),
                "perceptual_features": _extract_perceptual_features(samples, params.framerate),
                "quality_metrics": _extract_quality_metrics(samples, params)
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

    def _extract_basic_features(samples: List[int], params) -> Dict[str, Any]:
        """Extract basic audio features."""
        max_amp = max(abs(s) for s in samples) if samples else 0
        rms = math.sqrt(sum(s**2 for s in samples) / len(samples)) if samples else 0
        
        return {
            "max_amplitude": max_amp,
            "rms_amplitude": round(rms, 2),
            "dynamic_range_db": round(20 * math.log10(max_amp / (rms + 1)), 2),
            "peak_to_rms_ratio": round(max_amp / (rms + 1), 2),
            "amplitude_distribution": _analyze_amplitude_distribution(samples)
        }

    def _extract_spectral_features(samples: List[int], sample_rate: int) -> Dict[str, Any]:
        """Extract spectral features."""
        # Analisi spettrale semplificata
        spectral_centroid = _calculate_spectral_centroid(samples, sample_rate)
        dominant_freq = _find_dominant_frequency(samples, sample_rate)
        
        return {
            "spectral_centroid_hz": round(spectral_centroid, 2),
            "dominant_frequency_hz": round(dominant_freq, 2),
            "frequency_classification": _classify_pitch(dominant_freq),
            "bandwidth_estimate": _estimate_bandwidth(samples, sample_rate)
        }

    def _extract_temporal_features(samples: List[int], sample_rate: int) -> Dict[str, Any]:
        """Extract temporal features."""
        zcr = _calculate_zero_crossing_rate(samples)
        onset_times = _detect_onsets(samples, sample_rate)
        
        return {
            "zero_crossing_rate": round(zcr, 4),
            "onset_detection": {
                "onset_times": onset_times[:10],  # Prime 10 per brevità
                "onset_count": len(onset_times),
                "average_onset_interval": round(sum(onset_times[i+1] - onset_times[i] 
                                                  for i in range(len(onset_times)-1)) / max(1, len(onset_times)-1), 2) if len(onset_times) > 1 else 0
            }
        }

    def _extract_perceptual_features(samples: List[int], sample_rate: int) -> Dict[str, Any]:
        """Extract perceptual features."""
        loudness = _calculate_loudness(samples)
        brightness = _calculate_brightness(samples, sample_rate)
        
        return {
            "perceived_loudness": loudness,
            "brightness_metric": brightness,
            "content_classification": _classify_audio_content(
                _calculate_zero_crossing_rate(samples),
                _calculate_silence_percentage(samples),
                _find_dominant_frequency(samples, sample_rate)
            )
        }

    def _extract_quality_metrics(samples: List[int], params) -> Dict[str, Any]:
        """Extract audio quality metrics."""
        snr = _estimate_snr(samples)
        thd = _estimate_thd(samples, params.framerate)
        
        return {
            "estimated_snr_db": round(snr, 2),
            "estimated_thd_percent": round(thd * 100, 2),
            "quality_score": _calculate_quality_score(snr, thd, params),
            "clipping_detection": _detect_clipping(samples)
        }

    # Helper methods for advanced analysis
    def _calculate_spectral_centroid(samples: List[int], sample_rate: int) -> float:
        """Calculate the spectral centroid."""
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

    def _find_dominant_frequency(samples: List[int], sample_rate: int) -> float:
        """Find the dominant frequency via autocorrelation."""
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

    def _calculate_zero_crossing_rate(samples: List[int]) -> float:
        """Calculate the zero crossing rate."""
        if len(samples) < 2:
            return 0
        
        zero_crossings = sum(1 for i in range(1, len(samples)) 
                           if (samples[i] >= 0) != (samples[i-1] >= 0))
        return zero_crossings / len(samples)

    def _calculate_silence_percentage(samples: List[int]) -> float:
        """Calculate the silence percentage."""
        if not samples:
            return 100
        
        max_amp = max(abs(s) for s in samples)
        threshold = max_amp * 0.01  # 1% del massimo
        
        silence_samples = sum(1 for s in samples if abs(s) < threshold)
        return (silence_samples / len(samples)) * 100

    def _analyze_amplitude_distribution(samples: List[int]) -> Dict[str, Any]:
        """Analyze amplitude distribution."""
        if not samples:
            return {}
        
        max_amp = max(abs(s) for s in samples)
        if max_amp == 0:
            return {"uniform": True}
        
        # Create histogram buckets
        buckets = [0] * 10
        for sample in samples:
            bucket_idx = min(9, int(abs(sample) / (max_amp / 10)))
            buckets[bucket_idx] += 1
        
        total = len(samples)
        return {
            "histogram": buckets,
            "percentages": [round(b / total * 100, 2) for b in buckets]
        }

    def _estimate_bandwidth(samples: List[int], sample_rate: int) -> Dict[str, Any]:
        """Estimate frequency bandwidth."""
        # Simplified bandwidth estimation
        return {
            "estimated_bandwidth_hz": sample_rate / 2,  # Nyquist limit
            "method": "theoretical_maximum"
        }

    def _detect_onsets(samples: List[int], sample_rate: int) -> List[float]:
        """Detect onset times in audio."""
        if len(samples) < 100:
            return []
        
        # Simple onset detection based on energy changes
        window_size = sample_rate // 20  # 50ms windows
        onsets = []
        
        prev_energy = 0
        for i in range(0, len(samples) - window_size, window_size):
            window = samples[i:i + window_size]
            energy = sum(s**2 for s in window) / len(window)
            
            # Detect significant energy increase
            if energy > prev_energy * 1.5 and prev_energy > 0:
                onset_time = i / sample_rate
                onsets.append(round(onset_time, 3))
            
            prev_energy = energy
        
        return onsets[:20]  # Limit to first 20 onsets

    def _calculate_loudness(samples: List[int]) -> Dict[str, Any]:
        """Calculate perceived loudness."""
        if not samples:
            return {"loudness_lufs": 0}
        
        rms = math.sqrt(sum(s**2 for s in samples) / len(samples))
        # Simplified loudness estimation (not true LUFS)
        loudness_db = 20 * math.log10(rms + 1) if rms > 0 else -float('inf')
        
        return {
            "loudness_db": round(loudness_db, 2),
            "rms_amplitude": round(rms, 2),
            "loudness_category": "Loud" if loudness_db > 70 else "Medium" if loudness_db > 50 else "Quiet"
        }

    def _calculate_brightness(samples: List[int], sample_rate: int) -> float:
        """Calculate brightness (high frequency content)."""
        # Simplified brightness calculation
        # Higher zero crossing rate indicates more high frequencies
        if len(samples) < 2:
            return 0
        
        zero_crossings = sum(1 for i in range(1, len(samples)) 
                           if (samples[i] >= 0) != (samples[i-1] >= 0))
        zcr = zero_crossings / len(samples)
        
        # Normalize to 0-1 range
        brightness = min(1.0, zcr * 10)
        return round(brightness, 3)

    def _estimate_snr(samples: List[int]) -> float:
        """Estimate signal-to-noise ratio."""
        if not samples:
            return 0
        
        max_amp = max(abs(s) for s in samples)
        
        # Estimate noise floor (bottom 10% of amplitudes)
        sorted_amps = sorted([abs(s) for s in samples])
        noise_floor_idx = len(sorted_amps) // 10
        noise_floor = sorted_amps[noise_floor_idx] if sorted_amps else 1
        
        # Calculate SNR in dB
        snr = 20 * math.log10(max_amp / (noise_floor + 1)) if noise_floor > 0 else 100
        return min(100, max(0, snr))

    def _estimate_thd(samples: List[int], sample_rate: int) -> float:
        """Estimate total harmonic distortion."""
        # Simplified THD estimation
        # In a real implementation, this would analyze harmonic frequencies
        if not samples:
            return 0
        
        # Use zero crossing rate as a proxy for distortion
        zcr = _calculate_zero_crossing_rate(samples)
        
        # Higher ZCR might indicate more distortion
        # This is a very rough approximation
        thd = min(0.5, zcr * 2)
        return round(thd, 4)

    def _calculate_quality_score(snr: float, thd: float, params) -> int:
        """Calculate overall quality score."""
        # Score based on SNR (0-100)
        snr_score = min(100, snr)
        
        # Penalty for THD
        thd_penalty = thd * 100
        
        # Bonus for high sample rate and bit depth
        sr_bonus = 10 if params.framerate >= 44100 else 0
        bd_bonus = 10 if params.sampwidth >= 2 else 0
        
        quality = snr_score - thd_penalty + sr_bonus + bd_bonus
        return int(max(0, min(100, quality)))

    def _detect_clipping(samples: List[int]) -> Dict[str, Any]:
        """Detect clipping in audio."""
        if not samples:
            return {"clipping_detected": False}
        
        max_value = 32767
        min_value = -32768
        
        clipped_samples = sum(1 for s in samples if s >= max_value or s <= min_value)
        clipping_percentage = (clipped_samples / len(samples)) * 100
        
        return {
            "clipping_detected": clipped_samples > 0,
            "clipped_samples": clipped_samples,
            "clipping_percentage": round(clipping_percentage, 2),
            "severity": "High" if clipping_percentage > 5 else "Medium" if clipping_percentage > 1 else "Low" if clipped_samples > 0 else "None"
        }

    # ...existing methods continue with enhanced implementations...
    
    # ...existing code...