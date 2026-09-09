import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import matplotlib.pyplot as plt
from scipy.signal import decimate

# Import plotting styles
from src.audio_utils import plot_waveform, plot_magnitude_spectrum, get_fft

st.set_page_config(page_title="Speed & Pitch Lab", page_icon="🎵", layout="wide")
st.title("🎵 Audio Speed and Pitch Lab")
st.markdown("Explore how changing the sampling rate affects both the speed and pitch of an audio signal, and discover what happens when you downsample without filtering (Aliasing).")

st.header("1. Upload Audio")
uploaded_file = st.file_uploader("Upload a WAV/MP3 file", type=['wav', 'mp3', 'ogg'])

if uploaded_file is not None:
    sr_original = 16000
    
    with st.spinner("Loading audio..."):
        audio_bytes = uploaded_file.read()
        data, samplerate = sf.read(io.BytesIO(audio_bytes))
        if len(data.shape) > 1:
            data = data.mean(axis=1) # convert to mono
        if samplerate != sr_original:
            data = librosa.resample(data, orig_sr=samplerate, target_sr=sr_original)
            
    # Normalize
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))
        
    st.audio(data, sample_rate=sr_original)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("2. Naive Resampling (Speed & Pitch)")
        st.markdown("""
        **Naive Resampling** means we just change the playback speed by pretending the original samples were recorded at a different rate. 
        Because we process the samples faster or slower, the **speed changes**, and simultaneously the **pitch shifts**.
        """)
        
        speed_factor = st.slider("Playback Speed Multiplier", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
        
        new_sr = int(sr_original * speed_factor)
        st.info(f"Original Sample Rate: **{sr_original} Hz** | New Playback Rate: **{new_sr} Hz**")
        
        # We just play the original data at the new sample rate!
        st.markdown("**Naive Resampling (Chipmunk effect):**")
        st.audio(data, sample_rate=new_sr)
        
        st.markdown("""
        **Why does it sound different?**  
        When we speed up playback, we squish the entire waveform. This shifts the speaker's **formants** (the resonant frequencies of their vocal tract) upward, making them sound like a chipmunk!
        
        To speed up audio *without* changing the pitch or the speaker's identity, we must use a **Phase Vocoder**.
        """)
        
        if st.button("Apply Phase Vocoder (Time-Stretch)"):
            with st.spinner("Stretching time..."):
                # Use librosa's phase vocoder to stretch time without changing pitch
                stretched_data = librosa.effects.time_stretch(y=data, rate=speed_factor)
                st.markdown("**Pitch-Preserving Time Stretch (Phase Vocoder):**")
                # We play this back at the ORIGINAL sample rate!
                st.audio(stretched_data, sample_rate=sr_original)
        
    with col2:
        st.header("3. Aliasing Demonstration")
        st.markdown("""
        **Aliasing** happens when we downsample a signal (reduce the sample rate by dropping samples) *without* applying a low-pass filter first. 
        High frequencies fold back into the lower frequencies, creating distorted "ghost" sounds.
        """)
        
        downsample_factor = st.slider("Downsample Factor (Drop every Nth sample)", min_value=1, max_value=10, value=1)
        
        if downsample_factor > 1:
            # Naive downsampling (NO anti-aliasing filter)
            aliased_data = data[::downsample_factor]
            aliased_sr = sr_original // downsample_factor
            
            # Proper downsampling (WITH anti-aliasing filter)
            proper_data = decimate(data, downsample_factor, ftype='iir', zero_phase=True)
            
            st.warning(f"New Sample Rate: **{aliased_sr} Hz**. Notice the high-pitched distortion in the naive version!")
            
            st.markdown("**Naive Downsampling (With Aliasing distortion):**")
            st.audio(aliased_data, sample_rate=aliased_sr)
            
            st.markdown("**Proper Downsampling (Filtered, No Aliasing):**")
            st.audio(proper_data, sample_rate=aliased_sr)
            
            # Show spectra
            with st.expander("View Frequency Spectra Comparison"):
                f_orig, mag_orig, _ = get_fft(data, sr=sr_original)
                f_alias, mag_alias, _ = get_fft(aliased_data, sr=aliased_sr)
                f_prop, mag_prop, _ = get_fft(proper_data, sr=aliased_sr)
                
                fig, ax = plt.subplots(figsize=(8,4))
                ax.plot(f_orig, mag_orig, color="white", alpha=0.3, label="Original")
                ax.plot(f_alias, mag_alias, color="#FF007F", alpha=0.8, label="Aliased (Naive)")
                ax.plot(f_prop, mag_prop, color="#00E5FF", alpha=0.8, linestyle="--", label="Proper (Filtered)")
                ax.set_title("Frequency Spectra", fontweight="bold")
                ax.set_xlabel("Frequency (Hz)", fontweight="bold")
                ax.set_ylabel("Magnitude (dB)", fontweight="bold")
                ax.legend()
                ax.grid(True, linestyle=":", alpha=0.5)
                st.pyplot(fig)
else:
    st.info("Upload an audio file to begin the lab.")

