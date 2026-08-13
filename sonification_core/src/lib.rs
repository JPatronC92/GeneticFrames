use pyo3::prelude::*;
use hound;
use std::f32::consts::PI;

#[pyfunction]
fn generate_dna_audio(
    dna: &str, 
    output_path: &str, 
    sample_rate: u32, 
    duration_ms: u32
) -> PyResult<()> {
    
    let spec = hound::WavSpec {
        channels: 1,
        sample_rate,
        bits_per_sample: 32,
        sample_format: hound::SampleFormat::Float,
    };
    
    let mut writer = hound::WavWriter::create(output_path, spec)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let frames_per_note = (sample_rate as f32 * (duration_ms as f32 / 1000.0)) as usize;
    let fade_frames = frames_per_note / 10; 

    for base in dna.chars() {
        let freq = match base {
            'A' | 'a' => 261.63,
            'C' | 'c' => 293.66,
            'G' | 'g' => 329.63,
            'T' | 't' | 'U' | 'u' => 392.00,
            _ => 0.0, 
        };

        if freq > 0.0 {
            for t in 0..frames_per_note {
                let time = t as f32 / sample_rate as f32;
                
                // Additive synthesis: Base frequency + 1 harmonic
                let sample_base = (time * freq * 2.0 * PI).sin();
                let sample_harm = (time * freq * 2.0 * 2.0 * PI).sin() * 0.3; // Harmonic
                let sample = (sample_base + sample_harm) * 0.7; // Normalize slightly

                // ADSR-like Envelope
                let mut envelope = 1.0;
                if t < fade_frames {
                    envelope = t as f32 / fade_frames as f32; // Attack
                } else if t > frames_per_note - fade_frames {
                    envelope = (frames_per_note - t) as f32 / fade_frames as f32; // Release
                }

                writer.write_sample(sample * envelope)
                    .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
            }
        } else {
             // Silence for unknown bases
             for _ in 0..frames_per_note {
                writer.write_sample(0.0_f32)
                    .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
             }
        }
    }
    
    writer.finalize().map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
    Ok(())
}

#[pymodule]
fn sonification_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(generate_dna_audio, m)?)?;
    Ok(())
}
