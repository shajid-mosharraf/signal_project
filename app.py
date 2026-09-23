import streamlit as st
from src.theme import apply_custom_theme

st.set_page_config(page_title="Audio DSP Suite", page_icon="🎧", layout="wide")
apply_custom_theme()

st.title("🎧 Audio Engineering & DSP Suite")
st.markdown("""
Welcome to the interactive Audio DSP laboratory!

This suite contains powerful tools to explore, manipulate, and analyze audio signals using pure Digital Signal Processing (DSP) mathematics.

### 🔬 Available Labs (See Sidebar)

* **[2] Signal & Spectrogram Analysis:** Explore Time and Frequency domains, FFT Spectrograms, FIR/IIR filtering, and Channel Equalization.
* **[3] Audio Editor & Pitch Lab:** A non-linear editor to trim, scale, and add echo, plus a demonstration of Speed, Pitch, Phase Vocoders, and Aliasing.
* **[4] Speaker Matcher:** A biometric voice-fingerprinting system using MFCCs and Cosine Similarity.
### 🔬 Available Labs (See Sidebar)

* **[2] Master Audio Lab (Analysis & Editing):** A massive unified workspace. Upload a file once and instantly analyze its Spectrogram, apply FIR filters, simulate Comm Channels, or edit it (Trim, Scale, Echo, 10-Band Graphic EQ).
* **[3] Speaker Matcher:** A biometric voice-fingerprinting system using MFCCs and Cosine Similarity.

👈 **Select a lab from the sidebar to the left to get started!**
""")
