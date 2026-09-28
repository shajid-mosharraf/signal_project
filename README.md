# Master Audio Lab

Master Audio Lab is a browser-based audio engineering and digital signal processing (DSP) suite. It provides a FastAPI backend and a static JavaScript frontend for editing, analyzing, degrading, recovering, and classifying audio recordings.

## Features

- Upload audio files or record audio from the browser microphone.
- Play audio with a client-side Web Audio API volume control and 10-band equalizer.
- Trim, reverse, resample, time-stretch, and add convolution-based echo.
- Generate waveform, FFT magnitude, and spectrogram visualizations.
- Apply Butterworth low-pass, high-pass, and band-pass filters.
- Simulate communication-channel effects:
  - Multipath propagation using configurable channel taps.
  - Additive white Gaussian noise (AWGN).
  - Single-tone interference or jamming.
- Recover audio with Zero-Forcing (ZF) or Minimum Mean Square Error (MMSE) equalization.
- Reduce steady noise using moving-average smoothing or spectral subtraction.
- Detect speech and silence segments using short-time energy voice activity detection (VAD).
- Enroll speakers and identify unknown recordings using MFCC, pitch, spectral features, and cosine similarity.
- Store enrolled speaker signatures in SQLite by default, with optional PostgreSQL support through `DATABASE_URL`.

## Technology Stack

- Python 3
- FastAPI and Uvicorn
- NumPy and SciPy
- Librosa
- SoundFile
- Matplotlib
- SQLAlchemy
- SQLite by default; PostgreSQL is supported through the database URL
- HTML, CSS, and vanilla JavaScript
- Tailwind CSS loaded from its CDN by the frontend

## Project Structure

```text
signal_project/
├── main.py                 # FastAPI application and route registration
├── requirements.txt        # Python dependencies
├── speaker_db.sqlite       # Local SQLite database, created at runtime
├── ARCHITECTURE.md         # Architecture notes
├── api/
│   ├── dsp_routes.py       # Audio processing and visualization endpoints
│   ├── matcher_routes.py   # Speaker enrollment and identification endpoints
│   └── vad_routes.py       # Voice activity detection endpoint
├── src/
│   ├── channel.py          # Noise, multipath, delay, attenuation, interference
│   ├── equalizers.py       # ZF, MMSE, and LMS equalizers
│   ├── filters.py          # Butterworth filtering
│   ├── matcher.py          # Feature extraction, storage, and speaker scoring
│   └── vad.py              # Short-time energy VAD and plot generation
└── static/
    ├── index.html          # Web interface
    ├── app.js              # Frontend behavior and API calls
    └── style.css           # Application styling
```

## Installation

Create and activate a virtual environment from the project directory.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run the following once for the current user or activate the environment using the Python executable directly:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Running the Application

Start the development server from the directory containing `main.py`:

```powershell
python main.py
```

The application is available at:

- Web interface: `http://localhost:8000/`
- Swagger API documentation: `http://localhost:8000/docs`
- ReDoc API documentation: `http://localhost:8000/redoc`

The server uses Uvicorn with reload enabled when started through `main.py`.

You can also start it explicitly:

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Run commands from the project root so that `static/` and the SQLite database path resolve correctly.

## Database Configuration

The speaker matcher uses this default database:

```text
sqlite:///speaker_db.sqlite
```

