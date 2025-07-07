import streamlit as st
from dotenv import load_dotenv
import tempfile
from gemini_utils import process_text, transcribe_and_process_audio

load_dotenv()
st.set_page_config(page_title="Voice Privacy App", layout="centered")

st.title("🔐 Voice Privacy App")
st.write("Upload audio or type text to detect and encrypt sensitive information.")

input_mode = st.radio("Select input type:", ["Text", "Audio"], horizontal=True)

if input_mode == "Text":
    user_text = st.text_area("Enter your message:")
    if st.button("Analyze Text"):
        if user_text.strip():
            response = process_text(user_text)
            st.success("✅ Processed Successfully")
            st.markdown(response)
        else:
            st.warning("Please enter some text.")

else:
    uploaded_file = st.file_uploader("Upload audio file (.mp3/.wav/.ogg)", type=["mp3", "wav", "ogg"])
    if uploaded_file and st.button("Analyze Audio"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        response = transcribe_and_process_audio(tmp_path)
        st.success("✅ Processed Successfully")
        st.markdown(response)
