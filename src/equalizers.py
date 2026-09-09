import numpy as np

def zero_forcing_equalize(y, channel_taps):
    """
    Zero-Forcing Equalizer in frequency domain.
    Inverts the channel completely, but amplifies noise where channel spectrum is close to zero.
    """
    n = len(y)
    Y = np.fft.fft(y)
    # Pad taps to signal length
    h_padded = np.zeros(n)
    h_padded[:min(len(channel_taps), n)] = channel_taps[:min(len(channel_taps), n)]
    H = np.fft.fft(h_padded)
    
    # Avoid division by zero
    H[H == 0] = 1e-10
    
    X_eq = Y / H
    x_eq = np.fft.ifft(X_eq).real
    return x_eq

def mmse_equalize(y, channel_taps, snr_db):
    """
    Minimum Mean Square Error (MMSE) Equalizer in frequency domain.
    Balances channel inversion and noise amplification.
    """
    n = len(y)
    Y = np.fft.fft(y)
    h_padded = np.zeros(n)
    h_padded[:min(len(channel_taps), n)] = channel_taps[:min(len(channel_taps), n)]
    H = np.fft.fft(h_padded)
    
    # Noise variance
    snr_linear = 10**(snr_db / 10)
    # Assume signal power is 1 for simplicity of MMSE formula: W = H* / (|H|^2 + 1/SNR)
    W = np.conj(H) / (np.abs(H)**2 + 1.0/snr_linear)
    
    X_eq = Y * W
    x_eq = np.fft.ifft(X_eq).real
    return x_eq

def lms_equalize(y, reference_signal, filter_length=15, mu=0.01):
    """
    Least Mean Squares (LMS) Adaptive Equalizer.
    
    Args:
        y (ndarray): Received signal
        reference_signal (ndarray): Known training sequence (pilot)
        filter_length (int): Number of taps for the equalizer filter
        mu (float): Step size for adaptation
        
    Returns:
        ndarray: Equalized signal
        list: Learning curve (MSE over time)
    """
    n = len(y)
    w = np.zeros(filter_length) # Equalizer weights
    x_eq = np.zeros(n)
    mse_log = []
    
    # We can only train as long as the reference signal
    train_len = min(n, len(reference_signal))
    
    for i in range(filter_length, train_len):
        # Current input vector
        y_vec = y[i::-1][:filter_length]
        if len(y_vec) < filter_length:
            y_vec = np.pad(y_vec, (0, filter_length - len(y_vec)))
            
        # Filter output
        out = np.dot(w, y_vec)
        x_eq[i] = out
        
        # Error
        error = reference_signal[i] - out
        mse_log.append(error**2)
        
        # Update weights
        w = w + 2 * mu * error * y_vec
        
    # After training, apply frozen weights to the rest of the signal
    for i in range(train_len, n):
        y_vec = y[i::-1][:filter_length]
        if len(y_vec) < filter_length:
            y_vec = np.pad(y_vec, (0, filter_length - len(y_vec)))
        x_eq[i] = np.dot(w, y_vec)
        
    return x_eq, mse_log

