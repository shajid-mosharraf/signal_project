import numpy as np
from scipy import signal

def apply_filter(data, sr, cutoff, filter_type='lowpass', order=5, bandwidth=None):
    """
    Applies a digital Butterworth filter to the audio data.
    
    Args:
        data (ndarray): Input audio signal.
        sr (int): Sample rate.
        cutoff (float or tuple): Cutoff frequency in Hz. Tuple for bandpass/bandstop.
        filter_type (str): 'lowpass', 'highpass', 'bandpass', 'bandstop'.
        order (int): Filter order.
        bandwidth (float): Used if cutoff is a single float but filter is bandpass/stop.
        
    Returns:
        ndarray: Filtered audio signal.
    """
    nyquist = 0.5 * sr
    
    if filter_type in ['bandpass', 'bandstop']:
        if isinstance(cutoff, (list, tuple)):
            Wn = [cutoff[0]/nyquist, cutoff[1]/nyquist]
        else:
            if bandwidth is None:
                bandwidth = 500 # Default bandwidth
            Wn = [max(1, cutoff - bandwidth/2)/nyquist, min(nyquist-1, cutoff + bandwidth/2)/nyquist]
    else:
        Wn = cutoff / nyquist
        
    # Design Butterworth filter
    b, a = signal.butter(order, Wn, btype=filter_type)
    
    # Apply zero-phase filter
    filtered_data = signal.filtfilt(b, a, data)
    
    return filtered_data