Set `DATABASE_URL` to use another SQLAlchemy-compatible database. For example, in PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/audio_lab"
python main.py
```

The `speakers` table is created automatically when the matcher module initializes. Each enrollment creates one row containing the speaker name and a JSON-serialized feature vector. Enrolling the same person multiple times is supported and improves matching across different recordings.

## API Reference

All endpoints accept uploaded audio as multipart form data. Audio is decoded with SoundFile and stereo input is converted to mono.

### DSP and editing endpoints

| Method and path | Form fields | Response |
|---|---|---|
| `POST /api/spectrogram` | `file`, optional `n_fft`, `hop_length`, `cmap` | JSON containing a base64 PNG in `image` |
| `POST /api/phase_vocoder` | `file`, `speed_factor` | Processed WAV audio |
| `POST /api/filter` | `file`, `f_type`, `f_order`, `cutoff_low`, optional `cutoff_high` | Filtered WAV audio |
| `POST /api/channel` | `file`, `add_noise`, `snr`, `add_mp`, `taps`, `add_inter`, `inter_freq`, `inter_snr` | Channel-affected WAV audio |
| `POST /api/equalize` | `file`, `eq_type` (`ZF` or other for MMSE), `taps`, `snr` | Equalized WAV audio |
| `POST /api/analysis/plots` | `file` | JSON containing base64 waveform (`wave`) and FFT (`mag`) PNGs |
| `POST /api/trim` | `file`, `start`, `end` in seconds | Trimmed WAV audio |
| `POST /api/echo` | `file`, `delay_ms`, `decay`, `echoes` | Echo-processed WAV audio |
| `POST /api/resample` | `file`, `speed_factor` | WAV audio written at `original_rate * speed_factor` |
| `POST /api/reverse` | `file` | Reversed WAV audio |
| `POST /api/compare_plots` | `file_before`, `file_after`, optional `include_freq` | JSON containing before/after base64 PNGs |
| `POST /api/denoise` | `file`, `method` (`time` or `freq`), `strength` | Denoised WAV audio |

Example request:

```powershell
curl.exe -X POST http://localhost:8000/api/reverse `
  -F "file=@sample.wav" `
  -o reversed.wav
```

### Speaker matcher endpoints

| Method and path | Form fields | Response |
|---|---|---|
| `POST /api/matcher/enroll` | `file`, `name` | JSON success message |
| `POST /api/matcher/identify` | `file` | JSON with `match_name` and percentage `confidence` |
| `GET /api/matcher/list` | None | JSON list of enrolled speaker IDs and names |

Speaker feature extraction requires approximately 0.5 seconds or more of audio. The matcher resamples input to 16 kHz, removes DC offset, normalizes level, applies pre-emphasis, removes low-energy frames, and combines:

- 19 MFCC coefficients without the loudness coefficient.
- MFCC variation and delta variation.
- Four pitch statistics.
- Spectral centroid, bandwidth, rolloff, and flatness statistics.

The final score is based on cosine similarity after feature scaling. It is a similarity score, not a calibrated probability or security-grade biometric confidence value.

### VAD endpoint

| Method and path | Form fields | Response |
|---|---|---|
| `POST /api/vad/analyze` | `file`, optional `threshold` | JSON with a base64 plot, speech segments, and silence segments |

The VAD uses 30 ms frames, a 15 ms hop, and compares short-time energy to `maximum_energy * threshold`. Segment times are returned in seconds.

## Typical Workflow

1. Start the FastAPI server.
2. Open `http://localhost:8000/` in a browser.
3. Upload an audio file or record from a microphone.
4. Use the Master Lab tabs to edit or analyze the recording.
5. Use the Speaker Matcher page to enroll several recordings for a speaker, then identify a test recording.
6. Use the VAD page to inspect speech and silence intervals.

Most backend transformations return WAV data. The frontend keeps the current processed blob in memory and sends that blob to subsequent operations. Reset restores the originally uploaded file.

## Important Notes and Limitations

- The project currently has no automated test suite in the repository.
- Audio format support depends on the codecs available to SoundFile/libsndfile. WAV is the safest input and output format.
- Several DSP operations assume valid numeric parameters. Cutoff frequencies must be below the Nyquist frequency, and echo delay must produce a usable sample delay.
- Speaker identification should be evaluated with recordings from the intended microphones and environment. It is not intended to replace authentication or access control.
- `speaker_db.sqlite` contains application data. Back it up before changing branches or resolving Git conflicts because SQLite is a binary file and Git cannot merge its records automatically.
- The frontend loads Tailwind CSS from a CDN, so the styling may be incomplete when running without network access.
- The `streamlit` and PostgreSQL dependencies are included for compatibility or future use; the current entry point is FastAPI and SQLite is the default database.

## Git Notes

The local SQLite file should be treated as runtime data. If a merge reports a conflict in `speaker_db.sqlite`, choose one complete database version or export and combine records manually; do not edit the binary file as text.

After resolving source changes:

```powershell
git add .
git commit -m "Describe the change"
git push
```
