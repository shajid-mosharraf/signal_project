import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import librosa.display
import matplotlib.pyplot as plt
from scipy.signal import decimate, convolve

from src.audio_utils import (
    calculate_rms, calculate_energy, plot_waveform, plot_spectrogram, 
    get_fft, plot_magnitude_spectrum, plot_phase_spectrum, get_dominant_frequency,
    play_audio_with_visualizer
)
from src.channel import add_awgn, add_multipath, add_delay, add_attenuation, add_interference
from src.filters import apply_filter
from src.equalizers import zero_forcing_equalize, mmse_equalize, lms_equalize
from src.theme import apply_custom_theme

st.set_page_config(page_title="Master Audio Lab", page_icon="🎛️", layout="wide")
apply_custom_theme()

st.title("🎛️ Master Audio Lab (Analysis & Editing)")
st.markdown("A unified workspace for Time/Frequency Analysis, DSP Filtering, and Non-Linear Audio Editing.")

if 'editor_audio' not in st.session_state:
    st.session_state.editor_audio = None
if 'editor_sr' not in st.session_state:
    st.session_state.editor_sr = 16000

def load_file(file_obj, target_sr=16000):
    audio_bytes = file_obj.read()
    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    if len(data.shape) > 1:
        data = data.mean(axis=1) # to mono
    if samplerate != target_sr:
        data = librosa.resample(data, orig_sr=samplerate, target_sr=target_sr)
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))
    return data, target_sr

st.header("1. Global Audio Workspace")
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Upload base WAV/MP3 file", type=['wav', 'mp3', 'ogg'])
    
with col2:
    if uploaded_file is not None:
        if st.button("Load / Reset Audio", use_container_width=True):
            with st.spinner("Loading..."):
                data, sr = load_file(uploaded_file)
                st.session_state.editor_audio = data.copy()
                st.session_state.editor_sr = sr
                st.rerun()

