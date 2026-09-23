import requests
import soundfile as sf
import io
import numpy as np
data = np.zeros(160000) # 10 seconds at 16k
sf.write('dummy.wav', data, 16000)
with open('dummy.wav', 'rb') as f:
    files = {'file': ('dummy.wav', f, 'audio/wav')}
    data = {'start': 1.0, 'end': 3.0}
    r = requests.post('http://127.0.0.1:8081/api/trim', files=files, data=data)
    print('Status:', r.status_code)
    out_data, out_sr = sf.read(io.BytesIO(r.content))
    print('Length:', len(out_data) / out_sr)
