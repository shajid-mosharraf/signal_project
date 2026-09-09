import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import matplotlib.pyplot as plt

# Import custom modules
from src.audio_utils import load_audio, mix_audio, plot_waveform, plot_spectrogram
from src.channel import apply_channel
from src.transceiver import zero_forcing_equalize
from src.separator import mix_sources_for_ica, separate_sources_ica
from src.diarizer import diarize_audio

st.set_page_config(page_title="Multi-Speaker Comm System", page_icon="🎙️", layout="wide")

st.title("🎙️ Intelligent Multi-Speaker Comm System")
st.markdown("""
Welcome to the **Digital Communication & Signal Reconstruction** playground. 
This dashboard simulates a full pipeline: mixing multiple voices, transmitting them through a noisy multipath channel, and utilizing advanced signal processing (Equalization & Blind Source Separation) to reconstruct and identify the original speakers.
""")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Channel Constraints")
    snr_db = st.slider("Signal-to-Noise Ratio (SNR) in dB", min_value=-10, max_value=50, value=20, step=1, help="Lower SNR means more noise is added during transmission.")
    
    st.markdown("### Multipath Taps")
    tap_input = st.text_input("Taps (comma separated)", "1.0, 0.5", help="Defines the channel impulse response. e.g. '1.0, 0.5' is a direct path plus a delayed echo.")
    try:
        taps = [float(x.strip()) for x in tap_input.split(",")]
    except ValueError:
        st.error("Please enter valid numbers for taps.")
        taps = [1.0]

    st.subheader("System Expectations")
    n_speakers = st.number_input("Number of Speakers", min_value=2, max_value=4, value=2, help="How many voices should the system look to separate and diarize?")
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Adjust SNR and Taps *before* uploading to see their impact on the Equalization and Separation phases.")

# File upload section
st.header("📥 1. Input Sources")
uploaded_files = st.file_uploader("Upload 2 or more separate WAV/MP3 files (one for each speaker)", type=['wav', 'mp3', 'ogg'], accept_multiple_files=True)

if uploaded_files and len(uploaded_files) >= 2:
    sources = []
    sr = 16000
    
    with st.spinner('Loading and standardizing audio files...'):
        for f in uploaded_files:
            audio_bytes = f.read()
            data, samplerate = sf.read(io.BytesIO(audio_bytes))
            if len(data.shape) > 1:
                data = data.mean(axis=1) # to mono
            if samplerate != sr:
                data = librosa.resample(data, orig_sr=samplerate, target_sr=sr)
            sources.append(data)
            
    st.success(f"Successfully loaded {len(sources)} sources.")
    
    # We create tabs to make the UI much cleaner
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎛️ 1. Mixture", 
        "📡 2. Transmission", 
        "🛠️ 3. Equalization", 
        "✂️ 4. Separation", 
        "⏱️ 5. Diarization"
    ])
    
    with st.spinner('Running Signal Processing Pipeline...'):
        
        # 1. Mixture
        X_mixed, mixing_matrix = mix_sources_for_ica(sources[:n_speakers])
        norm_mix = X_mixed[:, 0] / (np.max(np.abs(X_mixed[:, 0])) + 1e-10)
        
        # 2. Transmission
        Y_received = np.zeros_like(X_mixed)
        for c in range(X_mixed.shape[1]):
            Y_received[:, c] = apply_channel(X_mixed[:, c], snr_db, taps)
        norm_rx = Y_received[:, 0] / (np.max(np.abs(Y_received[:, 0])) + 1e-10)
            
        # 3. Equalization
        X_eq = np.zeros_like(Y_received)
        for c in range(Y_received.shape[1]):
            X_eq[:, c] = zero_forcing_equalize(Y_received[:, c], taps)
        norm_eq = X_eq[:, 0] / (np.max(np.abs(X_eq[:, 0])) + 1e-10)
        
        # 4. Separation
        separated_sources = separate_sources_ica(X_eq, n_components=n_speakers)
        
        # 5. Diarization
        timeline = diarize_audio(norm_eq, sr=sr, n_speakers=n_speakers)
        
    # --- Rendering Tabs ---
    
    with tab1:
        st.subheader("Simulated Multi-Microphone Mixture")
        st.markdown("We simulate a scenario where multiple microphones pick up the voices simultaneously.")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Total Duration", f"{len(norm_mix)/sr:.2f}s")
            st.audio(norm_mix, sample_rate=sr)
        with col2:
            fig1 = plot_waveform(norm_mix, sr=sr, title="Transmitted Mixed Signal (Mic 1)")
            st.pyplot(fig1)

    with tab2:
        st.subheader("Channel Impairments (Noise & Multipath)")
        st.markdown(f"The signal travels through a channel adding AWGN (SNR: **{snr_db}dB**) and multipath fading.")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Applied SNR", f"{snr_db} dB")
            st.audio(norm_rx, sample_rate=sr)
        with col2:
            fig2 = plot_waveform(norm_rx, sr=sr, title="Received Degraded Signal")
            st.pyplot(fig2)

    with tab3:
        st.subheader("Zero-Forcing Equalization")
        st.markdown("The receiver attempts to invert the channel effects to remove echoes/multipath.")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.info("Notice how the sharpness of the waveform is recovered compared to the Transmission tab.")
            st.audio(norm_eq, sample_rate=sr)
        with col2:
            fig3 = plot_waveform(norm_eq, sr=sr, title="Equalized Signal")
            st.pyplot(fig3)

    with tab4:
        st.subheader("Blind Source Separation (FastICA)")
        st.markdown("The system separates the linearly mixed, equalized signals back into independent speaker sources.")
        cols = st.columns(n_speakers)
        for i, s_sep in enumerate(separated_sources):
            with cols[i]:
                st.markdown(f"**Speaker {i+1}**")
                st.audio(s_sep, sample_rate=sr)
                fig_sep = plot_waveform(s_sep, sr=sr, title="")
                st.pyplot(fig_sep)

    with tab5:
        st.subheader("Speaker Diarization (Who Spoke When)")
        st.markdown("Clustering the equalized mixture's audio features to map temporal speaker activity.")
        
        # Plot Gantt chart style timeline
        fig, ax = plt.subplots(figsize=(10, 3))
        colors = ['#00E5FF', '#FF007F', '#00FF88', '#B200FF']
        
        # Draw grid
        ax.grid(True, axis='x', linestyle=':', alpha=0.5)
        
        for segment in timeline:
            start, end, label = segment
            spk_idx = int(label.split(" ")[1])
            ax.barh(y=label, width=end-start, left=start, color=colors[spk_idx % len(colors)], edgecolor='black', linewidth=1, height=0.6, alpha=0.9)
            
        ax.set_xlabel("Time (seconds)", fontweight='bold')
        ax.set_title("Diarization Timeline", fontweight='bold')
        # Remove spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        st.pyplot(fig)
        
        with st.expander("View Raw Timeline Data"):
            for start, end, label in timeline:
                st.write(f"**{label}**: {start:.2f}s - {end:.2f}s")

elif uploaded_files and len(uploaded_files) < 2:
    st.warning("⚠️ Please upload at least 2 audio files to simulate multi-speaker communication.")
else:
    st.info("👋 Upload 2 or more audio files above to begin the simulation.")
