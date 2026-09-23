import streamlit as st
import streamlit.components.v1 as components

import base64
import os

@st.cache_data(show_spinner=False)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_custom_theme():
    """Injects massive custom CSS animations and a custom JS particle background."""
    
    # Load background image
    bg_img_path = os.path.join("assets", "bg_wave.jpg")
    if os.path.exists(bg_img_path):
        bg_ext = "jpg"
        bg_bin = get_base64_of_bin_file(bg_img_path)
        bg_style = f"background-image: url('data:image/{bg_ext};base64,{bg_bin}'); background-size: cover; background-position: center; background-repeat: no-repeat; background-attachment: fixed;"
    else:
        bg_style = "background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #1f4037, #99f2c8); background-size: 400% 400%; animation: GradientFlow 15s ease infinite;"
        
    # 1. Advanced CSS Animations
    custom_css = """
    <style>
    /* Global App Background - Intense Animated Gradient */
    /* Global App Background */
    .stApp {
        background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #1f4037, #99f2c8);
        background-size: 400% 400%;
        animation: GradientFlow 15s ease infinite;
        """ + bg_style + """
        color: #E0E0E0;
    }
    
    @keyframes GradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Hide default elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Animated Gradient Titles */
    h1, h2, h3 {
        background: linear-gradient(90deg, #00E5FF, #FF007F, #00FF88, #00E5FF);
        background-size: 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textShine 5s linear infinite;
        font-weight: 900 !important;
    }
    
    @keyframes textShine {
        to { background-position: 300%; }
    }
    
    /* Sidebar Animated Glass Background */
    [data-testid="stSidebar"] {
        background: rgba(10, 15, 25, 0.6) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(0, 229, 255, 0.2);
    }
    
    /* Floating Glassmorphism Main Panels */
    .stMainBlockContainer {
        background: rgba(15, 20, 30, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 40px !important;
        margin-top: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        animation: floatContainer 6s ease-in-out infinite;
    }
    
    @keyframes floatContainer {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
        100% { transform: translateY(0px); }
    }
    
    /* Neon Pulse Buttons */
    .stButton > button {
        background: linear-gradient(90deg, rgba(0,229,255,0.1), rgba(255,0,127,0.1));
        color: #00E5FF;
        border: 2px solid #00E5FF;
        border-radius: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #00E5FF, #FF007F);
        color: #fff;
        border-color: #FF007F;
        box-shadow: 0 0 20px #FF007F, 0 0 40px #00E5FF;
        transform: scale(1.05);
    }
    
    /* Metrics Hover Animation */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(0,0,0,0.6), rgba(20,20,30,0.6));
        border: 1px solid rgba(255, 0, 127, 0.3);
        padding: 20px;
        border-radius: 15px;
        transition: all 0.3s ease;
        border-bottom: 4px solid #FF007F;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-8px);
        box-shadow: 0 10px 20px rgba(255, 0, 127, 0.4);
        border-color: #00E5FF;
        border-bottom-color: #00E5FF;
    }
    
    /* Animated Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        transition: all 0.3s;
        border-bottom: 2px solid transparent;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, rgba(0,255,136,0.2), rgba(0,229,255,0.2)) !important;
        border-bottom: 2px solid #00FF88 !important;
        border-radius: 8px 8px 0 0;
        color: #00FF88 !important;
        transform: scale(1.02);
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # 2. Ambient Javascript Particle Animation (Injected via IFrame)
    js_particles = """
    <canvas id="particles"></canvas>
    <style>
        body, html { margin: 0; padding: 0; overflow: hidden; background: transparent; }
        canvas { position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; }
    </style>
    <script>
        const canvas = document.getElementById("particles");
        const ctx = canvas.getContext("2d");
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const particlesArray = [];
        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 3 + 1;
                this.speedX = Math.random() * 2 - 1;
                this.speedY = Math.random() * 2 - 1;
                this.color = Math.random() > 0.5 ? '#00E5FF' : '#FF007F';
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                if (this.size > 0.2) this.size -= 0.01;
            }
            draw() {
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        function handleParticles() {
            for (let i = 0; i < particlesArray.length; i++) {
                particlesArray[i].update();
                particlesArray[i].draw();
                if (particlesArray[i].size <= 0.2) {
                    particlesArray.splice(i, 1);
                    i--;
                }
            }
            if(particlesArray.length < 100) {
                particlesArray.push(new Particle());
            }
        }
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            handleParticles();
            requestAnimationFrame(animate);
        }
        animate();
    </script>
    """
    st.components.v1.html(
        js_particles + """
        <script>
            // Break out of Streamlit Iframe and apply to parent
            const parentDoc = window.parent.document;
            if(!parentDoc.getElementById('custom-particles-bg')) {
                const canvas = document.createElement('canvas');
                canvas.id = 'custom-particles-bg';
                canvas.style.position = 'fixed';
                canvas.style.top = '0';
                canvas.style.left = '0';
                canvas.style.width = '100vw';
                canvas.style.height = '100vh';
                canvas.style.pointerEvents = 'none';
                canvas.style.zIndex = '-1';
                parentDoc.body.prepend(canvas);
                
                const ctx = canvas.getContext('2d');
                function resize() {
                    canvas.width = window.innerWidth;
                    canvas.height = window.innerHeight;
                }
                window.parent.addEventListener('resize', resize);
                resize();
                
                const particlesArray = [];
                class Particle {
                    constructor() {
                        this.x = Math.random() * canvas.width;
                        this.y = Math.random() * canvas.height;
                        this.size = Math.random() * 3 + 1;
                        this.speedX = Math.random() * 1.5 - 0.75;
                        this.speedY = Math.random() * -2; // Float up
                        this.color = Math.random() > 0.5 ? 'rgba(0, 229, 255, 0.4)' : 'rgba(255, 0, 127, 0.4)';
                    }
                    update() {
                        this.x += this.speedX;
                        this.y += this.speedY;
                        if (this.size > 0.1) this.size -= 0.005;
                        if (this.y < 0) {
                            this.y = canvas.height;
                            this.size = Math.random() * 3 + 1;
                        }
                    }
                    draw() {
                        ctx.fillStyle = this.color;
                        ctx.beginPath();
                        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
                
                for(let i=0; i<150; i++) particlesArray.push(new Particle());
                
                function animate() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    for (let i = 0; i < particlesArray.length; i++) {
                        particlesArray[i].update();
                        particlesArray[i].draw();
                    }
                    window.parent.requestAnimationFrame(animate);
                }
                animate();
            }
        </script>
        """, 
        height=0
    )
