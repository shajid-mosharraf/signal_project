import os
import json
import numpy as np
import librosa
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# Configure PostgreSQL Database (Defaults to local speaker_db)
# Configure Database (Defaults to local SQLite file to avoid password/setup issues)
# Users can override this by setting the DATABASE_URL environment variable
DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/speaker_db")
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///speaker_db.sqlite")

Base = declarative_base()

class Speaker(Base):
    __tablename__ = 'speakers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    # Store MFCC array as JSON
    mfcc_features = Column(JSON, nullable=False)

def get_engine_and_session():
    """Initializes DB connection and creates tables if they don't exist."""
    try:
        if DB_URL.startswith("sqlite"):
            engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DB_URL)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return engine, SessionLocal
    except OperationalError as e:
        print(f"Could not connect to database at {DB_URL}. Ensure PostgreSQL is running.")
        return None, None

def extract_mfcc_signature(audio_data, sr=16000, n_mfcc=40):
    """
    Extracts a highly robust biometric 'voice print'.
    Uses silence trimming, Deltas, and statistical moments (Mean + Std).
    """
    # 1. Trim leading and trailing silence so background noise doesn't skew the fingerprint
    audio_trimmed, _ = librosa.effects.trim(audio_data, top_db=25)
    
    # Fallback if trimming removes everything
    if len(audio_trimmed) < int(sr * 0.1):
        audio_trimmed = audio_data
        
    # 2. Compute MFCCs
    mfccs = librosa.feature.mfcc(y=audio_trimmed, sr=sr, n_mfcc=n_mfcc)
    
    # 3. Drop the 0th coefficient (it captures volume/loudness, not voice identity)
    mfccs = mfccs[1:, :]
    
    # 4. Compute Delta (first derivative to capture dynamic voice changes over time)
    delta_mfccs = librosa.feature.delta(mfccs)
    
    # 5. Stack them together
    combined = np.vstack([mfccs, delta_mfccs])
    
    # 6. Take Mean AND Standard Deviation across time
    feat_mean = np.mean(combined, axis=1)
    feat_std = np.std(combined, axis=1)
    
    # 7. Concatenate into one massive signature vector
    signature = np.concatenate([feat_mean, feat_std])
    
    # 8. L2 Normalize the vector to ensure scale invariance
    norm = np.linalg.norm(signature)
    if norm > 0:
        signature = signature / norm
        
    return signature.tolist()

def cosine_similarity(v1, v2):
    """Calculates cosine similarity between two vectors."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def enroll_speaker(session, name, audio_data, sr=16000):
    """Extracts features and saves a new speaker to the database."""
    features = extract_mfcc_signature(audio_data, sr)
    new_speaker = Speaker(name=name, mfcc_features=features)
    session.add(new_speaker)
    session.commit()
    return True

def identify_speaker(session, audio_data, sr=16000):
    """
    Compares the input audio against all enrolled speakers.
    Returns the best match name and the similarity score (0.0 to 1.0).
    """
    # 1. Extract signature from unknown audio
    unknown_features = extract_mfcc_signature(audio_data, sr)
    unknown_vector = np.array(unknown_features)
    
    # 2. Fetch all enrolled speakers
    speakers = session.query(Speaker).all()
    if not speakers:
        return None, 0.0
        
    best_match = None
    highest_similarity = -1.0
    
    # 3. Compare unknown against all enrolled
    for spk in speakers:
        spk_vector = np.array(spk.mfcc_features)
        
        # Skip legacy database entries that were created before the algorithm upgrade
        if len(spk_vector) != len(unknown_vector):
            continue
            
        sim = cosine_similarity(unknown_vector, spk_vector)
        
        if sim > highest_similarity:
            highest_similarity = sim
            best_match = spk.name
            
    return best_match, highest_similarity

