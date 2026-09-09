import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt

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

def get_fft(audio, sr=16000):
    """Computes the FFT, returning frequency bins, magnitude, and phase."""
    n = len(audio)
    freqs = np.fft.rfftfreq(n, d=1/sr)
    fft_vals = np.fft.rfft(audio)
    
    magnitude = np.abs(fft_vals)
    magnitude_db = 20 * np.log10(np.clip(magnitude, 1e-10, None))
    
    phase = np.angle(fft_vals)
    return freqs, magnitude_db, phase

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
