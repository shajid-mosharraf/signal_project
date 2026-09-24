const audioUpload = document.getElementById('audio-upload');
const playerContainer = document.getElementById('player-container');
const mainAudio = document.getElementById('main-audio');
const resetBtn = document.getElementById('reset-btn');

let audioCtx;
let sourceNode;
let gainNode;
let eqNodes = [];
let currentFile = null;
let currentBlob = null;

// Initialize Audio Context on user interaction to bypass browser auto-play blocks
function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        sourceNode = audioCtx.createMediaElementSource(mainAudio);
        
        // Setup EQ and Gain
        gainNode = audioCtx.createGain();
        let prevNode = sourceNode;
        
        const freqs = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000];
        freqs.forEach(freq => {
            let filter = audioCtx.createBiquadFilter();
            filter.type = "peaking";
            filter.frequency.value = freq;
            filter.Q.value = 1.41;
            filter.gain.value = 0;
            prevNode.connect(filter);
            prevNode = filter;
            eqNodes.push(filter);
        });
        
        prevNode.connect(gainNode);
        gainNode.connect(audioCtx.destination);
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

// Handle File Upload
audioUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        currentFile = file;
        currentBlob = file;
        const url = URL.createObjectURL(file);
        mainAudio.src = url;
        playerContainer.classList.remove('hidden'); document.getElementById('editor-visuals').classList.add('hidden');
    }
});

mainAudio.addEventListener('play', initAudio);

// Tab Switching Logic
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        
        btn.classList.add('active');
        document.getElementById(btn.dataset.target).classList.remove('hidden');
    });
});

// UI: Volume
const volSlider = document.getElementById('vol-slider');
const volVal = document.getElementById('vol-val');
volSlider.addEventListener('input', (e) => {
    const v = parseFloat(e.target.value);
    volVal.innerText = v.toFixed(1);
    if(gainNode) gainNode.gain.value = v;
});

// REVERSE
document.getElementById('rev-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('rev-btn'); btn.innerText = 'Reversing...';
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav');
    try {
        const res = await fetch('/api/reverse', {method: 'POST', body: fd});
        if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
    btn.innerText = 'Reverse Audio';
});

// Backend: Phase Vocoder
document.getElementById('stretch-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('stretch-btn');
    btn.innerText = "Processing...";
    
    const formData = new FormData();
    formData.append("file", currentFile);
    formData.append("speed_factor", document.getElementById('speed-val').value);
    
    try {
        const res = await fetch("/api/phase_vocoder", { method: "POST", body: formData }); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob();
        currentBlob = blob;
        mainAudio.src = URL.createObjectURL(blob);
        mainAudio.play();
    } catch(err) {
        console.error(err);
        alert("Backend processing failed.");
    }
    btn.innerText = "Phase Vocoder (Keep Pitch)";
});

// Backend: Spectrogram
document.getElementById('spec-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    document.getElementById('spec-loading').classList.remove('hidden');
    document.getElementById('spec-img').classList.add('hidden');
    
    const formData = new FormData();
    formData.append("file", currentFile);
    formData.append("n_fft", document.getElementById('nfft-select').value);
    
    try {
        const res = await fetch("/api/spectrogram", { method: "POST", body: formData }); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const json = await res.json();
        const img = document.getElementById('spec-img');
        img.src = json.image;
        img.classList.remove('hidden');
    } catch(err) {
        console.error(err);
    }
    document.getElementById('spec-loading').classList.add('hidden');
});

