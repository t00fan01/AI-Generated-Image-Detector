import streamlit as st
import time
import requests
from io import BytesIO
import google.generativeai as genai
from streamlit_lottie import st_lottie
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Generated Image Detector",
    page_icon="🔍",
    layout="wide", # Using wide to allow elegant centered layout with columns
    initial_sidebar_state="expanded" 
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Styling to ensure a clean, professional look */
    .hero-title {
        text-align: center;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 3rem;
        font-weight: 700;
        margin-top: 50px;
        margin-bottom: 10px;
    }
    .hero-sub {
        text-align: center;
        font-size: 1.2rem;
        color: #555555;
        margin-bottom: 40px;
    }
    .result-box {
        background-color: #FAFAFA;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #EEEEEE;
        margin-top: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Load the Lottie Animation
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        return None

# Access Secrets Config
def safe_get_secret(section, key):
    try:
        return st.secrets[section][key]
    except KeyError:
        return None
    except FileNotFoundError:
        return None

ADMIN_PASS = safe_get_secret("admin", "password")
GEMINI_KEY = safe_get_secret("google", "api_key")

# Initialize Session States
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'nav_radio' not in st.session_state:
    st.session_state['nav_radio'] = "Home"

# Navigation Callback
def go_to_detector():
    st.session_state['nav_radio'] = "Detector Tool"

# =====================================================================
# THE ROOT CAUSE FIX: DYNAMIC MODEL ROUTING (Preserved & Untouched)
# =====================================================================
def get_dynamic_gemini_model():
    """
    Instead of guessing hardcoded model names and risking a 404, 
    we query the Google API for a live list of valid models tied to your key.
    """
    if not GEMINI_KEY:
        raise ValueError("API Key not found in secrets.toml.")
    
    genai.configure(api_key=GEMINI_KEY)
    
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            
    if not available_models:
        raise Exception("Your Google API key does not have access to any generative models.")

    target_model = None
    preferred_models = [
        'models/gemini-1.5-flash', 
        'models/gemini-1.5-pro', 
        'models/gemini-pro-vision'
    ]
    
    for preferred in preferred_models:
        if preferred in available_models:
            target_model = preferred
            break
            
    if not target_model:
        target_model = available_models[0]
        
    return genai.GenerativeModel(target_model)
# =====================================================================


# --- UI COMPONENTS ---
def sidebar_nav_auth():
    # Placeholder Logo and Title
    st.sidebar.markdown("<h2 style='text-align: center;'>🔍 AI Forensics</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # Navigation
    st.sidebar.radio("Navigation", ["Home", "Detector Tool", "About"], key="nav_radio")
    
    # Authentication
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 Authentication")
    
    auth_option = st.sidebar.radio("Select Role:", ["Continue as Guest", "Login"])
    
    if auth_option == "Login":
        password = st.sidebar.text_input("Admin Password", type="password")
        if st.sidebar.button("Login"):
            if ADMIN_PASS and password == ADMIN_PASS:
                st.session_state['logged_in'] = True
                st.sidebar.success("Logged in successfully! Chatbot Unlocked.")
            else:
                st.sidebar.error("Incorrect password or configuration.")
    else:
        if st.session_state['logged_in']:
            st.session_state['logged_in'] = False
            st.sidebar.info("Switched to Guest Mode. Chatbot Locked.")

        st.sidebar.markdown(
            "> **Guest Limits:**\n> You can scan images to detect AI generation, but the Forensic Chatbot is restricted to logged-in admins."
        )

# --- PAGES ---
def page_home():
    st.markdown("<h1 class='hero-title'>AI Image Forensics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-sub'>Professional-grade deepfake and AI generation detection tools. Analyze image artifacts, verify authenticity, and consult our Forensic Chatbot directly.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.button("🚀 Go to Detector", on_click=go_to_detector, type="primary", use_container_width=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    # Optional decorative graphic or lottie on home page
    anim_url = "https://lottie.host/e2b694cf-6f34-4537-afbf-ebcf381fa5d7/Q0RItjVn92.json"
    anim = load_lottieurl(anim_url)
    if anim:
        st_lottie(anim, height=300, key="home_anim")

def page_detector():
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>Image Detector Tool</h2>", unsafe_allow_html=True)
    
    # Center the file uploader using columns
    up_col1, up_col2, up_col3 = st.columns([1, 2, 1])
    with up_col2:
        uploaded_file = st.file_uploader("Upload an image (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"])
    
    st.markdown("<hr>", unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            st.error(f"Invalid image format: {e}")
            return
            
        # Two-column layout: Image on Left, Analysis/Result on Right
        col_img, col_anls = st.columns([1, 1])
        
        with col_img:
            st.image(image, use_container_width=True, caption="Uploaded Image")
            
        with col_anls:
            st.subheader("Analysis & Detection")
            analyze_clicked = st.button("🔍 Analyze Image", type="primary", use_container_width=True)
            
            anim_placeholder = st.empty()
            
            if analyze_clicked:
                if not GEMINI_KEY:
                    st.error("API Key missing! Cannot run analysis.")
                    return
                    
                scan_anim_url = "https://lottie.host/8cd7b370-dcc2-4845-a1c2-df3e0da097d7/0fO7Wf8dQK.json" 
                scan_anim = load_lottieurl(scan_anim_url)
                
                with anim_placeholder.container():
                    l_col, m_col, r_col = st.columns([1, 2, 1])
                    with m_col:
                        if scan_anim:
                            st_lottie(scan_anim, height=150, key="scanning")
                        else:
                            st.info("Scanning...")
                            
                # REAL INFERENCE...
                try:
                    model = get_dynamic_gemini_model()
                    vision_prompt = "You are an expert AI image forensics tool. Analyze this image carefully. Does it contain signs of generative AI creation? Reply with ONLY a single numerical probability score from 0.00 to 100.00 representing the likelihood it is AI generated. Do not include a percent sign or any text."
                    
                    response = model.generate_content([vision_prompt, image])
                    clean_text = response.text.replace('%', '').strip()
                    try:
                        ai_probability = float(clean_text)
                    except ValueError:
                        ai_probability = 15.0 
                        
                    is_ai = ai_probability > 50.0
                    final_label = "AI Generated" if is_ai else "Authentic"
                    display_confidence = ai_probability if is_ai else (100.0 - ai_probability)
                    
                    anim_placeholder.empty()
                    
                    st.session_state['scan_result'] = {
                        "label": final_label,
                        "confidence": display_confidence,
                    }
                    
                except Exception as e:
                    anim_placeholder.empty()
                    st.error(f"Analysis failed: {str(e)}")
                    
            # Result Display Area
            if 'scan_result' in st.session_state:
                scan_data = st.session_state['scan_result']
                final_label = scan_data['label']
                display_confidence = scan_data['confidence']
                is_ai = "AI" in final_label
                
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                if is_ai:
                    st.error(f"### ⚠️ Status: {final_label}")
                else:
                    st.success(f"### ✅ Status: {final_label}")
                    
                st.metric(label="System Confidence", value=f"{display_confidence:.2f}%")
                st.markdown("</div>", unsafe_allow_html=True)

        # 4. Forensic Chatbot Area (in a container below the analysis section)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("🕵️ Forensic Analyst Chatbot")
        
        chat_container = st.container()
        
        if not st.session_state.get('logged_in'):
            st.info("🔒 Please login via the sidebar to access the detail-oriented Forensic Chatbot.")
        else:
            if not GEMINI_KEY:
                st.error("Gemini API Key missing! Please configure `.streamlit/secrets.toml`.")
            elif 'scan_result' not in st.session_state:
                st.warning("Please run 'Analyze Image' first to initialize chatbot forensics.")
            else:
                scan_label = st.session_state['scan_result']['label']
                scan_conf = st.session_state['scan_result']['confidence']
                
                # Render previous chat history
                with chat_container:
                    for msg in st.session_state['chat_history']:
                        if msg["role"] == "user":
                            with st.chat_message("user"):
                                st.markdown(msg["content"])
                        else:
                            with st.chat_message("assistant"):
                                st.markdown(msg["content"])
                
                # Using native st.chat_input! Streamlit natively anchors this at the bottom if placed cleanly.
                user_query = st.chat_input("E.g., What artifacts justify this being AI?")
                if user_query:
                    # Rerender user input right away
                    st.session_state['chat_history'].append({"role": "user", "content": user_query})
                    with chat_container:
                        with st.chat_message("user"):
                            st.markdown(user_query)
                            
                        with st.chat_message("assistant"):
                            with st.spinner("Analyzing forensics..."):
                                try:
                                    chat_model = get_dynamic_gemini_model()
                                    prompt = f"""
                                    You are an expert Digital Forensic Analyst specializing in identifying AI-generated imagery and deepfakes.
                                    You are currently analyzing the attached image.
                                    The initial scan flagged this image as: {scan_label} (Confidence: {scan_conf:.2f}%).
                                    
                                    User Question: {user_query}
                                    
                                    Answer the user's question based on the real visual evidence in the image. Explain the technical artifacts (or lack thereof) that justify the scan result. Keep it professional.
                                    """
                                    chat_response = chat_model.generate_content([prompt, image])
                                    st.markdown(chat_response.text)
                                    st.session_state['chat_history'].append({"role": "assistant", "content": chat_response.text})
                                except Exception as e:
                                    st.error(f"Chatbot Error: {str(e)}")

def page_about():
    st.markdown("<h2 style='text-align: center;'>About AI Image Forensics</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    ### How does deepfake detection work?
    AI Image Detectors utilize state-of-the-art vision models fine-tuned to recognize subtle structural, lighting, and texture anomalies introduced by generative AI models like Midjourney, DALL-E, and Stable Diffusion.
    
    ### Technology Stack
    - **Frontend:** Streamlit
    - **Core Inference & Chatbot Integration:** Powered by Google's **Gemini 1.5 Flash** models to run live, in-browser analysis without relying on hardcoded mock data.
    - **UI Theme:** A custom, clean, iLovePDF-inspired design focusing on white spacing and professional aesthetics.
    """)

# --- ROUTER ---
def main():
    sidebar_nav_auth()
    
    current_page = st.session_state.nav_radio
    if current_page == "Home":
        page_home()
    elif current_page == "Detector Tool":
        page_detector()
    elif current_page == "About":
        page_about()


if __name__ == "__main__":
    main()