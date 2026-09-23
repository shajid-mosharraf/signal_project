import soundfile as sf
import io
import numpy as np
buf = io.BytesIO()
try:
    sf.write(buf, np.zeros(0), 16000, format='WAV')
    print('Success', len(buf.getvalue()))
except Exception as e:
    print('Error:', e)
