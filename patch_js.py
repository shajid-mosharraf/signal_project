import re

with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

vad_js = '''
// =====================================
// VOICE ACTIVITY DETECTOR (VAD)
// =====================================
let vadFile = null;

document.getElementById('vad-audio').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        vadFile = file;
    }
});

document.getElementById('vad-btn').addEventListener('click', async () => {
    if(!vadFile) { alert("Please upload audio for VAD first."); return; }
    
    const btn = document.getElementById('vad-btn');
    btn.innerText = 'Analyzing...';
    document.getElementById('vad-loading').classList.remove('hidden');
    document.getElementById('vad-plot').classList.add('hidden');
    
    const fd = new FormData();
    fd.append('file', vadFile);
    fd.append('threshold', document.getElementById('vad-thresh').value || 0.05);
    
    try {
        const res = await fetch('/api/vad/analyze', {method: 'POST', body: fd});
        if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        
        const data = await res.json();
        
        document.getElementById('vad-plot').src = data.plot;
        document.getElementById('vad-plot').classList.remove('hidden');
        
        const speechList = document.getElementById('vad-speech-list');
        speechList.innerHTML = '';
        data.speech.forEach(seg => {
            const li = document.createElement('li');
            li.innerText = `${seg.start.toFixed(3)}s - ${seg.end.toFixed(3)}s`;
            speechList.appendChild(li);
        });
        
        const silenceList = document.getElementById('vad-silence-list');
        silenceList.innerHTML = '';
        data.silence.forEach(seg => {
            const li = document.createElement('li');
            li.innerText = `${seg.start.toFixed(3)}s - ${seg.end.toFixed(3)}s`;
            silenceList.appendChild(li);
        });
        
    } catch (e) {
        console.error(e);
    }
    
    document.getElementById('vad-loading').classList.add('hidden');
    btn.innerText = 'Detect Activity';
});
'''

if 'VOICE ACTIVITY DETECTOR (VAD)' not in js:
    with open('static/app.js', 'a', encoding='utf-8') as f:
        f.write('\n' + vad_js)

