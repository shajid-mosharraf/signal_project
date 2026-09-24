import re
with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

nav_str = '<button class="nav-btn font-bold text-gray-400 hover:text-white" data-page="page-matcher">🔐 Speaker Matcher</button>'
if nav_str in html:
    html = html.replace(nav_str, nav_str + '\n                <button class="nav-btn font-bold text-gray-400 hover:text-white" data-page="page-vad">🎙️ Voice Activity Detector</button>')

vad_page = '''
        <!-- PAGE: VAD -->
        <div id="page-vad" class="page-content hidden">
            <div class="glass-panel p-8 rounded-2xl">
                <h2 class="text-3xl font-bold mb-4 text-cyan-400">🎙️ Voice Activity Detector (VAD)</h2>
                <p class="text-gray-300 mb-8">Detect speech and silence segments using Short-Time Energy (STE).</p>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <!-- Controls -->
                    <div class="bg-gray-800 p-6 rounded-xl col-span-1">
                        <h3 class="text-xl font-bold text-cyan-300 mb-4">1. Settings</h3>
                        <label class="text-gray-400 text-sm">Upload Audio:</label>
                        <input type="file" id="vad-audio" accept="audio/*" class="block w-full text-sm text-gray-400 mb-4 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-cyan-500 file:text-gray-900"/>
                        
                        <label class="text-gray-400 text-sm">Threshold Ratio (default 0.05):</label>
                        <input type="number" id="vad-thresh" step="0.01" value="0.05" class="w-full bg-gray-700 text-white p-2 rounded mb-4">
                        
                        <button id="vad-btn" class="w-full bg-cyan-500 hover:bg-cyan-400 text-gray-900 font-bold py-3 rounded-lg">Detect Activity</button>
                    </div>
                    
                    <!-- Results -->
                    <div class="bg-gray-800 p-6 rounded-xl col-span-1 md:col-span-2">
                        <h3 class="text-xl font-bold text-pink-300 mb-4">2. Analysis</h3>
                        <div id="vad-loading" class="hidden text-cyan-400 mb-4 animate-pulse">Analyzing audio...</div>
                        <img id="vad-plot" class="w-full rounded-xl hidden border border-gray-700 mb-6" alt="VAD Plot" />
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <h4 class="text-lg font-bold text-green-400 mb-2">Speech Segments</h4>
                                <ul id="vad-speech-list" class="text-sm text-gray-300 max-h-48 overflow-y-auto bg-gray-900 p-2 rounded"></ul>
                            </div>
                            <div>
                                <h4 class="text-lg font-bold text-gray-400 mb-2">Silent Segments</h4>
                                <ul id="vad-silence-list" class="text-sm text-gray-300 max-h-48 overflow-y-auto bg-gray-900 p-2 rounded"></ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div> <!-- End of PAGE: VAD -->
'''

if '<!-- PAGE: VAD -->' not in html:
    html = html.replace('<!-- End of PAGE: MATCHER -->', '<!-- End of PAGE: MATCHER -->\n' + vad_page)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

