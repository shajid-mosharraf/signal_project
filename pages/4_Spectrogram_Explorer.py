import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import librosa.display
import matplotlib.pyplot as plt

# Ensure modern plot styling
plt.style.use("dark_background")
plt.rcParams.update({
    "axes.facecolor": "#0E1117",
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

st.set_page_config(page_title="Spectrogram Explorer", page_icon="🔭", layout="wide")
st.title("🔭 Spectrogram Explorer")
st.markdown("""
Turn a sound clip into a time-frequency image using short overlapping FFT windows (STFT). 
Explore the fundamental **uncertainty principle** of signal processing: you cannot have perfect time resolution and perfect frequency resolution simultaneously!
""")

st.header("1. Upload Audio")
uploaded_file = st.file_uploader("Upload a WAV/MP3 file", type=['wav', 'mp3', 'ogg'])

if uploaded_file is not None:
    sr_target = 16000
    
    with st.spinner("Loading audio..."):
        audio_bytes = uploaded_file.read()
        data, samplerate = sf.read(io.BytesIO(audio_bytes))
        if len(data.shape) > 1:
            data = data.mean(axis=1) # convert to mono
        if samplerate != sr_target:
            data = librosa.resample(data, orig_sr=samplerate, target_sr=sr_target)
            
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))
        
    st.audio(data, sample_rate=sr_target)
    st.divider()
    
    st.header("2. Explore Time-Frequency Trade-offs")
    
    col_ctrl, col_plot = st.columns([1, 2.5])
    
    with col_ctrl:
        st.subheader("FFT Window Parameters")
        
        n_fft = st.select_slider(
            "Window Size (N_FFT)",
            options=[64, 128, 256, 512, 1024, 2048, 4096, 8192],
            value=1024,
            help="Larger windows give better frequency resolution (sharp horizontal lines) but worse time resolution (smudged vertical lines). Smaller windows do the opposite."
        )
        
        hop_length = st.select_slider(
            "Hop Length (Overlap)",
            options=[int(n_fft/8), int(n_fft/4), int(n_fft/2), n_fft],
            value=int(n_fft/4),
            help="How many samples to slide the window forward each step. Smaller hop = smoother image horizontally."
        )
        
        cmap = st.selectbox("Color Map", ["inferno", "magma", "viridis", "plasma", "cividis", "twilight"])
        
        st.markdown("---")
        st.markdown("**Observations:**")
        if n_fft <= 256:
            st.info("🕒 **High Time Resolution:** You can clearly see exactly *when* clicks and percussive sounds happen, but the pitch (frequency) is very blurry and blocky.")
        elif n_fft >= 2048:
            st.info("🎹 **High Frequency Resolution:** You can clearly see individual harmonics and pitches (sharp horizontal lines), but percussive transients are smeared across time.")
        else:
            st.info("⚖️ **Balanced Resolution:** A good compromise between seeing when events happen and what pitches they contain.")

    with col_plot:
        with st.spinner("Computing STFT Spectrogram..."):
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Compute STFT
            D = librosa.stft(data, n_fft=n_fft, hop_length=hop_length)
            D_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
            
            # Plot
            img = librosa.display.specshow(
                D_db, 
                sr=sr_target, 
                hop_length=hop_length, 
                x_axis='time', 
                y_axis='log', 
                ax=ax, 
                cmap=cmap
            )
            
            cbar = fig.colorbar(img, ax=ax, format="%+2.0f dB", pad=0.02)
            cbar.ax.tick_params(colors='#A0A0A0')
            cbar.outline.set_edgecolor('#444444')
            
            ax.set_title(f"Spectrogram (n_fft={n_fft}, hop_length={hop_length})", fontweight="bold", pad=15)
            ax.set_xlabel("Time (s)", fontweight="bold")
            ax.set_ylabel("Frequency (Hz)", fontweight="bold")
            
            plt.tight_layout()
            st.pyplot(fig)

else:
    st.info("Upload an audio file to begin the lab.")

