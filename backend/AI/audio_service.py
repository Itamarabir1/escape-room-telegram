import requests

from config import config


def generate_voice_over(text: str, filename: str):
    # ID של קול "רובוטי/מאיים" (אפשר לבחור מהספרייה שלהם)
    VOICE_ID = "onwK4e9ZoxP2sV2hZ69m"  # דוגמה לקול עמוק
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": config.ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2", # תומך גם בעברית!
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.content # ה-Bytes של ה-MP3
    return None