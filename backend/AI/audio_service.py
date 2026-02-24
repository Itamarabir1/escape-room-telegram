import logging

import requests

from config import config

logger = logging.getLogger(__name__)


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
    logger.info("audio_service: calling ElevenLabs TTS text_len=%d", len(text))
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
    except requests.RequestException as e:
        logger.exception("audio_service: ElevenLabs request failed: %s", e)
        return None
    if response.status_code == 200:
        logger.info("audio_service: ElevenLabs OK, response size=%d", len(response.content))
        return response.content
    logger.warning(
        "audio_service: ElevenLabs error status=%s body=%s",
        response.status_code,
        (response.text[:500] if response.text else ""),
    )
    return None