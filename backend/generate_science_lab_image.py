# pyright: reportMissingImports=false
"""
סקריפט ליצירת תמונת חדר בריחה "המעבדה הנטושה" עם FLUX.1-schnell (Hugging Face Inference API).

משתמש ב-HF_TOKEN מ-backend/.env.
התמונה נשמרת בתיקיית images/ בשם science_lab_room_YYYYMMDD_HHMMSS.png.
הפרומפט המלא לחדר: AI.prompts.SCIENCE_LAB_ROOM_SPECIFIC.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent
_env_path = _backend_dir / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

from huggingface_hub import InferenceClient

from AI.prompts import SCIENCE_LAB_IMAGE_PROMPT, SCIENCE_LAB_IMAGE_NEGATIVE_PROMPT

HF_MODEL = "black-forest-labs/FLUX.1-schnell"
WIDTH = 1280
HEIGHT = 768
_images_dir = _backend_dir.parent / "images"


def _output_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _images_dir / f"science_lab_room_{stamp}.png"


def main() -> None:
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        print("HF_TOKEN חסר. הגדר אותו ב-backend/.env", file=sys.stderr)
        sys.exit(1)

    client = InferenceClient(provider="hf-inference", api_key=token)
    out_path = _output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("שולח בקשה ל-Hugging Face (FLUX.1-schnell) – חדר המעבדה הנטושה...")
    image = client.text_to_image(
        prompt=SCIENCE_LAB_IMAGE_PROMPT,
        model=HF_MODEL,
        width=WIDTH,
        height=HEIGHT,
        num_inference_steps=4,
        negative_prompt=SCIENCE_LAB_IMAGE_NEGATIVE_PROMPT,
    )
    image.save(str(out_path))
    print(f"OK - התמונה נשמרה: {out_path}")


if __name__ == "__main__":
    main()
