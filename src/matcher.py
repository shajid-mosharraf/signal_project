import os
import numpy as np
import librosa
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# Defaults to a local SQLite file. Override with the DATABASE_URL environment variable.
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///speaker_db.sqlite")

Base = declarative_base()


class Speaker(Base):
    """One row per enrolled RECORDING. Enroll the same name several times."""
    __tablename__ = 'speakers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    mfcc_features = Column(JSON, nullable=False)


def get_engine_and_session():
    try:
        if DB_URL.startswith("sqlite"):
            engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DB_URL)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return engine, SessionLocal
    except OperationalError:
        print(f"Could not connect to database at {DB_URL}.")
        return None, None


# ----------------------------------------------------------------------------
# Feature extraction (pure DSP: pre-emphasis, energy VAD, MFCC, deltas,
# autocorrelation/YIN pitch, spectral shape statistics)
# ----------------------------------------------------------------------------
SR = 16000
N_FFT = 512      # 32 ms
WIN = 400        # 25 ms
HOP = 160        # 10 ms
N_MELS = 40
N_MFCC = 20      # c0 is dropped -> 19 coefficients
N_C = N_MFCC - 1

# Feature layout: [mfcc mean | mfcc std | delta std | pitch(4) | spectral mean(4) + std(4)]
FEATURE_DIM = N_C * 3 + 4 + 8
BLOCK_WEIGHTS = np.concatenate([
    np.full(N_C, 1.0),    # mfcc mean  (vocal tract shape)
    np.full(N_C, 0.7),    # mfcc std
    np.full(N_C, 0.5),    # delta std  (speaking dynamics)
    np.full(4, 1.5),      # pitch (only 4 dims, so weighted up)
    np.full(8, 0.6),      # spectral shape
])


def _prepare_audio(audio, sr):
    y = np.asarray(audio, dtype=np.float32)
    if y.ndim > 1:
        y = y.mean(axis=0)
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    y = y - np.mean(y)                         # remove DC offset
    peak = np.max(np.abs(y))
    if peak > 0:
        y = y / peak                           # level normalisation
    y_pre = librosa.effects.preemphasis(y, coef=0.97)  # boost highs, flatten spectral tilt
    return y, y_pre


def _active_mask(y):
    """Energy-based VAD: keeps frames within 30 dB of the loud frames (removes pauses too)."""
    rms = librosa.feature.rms(y=y, frame_length=N_FFT, hop_length=HOP)[0]
    db = 20 * np.log10(rms + 1e-8)
    return db > (np.percentile(db, 95) - 30)


