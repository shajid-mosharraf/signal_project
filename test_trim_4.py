import soundfile as sf
import io
import numpy as np
data = np.zeros(100)
buf = io.BytesIO()
sf.write(buf, data, 16000, format='WAV')
print('Size 1:', len(buf.getvalue()))
data2, sr = sf.read(io.BytesIO(buf.getvalue()))
buf2 = io.BytesIO()
sf.write(buf2, data2, sr, format='WAV')
print('Size 2:', len(buf2.getvalue()))
