import numpy as np
from scipy import signal

def add_awgn(x, snr_db):
    """
    Adds Additive White Gaussian Noise (AWGN) to a signal to achieve a specific SNR.
    """
    sig_power = np.mean(np.abs(x)**2)
    snr_linear = 10**(snr_db / 10)
    noise_power = sig_power / snr_linear
    noise = np.sqrt(noise_power) * np.random.randn(len(x))
    return x + noise

def add_multipath(x, taps):
    """
    Simulates a multipath channel by convolving the signal with given taps.
    """
    y = signal.convolve(x, taps, mode='full')
    return y[:len(x)] # Truncate tail for simplicity

def add_delay(x, delay_samples):
    """
    Adds a pure delay to the signal by padding zeros at the beginning.
    """
    if delay_samples <= 0:
        return x
    delayed = np.pad(x, (delay_samples, 0), mode='constant')
    return delayed[:len(x)]

def add_attenuation(x, attenuation_db):
    """
    Attenuates the signal by a given dB amount. (Negative dB means gain).
    """
    factor = 10**(-attenuation_db / 20)
    return x * factor

def add_interference(x, sr, freq, snr_db):
    """
    Adds a single-tone jamming interference to the signal.
    """
    sig_power = np.mean(np.abs(x)**2)
    snr_linear = 10**(snr_db / 10)
    interference_power = sig_power / snr_linear
    amplitude = np.sqrt(2 * interference_power) # amplitude for sine wave
    
    time = np.arange(len(x)) / sr
    interference = amplitude * np.sin(2 * np.pi * freq * time)
    return x + interference

def apply_channel(x, snr_db=20, taps=[1.0]):
    """
    Applies multipath and AWGN.
    """
    y = add_multipath(x, taps)
    y = add_awgn(y, snr_db)
    return y
