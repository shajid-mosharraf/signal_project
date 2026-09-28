# Audio Lab Parameter Guide

Use this guide to understand what each control changes, where it acts in the signal path, and how to tune it without introducing unwanted artifacts.

> **Quick rule:** make one change at a time, listen to the result, and keep the least aggressive setting that solves the problem.

## Contents

- [Mini Audio Editor](#mini-audio-editor)
- [Digital Filters](#digital-filters)
- [Communication Channel](#communication-channel)
- [Noise Reducer](#noise-reducer)
- [10-Band Graphic Equalizer](#10-band-graphic-equalizer)
- [Practical Tuning](#practical-tuning)

---

## Mini Audio Editor

### Trim Audio

| Parameter | What it controls | Tuning note |
|---|---|---|
| **Start Time (s)** | The point where the output begins. Samples before this time are removed. | Set it just before the first useful sound so the attack is not clipped. |
| **End Time (s)** | The point where the output ends. Samples after this time are removed. | Leave a small amount of silence after speech when a natural ending matters. |

### Add Echo

| Parameter | What it controls | Tuning note |
|---|---|---|
| **Delay (ms)** | The time between the original signal and each reflection. | Short delays sound like a small room; long delays sound more spacious. |
| **Decay Factor (0 to 1)** | The level multiplier applied to each successive reflection. | A value of `0.5` produces echoes at `50%`, `25%`, `12.5%`, and so on. Lower values keep the mix cleaner. |
| **Number of Echoes** | The number of reflections generated after the original signal. | More echoes create a longer tail but can reduce speech clarity. |

### Resample

| Parameter | What it controls | Tuning note |
|---|---|---|
| **Speed Factor** | The playback-rate multiplier. | `1.0` is normal, `2.0` is twice as fast, and `0.5` is half speed. Changing playback rate also changes pitch, creating the classic chipmunk or slow-motion effect. |

---

## Digital Filters

Filters change which frequency ranges are allowed through. The **filter order** controls how sharply the transition happens.

### Filter Configuration

| Parameter | What it controls | Tuning note |
|---|---|---|
| **Filter Type** | The shape of the frequency range that remains. See the table below. | Start with the least aggressive filter that addresses the noise or frequency problem. |
| **Cutoff Frequency (Hz)** | The primary frequency boundary where attenuation begins. | Keep it below the Nyquist frequency, which is half the sample rate. |
| **High Cutoff (Hz)** | The upper boundary for band-pass and band-stop filtering. | Use only with `Bandpass` or `Bandstop`; it must be higher than the low cutoff. |
| **Filter Order** | The steepness of the filter roll-off. | `1` is gentle. Higher values are sharper but can create ringing or instability near extreme settings. |

### Filter Types

| Type | Keeps | Typical use |
|---|---|---|
| **Lowpass** | Frequencies below the cutoff | Reduce hiss, harshness, or high-frequency static. |
| **Highpass** | Frequencies above the cutoff | Remove rumble, handling noise, or low-frequency wind. |
| **Bandpass** | Frequencies between the low and high cutoffs | Isolate a voice or telephone-like midrange. |
| **Bandstop (Notch)** | Everything except the selected range | Remove a narrow tone, hum, or jammer frequency. |

---

## Communication Channel

This section simulates how an audio signal can degrade while travelling through a channel, then applies an equalizer to recover it.

### Simulate Channel Degradation

| Parameter | What it controls | Tuning note |
|---|---|---|
| **Multipath / ISI Taps** | Delayed and attenuated copies of the signal. The first tap is usually the direct path; later taps represent reflections. | For example, `1.0, 0.6, 0.3` creates a direct signal followed by two reflections. Stronger or longer taps produce more smearing. |
| **Single-Tone Jammer Frequency (Hz)** | The frequency of a continuous interfering sine wave. | Place it inside the voice range to make the interference especially noticeable. |
| **Jammer SNR (dB)** | The jammer level relative to the signal. | Lower values mean a louder jammer. Higher values make the interference quieter. |

### Recover Audio

| Equalizer | How it works | Trade-off |
|---|---|---|
| **Zero-Forcing (ZF)** | Applies an approximate inverse of the channel taps to undo multipath distortion. | Can recover severe smearing, but may strongly amplify background noise. |
| **Minimum Mean Square Error (MMSE)** | Balances channel correction against the estimated noise level. | Usually more stable and natural than ZF when noise is present, though it may leave some residual distortion. |

---

## Noise Reducer

Choose the method based on the character of the noise and how much detail the recording needs to preserve.

| Parameter | What it controls | Tuning note |
|---|---|---|
| **Reduction Method** | Selects frequency-domain spectral subtraction or time-domain moving-average smoothing. | Spectral subtraction is better for steady hiss or fan noise; moving average is simpler but can soften transients. |
| **Reduction Strength** | The aggressiveness of the selected reduction method. | In frequency mode, it scales the estimated noise that is subtracted. In time mode, it increases the smoothing-window size. |

### Methods at a Glance

**Frequency-domain: spectral subtraction**

The audio is transformed with a short-time Fourier transform (STFT). An estimate of the steady noise spectrum is subtracted from each frame before the signal is converted back to audio.

**Time-domain: moving average**

Each sample is replaced by the average of nearby samples. This smooths sharp fluctuations, but excessive smoothing can remove consonants and other high-frequency detail.

> **Watch for:** metallic or watery artifacts in frequency mode, and muffled speech in time mode. Reduce the strength when either appears.

---

## 10-Band Graphic Equalizer

The equalizer uses Web Audio API peaking filters. Each slider changes the gain of one frequency band in decibels.

| Band | Main area affected |
|---:|---|
| **31 Hz** | Sub-bass, electrical rumble |
| **62 Hz** | Bass weight, low hum |
| **125 Hz** | Warmth and body |
| **250 Hz** | Lower-mid fullness; too much can sound muddy |
| **500 Hz** | Midrange body |
| **1 kHz** | Vocal presence and general clarity |
| **2 kHz** | Speech intelligibility and attack |
| **4 kHz** | Definition and consonants |
| **8 kHz** | Brightness and detail |
| **16 kHz** | Air and high-frequency sheen |

### Equalizer Tips

- Use small changes first. A few decibels can be clearly audible.
- Cut unwanted frequencies before boosting others; this leaves more headroom.
- If speech sounds muddy, try a small cut around `250 Hz`.
- If speech lacks clarity, try a small boost around `2 kHz` to `4 kHz`.
- If the output becomes harsh or hissy, reduce `4 kHz` to `16 kHz` rather than boosting the low bands further.

---

## Practical Tuning

1. **Listen to the original recording first.** Identify whether the problem is timing, noise, frequency balance, or channel distortion.
2. **Make the smallest useful adjustment.** Aggressive settings are more likely to create artifacts.
3. **Check speech transients.** Plosives, consonants, and the ends of words reveal over-filtering quickly.
4. **Watch output level.** Echo, equalization, and recovery can increase peaks and cause clipping.
5. **Compare before and after at the same listening level.** A louder signal can seem better even when it is only louder.

### Frequency Reference

For a sample rate of `16,000 Hz`, the Nyquist frequency is `8,000 Hz`. A filter cutoff must stay below that limit. At other sample rates, calculate it as:

```text
Nyquist frequency = sample rate / 2
```