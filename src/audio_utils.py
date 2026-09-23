import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# Apply a modern dark style globally for all plots
plt.style.use("dark_background")

# Set global matplotlib parameters for beautiful plots
plt.rcParams.update({
    "axes.facecolor": "#0E1117",  # Streamlit dark background color
    "figure.facecolor": "#0E1117",
    "axes.edgecolor": "#444444",
    "grid.color": "#333333",
    "text.color": "#E0E0E0",
    "axes.labelcolor": "#E0E0E0",
    "xtick.color": "#A0A0A0",
    "ytick.color": "#A0A0A0",
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False
})

def load_audio(filepath, sr=16000, mono=True):
    """Loads an audio file and resamples it."""
    try:
        audio, _ = librosa.load(filepath, sr=sr, mono=mono)
        return audio
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

@st.cache_data(show_spinner=False)
def spectral_subtraction(y, n_std_thresh=1.5):
    """
    Removes broadband noise using Spectral Gating/Subtraction.
    Removes broadband noise using a Wiener Filter approach.
    
    The Wiener filter is the mathematically optimal linear filter for
    recovering a signal from additive noise. For each time-frequency bin,
    it computes a gain:
        G(f,t) = max(0, 1 - noise_power / signal_power)
    This is far superior to simple spectral subtraction because it
    smoothly attenuates noisy bins rather than hard-zeroing them,
    which avoids the 'musical noise' artifacts.
    """
    # Compute STFT
    S = librosa.stft(y)
    mag = np.abs(S)
    phase = np.exp(1.j * np.angle(S))
    
    # Estimate noise from the quietest 10% of frames
    frame_energy = np.sum(mag, axis=0)
    noise_frames = np.argsort(frame_energy)[:max(1, int(mag.shape[1] * 0.1))]
    # Estimate noise profile from the quietest 15% of frames
    frame_energy = np.sum(mag ** 2, axis=0)
    n_noise_frames = max(1, int(mag.shape[1] * 0.15))
    noise_frames = np.argsort(frame_energy)[:n_noise_frames]
    
    # Mean and Std of noise magnitude
    noise_mag = np.mean(mag[:, noise_frames], axis=1, keepdims=True)
    noise_std = np.std(mag[:, noise_frames], axis=1, keepdims=True)
    # Noise power spectrum (average power per frequency bin)
    noise_power = np.mean(mag[:, noise_frames] ** 2, axis=1, keepdims=True)
    
    # Threshold for noise
    noise_thresh = noise_mag + (n_std_thresh * noise_std)
    # Apply overestimation factor to be more aggressive
    noise_power = noise_power * n_std_thresh
    
    # Spectral Gating (Subtract noise, floor at 0)
    mag_clean = mag - noise_thresh
    mag_clean[mag_clean < 0] = 0.0
    # Signal power
    signal_power = mag ** 2
    
    # Wiener gain: smoothly scales each bin between 0 and 1
    gain = np.maximum(0, 1.0 - (noise_power / (signal_power + 1e-10)))
    
    # Apply gain to magnitude
    mag_clean = mag * gain
    
    # Reconstruct signal
    S_clean = mag_clean * phase
    y_clean = librosa.istft(S_clean)
    
    # Ensure it matches original length precisely
    if len(y_clean) > len(y):
        y_clean = y_clean[:len(y)]
    else:
        y_clean = np.pad(y_clean, (0, len(y) - len(y_clean)))
        
    return y_clean

def save_audio(filepath, audio, sr=16000):
    """Saves a numpy array as an audio file."""
    sf.write(filepath, audio, sr)

def mix_audio(audio_list):
    """Mixes a list of audio arrays by padding to max length and summing."""
    if not audio_list:
        return np.array([])
    
    max_len = max(len(a) for a in audio_list)
    mixed = np.zeros(max_len)
    
    for a in audio_list:
        padded = np.pad(a, (0, max_len - len(a)), 'constant')
        mixed += padded
        
    # Normalize to avoid clipping
    if np.max(np.abs(mixed)) > 0:
        mixed = mixed / np.max(np.abs(mixed))
    return mixed

def calculate_rms(audio):
    """Calculates the Root Mean Square (RMS) amplitude."""
    return np.sqrt(np.mean(audio**2))

def calculate_energy(audio):
    """Calculates total signal energy."""
    return np.sum(audio**2)

def plot_waveform(audio, sr=16000, title="Waveform", color="#00E5FF"):
    """Returns a matplotlib figure of the waveform."""
    fig, ax = plt.subplots(figsize=(10, 3))
    time = np.arange(len(audio)) / sr
    
    ax.plot(time, audio, color=color, linewidth=1.2, alpha=0.9)
    ax.fill_between(time, audio, 0, color=color, alpha=0.15) # Add a nice glow effect underneath
    
    ax.set_title(title, fontweight="bold", pad=15)
    ax.set_xlabel("Time (s)", fontweight="bold")
    ax.set_ylabel("Amplitude", fontweight="bold")
    ax.grid(True, linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    return fig

def plot_spectrogram(audio, sr=16000, title="Spectrogram"):
    """Returns a matplotlib figure of the spectrogram."""
    fig, ax = plt.subplots(figsize=(10, 3))
    D = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)
    
    # Use 'inferno' or 'magma' for a blazing, attractive look
    img = librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log', ax=ax, cmap='inferno')
    
    cbar = fig.colorbar(img, ax=ax, format="%+2.0f dB", pad=0.02)
    cbar.ax.tick_params(colors='#A0A0A0')
    cbar.outline.set_edgecolor('#444444')
    
    ax.set_title(title, fontweight="bold", pad=15)
    ax.set_xlabel("Time (s)", fontweight="bold")
    ax.set_ylabel("Frequency (Hz)", fontweight="bold")
    
    plt.tight_layout()
    return fig

