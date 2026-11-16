"""Generate crisp flat-vector circular icons with WHITE circle background
matching the clean ring-bordered reference style (4x supersampled to 512x512).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1]
OUT_DIR = R / 'assets/graphics'
OUT_DIR.mkdir(parents=True, exist_ok=True)

NAVY = (20, 36, 51, 255)
NAVY_SOFT = (38, 64, 88, 255)
MINT = (88, 213, 181, 255)
MINT_DARK = (46, 155, 130, 255)
GOLD = (255, 204, 51, 255)
GOLD_DARK = (218, 152, 24, 255)
CORAL = (242, 92, 92, 255)
CORAL_DARK = (196, 56, 56, 255)
SKY = (76, 166, 232, 255)
WHITE = (255, 255, 255, 255)
GRAY_LIGHT = (232, 238, 244, 255)
GRAY_MID = (160, 175, 190, 255)


def make_base_circle(ring_col=MINT, S=2048):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = int(S * 0.04)
    ring_w = int(S * 0.045)
    # Crisp white circular interior + clean colored ring border
    d.ellipse([pad, pad, S - pad, S - pad], fill=WHITE, outline=ring_col, width=ring_w)
    return im, d, S


def finalize(im, filename, size=512):
    out = im.resize((size, size), Image.Resampling.LANCZOS)
    p = OUT_DIR / filename
    out.save(p)
    print(f"Saved: {p}")


def draw_salary():
    im, d, S = make_base_circle(GOLD)
    # Green banknote stack at angle
    d.rounded_rectangle([S*0.22, S*0.36, S*0.74, S*0.66], radius=S*0.04, fill=MINT_DARK, outline=NAVY, width=int(S*0.015))
    d.rounded_rectangle([S*0.26, S*0.31, S*0.78, S*0.61], radius=S*0.04, fill=MINT, outline=NAVY, width=int(S*0.015))
    # Inner white band on banknote
    d.rectangle([S*0.44, S*0.31, S*0.60, S*0.61], fill=WHITE, outline=NAVY, width=int(S*0.010))
    # Coin with Baht symbol on bottom right
    cx, cy, r = S*0.66, S*0.60, S*0.14
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=GOLD, outline=NAVY, width=int(S*0.015))
    d.ellipse([cx-r*0.72, cy-r*0.72, cx+r*0.72, cy+r*0.72], fill=GOLD, outline=GOLD_DARK, width=int(S*0.008))
    font = ImageFont.truetype(str(R / 'assets/fonts/Kanit-ExtraBold.ttf'), int(S*0.17))
    d.text((cx, cy - S*0.01), "฿", font=font, fill=NAVY, anchor='mm')
    finalize(im, 'icon_salary_white.png')


def draw_room():
    im, d, S = make_base_circle(MINT)
    # Cozy home / apartment room silhouette
    # Roof
    d.polygon([(S*0.22, S*0.47), (S*0.50, S*0.22), (S*0.78, S*0.47)], fill=CORAL, outline=NAVY, width=int(S*0.015))
    # Wall
    d.rounded_rectangle([S*0.28, S*0.46, S*0.72, S*0.74], radius=S*0.02, fill=GRAY_LIGHT, outline=NAVY, width=int(S*0.015))
    # Window with warm glow
    d.rounded_rectangle([S*0.34, S*0.51, S*0.47, S*0.62], radius=S*0.015, fill=GOLD, outline=NAVY, width=int(S*0.012))
    d.line([(S*0.405, S*0.51), (S*0.405, S*0.62)], fill=NAVY, width=int(S*0.008))
    d.line([(S*0.34, S*0.565), (S*0.47, S*0.565)], fill=NAVY, width=int(S*0.008))
    # Bed / Door on right
    d.rounded_rectangle([S*0.53, S*0.52, S*0.66, S*0.74], radius=S*0.015, fill=NAVY_SOFT, outline=NAVY, width=int(S*0.012))
    d.ellipse([S*0.62, S*0.62, S*0.645, S*0.645], fill=GOLD)
    finalize(im, 'icon_room_white.png')


def draw_bts():
    im, d, S = make_base_circle(MINT)
    # Elevated track beam
    d.rectangle([S*0.20, S*0.71, S*0.80, S*0.77], fill=GRAY_MID, outline=NAVY, width=int(S*0.012))
    # Sleek train front body
    d.rounded_rectangle([S*0.33, S*0.24, S*0.67, S*0.68], radius=S*0.07, fill=WHITE, outline=NAVY, width=int(S*0.016))
    # Accent stripe
    d.rectangle([S*0.33, S*0.49, S*0.67, S*0.55], fill=MINT, outline=NAVY, width=int(S*0.010))
    # Windshield
    d.rounded_rectangle([S*0.37, S*0.30, S*0.63, S*0.46], radius=S*0.03, fill=NAVY_SOFT, outline=NAVY, width=int(S*0.012))
    # Headlights
    d.ellipse([S*0.37, S*0.58, S*0.43, S*0.64], fill=GOLD, outline=NAVY, width=int(S*0.010))
    d.ellipse([S*0.57, S*0.58, S*0.63, S*0.64], fill=GOLD, outline=NAVY, width=int(S*0.010))
    # Rails
    d.line([(S*0.36, S*0.68), (S*0.28, S*0.79)], fill=NAVY, width=int(S*0.016))
    d.line([(S*0.64, S*0.68), (S*0.72, S*0.79)], fill=NAVY, width=int(S*0.016))
    finalize(im, 'icon_bts_white.png')


def draw_bus():
    im, d, S = make_base_circle(MINT)
    # Factory shuttle bus (side profile)
    d.rounded_rectangle([S*0.20, S*0.34, S*0.80, S*0.66], radius=S*0.05, fill=GOLD, outline=NAVY, width=int(S*0.015))
    # Roof stripe
    d.rounded_rectangle([S*0.22, S*0.34, S*0.78, S*0.41], radius=S*0.02, fill=MINT, outline=NAVY, width=int(S*0.010))
    # Windows
    for wx in [0.25, 0.39, 0.53, 0.67]:
        d.rounded_rectangle([S*wx, S*0.43, S*(wx+0.10), S*0.53], radius=S*0.015, fill=NAVY_SOFT, outline=NAVY, width=int(S*0.010))
    # Wheels
    for cx in [0.33, 0.67]:
        r = S*0.075
        d.ellipse([S*cx-r, S*0.66-r, S*cx+r, S*0.66+r], fill=NAVY, outline=NAVY, width=int(S*0.010))
        d.ellipse([S*cx-r*0.45, S*0.66-r*0.45, S*cx+r*0.45, S*0.66+r*0.45], fill=GRAY_LIGHT)
    finalize(im, 'icon_bus_white.png')


def draw_motorbike():
    im, d, S = make_base_circle(GOLD)
    # Wheels
    for cx in [0.31, 0.69]:
        r = S*0.095
        d.ellipse([S*cx-r, S*0.63-r, S*cx+r, S*0.63+r], fill=NAVY)
        d.ellipse([S*cx-r*0.5, S*0.63-r*0.5, S*cx+r*0.5, S*0.63+r*0.5], fill=GRAY_LIGHT)
    # Scooter body
    d.polygon([(S*0.28, S*0.56), (S*0.42, S*0.46), (S*0.54, S*0.48), (S*0.64, S*0.36), (S*0.72, S*0.56)], fill=MINT, outline=NAVY, width=int(S*0.015))
    # Seat
    d.rounded_rectangle([S*0.33, S*0.43, S*0.52, S*0.49], radius=S*0.02, fill=NAVY_SOFT, outline=NAVY, width=int(S*0.010))
    # Handlebar & headlight
    d.line([(S*0.64, S*0.36), (S*0.59, S*0.30)], fill=NAVY, width=int(S*0.020))
    d.ellipse([S*0.66, S*0.36, S*0.74, S*0.44], fill=GOLD, outline=NAVY, width=int(S*0.012))
    finalize(im, 'icon_motorbike_white.png')


def draw_car():
    im, d, S = make_base_circle(GOLD)
    # Car cabin
    d.polygon([(S*0.28, S*0.48), (S*0.35, S*0.32), (S*0.65, S*0.32), (S*0.72, S*0.48)], fill=SKY, outline=NAVY, width=int(S*0.015))
    # Car body front
    d.rounded_rectangle([S*0.22, S*0.46, S*0.78, S*0.66], radius=S*0.04, fill=CORAL, outline=NAVY, width=int(S*0.015))
    # Windshield
    d.polygon([(S*0.32, S*0.46), (S*0.37, S*0.35), (S*0.63, S*0.35), (S*0.68, S*0.46)], fill=WHITE, outline=NAVY, width=int(S*0.010))
    # Headlights
    d.ellipse([S*0.26, S*0.51, S*0.34, S*0.59], fill=GOLD, outline=NAVY, width=int(S*0.010))
    d.ellipse([S*0.66, S*0.51, S*0.74, S*0.59], fill=GOLD, outline=NAVY, width=int(S*0.010))
    # Tires
    d.rounded_rectangle([S*0.25, S*0.66, S*0.36, S*0.73], radius=S*0.02, fill=NAVY)
    d.rounded_rectangle([S*0.64, S*0.66, S*0.75, S*0.73], radius=S*0.02, fill=NAVY)
    finalize(im, 'icon_car_white.png')


def draw_food():
    im, d, S = make_base_circle(MINT)
    # Plate/Bowl with warm Thai food + spoon & fork
    # Bowl dome food
    d.chord([S*0.26, S*0.34, S*0.74, S*0.66], start=180, end=360, fill=GOLD, outline=NAVY, width=int(S*0.015))
    # Bowl base
    d.chord([S*0.23, S*0.32, S*0.77, S*0.72], start=0, end=180, fill=CORAL, outline=NAVY, width=int(S*0.015))
    d.rectangle([S*0.38, S*0.69, S*0.62, S*0.74], fill=CORAL_DARK, outline=NAVY, width=int(S*0.012))
    # Steam lines
    for sx in [0.39, 0.50, 0.61]:
        d.line([(S*sx, S*0.24), (S*sx, S*0.31)], fill=MINT_DARK, width=int(S*0.016))
    # Top garnish
    d.ellipse([S*0.44, S*0.39, S*0.56, S*0.46], fill=MINT, outline=NAVY, width=int(S*0.010))
    finalize(im, 'icon_food_white.png')


def draw_savings():
    im, d, S = make_base_circle(GOLD)
    # Jar / Savings coin stack
    d.rounded_rectangle([S*0.32, S*0.37, S*0.68, S*0.76], radius=S*0.07, fill=SKY, outline=NAVY, width=int(S*0.015))
    d.rounded_rectangle([S*0.36, S*0.31, S*0.64, S*0.37], radius=S*0.02, fill=GRAY_MID, outline=NAVY, width=int(S*0.014))
    # Gold coins inside jar
    for cy in [0.68, 0.61, 0.54]:
        d.rounded_rectangle([S*0.37, S*cy, S*0.63, S*(cy+0.05)], radius=S*0.02, fill=GOLD, outline=GOLD_DARK, width=int(S*0.008))
    # Dropping coin on top
    cx, cy, r = S*0.50, S*0.22, S*0.075
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=GOLD, outline=NAVY, width=int(S*0.012))
    finalize(im, 'icon_savings_white.png')


if __name__ == '__main__':
    draw_salary()
    draw_room()
    draw_bts()
    draw_bus()
    draw_motorbike()
    draw_car()
    draw_food()
    draw_savings()
