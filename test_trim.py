import requests
with open('speaker_db.sqlite', 'rb') as f:
    files = {'file': ('test.wav', f, 'audio/wav')}
    data = {'start': 0, 'end': 0}
    r = requests.post('http://127.0.0.1:8080/api/trim', files=files, data=data)
    print(r.status_code)