// UI: EQ Faders Injection
const eqContainer = document.getElementById('eq-container');
const freqs = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000];
freqs.forEach((freq, idx) => {
    const col = document.createElement('div');
    col.className = 'flex flex-col items-center justify-center w-full';
    
    const valLabel = document.createElement('span');
    valLabel.className = 'text-xs mb-2 text-pink-400';
    valLabel.innerText = '0dB';
    
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.min = '-12';
    slider.max = '12';
    slider.value = '0';
    slider.setAttribute('orient', 'vertical');
    slider.className = 'accent-cyan-400 cursor-pointer';
    slider.style.appearance = 'slider-vertical';
    
    const freqLabel = document.createElement('span');
    freqLabel.className = 'text-xs mt-2 text-gray-400';
    freqLabel.innerText = freq + 'Hz';
    
    slider.addEventListener('input', (e) => {
        const v = e.target.value;
        valLabel.innerText = (v > 0 ? '+' : '') + v + 'dB';
        valLabel.className = v == 0 ? 'text-xs mb-2 text-pink-400' : 'text-xs mb-2 text-cyan-400';
        if(eqNodes.length > 0) {
            eqNodes[idx].gain.value = v;
        }
    });
    
    col.appendChild(valLabel);
    col.appendChild(slider);
    col.appendChild(freqLabel);
    eqContainer.appendChild(col);
});

// UI: EQ Presets
const presets = {
    'flat': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'bass': [10, 8, 6, 2, 0, 0, 0, 0, 0, 0],
    'treble': [0, 0, 0, 0, 0, -2, -4, -6, -8, -12]
};

document.querySelectorAll('.eq-preset').forEach(btn => {
    btn.addEventListener('click', () => {
        const p = presets[btn.dataset.preset];
        const sliders = eqContainer.querySelectorAll('input[type=range]');
        const labels = eqContainer.querySelectorAll('span:first-child');
        
        p.forEach((v, idx) => {
            sliders[idx].value = v;
            labels[idx].innerText = (v > 0 ? '+' : '') + v + 'dB';
            labels[idx].className = v == 0 ? 'text-xs mb-2 text-pink-400' : 'text-xs mb-2 text-cyan-400';
            if(eqNodes.length > 0) {
                eqNodes[idx].gain.value = v;
            }
        });
    });
});


// PAGE NAVIGATION
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-btn').forEach(b => { b.classList.remove('active', 'text-cyan-400'); b.classList.add('text-gray-400'); });
        document.querySelectorAll('.page-content').forEach(c => c.classList.add('hidden'));
        btn.classList.add('active', 'text-cyan-400');
        btn.classList.remove('text-gray-400');
        document.getElementById(btn.dataset.page).classList.remove('hidden');
    });
});

