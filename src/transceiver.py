import numpy as np
from scipy import signal

def zero_forcing_equalize(y, taps):
    """
    Performs Zero-Forcing (ZF) equalization using an IIR inverse filter.
    Assuming the channel is modeled as an FIR filter: Y(z) = H(z)X(z) + N(z)
    The ZF equalizer applies 1/H(z).
    
    Args:
        y (ndarray): Received signal
        taps (list or ndarray): Known channel impulse response (h)
        
    Returns:
        ndarray: Equalized signal
    """
    # The inverse filter is 1 / H(z)
    # y is the input to the filter, [1.0] is the numerator (b), taps is the denominator (a)
    # This might be unstable if the roots of H(z) are outside the unit circle (non-minimum phase).
    # For a simple multipath (e.g. [1.0, 0.5]), it's minimum phase and stable.
    try:
        x_hat = signal.lfilter([1.0], taps, y)
        return x_hat
    except Exception as e:
        print(f"ZF Equalizer failed: {e}")
        return y

def mmse_equalize(y, taps, snr_db):
    """
    Minimum Mean Square Error (MMSE) equalizer in frequency domain.
    Better stability than ZF for noisy or non-minimum phase channels.
    """
    # For simplicity, we use frequency domain division with a regularization term
    Y_fft = np.fft.fft(y)
    
    # Pad taps to match the length of y for element-wise multiplication
    h_padded = np.zeros(len(y))
    h_padded[:len(taps)] = taps
    H_fft = np.fft.fft(h_padded)
    
    snr_linear = 10**(snr_db / 10)
    # Avoid division by zero by setting a lower bound on noise variance
    noise_var = 1 / snr_linear if snr_linear > 0 else 1e-6 
    
    # MMSE weights: W = H* / (|H|^2 + 1/SNR)
    W = np.conj(H_fft) / (np.abs(H_fft)**2 + noise_var)
    
    X_hat_fft = Y_fft * W
    x_hat = np.real(np.fft.ifft(X_hat_fft))
    
    return x_hat

