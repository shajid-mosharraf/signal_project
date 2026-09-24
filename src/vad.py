import numpy as np
import matplotlib.pyplot as plt
import io
import base64

def compute_ste(data, frame_size, hop_size):
    energies = []
    for i in range(0, len(data) - frame_size + 1, hop_size):
        frame = data[i:i+frame_size]
        energy = np.sum(frame**2)
        energies.append(energy)
    return np.array(energies)

def detect_voice_activity(data, sr, frame_duration=0.03, hop_duration=0.015, threshold_ratio=0.05):
    frame_size = int(frame_duration * sr)
    hop_size = int(hop_duration * sr)
    
    if len(data) < frame_size:
        return [], [], 0, [], [(0, len(data)/sr)]
        
    energies = compute_ste(data, frame_size, hop_size)
    threshold = np.max(energies) * threshold_ratio
    is_speech = energies > threshold
    
    speech_segments = []
    silent_segments = []
    in_speech = False
    start_time = 0.0
    
    times = np.arange(len(energies)) * hop_size / sr
    
    for i, speech_flag in enumerate(is_speech):
        current_time = times[i]
        if speech_flag and not in_speech:
            if start_time < current_time: silent_segments.append((start_time, current_time))
            start_time = current_time
            in_speech = True
        elif not speech_flag and in_speech:
            if start_time < current_time: speech_segments.append((start_time, current_time))
            start_time = current_time
            in_speech = False
            
    final_time = len(data) / sr
    if start_time < final_time:
        if in_speech:
            speech_segments.append((start_time, final_time))
        else:
            silent_segments.append((start_time, final_time))
            
    return times, energies, threshold, speech_segments, silent_segments

def generate_vad_plot(data, sr, times, energies, threshold, speech_segments):
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    
    time_axis = np.linspace(0, len(data)/sr, len(data))
    ax1.plot(time_axis, data, color='#00E5FF', linewidth=0.5)
    ax1.set_title('Waveform with Speech Regions Highlighted (Magenta)', color='white')
    ax1.set_ylabel('Amplitude')
    for (start, end) in speech_segments:
        ax1.axvspan(start, end, color='#FF00FF', alpha=0.3)
        
    ax2.plot(times, energies, color='#00FF88', linewidth=1.5, label='Short-Time Energy')
    ax2.axhline(threshold, color='#FF00FF', linestyle='--', label='Threshold')
    ax2.set_title('Short-Time Energy & Decision Threshold', color='white')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Energy')
    ax2.legend()
    
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

