from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from src.vad import detect_voice_activity, generate_vad_plot
from api.dsp_routes import get_audio_from_upload

router = APIRouter()

@router.post('/analyze')
async def analyze_vad(file: UploadFile = File(...), threshold: float = Form(0.05)):
    data, sr = get_audio_from_upload(file)
    times, energies, thresh_val, speech_segments, silent_segments = detect_voice_activity(data, sr, threshold_ratio=threshold)
    
    plot_b64 = generate_vad_plot(data, sr, times, energies, thresh_val, speech_segments)
    
    return {
        'plot': 'data:image/png;base64,' + plot_b64,
        'speech': [{'start': round(s, 3), 'end': round(e, 3)} for s, e in speech_segments],
        'silence': [{'start': round(s, 3), 'end': round(e, 3)} for s, e in silent_segments]
    }

