# pyright: reportMissingImports=false
"""
סקריפט ליצירת תמונת חדר בריחה ריאליסטית עם FLUX.1-schnell (Hugging Face Inference API).

משתמש ב-HF_TOKEN מ-backend/.env.
התמונה נשמרת ברוחב גדול (פנורמה) כדי שתוכל לגלול ימינה/שמאלה במסך (למשל בפאלאפון).
כיוון עיצוב: בפרומפט מפורטים כספת בולטת, שעון ברור, ולוח חשמל עם אורות/נורות מהבהבות – בסגנון חדר בריחה קלאסי (המודל text-to-image בלבד, אין שליחת תמונת reference).

הערות:
- FLUX.1-schnell מייצר תמונות סטטיות בלבד – אין בו תמיכה באנימציה/וידאו.
  לאנימציה נדרש מודל אחר (למשל Stable Video Diffusion, AnimateDiff, או יצירת מספר פריימים וחיבור לוידאו).
- גודל התמונה: WIDTH/HEIGHT למטה (מקסימום רוחב 1280 ב-API).
- גלילה ימינה/שמאלה: מתבצעת בפרונט – להציג את התמונה בתוך container עם
  overflow-x: auto (או overflow: auto) ולוודא שהתמונה לא מתכווצת לרוחב המסך
  (למשל min-width של התמונה = רוחב התמונה בפיקסלים), כך שהמשתמש יגלול כדי לראות הכל.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# טעינת .env מתיקיית backend
_backend_dir = Path(__file__).resolve().parent
_env_path = _backend_dir / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

from huggingface_hub import InferenceClient

from AI.prompts import ROOM_WALLS_IMAGE_PROMPT, ROOM_IMAGE_NEGATIVE_PROMPT

# --- הגדרות --- (router.huggingface.co — ה-API הישן לא נתמך יותר)
HF_MODEL = "black-forest-labs/FLUX.1-schnell"
WIDTH = 1280
HEIGHT = 768
_images_dir = _backend_dir.parent / "images"

def _output_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _images_dir / f"escape_room_{stamp}.png"

def main() -> None:
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        print("HF_TOKEN חסר. הגדר אותו ב-backend/.env", file=sys.stderr)
        sys.exit(1)

    client = InferenceClient(provider="hf-inference", api_key=token)
    out_path = _output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("שולח בקשה ל-Hugging Face (FLUX.1-schnell)...")
    image = client.text_to_image(
        prompt=ROOM_WALLS_IMAGE_PROMPT,
        model=HF_MODEL,
        width=WIDTH,
        height=HEIGHT,
        num_inference_steps=4,
        negative_prompt=ROOM_IMAGE_NEGATIVE_PROMPT,
    )
    image.save(str(out_path))
    print(f"OK - התמונה נשמרה: {out_path}")


if __name__ == "__main__":
    main()
