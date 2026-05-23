import streamlit as st
import os
import tempfile
from groq import Groq

# Cấu hình trang web
st.set_page_config(page_title="TikTok Transcript Tool", page_icon="🎙️")
st.title("🎙️ TikTok to Text MVP")

# Khởi tạo state để lưu Raw Text (phục vụ yêu cầu e: Format không có nút Back)
if "raw_text" not in st.session_state:
    st.session_state.raw_text = None

# --- YÊU CẦU a/: Chỗ nhập API Key ---
st.subheader("1. Cấu hình hệ thống")
api_key = st.text_input("Nhập Groq API Key của bạn:", type="password", help="Key chỉ được sử dụng trong phiên làm việc này, không lưu trữ lại.")

# --- YÊU CẦU c/: Chỗ nhập link TikTok (Disabled) ---
st.subheader("2. Nguồn dữ liệu")
col1, col2 = st.columns([3, 1])
with col1:
    st.text_input("Link TikTok (Tính năng đang phát triển):", disabled=True, placeholder="https://tiktok.com/@user/video/123...")
with col2:
    # Nút bấm cũng bị disable
    st.button("Tải & Dịch", disabled=True, use_container_width=True)

# --- YÊU CẦU b/: Chỗ Upload Video ---
uploaded_file = st.file_uploader("Hoặc Upload file Video/Audio từ máy tính:", type=["mp4", "mp3", "wav", "m4a"])

if uploaded_file is not None:
    if not api_key:
        st.warning("⚠️ Vui lòng nhập Groq API Key ở trên trước.")
    else:
        if st.button("🚀 Bắt đầu bóc băng", type="primary"):
            with st.spinner("Đang gửi lên Groq xử lý siêu tốc..."):
                try:
                    client = Groq(api_key=api_key)
                    
                    # Tạo file tạm trên server để gửi qua API (Yêu cầu f: Không lưu lại file srt/video)
                    file_extension = uploaded_file.name.split('.')[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    with open(tmp_file_path, "rb") as file:
                        # Yêu cầu d/: Chỉnh response_format="text" để chỉ lấy raw text, bỏ cấu trúc SRT
                        response = client.audio.transcriptions.create(
                            file=(uploaded_file.name, file.read()),
                            model="whisper-large-v3",
                            response_format="text", 
                            language="vi"
                        )
                    
                    # Xóa ngay file tạm sau khi gửi xong, giữ máy chủ sạch sẽ
                    os.remove(tmp_file_path)
                    
                    # Lưu kết quả vào session_state
                    st.session_state.raw_text = response
                    
                except Exception as e:
                    st.error(f"Có lỗi xảy ra: {e}")

# --- YÊU CẦU d/, e/, f/: Khu vực hiển thị và xử lý kết quả ---
if st.session_state.raw_text:
    st.divider()
    st.subheader("📝 Kết quả (Raw Text):")
    
    # Yêu cầu e/: Nút Format (Xóa xuống dòng thành 1 đoạn duy nhất, thay đổi thẳng vào state)
    if st.button("🧹 Format (Gộp dòng)"):
        # Dùng split() và join() sẽ xóa sạch mọi khoảng trắng thừa, \n, \n\n
        formatted_text = " ".join(st.session_state.raw_text.split())
        st.session_state.raw_text = formatted_text
        st.rerun() # Refresh lại UI ngay lập tức

    # Yêu cầu d/ & f/: Hiển thị raw text + Nút Copy
    # Dùng st.code là cách hoàn hảo nhất trong Streamlit vì nó tích hợp sẵn Nút Copy góc trên bên phải
    st.code(st.session_state.raw_text, language="markdown", wrap_lines=True)