def extract_mfcc_signature(audio_data, sr=16000):
    y, y_pre = _prepare_audio(audio_data, sr)
    if len(y) < int(SR * 0.5):
        raise ValueError("Recording too short (need at least ~0.5 s of audio).")

    mask = _active_mask(y)

    mfcc = librosa.feature.mfcc(
        y=y_pre, sr=SR, n_mfcc=N_MFCC, n_fft=N_FFT, win_length=WIN,
        hop_length=HOP, n_mels=N_MELS, fmin=80, fmax=7600, lifter=22
    )[1:]                                       # drop c0 (loudness)
    d1 = librosa.feature.delta(mfcc, width=9, order=1)

    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP, win_length=WIN))
    spec = np.vstack([
        librosa.feature.spectral_centroid(S=S, sr=SR),
        librosa.feature.spectral_bandwidth(S=S, sr=SR),
        librosa.feature.spectral_rolloff(S=S, sr=SR, roll_percent=0.85),
        librosa.feature.spectral_flatness(S=S),
    ])
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=N_FFT, hop_length=HOP)[0]
    f0 = librosa.yin(y, fmin=70, fmax=400, sr=SR, frame_length=1024, hop_length=HOP)

    # Align every stream to the same number of frames
    T = min(mfcc.shape[1], d1.shape[1], spec.shape[1], zcr.shape[0], f0.shape[0], mask.shape[0])
    mfcc, d1, spec, zcr, f0, mask = mfcc[:, :T], d1[:, :T], spec[:, :T], zcr[:T], f0[:T], mask[:T]

    if mask.sum() < 20:                         # VAD removed almost everything -> use all frames
        mask = np.ones(T, dtype=bool)

    # Pitch: only voiced-looking frames (energetic, low ZCR, inside YIN's search range)
    voiced = mask & (zcr < 0.12) & (f0 > 75) & (f0 < 395)
    if voiced.sum() >= 10:
        lf = np.log(f0[voiced])
        pitch = [np.median(lf), np.std(lf), np.percentile(lf, 10), np.percentile(lf, 90)]
    else:
        pitch = [np.log(150.0), 0.0, np.log(150.0), np.log(150.0)]

    m = mfcc[:, mask]
    sig = np.concatenate([
        m.mean(axis=1),
        m.std(axis=1),
        d1[:, mask].std(axis=1),
        pitch,
        spec[:, mask].mean(axis=1),
        spec[:, mask].std(axis=1),
    ])
    return sig.tolist()


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------
def cosine_similarity(v1, v2):
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def _fit_normalizer(vectors):
    """
    Per-dimension standardisation using the enrolled recordings, so that big-valued
    features (MFCC means, spectral centroid) don't drown out small-valued ones (pitch).
    With very few recordings the statistics are unreliable, so fall back to
    relative scaling.
    """
    X = np.vstack(vectors)
    if len(X) >= 5:
        mu = X.mean(axis=0)
        sd = X.std(axis=0)
        sd = np.maximum(sd, 0.25 * np.median(sd))   # floor to avoid exploding tiny variances
    else:
        mu = np.zeros(X.shape[1])
        a = np.abs(X.mean(axis=0))
        sd = np.maximum(a, np.median(a)) + 1e-9
    return mu, sd


def enroll_speaker(session, name, audio_data, sr=16000):
    """Call this several times per person (different sessions/sentences) for best accuracy."""
    features = extract_mfcc_signature(audio_data, sr)
    session.add(Speaker(name=name, mfcc_features=features))
    session.commit()
    return True


def rank_speakers(session, audio_data, sr=16000):
    """Returns [(name, score), ...] sorted best-first, or [] if nothing usable is enrolled."""
    rows = [r for r in session.query(Speaker).all()
            if len(r.mfcc_features) == FEATURE_DIM]   # skips legacy entries
    if not rows:
        return []

    unknown = np.array(extract_mfcc_signature(audio_data, sr))
    mu, sd = _fit_normalizer([np.array(r.mfcc_features) for r in rows])

    def prep(v):
        return ((np.asarray(v) - mu) / sd) * BLOCK_WEIGHTS

    q = prep(unknown)
    by_name = {}
    for r in rows:
        by_name.setdefault(r.name, []).append(prep(r.mfcc_features))

    ranking = []
    for name, vecs in by_name.items():
        best_single = max(cosine_similarity(q, v) for v in vecs)
        centroid = cosine_similarity(q, np.mean(vecs, axis=0))
        ranking.append((name, 0.5 * best_single + 0.5 * centroid))
    ranking.sort(key=lambda t: t[1], reverse=True)
    return ranking


def identify_speaker(session, audio_data, sr=16000, threshold=None, min_margin=None):
    """
    Returns (best_name, score). Score is a correlation-like value in [-1, 1].
    Optional open-set rejection: returns (None, score) if score < threshold,
    or if the gap to the runner-up is below min_margin.
    Tune both numbers on your own recordings (see the note in the chat).
    """
    ranking = rank_speakers(session, audio_data, sr)
    if not ranking:
        return None, 0.0
    name, score = ranking[0]
    if threshold is not None and score < threshold:
        return None, score
    if min_margin is not None and len(ranking) > 1 and (score - ranking[1][1]) < min_margin:
        return None, score
    return name, score