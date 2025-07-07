import os
import re
import google.generativeai as genai
from security_utils import encrypt_text
from rag_utils import init_chroma, is_similar_to_sensitive_db, add_to_sensitive_db
from pydub import AudioSegment

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
sensitive_log = []

def mask_known_sensitive(text):
    patterns = [
        (r'\b(?:\d[ -]*?){13,16}\b', '****CARD****'),
        (r'\b\d{4,6}\b', '***PIN***'),
        (r'\b[A-Z]{4}0[A-Z0-9]{6}\b', '***IFSC***'),
        (r'\b\d{9,18}\b', '***ACCOUNT***'),
        (r'\b[6-9]\d{9}\b', '***PHONE***'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '***EMAIL***'),
        (r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', '***PAN***'),
    ]

    def mask_and_store(match, label):
        val = match.group()
        sensitive_log.append((label, encrypt_text(val)))
        return label

    for regex, label in patterns:
        text = re.sub(regex, lambda m: mask_and_store(m, label), text)

    return text

def process_text(text):
    sensitive_log.clear()
    init_chroma()

    text = text.strip()
    masked = mask_known_sensitive(text)

    for word in text.split():
        if word not in masked:
            continue
        if is_similar_to_sensitive_db(word) or is_sensitive_with_gemini(word):
            encrypted = encrypt_text(word)
            masked = masked.replace(word, "***SENSITIVE***")
            sensitive_log.append(("***SENSITIVE***", encrypted))
            add_to_sensitive_db(word)

    return build_response(masked)

def transcribe_and_process_audio(file_path):
    sensitive_log.clear()
    init_chroma()

    # Convert to MP3 if needed
    audio = AudioSegment.from_file(file_path)
    mp3_bytes = audio.export(format="mp3").read()

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content([
        "Translate this voice note into English. Do not transcribe.",
        {"mime_type": "audio/mp3", "data": mp3_bytes}
    ])
    translated = response.text.strip()

    masked = mask_known_sensitive(translated)

    for word in translated.split():
        if word not in masked:
            continue
        if is_similar_to_sensitive_db(word) or is_sensitive_with_gemini(word):
            encrypted = encrypt_text(word)
            masked = masked.replace(word, "***SENSITIVE***")
            sensitive_log.append(("***SENSITIVE***", encrypted))
            add_to_sensitive_db(word)

    return build_response(masked)

def is_sensitive_with_gemini(word):
    model = genai.GenerativeModel("models/gemini-2.0-pro")
    prompt = f"""Does this word represent personal or sensitive information?

    "{word}"

    Just reply YES or NO."""
    try:
        res = model.generate_content(prompt)
        return "yes" in res.text.lower()
    except:
        return False

def build_response(masked_text):
    if sensitive_log:
        encrypted_list = "\n".join([f"{label}: `{val}`" for label, val in sensitive_log])
        return f"""📝 **Processed Text:**\n\n{masked_text}\n\n🔒 **Encrypted Items:**\n{encrypted_list}\n\n⚠️ Please avoid sharing personal/sensitive data."""
    return f"📝 **Processed Text:**\n\n{masked_text}"
