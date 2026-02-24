# פרומפט ליצירת תמונת החדר – מתאר מה יש בכל קיר (לשימוש ב-generate_escape_room_image.py)
ROOM_WALLS_IMAGE_PROMPT = (
    "photorealistic escape room interior, moody warm lighting, "
    "dark green and brown walls, ornate red carpet on floor, "
    "drop ceiling with fluorescent lights, atmospheric, immersive, "
    "LEFT wall: large electrical control panel with glowing amber and green panels, "
    "toggle switches, blinking LED indicators, analog dials, "
    "BACK wall center: ONE round analog wall clock with clear dial, "
    "server rack with blinking blue LEDs next to clock, "
    "whiteboard with binary numbers 01010111, "
    "RIGHT wall: ONE wooden door with metal handle, closed, "
    "small electrical panel with switches on right wall, "
    "in the far right corner of the room on the floor: "
    "a small black metal safe box with a keypad on its door, "
    "the safe is a cube sitting on the carpet, "
    "CENTER: wooden desk with computer monitor showing green terminal text, "
    "mechanical keyboard, tangled cables on desk, "
    "photorealistic, 8k, highly detailed, real escape room photograph"
)

ROOM_IMAGE_NEGATIVE_PROMPT = (
    "vault door, round wheel, wall safe, embedded safe, "
)

# חדר 2: המעבדה הנטושה – פרומפט מלא (תמה, סגנון, פריסה, פריטים)
SCIENCE_LAB_ROOM_SPECIFIC = """
Theme: "The Abandoned Science Laboratory"
Style: sci-fi illustration, cold blue and white tones, neon lighting, futuristic 2D digital illustration, vibrant colors

Room layout:
LEFT wall: tall metal shelves with broken equipment, shattered glass beakers,
chemical containers with warning labels, sparking exposed wires hanging from ceiling,
flickering neon tube lights casting blue shadows

BACK wall center: large holographic screen mounted on wall displaying encrypted glitching data,
error messages and corrupted files visible on screen,
broken robot collapsed on the floor beneath the screen,
its chest panel open showing damaged circuits, small screen on robot displaying a faint encrypted message

RIGHT wall: heavy reinforced metal safe embedded in the wall with a digital keypad,
keypad glowing red, warning stickers around it,
next to the safe: a whiteboard with erased formulas, only fragments visible

FLOOR: cracked laboratory tiles, puddles reflecting neon blue light,
scattered papers and broken equipment

CENTER: long metallic lab desk with overturned chairs,
smashed monitors, tangled cables, one monitor still flickering with green terminal text

Items:
- safe: כספת המחקר הסודי, action_type unlock (RIGHT wall)
- item_2: רובוט פגום עם הודעה מוצפנת, action_type examine (BACK wall)
- item_3: מסך הולוגרמה עם נתונים חסויים, action_type collect (BACK wall center)
"""

# פרומפט ליצירת תמונה בלבד (בלי Items) – לשימוש ב-generate_science_lab_image.py
SCIENCE_LAB_IMAGE_PROMPT = (
    "sci-fi illustration, cold blue and white tones, neon lighting, "
    "futuristic 2D digital illustration, vibrant colors, "
    "The Abandoned Science Laboratory, "
    "LEFT wall: tall metal shelves with broken equipment, shattered glass beakers, "
    "chemical containers with warning labels, sparking exposed wires hanging from ceiling, "
    "flickering neon tube lights casting blue shadows, "
    "BACK wall center: large holographic screen mounted on wall displaying encrypted glitching data, "
    "error messages and corrupted files visible on screen, "
    "broken robot collapsed on the floor beneath the screen, "
    "its chest panel open showing damaged circuits, small screen on robot displaying a faint encrypted message, "
    "RIGHT wall: heavy reinforced metal safe embedded in the wall with a digital keypad, "
    "keypad glowing red, warning stickers around it, "
    "next to the safe: a whiteboard with erased formulas, only fragments visible, "
    "FLOOR: cracked laboratory tiles, puddles reflecting neon blue light, scattered papers and broken equipment, "
    "CENTER: long metallic lab desk with overturned chairs, smashed monitors, tangled cables, "
    "one monitor still flickering with green terminal text, "
    "highly detailed, 8k"
)

SCIENCE_LAB_IMAGE_NEGATIVE_PROMPT = "vault door, round wheel, cartoon, blurry, low resolution"

CS_ROOM_PROMPT = """
You are a Computer Science themed Escape Room architect. 
Generate a room where the puzzles are based on CS concepts (Binary, Data Structures, Algorithms).

Rules:
1. The theme must be: "The Malfunctioning Server Room".
2. Items: exactly 3 — one must be a safe (כספת) with action_type "unlock"; the other two: one related to Binary Code or Linked Lists, one to Recursion or another CS concept.
3. The safe must appear in the scene: label in Hebrew (e.g. "כספת", "כספת השרת") and action_type "unlock". Include the safe in the visual_prompt so the image shows a safe.
4. Coordinates (x, y) for each item: integers between 15 and 85.
5. Language: 
   - Hebrew: room_name, description, item labels, and lore.
   - English: visual_prompt (for high-quality image generation).
6. Lore: Write a dramatic 2-sentence back-story in Hebrew. Use commas and periods for dramatic pauses. This will be the script for a robotic voice-over.
7. "visual_prompt": string, English, one detailed sentence. Must include: "cartoon style" or "caricature style", "2D digital illustration", "vibrant colors", "Computer Science escape room theme", a safe/vault in the scene, and briefly mention the 3 items. Keep it one sentence for image generation.
You must return ONLY valid JSON in this exact shape. Do not include any markdown formatting like ```json or intro/outro text.

{
  "room_name": "string, Hebrew",
  "description": "string, Hebrew, 1-2 sentences",
  "lore": "string, Hebrew, dramatic 2-sentence opening story",
  "visual_prompt": "string, English, one sentence: cartoon/caricature style 2D illustration, vibrant colors, CS escape room, + the 3 items",
  "items": [
    { "id": "safe_1", "label": "כספת (or similar Hebrew)", "x": 20, "y": 30, "action_type": "unlock" },
    { "id": "unique short id", "label": "string, Hebrew", "x": 20, "y": 30, "action_type": "examine or collect" },
    { "id": "unique short id", "label": "string, Hebrew", "x": 20, "y": 30, "action_type": "examine or collect" }
  ]
}
"""