@st.cache_data(show_spinner=False)
def get_fft(audio, sr=16000):
    """Computes the FFT, returning frequency bins, magnitude, and phase."""
    n = len(audio)
    freqs = np.fft.rfftfreq(n, d=1/sr)
    fft_vals = np.fft.rfft(audio)
    
    magnitude = np.abs(fft_vals)
    magnitude_db = 20 * np.log10(np.clip(magnitude, 1e-10, None))
    
    phase = np.angle(fft_vals)
    return freqs, magnitude_db, phase

import base64
import io
import streamlit.components.v1 as components

def play_audio_with_visualizer(audio, sr=16000):
    """Replaces standard st.audio with a custom JS Audio Visualizer (Bouncing Bars)."""
    # 1. Convert numpy array to WAV bytes in memory
    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format='WAV')
    buffer.seek(0)
    
    # 2. Encode to base64
    audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    audio_src = f"data:audio/wav;base64,{audio_base64}"
    
    # 3. Create the HTML/JS Component
    html_code = f"""
    <div style="background: rgba(0,0,0,0.4); padding: 20px; border-radius: 15px; border: 1px solid rgba(0,229,255,0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
        <audio id="audio-player" controls style="width: 100%; outline: none;">
            <source src="{audio_src}" type="audio/wav">
        </audio>
        <canvas id="visualizer" style="width: 100%; height: 150px; margin-top: 15px; border-radius: 8px; background: rgba(0,0,0,0.6);"></canvas>
    </div>
    
    <script>
        const audio = document.getElementById("audio-player");
        const canvas = document.getElementById("visualizer");
        const ctx = canvas.getContext("2d");
        
        let audioCtx;
        let analyser;
        let source;
        let isInitialized = false;
        
        // Match canvas internal resolution to display size
        function resize() {{
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        }}
        window.addEventListener('resize', resize);
        resize();

        audio.onplay = function() {{
            if (!isInitialized) {{
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioCtx.createAnalyser();
                source = audioCtx.createMediaElementSource(audio);
                source.connect(analyser);
                analyser.connect(audioCtx.destination);
                analyser.fftSize = 256;
                isInitialized = true;
            }}
            
            if (audioCtx.state === 'suspended') {{
                audioCtx.resume();
            }}
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            function draw() {{
                if (audio.paused) return; // Stop drawing when paused
                
                requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);
                
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                const barWidth = (canvas.width / bufferLength) * 2.5;
                let barHeight;
                let x = 0;
                
                for(let i = 0; i < bufferLength; i++) {{
                    barHeight = dataArray[i];
                    
                    // Create Neon Gradient
                    let gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
                    gradient.addColorStop(0, '#00E5FF'); // Cyan
                    gradient.addColorStop(0.5, '#FF007F'); // Pink
                    gradient.addColorStop(1, '#00FF88'); // Green
                    
                    ctx.fillStyle = gradient;
                    
                    // Draw bouncing bar
                    ctx.fillRect(x, canvas.height - barHeight/1.5, barWidth, barHeight/1.5);
                    
                    x += barWidth + 1;
                }}
            }}
            draw();
        }};
    </script>
    """
    components.html(html_code, height=250)

