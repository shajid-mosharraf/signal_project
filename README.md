# Digital Signal Processing & Communications Suite 🎙️📈

A comprehensive suite of interactive Digital Signal Processing (DSP) and communication system simulations built with Streamlit and Python. This tool allows users to visually and audibly explore complex signal processing concepts through a modern, neon-styled dashboard.

## 🌟 Features

This application contains multiple distinct "labs" and tools, available via the sidebar:

### 1. Multi-Speaker Comm System (Main App)
Simulates a full telecommunications pipeline:
- **Mixture**: Mixes multiple independent voices into a simulated multi-microphone environment.
- **Transmission**: Simulates signal degradation through a channel with Additive White Gaussian Noise (AWGN) and multipath fading.
- **Equalization**: Uses Zero-Forcing to mitigate channel impairments.
- **Separation**: Applies FastICA (Blind Source Separation) to disentangle the overlapping voices.
- **Diarization**: Maps temporal speaker activity to determine "who spoke when."

### 2. Digital Signal Analysis Toolkit
A massive interactive dashboard to analyze and process a single audio signal:
- **Time Domain**: Calculates RMS, Energy, and plots waveforms.
- **Frequency Domain**: Computes FFT, plotting Magnitude Spectrum, Phase Spectrum, and STFT Spectrograms.
- **Digital Filtering**: Apply interactive FIR/IIR Low-pass, High-pass, Band-pass, and Notch filters.
- **Channel Simulation**: Add specific delay, attenuation, single-tone jamming interference, and noise.
- **Advanced Equalization**: Apply Zero-Forcing, MMSE, and Machine-Learning based LMS Adaptive Equalization (with learning curves).

### 3. Audio Speed and Pitch Lab
Explores the effects of naive resampling and downsampling:
- **Naive Resampling**: Change playback speed to demonstrate how it simultaneously shifts formants (the "chipmunk effect"), contrasted with Phase Vocoder pitch-preserving time-stretching.
- **Aliasing**: Visually and audibly demonstrates the distortion caused by downsampling without an anti-aliasing filter.

### 4. Spectrogram Explorer
Demonstrates the fundamental uncertainty principle of signal processing:
- Interactively adjust the `N_FFT` window size and hop length to observe the direct trade-off between time resolution and frequency resolution.

### 5. Mini Audio Editor
A sequential, non-linear audio editor:
- Trim, Reverse, Scale (Volume), Fade in/out, and Join audio clips.
- Apply a custom Convolution-Based Echo effect by simulating an impulse response.

## 🛠️ Installation & Setup

1. Clone this repository.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
4. Open the provided localhost link in your web browser.

## 💻 Tech Stack
- **Frontend**: Streamlit
- **Signal Processing**: Numpy, SciPy, Librosa
- **Visualization**: Matplotlib

