import requests

from config import config


def generate_voice_over(text: str, filename: str):
    """Call ElevenLabs TTS. Returns MP3 bytes or None on failure."""
    VOICE_ID = "onwK4e9ZoxP2sV2hZ69m"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": config.ELEVEN_API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
    except requests.RequestException:
        return None
    if response.status_code == 200:
        return response.content
    return None