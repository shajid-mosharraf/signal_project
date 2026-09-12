import streamlit as st
import numpy as np
import io
import soundfile as sf
import librosa
import matplotlib.pyplot as plt

# Import custom styling
from src.audio_utils import plot_spectrogram
from src.matcher import get_engine_and_session, enroll_speaker, identify_speaker, Speaker

st.set_page_config(page_title="Speaker Matcher", page_icon="🔐", layout="wide")

# Apply modern dark styling
plt.style.use("dark_background")
plt.rcParams.update({
    "axes.facecolor": "#0E1117", "figure.facecolor": "#0E1117", "axes.edgecolor": "#444444",
    "grid.color": "#333333", "text.color": "#E0E0E0", "axes.labelcolor": "#E0E0E0",
    "xtick.color": "#A0A0A0", "ytick.color": "#A0A0A0", "axes.spines.top": False, "axes.spines.right": False
})

st.title("🔐 Speaker Matcher (Voice Biometrics)")
st.markdown("Record or upload audio to enroll speakers into a PostgreSQL database. Then, upload unknown audio to automatically identify the speaker using MFCC short-spectra matching!")

# Attempt to connect to DB
engine, SessionLocal = get_engine_and_session()

if SessionLocal is None:
    st.error("🚨 **Database Connection Failed!**")
    st.markdown("""
    Could not connect to the PostgreSQL database. By default, it expects:
    `postgresql://postgres:postgres@localhost:5432/speaker_db`
    Could not connect to the database. By default, it expects a local SQLite file:
    `sqlite:///speaker_db.sqlite`
    
    **How to fix this:**
    1. Make sure PostgreSQL is installed and running on your machine.
    2. Ensure a database named `speaker_db` exists.
    3. Update the credentials in `src/matcher.py` or set the `DATABASE_URL` environment variable.
    1. Check your folder permissions.
    2. Check the `DATABASE_URL` in `src/matcher.py`.
    """)
    st.stop()

# Helper to load audio robustly
def load_uploaded_audio(uploaded_file, target_sr=16000):
    audio_bytes = uploaded_file.read()
    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    if len(data.shape) > 1:
        data = data.mean(axis=1) # to mono
    if samplerate != target_sr:
        data = librosa.resample(data, orig_sr=samplerate, target_sr=target_sr)
    # Normalize
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))
    return data, target_sr

tab1, tab2, tab3 = st.tabs(["👤 1. Enroll Speaker", "🔍 2. Identify Speaker", "🗄️ 3. Database View"])

# ----------------------------
# TAB 1: ENROLLMENT
# ----------------------------
with tab1:
    st.header("Enroll a New Speaker")
    st.markdown("Upload a clear voice sample (e.g., 5 to 10 seconds of speech) to extract their unique vocal tract signature.")
    
    speaker_name = st.text_input("Speaker Name", placeholder="e.g., Alice")
    enroll_audio = st.file_uploader("Upload Audio for Enrollment", type=['wav', 'mp3', 'ogg'], key="enroll")
    
    if st.button("Save to Database"):
        if not speaker_name:
            st.warning("Please enter a name.")
        elif enroll_audio is None:
            st.warning("Please upload an audio file.")
        else:
            with st.spinner("Extracting features and saving to Postgres..."):
                data, sr = load_uploaded_audio(enroll_audio)
                
                # Use a session to interact with DB
                with SessionLocal() as session:
                    success = enroll_speaker(session, speaker_name, data, sr)
                    if success:
                        st.success(f"✅ Speaker '{speaker_name}' enrolled successfully!")
                
                # Show spectrogram so they see the "short spectra"
                st.markdown("**Extracted Short Spectra (Spectrogram):**")
                st.pyplot(plot_spectrogram(data, sr=sr, title=f"Voice Signature for {speaker_name}"))

# ----------------------------
# TAB 2: MATCHING
# ----------------------------
with tab2:
    st.header("Identify Unknown Audio")
    st.markdown("Upload a new audio clip and the system will compare its MFCC signature against everyone in the database using Cosine Similarity.")
    
    test_audio = st.file_uploader("Upload Unknown Audio", type=['wav', 'mp3', 'ogg'], key="test")
    
    if st.button("Identify Match"):
        if test_audio is None:
            st.warning("Please upload an audio file to test.")
        else:
            with st.spinner("Analyzing and querying database..."):
                data, sr = load_uploaded_audio(test_audio)
                
                with SessionLocal() as session:
                    match_name, similarity = identify_speaker(session, data, sr)
                    
                if match_name is None:
                    st.warning("No speakers enrolled in the database yet!")
                else:
                    # Convert cosine similarity (-1 to 1) to a percentage (0 to 100)
                    # For MFCCs, similarity is typically between 0.8 and 1.0 for matches
                    confidence = max(0, similarity) * 100
                    
                    st.subheader("Match Results")
                    col1, col2 = st.columns(2)
                    col1.metric("Predicted Speaker", match_name)
                    col2.metric("Similarity Score", f"{confidence:.2f}%")
                    
                    if confidence > 98.0:
                        st.success("🟢 High Confidence Match! This is almost certainly the same person.")
                    elif confidence > 95.0:
                        st.info("🟡 Medium Confidence Match. Likely the same person.")
                    else:
                        st.error("🔴 Low Confidence Match. The database might not contain this person, or the audio is too noisy.")
                    
                    st.markdown("**Unknown Audio Short Spectra:**")
                    st.pyplot(plot_spectrogram(data, sr=sr, title="Unknown Voice Signature"))

# ----------------------------
# TAB 3: DATABASE VIEW
# ----------------------------
with tab3:
    st.header("Enrolled Speakers Database")
    if st.button("Refresh Database View"):
        with SessionLocal() as session:
            speakers = session.query(Speaker).all()
            if not speakers:
                st.write("Database is empty.")
            else:
                for spk in speakers:
                    st.write(f"**ID:** {spk.id} | **Name:** {spk.name} | **Features Saved:** {len(spk.mfcc_features)} MFCC bands")

