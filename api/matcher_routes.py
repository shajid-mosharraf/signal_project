import io
import soundfile as sf
import librosa
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

from src.matcher import get_engine_and_session, enroll_speaker, identify_speaker, Speaker

router = APIRouter()
engine, SessionLocal = get_engine_and_session()

def get_audio_from_upload(file: UploadFile):
    audio_bytes = file.file.read()
    data, sr = sf.read(io.BytesIO(audio_bytes))
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))
    return data, sr

@router.post("/enroll")
async def enroll(file: UploadFile = File(...), name: str = Form(...)):
    if SessionLocal is None:
        return JSONResponse({"error": "Database not connected"}, status_code=500)
        
    data, sr = get_audio_from_upload(file)
    with SessionLocal() as session:
        success = enroll_speaker(session, name, data, sr)
        if success:
            return {"message": f"Successfully enrolled {name}"}
        else:
            return JSONResponse({"error": "Failed to enroll speaker"}, status_code=500)

@router.post("/identify")
async def identify(file: UploadFile = File(...)):
    if SessionLocal is None:
        return JSONResponse({"error": "Database not connected"}, status_code=500)
        
    data, sr = get_audio_from_upload(file)
    with SessionLocal() as session:
        match_name, similarity = identify_speaker(session, data, sr)
        
    if match_name is None:
        return {"match_name": None, "confidence": 0}
        
    confidence = max(0, similarity) * 100
    return {"match_name": match_name, "confidence": confidence}

@router.get("/list")
async def list_speakers():
    if SessionLocal is None:
        return JSONResponse({"error": "Database not connected"}, status_code=500)
        
    with SessionLocal() as session:
        speakers = session.query(Speaker).all()
        return {"speakers": [{"id": s.id, "name": s.name} for s in speakers]}

