import os
import sys
import subprocess

# --- JALUR BYPASS FFmpeg ---
# Kode ini memaksa Python mengenali folder di D:/ffmpeg/bin milikmu
# ffmpeg_bin_path = r'D:\ffmpeg\bin'
# os.environ["PATH"] += os.pathsep + ffmpeg_bin_path

# Tambahan khusus untuk library MoviePy agar tidak bingung
import moviepy.config as mp_config
# mp_config.FFMPEG_BINARY = os.path.join(ffmpeg_bin_path, "ffmpeg.exe")

import streamlit as st
import whisper
import yt_dlp
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip
from datetime import datetime
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState

def seconds_to_srt_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"

# --- KONTROL LAYOUT ---
st.set_page_config(page_title="AI Video Compositor Pro", layout="wide", page_icon="🎬")

# --- CSS CUSTOM UNTUK TAMPILAN PROFESIONAL ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0.8); }
    .stButton>button { background: linear-gradient(45deg, #FF6B6B, #4ECDC4); color: white; border: none; border-radius: 25px; padding: 10px 20px; font-weight: bold; transition: all 0.3s ease; }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select { background-color: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 10px; }
    .stSidebar { background: rgba(0,0,0,0.8); border-right: 2px solid #4ECDC4; }
    .css-1d391kg { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px; }
    h1, h2, h3 { color: #4ECDC4; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
    </style>
    """, unsafe_allow_html=True)

# --- MENU SETELAN (POJOK KANAN ATAS) ---
header_left, header_right = st.columns([8, 2])

with header_right:
    with st.popover("⚙️ Settings & Branding"):
        st.subheader("🤖 AI Configuration")
        ai_model = st.selectbox("Model Whisper", ["tiny", "base", "small"], index=1)

        st.divider()
        st.subheader("🖼️ Branding Logo")
        logo_file = st.file_uploader("Upload Logo (PNG)", type=["png"])
        logo_size = st.slider("Ukuran Logo", 50, 250, 100)
        logo_pos = st.selectbox("Posisi Logo", ["Top-Right", "Top-Left", "Bottom-Right", "Bottom-Left"])

        st.divider()
        st.subheader("✍️ Headline Style")
        headline_text = st.text_input("Teks Headline (Atas)", "TIPS HARI INI")
        head_color = st.color_picker("Warna Headline", "#FFFFFF")
        head_bg = st.color_picker("Warna Background Headline", "#FF0000")

# --- MENU UTAMA ---
with header_left:
    st.title("🎬 AI Video Compositor Pro")
    st.caption("Node-based video editing like Nuke - Professional workflow for content creators")

st.divider()

# --- NODE EDITOR ---
st.header("🎯 Node-Based Video Compositor")

# Initialize session state for nodes
if 'nodes' not in st.session_state:
    st.session_state.nodes = [
        StreamlitFlowNode(id='input', pos=(100, 100), data={'label': '📥 Input Video'}, node_type='input', source_position='right'),
        StreamlitFlowNode(id='cut', pos=(300, 100), data={'label': '✂️ Cut/Trim'}, node_type='default', source_position='right', target_position='left'),
        StreamlitFlowNode(id='text', pos=(500, 50), data={'label': '📝 Add Text'}, node_type='default', source_position='right', target_position='left'),
        StreamlitFlowNode(id='logo', pos=(500, 150), data={'label': '🏷️ Add Logo'}, node_type='default', source_position='right', target_position='left'),
        StreamlitFlowNode(id='output', pos=(700, 100), data={'label': '🎬 Render Output'}, node_type='output', target_position='left'),
    ]

if 'edges' not in st.session_state:
    st.session_state.edges = []

# Node editor interface
col_editor, col_properties = st.columns([3, 1])

with col_editor:
    st.subheader("Node Graph")
    flow_state = streamlit_flow(
        st.session_state.nodes,
        st.session_state.edges,
        fit_view=True,
        height=400,
        show_controls=True,
        show_mini_map=True,
    )
    # Update session state to persist changes
    st.session_state.nodes = flow_state.nodes
    st.session_state.edges = flow_state.edges

with col_properties:
    st.subheader("Node Properties")

    # Initialize defaults to prevent NameError
    start_sec, end_sec = 0, 10
    text_content, text_color, bg_color = "TIPS HARI INI", "#FFFFFF", "#FF0000"
    logo_upload, logo_size, logo_pos = None, 100, "Top-Right"

    # Input Node Properties
    if any(node.id == 'input' for node in flow_state.nodes):
        with st.expander("📥 Input Video Settings"):
            source_type = st.radio("Source:", ["YouTube Link", "Upload Manual"], key="input_source")
            if source_type == "YouTube Link":
                url = st.text_input("YouTube URL:", key="input_url")
                if st.button("Download", key="download_btn"):
                    with st.spinner("Downloading..."):
                        ydl_opts = {'format': 'mp4', 'outtmpl': 'input_video.mp4', 'quiet': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                        st.success("Downloaded!")
            else:
                uploaded = st.file_uploader("Upload Video:", type=["mp4", "mov"], key="input_upload")
                if uploaded:
                    with open("input_video.mp4", "wb") as f:
                        f.write(uploaded.getbuffer())
                    st.success("Uploaded!")

    # Cut Node Properties
    if any(node.id == 'cut' for node in flow_state.nodes):
        with st.expander("✂️ Cut/Trim Settings"):
            start_sec = st.number_input("Start (sec):", 0.0, key="cut_start")
            end_sec = st.number_input("End (sec):", start_sec + 1, key="cut_end")

    # Text Node Properties
    if any(node.id == 'text' for node in flow_state.nodes):
        with st.expander("📝 Text Settings"):
            text_content = st.text_input("Text:", "TIPS HARI INI", key="text_content")
            text_color = st.color_picker("Text Color:", "#FFFFFF", key="text_color")
            bg_color = st.color_picker("Background:", "#FF0000", key="text_bg")

    # Logo Node Properties
    if any(node.id == 'logo' for node in flow_state.nodes):
        with st.expander("🏷️ Logo Settings"):
            logo_upload = st.file_uploader("Upload Logo:", type=["png"], key="logo_upload")
            logo_size = st.slider("Size:", 50, 250, 100, key="logo_size")
            logo_pos = st.selectbox("Position:", ["Top-Right", "Top-Left", "Bottom-Right", "Bottom-Left"], key="logo_pos")

# --- RENDER BUTTON ---
st.divider()
col_render, col_preview = st.columns([1, 2])

with col_render:
    if st.button("🚀 RENDER COMPOSITION", use_container_width=True, type="primary"):
        if os.path.exists("input_video.mp4"):
            with st.status("🎨 Compositing video...", expanded=True) as status:
                # Load base video
                clip = VideoFileClip("input_video.mp4")

                # Apply cut if connected
                if any(edge.target == 'cut' for edge in flow_state.edges):
                    clip = clip.subclip(start_sec, end_sec)

                # Reframe to portrait
                w, h = clip.size
                target_w = h * 9/16
                target_w = int(h * 9/16)
                clip = clip.crop(x_center=w/2, width=target_w)

                layers = [clip]

                # Add text if connected
                if any(edge.target == 'text' for edge in flow_state.edges):
                    try:
                        txt = TextClip(text_content, fontsize=40, color=text_color, bg_color=bg_color,
                                       font='Arial-Bold', method='caption', size=(target_w, 100))
                        txt = txt.set_pos(('center', 'top')).set_duration(clip.duration)
                        layers.append(txt)
                    except Exception as e:
                        st.warning(f"Text rendering failed: {e}. Ensure ImageMagick is installed.")

                # Add logo if connected
                if any(edge.target == 'logo' for edge in flow_state.edges) and logo_upload:
                    with open("logo.png", "wb") as f:
                        f.write(logo_upload.getbuffer())
                    logo = (ImageClip("logo.png")
                            .resize(width=logo_size)
                            .set_duration(clip.duration))

                    pos_map = {"Top-Right": ("right", "top"), "Top-Left": ("left", "top"),
                               "Bottom-Right": ("right", "bottom"), "Bottom-Left": ("left", "bottom")}
                    logo = logo.set_pos(pos_map[logo_pos])
                    layers.append(logo)

                # Render final composition
                final = CompositeVideoClip(layers)
                output_file = "composition_output.mp4"
                final.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=24)

                status.update(label="✨ Composition Complete!", state="complete")

with col_preview:
    if os.path.exists("composition_output.mp4"):
        st.subheader("🎥 Final Composition")
        st.video("composition_output.mp4")
        st.download_button("📥 Download Video", open("composition_output.mp4", "rb"), "video_composition.mp4")

        # SRT for connected text
        if any(edge.target == 'text' for edge in flow_state.edges):
            duration = end_sec - start_sec if 'end_sec' in locals() else 30
            srt_text = f"1\n00:00:00,000 --> {seconds_to_srt_time(duration)}\n{text_content}"
            st.download_button("📄 Download SRT (CapCut)", srt_text, "subtitles.srt")
    else:
        st.info("Connect nodes and render your composition!")
