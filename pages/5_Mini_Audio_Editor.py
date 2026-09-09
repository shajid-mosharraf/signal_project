import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import matplotlib.pyplot as plt
from scipy.signal import convolve

from src.audio_utils import plot_waveform

st.set_page_config(page_title="Mini Audio Editor", page_icon="✂️", layout="wide")

# Styling to match the rest of the app
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

st.title("✂️ Mini Audio Editor")
st.markdown("A simple non-linear audio editor to trim, reverse, scale, fade, join, and apply convolution-based effects.")

# Initialize Session State for audio
if 'editor_audio' not in st.session_state:
    st.session_state.editor_audio = None
if 'editor_sr' not in st.session_state:
    st.session_state.editor_sr = 16000
if 'original_audio' not in st.session_state:
    st.session_state.original_audio = None

def load_file(file_obj, target_sr=16000):
    audio_bytes = file_obj.read()
    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    if len(data.shape) > 1:
        data = data.mean(axis=1) # to mono
    if samplerate != target_sr:
        data = librosa.resample(data, orig_sr=samplerate, target_sr=target_sr)
    return data, target_sr

st.header("1. Load Audio")
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Upload base WAV/MP3 file", type=['wav', 'mp3', 'ogg'])
    
with col2:
    if uploaded_file is not None:
        if st.button("Load / Reset Audio", use_container_width=True):
            with st.spinner("Loading..."):
                data, sr = load_file(uploaded_file)
                st.session_state.original_audio = data.copy()
                st.session_state.editor_audio = data.copy()
                st.session_state.editor_sr = sr
                st.rerun()

if st.session_state.editor_audio is not None:
    data = st.session_state.editor_audio
    sr = st.session_state.editor_sr
    duration = len(data) / sr
    
    st.divider()
    
    # -----------------------------------------------------
    # DISPLAY CURRENT AUDIO STATE
    # -----------------------------------------------------
    st.header("Current Audio State")
    st.metric("Duration", f"{duration:.2f} s")
    st.audio(data, sample_rate=sr)
    
    fig = plot_waveform(data, sr=sr, title="Current Waveform", color="#FF007F")
    st.pyplot(fig)
    
    st.divider()
    
    # -----------------------------------------------------
    # EDITING TOOLS
    # -----------------------------------------------------
    st.header("2. Editing Tools")
    
    t_trim, t_rev, t_scale, t_fade, t_join, t_conv = st.tabs([
        "✂️ Trim", "🔄 Reverse", "🔊 Scale (Volume)", "🌊 Fade", "➕ Join", "🎛️ Echo (Convolution)"
    ])
    
    with t_trim:
        st.subheader("Trim Audio")
        trim_range = st.slider("Select time range to keep (seconds)", 0.0, duration, (0.0, duration), step=0.1)
        if st.button("Apply Trim"):
            start_sample = int(trim_range[0] * sr)
            end_sample = int(trim_range[1] * sr)
            st.session_state.editor_audio = data[start_sample:end_sample]
            st.rerun()
            
    with t_rev:
        st.subheader("Reverse Audio")
        st.markdown("Play the audio backwards.")
        if st.button("Apply Reverse"):
            st.session_state.editor_audio = data[::-1]
            st.rerun()
            
    with t_scale:
        st.subheader("Scale Volume")
        gain = st.slider("Volume Multiplier", 0.0, 3.0, 1.0, step=0.1)
        if st.button("Apply Scaling"):
            st.session_state.editor_audio = data * gain
            st.rerun()
            
    with t_fade:
        st.subheader("Fade In / Out")
        fade_in = st.number_input("Fade-in duration (s)", min_value=0.0, max_value=duration/2, value=0.5, step=0.1)
        fade_out = st.number_input("Fade-out duration (s)", min_value=0.0, max_value=duration/2, value=0.5, step=0.1)
        
        if st.button("Apply Fades"):
            new_data = data.copy()
            # Fade In
            fade_in_samples = int(fade_in * sr)
            if fade_in_samples > 0:
                fade_in_curve = np.linspace(0, 1, fade_in_samples)
                new_data[:fade_in_samples] = new_data[:fade_in_samples] * fade_in_curve
                
            # Fade Out
            fade_out_samples = int(fade_out * sr)
            if fade_out_samples > 0:
                fade_out_curve = np.linspace(1, 0, fade_out_samples)
                new_data[-fade_out_samples:] = new_data[-fade_out_samples:] * fade_out_curve
                
            st.session_state.editor_audio = new_data
            st.rerun()
            
    with t_join:
        st.subheader("Join / Append Audio")
        st.markdown("Upload a second audio file to append to the end of the current one.")
        second_file = st.file_uploader("Upload audio to append", type=['wav', 'mp3', 'ogg'], key="join_uploader")
        if second_file is not None:
            if st.button("Append File"):
                with st.spinner("Appending..."):
                    second_data, _ = load_file(second_file, target_sr=sr)
                    st.session_state.editor_audio = np.concatenate((data, second_data))
                    st.rerun()
                    
    with t_conv:
        st.subheader("Convolution-Based Echo")
        st.markdown("""
        Create an echo effect by convolving the audio with an **Impulse Response**.
        An impulse response containing spikes spaced out in time creates echoes.
        """)
        
        echo_delay = st.slider("Echo Delay (ms)", 50, 1000, 300, step=50)
        echo_decay = st.slider("Echo Decay (Amplitude multiplier)", 0.1, 0.9, 0.5)
        num_echoes = st.slider("Number of Echoes", 1, 5, 2)
        
        if st.button("Apply Convolution Echo"):
            with st.spinner("Convolving..."):
                # Create impulse response
                # Length of impulse response accommodates the final echo
                delay_samples = int((echo_delay / 1000.0) * sr)
                ir_length = (delay_samples * num_echoes) + 1
                impulse_response = np.zeros(ir_length)
                
                # Direct path
                impulse_response[0] = 1.0
                
                # Echoes
                for i in range(1, num_echoes + 1):
                    impulse_response[i * delay_samples] = echo_decay ** i
                    
                # Convolve
                # mode='full' adds the echo tail to the end of the file
                convolved_data = convolve(data, impulse_response, mode='full')
                
                # Normalize so it doesn't blow out speakers
                if np.max(np.abs(convolved_data)) > 0:
                    convolved_data = convolved_data / np.max(np.abs(convolved_data))
                    
                st.session_state.editor_audio = convolved_data
                st.rerun()

else:
    st.info("Upload an audio file and click 'Load' to begin editing.")

