import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import matplotlib.pyplot as plt

# Import custom modules
from src.audio_utils import load_audio, mix_audio, plot_waveform, plot_spectrogram, spectral_subtraction
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
    n_speakers = st.number_input("Number of Speakers", min_value=2, max_value=5, value=2, help="How many voices should the system look to separate and diarize?")
    
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
                data = data.mean(axis=1)  # to mono
            if samplerate != sr:
                data = librosa.resample(data, orig_sr=samplerate, target_sr=sr)
            sources.append(data)
            
    st.success(f"Successfully loaded {len(sources)} sources.")
    
    # Safety Check: FastICA cannot separate more sources than we have microphones (files)
    actual_n_speakers = min(n_speakers, len(sources))
    if actual_n_speakers < n_speakers:
        st.warning(f"⚠️ You requested {n_speakers} speakers, but only uploaded {len(sources)} files. Proceeding with {actual_n_speakers} speakers.")
    
    tab1, tab2, tab3, tab4, tab_denoise, tab5 = st.tabs([
        "🎛️ 1. Mixture",
        "📡 2. Transmission",
        "🛠️ 3. Equalization",
        "✂️ 4. Separation",
        "🔇 5. Denoising",
        "⏱️ 6. Diarization"
    ])
    
    with st.spinner('Running Signal Processing Pipeline...'):
        
        # 1. Mixture
        X_mixed, mixing_matrix = mix_sources_for_ica(sources[:actual_n_speakers])
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
        
        # 4. Separation (MUST happen on linear signals, before non-linear denoising)
        separated_sources_raw = separate_sources_ica(X_eq, n_components=actual_n_speakers)
        
        # 5. Denoising (applied to each separated voice individually)
        separated_sources = []
        for s_raw in separated_sources_raw:
            s_clean = spectral_subtraction(s_raw, n_std_thresh=2.0)
            s_clean = s_clean / (np.max(np.abs(s_clean)) + 1e-10)
            separated_sources.append(s_clean)
            
        # Also denoise the mixed signal for visualization
        norm_denoise = spectral_subtraction(norm_eq, n_std_thresh=2.0)
        norm_denoise = norm_denoise / (np.max(np.abs(norm_denoise)) + 1e-10)
        
        # 6. Diarization
        timeline = diarize_audio(norm_denoise, sr=sr, n_speakers=actual_n_speakers)
        
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
        cols = st.columns(actual_n_speakers)
        for i, s_sep in enumerate(separated_sources):
            with cols[i]:
                st.markdown(f"**Speaker {i+1}**")
                st.audio(s_sep, sample_rate=sr)
                fig_sep = plot_waveform(s_sep, sr=sr, title="")
                st.pyplot(fig_sep)

    with tab_denoise:
        st.subheader("Noise Reduction (Wiener Filter)")
        st.markdown("""
        The Wiener Filter is the **mathematically optimal** linear estimator for recovering a signal from additive noise.
        For each time-frequency bin, it computes a smooth gain between 0 and 1, suppressing noise while preserving the speech.
        
        **Compare the three signals below** to hear how close the denoised version is to the original mixture before transmission!
        """)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**🟢 Original Mixture**")
            st.caption("Before Channel")
            st.audio(norm_mix, sample_rate=sr)
        with col2:
            st.markdown("**🔴 Noisy Received**")
            st.caption("After Channel + AWGN")
            st.audio(norm_rx, sample_rate=sr)
        with col3:
            st.markdown("**🔵 Denoised Recovered**")
            st.caption("After Wiener Filter")
            st.audio(norm_denoise, sample_rate=sr)
        
        st.divider()
        
        # Stacked waveform comparison
        fig, axes = plt.subplots(3, 1, figsize=(10, 5), sharex=True)
        t = np.arange(len(norm_mix)) / sr
        
        axes[0].plot(t, norm_mix, color="#00FF88", linewidth=0.5)
        axes[0].fill_between(t, norm_mix, 0, color="#00FF88", alpha=0.1)
        axes[0].set_title("Original Mixture", fontweight="bold", fontsize=10)
        axes[0].set_ylabel("Amp")
        
        t_rx = np.arange(len(norm_rx)) / sr
        axes[1].plot(t_rx, norm_rx, color="#FF007F", linewidth=0.5)
        axes[1].fill_between(t_rx, norm_rx, 0, color="#FF007F", alpha=0.1)
        axes[1].set_title("Noisy Received", fontweight="bold", fontsize=10)
        axes[1].set_ylabel("Amp")
        
        t_dn = np.arange(len(norm_denoise)) / sr
        axes[2].plot(t_dn, norm_denoise, color="#00E5FF", linewidth=0.5)
        axes[2].fill_between(t_dn, norm_denoise, 0, color="#00E5FF", alpha=0.1)
        axes[2].set_title("Denoised Recovered", fontweight="bold", fontsize=10)
        axes[2].set_ylabel("Amp")
        axes[2].set_xlabel("Time (s)")
        
        for ax in axes:
            ax.grid(True, linestyle=':', alpha=0.4)
        
        plt.tight_layout()
        st.pyplot(fig)

    with tab5:
        st.subheader("Speaker Diarization (Who Spoke When)")
        st.markdown("Clustering the denoised mixture's audio features to map temporal speaker activity.")
        
        # Plot Gantt chart style timeline
        fig, ax = plt.subplots(figsize=(10, 3))
        colors = ['#00E5FF', '#FF007F', '#00FF88', '#B200FF', '#FFD700']
        
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
