"""
car_recolor.py

Recolors a car's body panels in a photo using a color-tolerance mask,
with a hand-drawn mask fallback for tougher cases (multi-tone paint,
strong reflections).
"""

from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

# ------------------- CONFIG -------------------
BASE_DIR = Path(__file__).parent
INPUT_PHOTO = BASE_DIR / "examples" / "input.jpeg"
OUTPUT_PHOTO = BASE_DIR / "examples" / "output_recolored.png"
MASK_OUTPUT = BASE_DIR / "examples" / "debug_mask.png"

USE_HAND_DRAWN_MASK = False
MASK_PATH = BASE_DIR / "examples" / "hand_mask.png"

NEW_COLOR = (20, 90, 200)
BLEND_STRENGTH = 0.65

SAMPLE_POINT = (1400, 1550)
COLOR_TOLERANCE = 38
# ------------------------------------------------


def build_color_based_mask(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    arr = np.array(rgb).astype(int)

    sample_color = np.array(rgb.getpixel(SAMPLE_POINT))
    print(f"Sampled paint color at {SAMPLE_POINT}: {tuple(sample_color)}")

    diff = np.sqrt(((arr - sample_color) ** 2).sum(axis=2))
    mask_arr = (diff < COLOR_TOLERANCE).astype("uint8") * 255

    mask_img = Image.fromarray(mask_arr, mode="L")
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=4))
    return mask_img


def load_hand_drawn_mask(size) -> Image.Image:
    mask_img = Image.open(MASK_PATH).convert("L")
    if mask_img.size != size:
        mask_img = mask_img.resize(size)
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=3))
    return mask_img


def apply_recolor(img: Image.Image, mask: Image.Image, color, strength: float) -> Image.Image:
    base = img.convert("RGB")
    base_arr = np.array(base).astype(float)

    lightness = np.array(base.convert("L")).astype(float) / 255.0
    lightness = lightness[..., None]

    color_arr = np.array(color, dtype=float)
    tinted = lightness * color_arr

    mask_arr = np.array(mask).astype(float) / 255.0
    mask_arr = mask_arr[..., None]

    blended = base_arr * (1 - mask_arr * strength) + tinted * (mask_arr * strength)
    blended = np.clip(blended, 0, 255).astype("uint8")

    return Image.fromarray(blended, mode="RGB")


def main():
    if not INPUT_PHOTO.exists():
        raise FileNotFoundError(
            f"Put a car photo at {INPUT_PHOTO} before running this script."
        )

    img = Image.open(INPUT_PHOTO).convert("RGB")
    print(f"Loaded {INPUT_PHOTO} — size {img.size}")

    if USE_HAND_DRAWN_MASK:
        mask = load_hand_drawn_mask(img.size)
        print(f"Using hand-drawn mask from {MASK_PATH}")
    else:
        mask = build_color_based_mask(img)
        print("Using automatic color-based mask")

    mask.save(MASK_OUTPUT)
    print(f"Saved {MASK_OUTPUT} — check this to see what got selected")

    result = apply_recolor(img, mask, NEW_COLOR, BLEND_STRENGTH)
    result.save(OUTPUT_PHOTO)
    print(f"Saved result to {OUTPUT_PHOTO}")


if __name__ == "__main__":
    main()