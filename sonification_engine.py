import numpy as np
from scipy.io import wavfile
import os

def generate_tone(frequency, duration, sample_rate=44100):
    """Genera un tono sinusoidal con envolvente suave."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Envolvente (fade in/out) de 10ms para evitar 'clicks'
    envelope = np.ones_like(t)
    fade_len = int(sample_rate * 0.01)
    if fade_len > 0 and len(t) > 2 * fade_len:
        envelope[:fade_len] = np.linspace(0, 1, fade_len)
        envelope[-fade_len:] = np.linspace(1, 0, fade_len)
        
    return wave * envelope

def dna_to_audio(sequence, filepath, duration_per_base=0.15, sample_rate=44100):
    """
    Traduce una secuencia de ADN a un archivo de audio WAV.
    Utiliza una escala pentatónica mayor para un sonido armónico.
    A -> Do (C4)
    C -> Re (D4)
    G -> Mi (E4)
    T -> Sol (G4)
    """
    freqs = {
        'A': 261.63, # C4
        'C': 293.66, # D4
        'G': 329.63, # E4
        'T': 392.00, # G4
        'U': 392.00  # Tratado como T
    }
    
    sequence = sequence.upper().replace(' ', '')
    audio_data = []
    
    for base in sequence:
        freq = freqs.get(base, 0) # Silencio si no es ACGT
        if freq > 0:
            tone = generate_tone(freq, duration_per_base, sample_rate)
        else:
            tone = np.zeros(int(sample_rate * duration_per_base))
        audio_data.append(tone)
        
    if audio_data:
        final_wave = np.concatenate(audio_data)
        # Normalizar a 16-bit PCM
        max_amp = np.max(np.abs(final_wave))
        if max_amp > 0:
            final_wave = final_wave / max_amp
        final_wave_int16 = np.int16(final_wave * 32767)
        wavfile.write(filepath, sample_rate, final_wave_int16)
        return True
    return False

if __name__ == "__main__":
    # Prueba del prototipo
    sample_dna = "ATGCGTACGTAGCTAGCTAGCTGATCGATCGTAGCTAGCTAGCTGA"
    output_path = "sample_sonification.wav"
    print(f"Generando audio para {len(sample_dna)} pares de bases...")
    success = dna_to_audio(sample_dna, output_path)
    if success:
        print(f"Audio generado exitosamente en: {output_path}")
    else:
        print("Error al generar audio.")
