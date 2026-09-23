import requests
import soundfile as sf
import numpy as np
# Create dummy wav
data = np.zeros(1000)
sf.write('dummy.wav', data, 16000)

with open('dummy.wav', 'rb') as f:
    files = {'file': ('dummy.wav', f, 'audio/wav')}
    data = {'start': 0, 'end': 0}
    r = requests.post('http://127.0.0.1:8081/api/trim', files=files, data=data)
    print(r.text)
