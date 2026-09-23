import io
import base64
import librosa
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from scipy.signal import decimate

from src.filters import apply_filter
from src.channel import add_awgn, add_multipath, add_interference
from src.equalizers import zero_forcing_equalize, mmse_equalize

router = APIRouter()

def get_audio_from_upload(file: UploadFile):
    audio_bytes = file.file.read()
    data, sr = sf.read(io.BytesIO(audio_bytes))
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    return data, sr

def audio_to_wav_bytes(data, sr):
    buffer = io.BytesIO()
    sf.write(buffer, data, sr, format='WAV')
    return buffer.getvalue()

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

@router.post("/spectrogram")
async def get_spectrogram(
    file: UploadFile = File(...), 
    n_fft: int = Form(1024), 
    hop_length: int = Form(256), 
    cmap: str = Form("inferno")
):
    data, sr = get_audio_from_upload(file)
    
    D = librosa.stft(data, n_fft=n_fft, hop_length=hop_length)
    D_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')
    
    img = librosa.display.specshow(D_db, sr=sr, hop_length=hop_length, x_axis='time', y_axis='log', ax=ax, cmap=cmap)
    fig.colorbar(img, ax=ax, format="%+2.0f dB", pad=0.02)
    ax.set_title(f"Spectrogram (n_fft={n_fft})", fontweight="bold", color="white")
    
    b64 = fig_to_base64(fig)
    return JSONResponse({"image": f"data:image/png;base64,{b64}"})

@router.post("/phase_vocoder")
async def apply_phase_vocoder(file: UploadFile = File(...), speed_factor: float = Form(1.0)):
    data, sr = get_audio_from_upload(file)
    stretched = librosa.effects.time_stretch(y=data, rate=speed_factor)
    wav_bytes = audio_to_wav_bytes(stretched, sr)
    return Response(content=wav_bytes, media_type="audio/wav")

@router.post("/filter")
async def route_filter(
    file: UploadFile = File(...),
    f_type: str = Form(...),
    f_order: int = Form(5),
    cutoff_low: float = Form(None),
    cutoff_high: float = Form(None)
):
    data, sr = get_audio_from_upload(file)
    if f_type in ["lowpass", "highpass"]:
        filtered = apply_filter(data, sr=sr, filter_type=f_type, order=f_order, cutoff=cutoff_low)
    else:
        filtered = apply_filter(data, sr=sr, filter_type=f_type, order=f_order, cutoff=(cutoff_low, cutoff_high))
    
    wav_bytes = audio_to_wav_bytes(filtered, sr)
    return Response(content=wav_bytes, media_type="audio/wav")

@router.post("/channel")
async def route_channel(
    file: UploadFile = File(...),
    add_noise: bool = Form(True),
    snr: float = Form(20.0),
    add_mp: bool = Form(True),
    taps: str = Form("1.0, 0.6, 0.3"),
    add_inter: bool = Form(False),
    inter_freq: float = Form(1000.0),
    inter_snr: float = Form(10.0)
):
    data, sr = get_audio_from_upload(file)
    ch_data = data.copy()
    if add_mp:
        tap_list = [float(x.strip()) for x in taps.split(',')]
        ch_data = add_multipath(ch_data, tap_list)
    if add_noise:
        ch_data = add_awgn(ch_data, snr)
    if add_inter:
        ch_data = add_interference(ch_data, sr, inter_freq, inter_snr)
        
    wav_bytes = audio_to_wav_bytes(ch_data, sr)
    return Response(content=wav_bytes, media_type="audio/wav")

@router.post("/equalize")
async def route_equalize(
    file: UploadFile = File(...),
    eq_type: str = Form("ZF"),
    taps: str = Form("1.0, 0.6, 0.3"),
    snr: float = Form(20.0)
):
    data, sr = get_audio_from_upload(file)
    tap_list = [float(x.strip()) for x in taps.split(',')]
    if eq_type == "ZF":
        eq_data = zero_forcing_equalize(data, tap_list)
    else:
        eq_data = mmse_equalize(data, tap_list, snr)
        
    wav_bytes = audio_to_wav_bytes(eq_data, sr)
    return Response(content=wav_bytes, media_type="audio/wav")


