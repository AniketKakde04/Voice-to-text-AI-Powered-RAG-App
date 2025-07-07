import os
import re
import google.generativeai as genai
from security_utils import encrypt_text
from rag_utils import init_chroma, is_similar_to_sensitive_db, add_to_sensitive_db

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

def transcribe_and_process(audio_bytes):
    sensitive_log.clear()
    init_chroma()

    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content([
        "Translate this audio into English. Do not transcribe.",
        {"mime_type": "audio/mp3", "data": audio_bytes}
    ])
    translated = response.text.strip()

    text = mask_known_sensitive(translated)

    for word in translated.split():
        if word not in text:
            continue
        if is_similar_to_sensitive_db(word) or is_sensitive_with_gemini(word):
            encrypted = encrypt_text(word)
            text = text.replace(word, "***SENSITIVE***")
            sensitive_log.append(("***SENSITIVE***", encrypted))
            add_to_sensitive_db(word)

    if sensitive_log:
        return f"""📝 {text}
⚠️ Sensitive info detected and encrypted."""
    return text

def is_sensitive_with_gemini(word):
    model = genai.GenerativeModel("models/gemini-2.0-pro")
    prompt = f"""Does this word or phrase represent personal or sensitive information?

    "{word}"

    Just reply YES or NO."""
    try:
        res = model.generate_content(prompt)
        return "yes" in res.text.lower()
    except:
        return False
