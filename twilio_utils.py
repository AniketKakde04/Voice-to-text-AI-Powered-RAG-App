import requests
import os

def download_audio_file(url):
    auth = (os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    res = requests.get(url, auth=auth)
    res.raise_for_status()
    return res.content