@router.post('/analysis/plots')
async def get_analysis_plots(file: UploadFile = File(...)):
    data, sr = get_audio_from_upload(file)
    
    plt.style.use('dark_background')
    # Waveform
    fig1, ax1 = plt.subplots(figsize=(10, 2))
    ax1.plot(np.linspace(0, len(data)/sr, len(data)), data, color='#00E5FF', linewidth=1)
    ax1.set_title('Waveform')
    b64_wave = fig_to_base64(fig1)
    
    # FFT
    n = len(data)
    freqs = np.fft.rfftfreq(n, d=1/sr)
    fft_vals = np.fft.rfft(data)
    mag_db = 20 * np.log10(np.clip(np.abs(fft_vals), 1e-10, None))
    
    fig2, ax2 = plt.subplots(figsize=(10, 2))
    ax2.plot(freqs, mag_db, color='#FF007F', linewidth=1)
    ax2.set_title('Magnitude Spectrum')
    b64_mag = fig_to_base64(fig2)
    
    return JSONResponse({'wave': f'data:image/png;base64,{b64_wave}', 'mag': f'data:image/png;base64,{b64_mag}'})

from scipy.signal import convolve

@router.post('/trim')
async def route_trim(file: UploadFile = File(...), start: float = Form(...), end: float = Form(...)):
    data, sr = get_audio_from_upload(file)
    start_idx = int(start * sr)
    end_idx = int(end * sr)
    if end_idx <= start_idx:
        end_idx = len(data)
    if len(data[start_idx:end_idx]) == 0:
        return Response(content="Error: Trimmed audio is empty. You probably trimmed past the end of the file.", status_code=400)
    wav_bytes = audio_to_wav_bytes(data[start_idx:end_idx], sr)
    return Response(content=wav_bytes, media_type='audio/wav')

@router.post('/echo')
async def route_echo(file: UploadFile = File(...), delay_ms: float = Form(...), decay: float = Form(...), echoes: int = Form(...)):
    data, sr = get_audio_from_upload(file)
    delay_samples = int((delay_ms / 1000.0) * sr)
    ir_length = (delay_samples * echoes) + 1
    impulse_response = np.zeros(ir_length)
    impulse_response[0] = 1.0
    for i in range(1, echoes + 1):
        impulse_response[i * delay_samples] = decay ** i
    convolved_data = convolve(data, impulse_response, mode='full')
    if np.max(np.abs(convolved_data)) > 0:
        convolved_data = convolved_data / np.max(np.abs(convolved_data))
    wav_bytes = audio_to_wav_bytes(convolved_data, sr)
    return Response(content=wav_bytes, media_type='audio/wav')

@router.post('/resample')
async def route_resample(file: UploadFile = File(...), speed_factor: float = Form(...)):
    data, sr = get_audio_from_upload(file)
    new_sr = int(sr * speed_factor)
    wav_bytes = audio_to_wav_bytes(data, new_sr)
    return Response(content=wav_bytes, media_type='audio/wav')

@router.post('/alias')
async def route_alias(file: UploadFile = File(...), factor: int = Form(...), proper: bool = Form(...)):
    data, sr = get_audio_from_upload(file)
    aliased_sr = sr // factor
    if proper:
        out_data = decimate(data, factor, ftype='iir', zero_phase=True)
    else:
        out_data = data[::factor]
    wav_bytes = audio_to_wav_bytes(out_data, aliased_sr)
    return Response(content=wav_bytes, media_type='audio/wav')




@router.post('/reverse')
async def route_reverse(file: UploadFile = File(...)):
    data, sr = get_audio_from_upload(file)
    reversed_data = data[::-1]
    wav_bytes = audio_to_wav_bytes(reversed_data, sr)
    return Response(content=wav_bytes, media_type='audio/wav')


@router.post('/compare_plots')
async def route_compare_plots(file_before: UploadFile = File(...), file_after: UploadFile = File(...)):
    data_b, sr_b = get_audio_from_upload(file_before)
    data_a, sr_a = get_audio_from_upload(file_after)

    plt.style.use('dark_background')
    fig_b, ax_b = plt.subplots(figsize=(8, 2))
    ax_b.plot(np.linspace(0, len(data_b)/sr_b, len(data_b)), data_b, color='#00E5FF', linewidth=1)
    ax_b.set_title('Before (Actual)', color='white')

    fig_a, ax_a = plt.subplots(figsize=(8, 2))
    ax_a.plot(np.linspace(0, len(data_a)/sr_a, len(data_a)), data_a, color='#FF00FF', linewidth=1)
    ax_a.set_title('After (Modified)', color='white')

    return {
        'before': 'data:image/png;base64,' + fig_to_base64(fig_b),
        'after': 'data:image/png;base64,' + fig_to_base64(fig_a)
    }



