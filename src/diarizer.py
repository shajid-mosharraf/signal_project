


import librosa
import numpy as np
from sklearn.cluster import KMeans
from scipy.signal import medfilt

def diarize_audio(audio, sr=16000, n_speakers=2, frame_length=0.5, hop_length=0.25):
    """
    Performs basic unsupervised speaker diarization using MFCCs and K-Means.
    
    Args:
        audio (ndarray): The mixed or separated audio signal.
        sr (int): Sample rate.
        n_speakers (int): Number of speakers to cluster.
        frame_length (float): Length of each analysis frame in seconds.
        hop_length (float): Hop length between frames in seconds.
        
    Returns:
        list of tuples: Timeline of speakers, e.g., [(start_time, end_time, "Speaker 0"), ...]
    """
    if len(audio) == 0:
        return []

    # Number of samples per frame and hop
    n_fft = int(frame_length * sr)
    hop_samples = int(hop_length * sr)
    
    # Ensure n_fft is a power of 2 for efficiency (optional, but librosa handles it)
    
    # Extract MFCC features
    # MFCC shape: (n_mfcc, n_frames)
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13, n_fft=n_fft, hop_length=hop_samples)
    
    # Transpose for sklearn: (n_frames, n_mfcc)
    features = mfccs.T
    
    # Standardize features
    features = (features - np.mean(features, axis=0)) / (np.std(features, axis=0) + 1e-8)
    
    # Cluster using K-Means
    kmeans = KMeans(n_clusters=n_speakers, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features)
    
    # Smooth labels to remove rapid switching (median filter)
    # Kernel size must be odd
    smoothed_labels = medfilt(labels, kernel_size=5)
    
    # Convert labels to timeline
    timeline = []
    current_label = smoothed_labels[0]
    start_time = 0.0
    
    for i, label in enumerate(smoothed_labels):
        if label != current_label:
            end_time = i * hop_length
            timeline.append((start_time, end_time, f"Speaker {int(current_label)}"))
            start_time = end_time
            current_label = label
            
    # Add final segment
    timeline.append((start_time, len(audio)/sr, f"Speaker {int(current_label)}"))
    
    return timeline