if st.session_state.editor_audio is not None:
    data = st.session_state.editor_audio
    sr = st.session_state.editor_sr
    duration = len(data) / sr
    
    st.metric("Current Duration", f"{duration:.2f} s")
    play_audio_with_visualizer(data, sr)
    
    st.divider()
    
    main_tab_analysis, main_tab_edit = st.tabs(["🔍 Signal Analysis Lab", "✂️ Audio Editor Lab"])
    
    # ==========================================
    # MAIN TAB 1: SIGNAL ANALYSIS LAB
    # ==========================================
    with main_tab_analysis:
        st.header("Signal & Spectrogram Analysis")
        tab_time, tab_freq, tab_spec, tab_filter, tab_channel, tab_eq = st.tabs([
            "⏱️ Time Domain", "📻 Frequency Domain", "🔭 Spectrogram", "🎛️ Digital Filters", "📡 Channel Sim", "🛠️ Comm EQ"
        ])
        
        with tab_time:
            st.subheader("Time-Domain Analysis")
            c1, c2, c3 = st.columns(3)
            c1.metric("Duration", f"{duration:.2f} s")
            c2.metric("RMS Amplitude", f"{calculate_rms(data):.4f}")
            c3.metric("Total Energy", f"{calculate_energy(data):.2f}")
            st.pyplot(plot_waveform(data, sr=sr, title="Current Audio Waveform"))
            
        with tab_freq:
            st.subheader("Frequency-Domain Analysis")
            with st.spinner("Computing FFT..."):
                freqs, mag_db, phase = get_fft(data, sr)
                dom_freq = get_dominant_frequency(freqs, mag_db)
            st.metric("Dominant Frequency", f"{dom_freq:.2f} Hz")
            c1, c2 = st.columns(2)
            with c1: st.pyplot(plot_magnitude_spectrum(freqs, mag_db))
            with c2: st.pyplot(plot_phase_spectrum(freqs, phase))
                
        with tab_spec:
            st.subheader("Time-Frequency Trade-offs (Spectrogram)")
            col_ctrl, col_plot = st.columns([1, 2.5])
            with col_ctrl:
                n_fft = st.select_slider("Window Size (N_FFT)", options=[64, 128, 256, 512, 1024, 2048, 4096, 8192], value=1024)
                hop_length = st.select_slider("Hop Length (Overlap)", options=[int(n_fft/8), int(n_fft/4), int(n_fft/2), n_fft], value=int(n_fft/4))
                cmap = st.selectbox("Color Map", ["inferno", "magma", "viridis", "plasma"])
            with col_plot:
                with st.spinner("Computing STFT Spectrogram..."):
                    @st.cache_data(show_spinner=False)
                    def compute_stft(audio_data, n_fft, hop_length):
                        D = librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length)
                        return librosa.amplitude_to_db(np.abs(D), ref=np.max)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    D_db = compute_stft(data, n_fft, hop_length)
                    img = librosa.display.specshow(D_db, sr=sr, hop_length=hop_length, x_axis='time', y_axis='log', ax=ax, cmap=cmap)
                    fig.colorbar(img, ax=ax, format="%+2.0f dB", pad=0.02)
                    ax.set_title(f"Spectrogram (n_fft={n_fft})", fontweight="bold", pad=15)
                    st.pyplot(fig)
                    
        with tab_filter:
            st.subheader("FIR/IIR Filtering")
            f_type = st.selectbox("Filter Type", ["lowpass", "highpass", "bandpass", "bandstop"])
            f_order = st.slider("Filter Order", min_value=1, max_value=10, value=5)
            if f_type in ["lowpass", "highpass"]:
                cutoff = st.slider("Cutoff Frequency (Hz)", min_value=20, max_value=int(sr/2)-1, value=1000)
                f_kwargs = {'cutoff': cutoff}
            else:
                c1, c2 = st.columns(2)
                low_cut = c1.slider("Lower Cutoff (Hz)", min_value=20, max_value=int(sr/2)-100, value=500)
                high_cut = c2.slider("Upper Cutoff (Hz)", min_value=low_cut+10, max_value=int(sr/2)-1, value=2000)
                f_kwargs = {'cutoff': (low_cut, high_cut)}
                
            if st.button("Apply Filter to Workspace"):
                with st.spinner("Filtering..."):
                    @st.cache_data(show_spinner=False)
                    def compute_filter(audio_data, f_type, f_order, **kwargs):
                        return apply_filter(audio_data, sr=sr, filter_type=f_type, order=f_order, **kwargs)
                    st.session_state.editor_audio = compute_filter(data, f_type, f_order, **f_kwargs)
                    st.rerun()
                    
        with tab_channel:
            st.subheader("Communication Channel Simulation")
            c_awgn = st.checkbox("Add AWGN Noise", value=True)
            snr_ch = st.slider("SNR (dB)", -10, 50, 20) if c_awgn else None
            c_multipath = st.checkbox("Add Multipath / ISI", value=True)
            taps_input = st.text_input("Multipath Taps", "1.0, 0.6, 0.3") if c_multipath else None
            
            if st.button("Simulate Channel"):
                ch_data = data.copy()
                if c_multipath: 
                    taps = [float(x.strip()) for x in taps_input.split(',')]
                    ch_data = add_multipath(ch_data, taps)
                if c_awgn: ch_data = add_awgn(ch_data, snr_ch)
                st.session_state['ch_taps'] = taps if c_multipath else [1.0]
                st.session_state['ch_snr'] = snr_ch if c_awgn else 50
                st.session_state.editor_audio = ch_data
                st.rerun()
                
        with tab_eq:
            st.subheader("Channel Equalization & Recovery")
            if 'ch_taps' not in st.session_state:
                st.warning("Please run the Channel Simulation in the previous tab first to set the taps.")
            else:
                taps = st.session_state['ch_taps']
                snr = st.session_state['ch_snr']
                eq_type = st.radio("Select Equalizer Type", ["Zero-Forcing (ZF)", "MMSE"])
                if st.button("Equalize Signal"):
                    with st.spinner("Running Equalizer..."):
                        if eq_type == "Zero-Forcing (ZF)":
                            eq_data = zero_forcing_equalize(data, taps)
                        elif eq_type == "MMSE":
                            eq_data = mmse_equalize(data, taps, snr)
                    st.session_state.editor_audio = eq_data
                    st.rerun()

    # ==========================================
    # MAIN TAB 2: AUDIO EDITOR LAB
    # ==========================================
    with main_tab_edit:
        st.header("Audio Editing & Pitch Manipulation")
        t_trim, t_rev, t_scale, t_conv, t_pitch, t_eq_graphic, t_alias = st.tabs([
            "✂️ Trim", "🔄 Reverse", "🔊 Scale", "🎛️ Echo", "🎵 Speed & Pitch", "🎚️ Graphic EQ", "📉 Aliasing Demo"
        ])
        
        with t_trim:
            st.subheader("Trim Audio")
            trim_range = st.slider("Select time range to keep (seconds)", 0.0, duration, (0.0, duration), step=0.1, key="trim_slider")
            if st.button("Apply Trim"):
                start_sample = int(trim_range[0] * sr)
                end_sample = int(trim_range[1] * sr)
                st.session_state.editor_audio = data[start_sample:end_sample]
                st.rerun()
                
        with t_rev:
            st.subheader("Reverse Audio")
            if st.button("Apply Reverse"):
                st.session_state.editor_audio = data[::-1]
                st.rerun()
                
        with t_scale:
            st.subheader("Scale Volume")
            gain = st.slider("Volume Multiplier", 0.0, 3.0, 1.0, step=0.1)
            if st.button("Apply Scaling"):
                st.session_state.editor_audio = data * gain
                st.rerun()
                
        with t_conv:
            st.subheader("Convolution-Based Echo")
            echo_delay = st.slider("Echo Delay (ms)", 50, 1000, 300, step=50)
            echo_decay = st.slider("Echo Decay", 0.1, 0.9, 0.5)
            num_echoes = st.slider("Number of Echoes", 1, 5, 2)
            if st.button("Apply Convolution Echo"):
                with st.spinner("Convolving..."):
                    delay_samples = int((echo_delay / 1000.0) * sr)
                    ir_length = (delay_samples * num_echoes) + 1
                    impulse_response = np.zeros(ir_length)
                    impulse_response[0] = 1.0
                    for i in range(1, num_echoes + 1):
                        impulse_response[i * delay_samples] = echo_decay ** i
                    convolved_data = convolve(data, impulse_response, mode='full')
                    if np.max(np.abs(convolved_data)) > 0:
                        convolved_data = convolved_data / np.max(np.abs(convolved_data))
                    st.session_state.editor_audio = convolved_data
                    st.rerun()
                    
        with t_pitch:
            st.subheader("Speed & Pitch (Resampling vs Phase Vocoder)")
            speed_factor = st.slider("Playback Speed Multiplier", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
            new_sr = int(sr * speed_factor)
            st.info(f"Original Sample Rate: **{sr} Hz** | New Playback Rate: **{new_sr} Hz**")
            if st.button("Apply Naive Resampling (Chipmunk Effect)"):
                st.session_state.editor_sr = new_sr
                st.rerun()
            if st.button("Apply Phase Vocoder (Time-Stretch without pitch change)"):
                with st.spinner("Stretching time..."):
                    @st.cache_data(show_spinner=False)
                    def compute_stretch(audio_data, rate):
                        return librosa.effects.time_stretch(y=audio_data, rate=rate)
                    st.session_state.editor_audio = compute_stretch(data, speed_factor)
                    st.rerun()

        with t_eq_graphic:
            st.subheader("Professional Live Graphic Equalizer")
            st.markdown("Unlike the old Streamlit sliders, this is a **Real-Time Javascript Audio Mixer**. Hit play, then drag the faders up and down to instantly hear the bass boost or treble cut without waiting for the server to reload!")
            
            from src.audio_utils import render_professional_eq
            render_professional_eq(data, sr)
                    
        with t_alias:
            st.subheader("Aliasing Demonstration (Downsampling)")
            downsample_factor = st.slider("Downsample Factor (Drop every Nth sample)", min_value=1, max_value=10, value=1)
            if downsample_factor > 1:
                aliased_sr = sr // downsample_factor
                st.warning(f"New Sample Rate: **{aliased_sr} Hz**. Notice the high-pitched distortion in the naive version!")
                if st.button("Apply Naive Downsampling (With Aliasing distortion)"):
                    st.session_state.editor_audio = data[::downsample_factor]
                    st.session_state.editor_sr = aliased_sr
                    st.rerun()
                if st.button("Apply Proper Downsampling (Filtered, No Aliasing)"):
                    st.session_state.editor_audio = decimate(data, downsample_factor, ftype='iir', zero_phase=True)
                    st.session_state.editor_sr = aliased_sr
                    st.rerun()

else:
    st.info("Upload an audio file to begin the Master Audio Lab.")

