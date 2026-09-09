import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import matplotlib.pyplot as plt

from src.audio_utils import (
    calculate_rms, calculate_energy, plot_waveform, plot_spectrogram, 
    get_fft, plot_magnitude_spectrum, plot_phase_spectrum, get_dominant_frequency
)
from src.channel import add_awgn, add_multipath, add_delay, add_attenuation, add_interference
from src.filters import apply_filter
from src.equalizers import zero_forcing_equalize, mmse_equalize, lms_equalize

st.set_page_config(page_title="Digital Signal Analysis", page_icon="📈", layout="wide")

st.title("📈 Digital Signal Analysis Toolkit")
st.markdown("A comprehensive tool for Time & Frequency Domain Analysis, Digital Filtering, Channel Simulation, and Signal Recovery of audio signals.")

# 1. File Upload
st.header("1. Upload Audio Signal")
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
            
    # Normalize
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))
        
    st.success("Audio loaded successfully.")
    st.audio(data, sample_rate=sr_target)
    
    # Create Tabs
    tab_time, tab_freq, tab_filter, tab_channel, tab_eq = st.tabs([
        "⏱️ Time Domain", 
        "📻 Frequency Domain", 
        "🎛️ Digital Filtering", 
        "📡 Channel Simulation", 
        "🛠️ Equalization"
    ])
    
    # ------------------
    # TAB 1: Time Domain
    # ------------------
    with tab_time:
        st.subheader("Time-Domain Analysis")
        col1, col2, col3 = st.columns(3)
        
        duration = len(data) / sr_target
        rms = calculate_rms(data)
        energy = calculate_energy(data)
        
        col1.metric("Duration", f"{duration:.2f} s")
        col2.metric("RMS Amplitude", f"{rms:.4f}")
        col3.metric("Total Energy", f"{energy:.2f}")
        
        st.pyplot(plot_waveform(data, sr=sr_target, title="Original Audio Waveform"))
        
    # ------------------
    # TAB 2: Frequency Domain
    # ------------------
    with tab_freq:
        st.subheader("Frequency-Domain Analysis")
        with st.spinner("Computing FFT and Spectrogram..."):
            freqs, mag_db, phase = get_fft(data, sr=sr_target)
            dom_freq = get_dominant_frequency(freqs, mag_db)
            
        st.metric("Dominant Frequency", f"{dom_freq:.2f} Hz")
        
        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(plot_magnitude_spectrum(freqs, mag_db))
        with col2:
            st.pyplot(plot_phase_spectrum(freqs, phase))
            
        st.subheader("Spectrogram (STFT)")
        st.pyplot(plot_spectrogram(data, sr=sr_target))
        
    # ------------------
    # TAB 3: Digital Filtering
    # ------------------
    with tab_filter:
        st.subheader("FIR/IIR Filtering")
        st.markdown("Apply low-pass, high-pass, band-pass, or notch filters to the signal.")
        
        f_type = st.selectbox("Filter Type", ["lowpass", "highpass", "bandpass", "bandstop"])
        f_order = st.slider("Filter Order", min_value=1, max_value=10, value=5)
        
        if f_type in ["lowpass", "highpass"]:
            cutoff = st.slider("Cutoff Frequency (Hz)", min_value=20, max_value=int(sr_target/2)-1, value=1000)
            f_kwargs = {'cutoff': cutoff}
        else:
            c1, c2 = st.columns(2)
            low_cut = c1.slider("Lower Cutoff (Hz)", min_value=20, max_value=int(sr_target/2)-100, value=500)
            high_cut = c2.slider("Upper Cutoff (Hz)", min_value=low_cut+10, max_value=int(sr_target/2)-1, value=2000)
            f_kwargs = {'cutoff': (low_cut, high_cut)}
            
        if st.button("Apply Filter"):
            with st.spinner("Filtering..."):
                filtered_data = apply_filter(data, sr=sr_target, filter_type=f_type, order=f_order, **f_kwargs)
            st.audio(filtered_data, sample_rate=sr_target)
            st.pyplot(plot_waveform(filtered_data, sr=sr_target, title=f"Filtered Waveform ({f_type})"))
            
            # Show freq domain of filtered
            f_freqs, f_mag_db, _ = get_fft(filtered_data, sr=sr_target)
            st.pyplot(plot_magnitude_spectrum(f_freqs, f_mag_db, title="Filtered Magnitude Spectrum"))

    # ------------------
    # TAB 4: Channel Simulation
    # ------------------
    with tab_channel:
        st.subheader("Communication Channel Simulation")
        st.markdown("Simulate how a transmission channel degrades the signal.")
        
        c_awgn = st.checkbox("Add AWGN Noise", value=True)
        snr_ch = st.slider("SNR (dB)", -10, 50, 20) if c_awgn else None
        
        c_multipath = st.checkbox("Add Multipath / ISI", value=True)
        taps_input = st.text_input("Multipath Taps", "1.0, 0.6, 0.3") if c_multipath else None
        
        c_delay = st.checkbox("Add Signal Delay")
        delay_ms = st.slider("Delay (ms)", 1, 500, 50) if c_delay else None
        
        c_atten = st.checkbox("Add Attenuation")
        atten_db = st.slider("Attenuation (dB)", 1, 40, 10) if c_atten else None
        
        c_interf = st.checkbox("Add Tone Interference")
        i_freq = st.number_input("Interference Freq (Hz)", 50, 8000, 1000) if c_interf else None
        i_snr = st.slider("Interference SNR (dB)", -20, 20, 0) if c_interf else None

        if st.button("Simulate Channel"):
            ch_data = data.copy()
            if c_atten: ch_data = add_attenuation(ch_data, atten_db)
            if c_delay: ch_data = add_delay(ch_data, int((delay_ms/1000)*sr_target))
            if c_multipath: 
                taps = [float(x.strip()) for x in taps_input.split(',')]
                ch_data = add_multipath(ch_data, taps)
            if c_interf: ch_data = add_interference(ch_data, sr_target, i_freq, i_snr)
            if c_awgn: ch_data = add_awgn(ch_data, snr_ch)
            
            # Store in session state so Equalization tab can use it
            st.session_state['ch_data'] = ch_data
            if c_multipath: st.session_state['ch_taps'] = taps
            else: st.session_state['ch_taps'] = [1.0]
            if c_awgn: st.session_state['ch_snr'] = snr_ch
            else: st.session_state['ch_snr'] = 50 # High SNR assumption
            
            st.success("Channel simulation applied!")
            st.audio(ch_data, sample_rate=sr_target)
            st.pyplot(plot_waveform(ch_data, sr=sr_target, title="Degraded Signal"))

    # ------------------
    # TAB 5: Equalization
    # ------------------
    with tab_eq:
        st.subheader("Channel Equalization & Recovery")
        
        if 'ch_data' not in st.session_state:
            st.warning("Please run the Channel Simulation in the previous tab first to generate a degraded signal.")
        else:
            ch_data = st.session_state['ch_data']
            taps = st.session_state['ch_taps']
            snr = st.session_state['ch_snr']
            
            eq_type = st.radio("Select Equalizer Type", ["Zero-Forcing (ZF)", "MMSE", "LMS Adaptive"])
            
            if st.button("Equalize Signal"):
                with st.spinner("Running Equalizer..."):
                    if eq_type == "Zero-Forcing (ZF)":
                        eq_data = zero_forcing_equalize(ch_data, taps)
                    elif eq_type == "MMSE":
                        eq_data = mmse_equalize(ch_data, taps, snr)
                    else:
                        # LMS
                        ref_signal = data.copy() # In reality, we only have a short pilot. We use the original as perfect pilot for demo.
                        eq_data, mse = lms_equalize(ch_data, ref_signal, filter_length=len(taps)*2, mu=0.005)
                        
                        st.write("LMS Learning Curve (Mean Square Error)")
                        fig, ax = plt.subplots(figsize=(6,2))
                        ax.plot(mse[:5000], color="#00FF88", linewidth=1.2)
                        ax.fill_between(range(len(mse[:5000])), mse[:5000], 0, color="#00FF88", alpha=0.15)
                        ax.set_ylabel("MSE", fontweight="bold")
                        ax.set_xlabel("Iterations", fontweight="bold")
                        ax.grid(True, linestyle=':', alpha=0.5)
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                st.audio(eq_data, sample_rate=sr_target)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.pyplot(plot_waveform(ch_data, sr=sr_target, title="Before Equalization"))
                with col2:
                    st.pyplot(plot_waveform(eq_data, sr=sr_target, title="After Equalization"))

else:
    st.info("Upload an audio file to begin analysis.")