def render_professional_eq(audio, sr=16000):
    """Renders a real-time, professional 10-band Graphic EQ using Web Audio API."""
    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format='WAV')
    buffer.seek(0)
    audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    audio_src = f"data:audio/wav;base64,{audio_base64}"
    
    html_code = f"""
    <div style="background: rgba(15,20,30,0.8); padding: 30px; border-radius: 15px; border: 1px solid rgba(0,229,255,0.4); box-shadow: 0 10px 30px rgba(0,0,0,0.8); color: #fff; font-family: sans-serif;">
        <h3 style="margin-top:0; text-align:center; color: #00E5FF; text-transform: uppercase; letter-spacing: 2px;">Live 10-Band EQ Mixer</h3>
        <audio id="eq-audio" controls style="width: 100%; margin-bottom: 20px; outline: none;">
            <source src="{audio_src}" type="audio/wav">
        </audio>
        
        <div style="display: flex; justify-content: center; gap: 10px; margin-bottom: 20px;">
            <button onclick="setPreset('flat')" style="background: #333; color: white; border: none; padding: 5px 15px; border-radius: 5px; cursor: pointer;">Flat</button>
            <button onclick="setPreset('bass')" style="background: #FF007F; color: white; border: none; padding: 5px 15px; border-radius: 5px; cursor: pointer;">Bass Boost</button>
            <button onclick="setPreset('treble_cut')" style="background: #00E5FF; color: black; border: none; padding: 5px 15px; border-radius: 5px; cursor: pointer;">Treble Cut</button>
            <button onclick="setPreset('vshape')" style="background: #00FF88; color: black; border: none; padding: 5px 15px; border-radius: 5px; cursor: pointer;">V-Shape (Pop)</button>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: flex-end; height: 200px; padding: 20px; background: rgba(0,0,0,0.5); border-radius: 10px;">
            {''.join([f'''
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 8%;">
                <span style="font-size: 12px; margin-bottom: 10px; color: #FF007F;" id="val-{f}">{0}dB</span>
                <input type="range" id="fader-{f}" min="-12" max="12" value="0" step="1" 
                    style="appearance: slider-vertical; width: 20px; height: 120px; cursor: pointer; accent-color: #00E5FF;">
                <span style="font-size: 10px; margin-top: 10px; color: #A0A0A0;">{f}Hz</span>
            </div>
            ''' for f in [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]])}
        </div>
    </div>
    
    <script>
        const audio = document.getElementById("eq-audio");
        let audioCtx;
        let source;
        let filters = [];
        const freqs = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000];
        let isInitialized = false;

        const presets = {{
            'flat': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'bass': [10, 8, 6, 2, 0, 0, 0, 0, 0, 0],
            'treble_cut': [0, 0, 0, 0, 0, -2, -4, -6, -8, -12],
            'vshape': [8, 6, 2, 0, -2, -2, 0, 2, 6, 8]
        }};

        function setPreset(name) {{
            const gains = presets[name];
            freqs.forEach((freq, index) => {{
                const fader = document.getElementById('fader-' + freq);
                const valLabel = document.getElementById('val-' + freq);
                const v = gains[index];
                fader.value = v;
                valLabel.innerText = (v > 0 ? '+' : '') + v + 'dB';
                valLabel.style.color = v == 0 ? '#FF007F' : '#00E5FF';
                
                if(filters[index]) {{
                    filters[index].gain.value = v;
                }}
            }});
        }}

        audio.onplay = function() {{
            if (!isInitialized) {{
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                source = audioCtx.createMediaElementSource(audio);
                
                // Create a chain of 10 Biquad Peaking Filters
                let prevNode = source;
                freqs.forEach((freq, index) => {{
                    let filter = audioCtx.createBiquadFilter();
                    filter.type = "peaking";
                    filter.frequency.value = freq;
                    filter.Q.value = 1.41; // Standard bandwidth for octave EQ
                    filter.gain.value = document.getElementById('fader-' + freq).value;
                    
                    prevNode.connect(filter);
                    prevNode = filter;
                    filters.push(filter);
                    
                    // Add listener to fader to update filter gain in real-time
                    const fader = document.getElementById('fader-' + freq);
                    const valLabel = document.getElementById('val-' + freq);
                    fader.addEventListener('input', function(e) {{
                        const v = e.target.value;
                        filter.gain.value = v;
                        valLabel.innerText = (v > 0 ? '+' : '') + v + 'dB';
                        valLabel.style.color = v == 0 ? '#FF007F' : '#00E5FF';
                    }});
                }});
                
                // Connect the last filter to the speakers
                prevNode.connect(audioCtx.destination);
                isInitialized = true;
            }}
            
            if (audioCtx.state === 'suspended') {{
                audioCtx.resume();
            }}
        }};
    </script>
    """
    components.html(html_code, height=450)

def plot_magnitude_spectrum(freqs, magnitude_db, title="Magnitude Spectrum", color="#FF007F"):
    """Returns a matplotlib figure of the magnitude spectrum."""
    fig, ax = plt.subplots(figsize=(10, 3))
    
    ax.plot(freqs, magnitude_db, color=color, linewidth=1.5, alpha=0.9)
    ax.fill_between(freqs, magnitude_db, np.min(magnitude_db), color=color, alpha=0.15)
    
    ax.set_title(title, fontweight="bold", pad=15)
    ax.set_xlabel("Frequency (Hz)", fontweight="bold")
    ax.set_ylabel("Magnitude (dB)", fontweight="bold")
    ax.grid(True, linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    return fig

def plot_phase_spectrum(freqs, phase, title="Phase Spectrum", color="#B200FF"):
    """Returns a matplotlib figure of the phase spectrum."""
    fig, ax = plt.subplots(figsize=(10, 3))
    
    ax.scatter(freqs, phase, color=color, s=2, alpha=0.5)
    
    ax.set_title(title, fontweight="bold", pad=15)
    ax.set_xlabel("Frequency (Hz)", fontweight="bold")
    ax.set_ylabel("Phase (Radians)", fontweight="bold")
    ax.grid(True, linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    return fig

def get_dominant_frequency(freqs, magnitude):
    """Finds the frequency with the maximum magnitude."""
    idx = np.argmax(magnitude)
    return freqs[idx]
