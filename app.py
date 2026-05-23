import streamlit as st
import os
import tempfile
import asyncio
import edge_tts
from groq import Groq

# Cấu hình trang web
st.set_page_config(page_title="AI Audio Toolset", page_icon="⚡", layout="wide")
st.title("⚡ AI Audio Toolset (Two-Way MVP)")

# Khởi tạo state để lưu dữ liệu giữa các lần render
if "raw_text" not in st.session_state:
    st.session_state.raw_text = None

# --- CẤU HÌNH API KEY CHUNG ---
st.sidebar.subheader("🔑 Cấu hình Hệ thống")
api_key = st.sidebar.text_input("Nhập Groq API Key:", type="password", help="Chỉ dùng cho tính năng Video ➔ Text")

# --- PHÂN CHIA TAB UI ---
tab1, tab2 = st.tabs(["🎙️ Chiều 1: Video ➔ Text", "🔊 Chiều 2: Text ➔ Audio"])

# =====================================================================
# TAB 1: VIDEO TO TEXT (WHISPER LARGE-V3)
# =====================================================================
with tab1:
    st.header("🎙️ Chuyển đổi Video/Audio thành Văn bản")
    
    # Khu vực nhập link TikTok (Tạm thời khóa như kế hoạch)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("Link TikTok (Feature đang phát triển):", disabled=True, key="tk_link")
    with col2:
        st.button("Tải & Dịch", disabled=True, use_container_width=True, key="tk_btn")
        
    # Khu vực Upload File
    uploaded_file = st.file_uploader("Upload file Video/Audio của bạn:", type=["mp4", "mp3", "wav", "m4a"], key="v2t_uploader")
    
    if uploaded_file is not None:
        if not api_key:
            st.warning("⚠️ Vui lòng điền Groq API Key ở thanh bên trái (Sidebar).")
        else:
            if st.button("🚀 Bắt đầu bóc băng", type="primary", key="v2t_btn"):
                with st.spinner("Groq đang bóc băng siêu tốc..."):
                    try:
                        client = Groq(api_key=api_key)
                        file_extension = uploaded_file.name.split('.')[-1]
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        with open(tmp_file_path, "rb") as file:
                            # Đổi response_format thành "verbose_json" để lấy sạch segment, tránh nuốt chữ
                            response_json = client.audio.transcriptions.create(
                                file=(uploaded_file.name, file.read()),
                                model="whisper-large-v3",
                                response_format="verbose_json", 
                                language="vi",
                                temperature=0.0,
                                # Dùng prompt generic siêu sạch để tránh lỗi Prompt Contamination
                                prompt="Đây là một video podcast chia sẻ về kiến thức trading, tài chính, đầu tư, quản lý vốn. Hãy chú ý viết đúng chính tả các từ như xác suất, trading, FOMO và thêm dấu chấm câu đầy đủ. Đây là một video podcast nói liền mạch, không được bỏ sót bất kỳ từ nào của người nói."
                            )
                        
                        os.remove(tmp_file_path)
                        
                        # Tự nối các segment bằng Python để đảm bảo không mất chữ
                        raw_text_list = [segment['text'].strip() for segment in response_json.segments]
                        st.session_state.raw_text = " ".join(raw_text_list)
                        
                    except Exception as e:
                        st.error(f"Có lỗi xảy ra: {e}")

    # Hiển thị kết quả của Tab 1
    if st.session_state.raw_text:
        st.divider()
        st.subheader("📝 Kết quả văn bản thô:")
        
        if st.button("🧹 Format (Gộp dòng)", key="format_btn"):
            st.session_state.raw_text = " ".join(st.session_state.raw_text.split())
            st.rerun()
            
        # Dùng st.text_area thay cho st.code để bạn có thể dễ dàng AUDIT / SỬA lỗi typo ngay trên giao diện
        edited_text = st.text_area("Bạn có thể chỉnh sửa trực tiếp đoạn text dưới đây trước khi copy:", 
                                   value=st.session_state.raw_text, 
                                   height=250)
        st.session_state.raw_text = edited_text


# =====================================================================
# TAB 2: TEXT TO AUDIO (EDGE-TTS)
# =====================================================================
# =====================================================================
# TAB 2: TEXT TO AUDIO (EDGE-TTS)
# =====================================================================
with tab2:
    st.header("🔊 Chuyển đổi Văn bản thành Giọng nói AI")
    st.write("Hệ thống sử dụng AI đa ngôn ngữ thế hệ mới. Hãy chọn đúng giọng đọc khớp với ngôn ngữ của đoạn văn.")

    text_to_speak = st.text_area("Nhập hoặc dán đoạn văn bản cần chuyển thành giọng nói tại đây:", 
                                 placeholder="Ví dụ: Hello các vợ, hôm nay mình đi trade dính ngay FOMO cháy luôn tài khoản...",
                                 height=200)
    
    # SỬA LỖI 2 & 3: Cập nhật danh sách giọng đọc chuẩn xác, bổ sung giọng Tiếng Anh
    voice_options = {
        "🇻🇳 Nam miền Bắc (NamMinh)": "vi-VN-NamMinhNeural",
        "🇻🇳 Nữ miền Nam (HoaiMy)": "vi-VN-HoaiMyNeural",  # Đã đổi từ HoaiAn thành HoaiMy
        "🇺🇸 Nữ tiếng Anh Mỹ (Aria)": "en-US-AriaNeural", # Thêm giọng đọc full Tiếng Anh
        "🇺🇸 Nam tiếng Anh Mỹ (Guy)": "en-US-GuyNeural"
    }
    
    col_voice, col_speed = st.columns(2)
    with col_voice:
        selected_voice_label = st.selectbox("Chọn giọng đọc AI:", options=list(voice_options.keys()))
        actual_voice = voice_options[selected_voice_label] # Ánh xạ từ Label sang Mã API
        
    with col_speed:
        speed_option = st.slider("Tốc độ đọc (Phần trăm thay đổi):", min_value=-50, max_value=50, value=0, step=5, format="%d%%")
        speed_str = f"{speed_option:+d}%" if speed_option != 0 else "+0%"

    if st.button("🎵 Tạo giọng nói AI", type="primary", key="t2a_btn"):
        if not text_to_speak.strip():
            st.warning("⚠️ Vui lòng nhập nội dung văn bản trước khi bấm tạo.")
        else:
            with st.spinner("Đang tổng hợp giọng nói..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                        tmp_audio_path = tmp_audio.name
                    
                    async def generate_audio():
                        communicate = edge_tts.Communicate(text_to_speak, actual_voice, rate=speed_str)
                        await communicate.save(tmp_audio_path)
                    
                    asyncio.run(generate_audio())
                    
                    with open(tmp_audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    os.remove(tmp_audio_path)
                    
                    st.success("🎉 Đã tổng hợp xong âm thanh!")
                    
                    # Cột để trình phát nhạc và nút Download thẳng hàng nhau
                    col_player, col_download = st.columns([3, 1])
                    
                    with col_player:
                        st.audio(audio_bytes, format="audio/mp3")
                        
                    with col_download:
                        # SỬA LỖI 1: Bổ sung nút Download MP3 chuyên dụng cực to và rõ ràng
                        st.download_button(
                            label="⬇️ Tải file MP3 về máy",
                            data=audio_bytes,
                            file_name="giong_noi_ai.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        )
                    
                except Exception as e:
                    st.error(f"Lỗi hệ thống tổng hợp: {e}")