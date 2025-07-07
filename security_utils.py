import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
fernet = Fernet(os.getenv("FERNET_KEY").encode())

def encrypt_text(text):
    return fernet.encrypt(text.encode()).decode()

def decrypt_text(token):
    return fernet.decrypt(token.encode()).decode()