let enrollFile = null;
let testFile = null;
// SPEAKER MATCHER API
document.getElementById('enroll-btn').addEventListener('click', async () => {
    const name = document.getElementById('enroll-name').value;
    const file = enrollFile || document.getElementById('enroll-audio').files[0];
    if(!name || !file) return alert('Name and Audio required');
    const btn = document.getElementById('enroll-btn'); btn.innerText = 'Enrolling...';
    const fd = new FormData(); fd.append('name', name); fd.append('file', file);
    try {
        const res = await fetch('/api/matcher/enroll', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const data = await res.json();
        document.getElementById('enroll-status').innerText = data.message || data.error;
        document.getElementById('enroll-status').classList.remove('hidden');
    } catch(e) { console.error(e); }
    btn.innerText = 'Save to Database';
});

document.getElementById('test-btn').addEventListener('click', async () => {
    const file = testFile || document.getElementById('test-audio').files[0];
    if(!file) return alert('Audio required');
    const btn = document.getElementById('test-btn'); btn.innerText = 'Identifying...';
    const fd = new FormData(); fd.append('file', file);
    try {
        const res = await fetch('/api/matcher/identify', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const data = await res.json();
        document.getElementById('test-results').classList.remove('hidden');
        if(data.match_name) {
            document.getElementById('test-name').innerText = data.match_name;
            document.getElementById('test-score').innerText = data.confidence.toFixed(2) + '%';
        } else {
            document.getElementById('test-name').innerText = 'No Match Found';
            document.getElementById('test-score').innerText = '0%';
        }
    } catch(e) { console.error(e); }
    btn.innerText = 'Identify Match';
});

// ANALYSIS PLOTS
document.getElementById('analyze-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    document.getElementById('analysis-loading').classList.remove('hidden');
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav');
    try {
        const res = await fetch('/api/analysis/plots', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const data = await res.json();
        document.getElementById('wave-img').src = data.wave; document.getElementById('wave-img').classList.remove('hidden');
        document.getElementById('mag-img').src = data.mag; document.getElementById('mag-img').classList.remove('hidden');
    } catch(e) { console.error(e); }
    document.getElementById('analysis-loading').classList.add('hidden');
});

// FILTERS
document.getElementById('filter-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('filter-btn'); btn.innerText = 'Filtering...';
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav'); fd.append('f_type', document.getElementById('f-type').value); fd.append('f_order', 5); fd.append('cutoff_low', document.getElementById('f-cut').value);
    try {
        const res = await fetch('/api/filter', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
    btn.innerText = 'Apply Filter via Backend';
});

// CHANNEL
document.getElementById('channel-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('channel-btn'); btn.innerText = 'Simulating...';
        const fd = new FormData(); 
    fd.append('file', currentBlob, 'audio.wav'); 
    fd.append('taps', document.getElementById('ch-taps').value); 
    fd.append('snr', document.getElementById('ch-snr').value); 
    fd.append('add_mp', document.getElementById('ch-mp-check').checked); 
    fd.append('add_noise', document.getElementById('ch-awgn-check').checked);
    fd.append('add_inter', document.getElementById('ch-inter-check').checked);
    fd.append('inter_freq', document.getElementById('ch-inter-freq').value);
    fd.append('inter_snr', document.getElementById('ch-inter-snr').value);
    try {
        const res = await fetch('/api/channel', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
    btn.innerText = 'Simulate Channel (Backend)';
});

// EQUALIZE
document.getElementById('eq-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('eq-btn'); btn.innerText = 'Equalizing...';
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav'); fd.append('taps', document.getElementById('ch-taps').value); fd.append('snr', document.getElementById('ch-snr').value); fd.append('eq_type', document.getElementById('eq-type').value);
    try {
        const res = await fetch('/api/equalize', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
    btn.innerText = '??? Recover Audio (Apply Equalizer)';
});

// TRIM
document.getElementById('trim-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('trim-btn'); btn.innerText = 'Trimming...';
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav'); fd.append('start', document.getElementById('trim-start').value || 0); fd.append('end', document.getElementById('trim-end').value || 0);
    try {
        const res = await fetch('/api/trim', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); } if(!res.ok) { alert(await res.text()); throw new Error('Backend error'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
    btn.innerText = 'Trim';
});

// ECHO
document.getElementById('echo-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('echo-btn'); btn.innerText = 'Adding Echo...';
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav'); fd.append('delay_ms', document.getElementById('echo-delay').value); fd.append('decay', document.getElementById('echo-decay').value); fd.append('echoes', document.getElementById('echo-count').value);
    try {
        const res = await fetch('/api/echo', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
    btn.innerText = 'Add Echo (Backend)';
});

// RESAMPLE
document.getElementById('resample-btn').addEventListener('click', async () => {
    if(!currentFile) return;
    const btn = document.getElementById('resample-btn'); btn.innerText = 'Resampling...';
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav'); fd.append('speed_factor', document.getElementById('speed-val').value);
    try {
        const res = await fetch('/api/resample', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
    btn.innerText = 'Resample (Chipmunk)';
});

// ALIASING
async function applyAliasing(proper) {
    if(!currentFile) return;
    const fd = new FormData(); fd.append('file', currentBlob, 'audio.wav'); fd.append('factor', document.getElementById('alias-factor').value); fd.append('proper', proper);
    try {
        const res = await fetch('/api/alias', {method: 'POST', body: fd}); if(!res.ok) { alert('Backend Error: ' + await res.text()); throw new Error('Backend failed'); }
        const blob = await res.blob(); updateEditorPlots(currentBlob, blob); currentBlob = blob; mainAudio.src = URL.createObjectURL(blob); mainAudio.play();
    } catch(e) {}
}
document.getElementById('alias-proper-btn').addEventListener('click', () => applyAliasing(true));
document.getElementById('alias-bad-btn').addEventListener('click', () => applyAliasing(false));






resetBtn.addEventListener('click', () => { document.getElementById('editor-visuals').classList.add('hidden'); 
    if(currentFile) {
        currentBlob = currentFile;
        mainAudio.src = URL.createObjectURL(currentFile);
        mainAudio.play();
    }
});






async function updateEditorPlots(oldBlob, newBlob) {
    document.getElementById('editor-visuals').classList.remove('hidden');
    document.getElementById('plot-before').src = ''; document.getElementById('plot-after').src = '';
    const fd = new FormData();
    fd.append('file_before', oldBlob, 'before.wav');
    fd.append('file_after', newBlob, 'after.wav');
    try {
        const res = await fetch('/api/compare_plots', {method: 'POST', body: fd});
        const data = await res.json();
        document.getElementById('plot-before').src = data.before;
        document.getElementById('plot-after').src = data.after;
    } catch(e) { console.error('Plotting failed', e); }
}




// =====================================
// VOICE ACTIVITY DETECTOR (VAD)
// =====================================
let vadFile = null;

document.getElementById('vad-audio').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        vadFile = file;
        const player = document.getElementById('vad-audio-player');
        player.src = URL.createObjectURL(file);
        player.classList.remove('hidden');
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


// =====================================
// MICROPHONE RECORDER (WITH NATIVE WAV ENCODING)
// =====================================
let mediaRecorder;
let audioChunks = [];

const recordStartBtn = document.getElementById('record-start-btn');
const recordStopBtn = document.getElementById('record-stop-btn');
const recordIndicator = document.getElementById('record-indicator');

if (recordStartBtn) {
    recordStartBtn.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });
            
            mediaRecorder.addEventListener('stop', async () => {
                const webmBlob = new Blob(audioChunks);
                
                // Decode WebM/Ogg to raw AudioBuffer using AudioContext
                const actx = new (window.AudioContext || window.webkitAudioContext)();
                const arrayBuffer = await webmBlob.arrayBuffer();
                const audioBuffer = await actx.decodeAudioData(arrayBuffer);
                
                // Encode raw AudioBuffer to standard WAV using helper function below
                const wavBuffer = audioBufferToWav(audioBuffer, {float32: false});
                const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
                
                // Feed the newly created WAV into our existing pipeline!
                const file = new File([wavBlob], "microphone_recording.wav", { type: 'audio/wav' });
                currentFile = file; currentBlob = file; mainAudio.src = URL.createObjectURL(file); playerContainer.classList.remove('hidden'); document.getElementById('editor-visuals').classList.add('hidden');
                
                // Clean up tracks
                stream.getTracks().forEach(track => track.stop());
            });
            
            mediaRecorder.start();
            
            recordStartBtn.classList.add('hidden');
            recordStopBtn.classList.remove('hidden');
            recordIndicator.classList.remove('hidden');
            
        } catch (err) {
            alert('Microphone access denied or not available: ' + err);
        }
    });

    recordStopBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        recordStopBtn.classList.add('hidden');
        recordStartBtn.classList.remove('hidden');
        recordIndicator.classList.add('hidden');
    });
}

// Minimal WAV encoder helper
function audioBufferToWav(buffer, opt) {
    opt = opt || {};
    var numChannels = buffer.numberOfChannels;
    var sampleRate = buffer.sampleRate;
    var format = opt.float32 ? 3 : 1;
    var bitDepth = format === 3 ? 32 : 16;
    
    var result;
    if (numChannels === 2) {
        var inputL = buffer.getChannelData(0);
        var inputR = buffer.getChannelData(1);
        var length = inputL.length + inputR.length;
        result = new Float32Array(length);
        var index = 0, inputIndex = 0;
        while (index < length) {
            result[index++] = inputL[inputIndex];
            result[index++] = inputR[inputIndex];
            inputIndex++;
        }
    } else {
        result = buffer.getChannelData(0);
    }
    
    var bytesPerSample = bitDepth / 8;
    var blockAlign = numChannels * bytesPerSample;
    var outBuffer = new ArrayBuffer(44 + result.length * bytesPerSample);
    var view = new DataView(outBuffer);
    
    function writeString(view, offset, string) {
        for (var i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }
    
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + result.length * bytesPerSample, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, format, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * blockAlign, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitDepth, true);
    writeString(view, 36, 'data');
    view.setUint32(40, result.length * bytesPerSample, true);
    
    var offset = 44;
    for (var i = 0; i < result.length; i++, offset += 2) {
        var s = Math.max(-1, Math.min(1, result[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    
    return outBuffer;
}



// =====================================
// REUSABLE MICROPHONE RECORDER LOGIC
// =====================================
function setupMicRecorder(prefix, onWavReady) {
    const startBtn = document.getElementById(`${prefix}-record-btn`);
    const stopBtn = document.getElementById(`${prefix}-stop-btn`);
    const indicator = document.getElementById(`${prefix}-indicator`);
    let localMediaRecorder;
    let localAudioChunks = [];

    if (!startBtn) return;

    startBtn.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            localMediaRecorder = new MediaRecorder(stream);
            localAudioChunks = [];
            
            localMediaRecorder.addEventListener('dataavailable', event => {
                localAudioChunks.push(event.data);
            });
            
            localMediaRecorder.addEventListener('stop', async () => {
                const webmBlob = new Blob(localAudioChunks);
                const actx = new (window.AudioContext || window.webkitAudioContext)();
                const arrayBuffer = await webmBlob.arrayBuffer();
                const audioBuffer = await actx.decodeAudioData(arrayBuffer);
                const wavBuffer = audioBufferToWav(audioBuffer, {float32: false});
                const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
                const file = new File([wavBlob], `mic_${prefix}.wav`, { type: 'audio/wav' });
                
                onWavReady(file);
                stream.getTracks().forEach(track => track.stop());
            });
            
            localMediaRecorder.start();
            startBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
            indicator.classList.remove('hidden');
        } catch (err) {
            alert('Microphone access denied: ' + err);
        }
    });

    stopBtn.addEventListener('click', () => {
        if (localMediaRecorder && localMediaRecorder.state !== 'inactive') {
            localMediaRecorder.stop();
        }
        stopBtn.classList.add('hidden');
        startBtn.classList.remove('hidden');
        indicator.classList.add('hidden');
    });
}

// Setup the additional microphones:
setupMicRecorder('enroll', (file) => { 
    enrollFile = file; 
    const player = document.getElementById('enroll-audio-player');
    player.src = URL.createObjectURL(file);
    player.classList.remove('hidden');
});
setupMicRecorder('test', (file) => { 
    testFile = file; 
    const player = document.getElementById('test-audio-player');
    player.src = URL.createObjectURL(file);
    player.classList.remove('hidden');
});
setupMicRecorder('vad', (file) => { 
    vadFile = file; 
    const player = document.getElementById('vad-audio-player');
    player.src = URL.createObjectURL(file);
    player.classList.remove('hidden');
});



// =====================================
// SPEAKER MATCHER DATABASE VIEWER
// =====================================
async function loadSpeakerDatabase() {
    const dbLoading = document.getElementById('db-loading');
    const dbList = document.getElementById('db-list');
    const dbEmpty = document.getElementById('db-empty');
    if (!dbLoading) return;
    
    dbLoading.classList.remove('hidden');
    dbList.innerHTML = '';
    
    try {
        const res = await fetch('/api/matcher/list');
        const data = await res.json();
        
        if (data.speakers && data.speakers.length > 0) {
            dbEmpty.classList.add('hidden');
            data.speakers.forEach(speaker => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td class="py-2">${speaker.id}</td><td class="py-2 text-cyan-400 font-bold">${speaker.name}</td>`;
                dbList.appendChild(tr);
            });
        } else {
            dbEmpty.classList.remove('hidden');
        }
    } catch(e) {
        console.error(e);
    }
    dbLoading.classList.add('hidden');
}

if (document.getElementById('db-refresh-btn')) {
    document.getElementById('db-refresh-btn').addEventListener('click', loadSpeakerDatabase);
    // Load once on startup if button exists
    loadSpeakerDatabase();
}
