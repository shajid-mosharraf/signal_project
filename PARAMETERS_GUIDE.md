# 🎛️ Frontend Parameters Guide

This document explains every single parameter, slider, and dropdown available in the Frontend UI, detailing exactly what they do mathematically and how they affect your audio signals.

---

## 1. ✂️ Mini Audio Editor Tab

### **Trim Audio**
*   **Start Time (s):** The exact second in the audio file where the cut should begin. Anything before this timestamp is deleted.
*   **End Time (s):** The exact second where the cut should stop. Anything after this timestamp is deleted.

### **Add Echo (Reverb)**
*   **Delay (ms):** The physical distance (in milliseconds) between the original sound and the first reflection hitting your ear. Larger values sound like a massive canyon; smaller values sound like a small bathroom.
*   **Decay Factor (0 to 1):** The volume multiplier for each subsequent bounce. A decay of `0.5` means the first echo is 50% volume, the second is 25%, the third is 12.5%.
*   **Number of Echoes:** The total number of mathematical trailing reflections to generate. 

### **Resample (Chipmunk Effect)**
*   **Speed Factor:** A multiplier applied to the playback sample rate. `1.0` is normal speed. `2.0` plays the audio twice as fast (doubling the pitch). `0.5` plays it at half speed (halving the pitch).

---

## 2. 🎚️ Digital Filters Tab

### **Filter Configuration**
*   **Filter Type:**
    *   **Lowpass:** Allows low frequencies (bass/voice) to pass while aggressively cutting high frequencies (hiss/static).
    *   **Highpass:** Allows high frequencies to pass while aggressively cutting low frequencies (rumbles/wind noise).
    *   **Bandpass:** Isolates a specific middle range (like isolating a telephone voice) and removes everything else.
    *   **Bandstop (Notch):** Carves out a specific frequency (like a single-tone jammer beep) and leaves the rest intact.
*   **Cutoff Freq (Hz):** The primary boundary where the filter begins cutting.
*   **High Cutoff (Hz):** (Only active for Bandpass/Bandstop). The upper boundary of the frequency range you are targeting.
*   **Filter Order (Sharpness):** Mathematically, this dictates the number of poles in the Butterworth filter. A value of `1` produces a very gentle, sloping roll-off. A value of `10` produces a highly aggressive, near-vertical brick-wall cut.

---



## 3. 🔇 Noise Reducer Tab

### **Reduction Method**
*   **Frequency-Domain (Spectral Subtraction):** Converts the audio to the frequency domain (using STFT), calculates the average volume of the steady static/fan noise, and literally subtracts that static magnitude from the entire file before converting it back to audio.
*   **Time-Domain (Moving Average):** Glides a mathematical "window" across the raw audio samples, averaging adjacent points together. This smooths out sharp, high-frequency spikes (like static).
*   **Reduction Strength:** 
    *   In Freq-Domain: Acts as a multiplier for how much static to subtract.
    *   In Time-Domain: Increases the size of the smoothing window.

---

## 4. 🎛️ 10-Band Graphic Equalizer Tab

*   **Sliders (31Hz - 16000Hz):** These are HTML5 Web Audio API `BiquadFilterNodes` set to `peaking`. Moving the slider adjusts the `gain` (measured in decibels) of that specific frequency band, boosting or cutting it in real-time on your local CPU.
