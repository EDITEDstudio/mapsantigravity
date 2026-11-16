"""Generate crisp 4x-supersampled white-circle icons for EP07 (Longest Flights from Thailand):
- icon_clock_white.png (flight hours / transit clock)
- icon_distance_white.png (globe distance route arc + ticket)
- icon_globe_white.png (world globe + flight pin for hook/CTA)
- icon_can_maple_white.png (Canada: crimson maple leaf)
- icon_bra_christ_white.png (Brazil: Christ the Redeemer & Sun / Green-Gold hill)
- icon_arg_glacier_white.png (Argentina: Perito Moreno Glacier / Andean ice peak)
- icon_chl_moai_white.png (Chile: Easter Island Moai & Andes)
- icon_per_machupicchu_white.png (Peru: Machu Picchu citadel & mountain peak)
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw

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
CRIMSON = (216, 36, 42, 255)
SKY = (76, 166, 232, 255)
SKY_DARK = (42, 118, 182, 255)
WHITE = (255, 255, 255, 255)


def make_base_circle(ring_col=MINT, S=2048):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = int(S * 0.04)
    ring_w = int(S * 0.045)
    d.ellipse([pad, pad, S - pad, S - pad], fill=WHITE, outline=ring_col, width=ring_w)
    return im, d, S


def finalize(im, filename, size=512):
    out = im.resize((size, size), Image.Resampling.LANCZOS)
    p = OUT_DIR / filename
    out.save(p)
    print(f"Saved: {p}")


def draw_clock():
    im, d, S = make_base_circle(SKY)
    lw = int(S * 0.016)
    cx, cy, r = S * 0.50, S * 0.52, S * 0.25
    # Stopwatch top crown & side button
    d.rounded_rectangle([cx - S * 0.055, cy - r - S * 0.075, cx + S * 0.055, cy - r - S * 0.01], radius=S * 0.015, fill=CORAL, outline=NAVY, width=lw)
    d.line([(cx, cy - r - S * 0.01), (cx, cy - r + S * 0.02)], fill=NAVY, width=int(S * 0.025))
    # Outer clock body
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(235, 246, 255, 255), outline=NAVY, width=lw)
    # 12/3/6/9 ticks
    for ang_deg in (0, 90, 180, 270):
        a = math.radians(ang_deg)
        d.line([
            (cx + r * 0.72 * math.cos(a), cy + r * 0.72 * math.sin(a)),
            (cx + r * 0.88 * math.cos(a), cy + r * 0.88 * math.sin(a)),
        ], fill=NAVY_SOFT, width=int(S * 0.014))
    # Sweeping red arc (long flight!)
    d.arc([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62], start=-90, end=215, fill=CORAL, width=int(S * 0.028))
    # Hands
    d.line([(cx, cy), (cx, cy - r * 0.56)], fill=NAVY, width=int(S * 0.022))
    d.line([(cx, cy), (cx + r * 0.44, cy + r * 0.25)], fill=CORAL, width=int(S * 0.018))
    d.ellipse([cx - S * 0.024, cy - S * 0.024, cx + S * 0.024, cy + S * 0.024], fill=NAVY)
    finalize(im, 'icon_clock_white.png')


def draw_distance():
    im, d, S = make_base_circle(GOLD)
    lw = int(S * 0.015)
    # Curved route line between two pins across globe horizon
    d.arc([S * 0.18, S * 0.36, S * 0.82, S * 0.92], start=205, end=335, fill=MINT_DARK, width=int(S * 0.016))
    # Dashed flight arc over top
    for i in range(6):
        u0 = i / 6.0
        u1 = u0 + 0.09
        x0 = S * (0.28 + 0.44 * u0)
        y0 = S * (0.52 - 0.23 * math.sin(u0 * math.pi))
        x1 = S * (0.28 + 0.44 * u1)
        y1 = S * (0.52 - 0.23 * math.sin(u1 * math.pi))
        d.line([(x0, y0), (x1, y1)], fill=SKY_DARK, width=int(S * 0.018))
    # Left & Right Map Pins
    for px, py, col in [(S * 0.28, S * 0.52, MINT), (S * 0.72, S * 0.52, CORAL)]:
        pr = S * 0.085
        d.polygon([(px - pr * 0.78, py), (px, py + pr * 1.45), (px + pr * 0.78, py)], fill=col, outline=NAVY, width=int(lw * 0.85))
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=col, outline=NAVY, width=int(lw * 0.85))
        d.ellipse([px - pr * 0.38, py - pr * 0.38, px + pr * 0.38, py + pr * 0.38], fill=WHITE)
    finalize(im, 'icon_distance_white.png')


def draw_globe():
    im, d, S = make_base_circle(MINT)
    lw = int(S * 0.015)
    cx, cy, gr = S * 0.50, S * 0.50, S * 0.25
    d.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=SKY, outline=NAVY, width=lw)
    # Stylized green continents
    d.polygon([(cx - gr * 0.65, cy - gr * 0.45), (cx - gr * 0.20, cy - gr * 0.55), (cx - gr * 0.10, cy - gr * 0.15), (cx - gr * 0.45, cy + gr * 0.10)], fill=MINT)
    d.polygon([(cx + gr * 0.15, cy - gr * 0.35), (cx + gr * 0.68, cy - gr * 0.25), (cx + gr * 0.55, cy + gr * 0.40), (cx + gr * 0.12, cy + gr * 0.15)], fill=MINT)
    # Grid lines
    d.ellipse([cx - gr * 0.48, cy - gr, cx + gr * 0.48, cy + gr], outline=WHITE, width=int(S * 0.008))
    d.line([(cx - gr, cy), (cx + gr, cy)], fill=WHITE, width=int(S * 0.008))
    # Orbiting mini gold plane ring
    d.arc([cx - gr * 1.32, cy - gr * 0.55, cx + gr * 1.32, cy + gr * 0.55], start=15, end=165, fill=GOLD, width=int(S * 0.020))
    d.polygon([(cx + gr * 0.95, cy - gr * 0.42), (cx + gr * 1.25, cy - gr * 0.56), (cx + gr * 1.10, cy - gr * 0.22)], fill=CORAL, outline=NAVY, width=int(lw * 0.7))
    finalize(im, 'icon_globe_white.png')


def draw_can_maple():
    im, d, S = make_base_circle(CRIMSON)
    lw = int(S * 0.014)
    # Crisp 11-point Canadian Maple Leaf silhouette centered
    pts_norm = [
        (0.50, 0.21), (0.55, 0.33), (0.64, 0.30), (0.60, 0.45),
        (0.71, 0.39), (0.73, 0.46), (0.81, 0.47), (0.77, 0.54),
        (0.80, 0.60), (0.63, 0.62), (0.66, 0.68), (0.525, 0.65),
        (0.525, 0.80), (0.475, 0.80), (0.475, 0.65), (0.34, 0.68),
        (0.37, 0.62), (0.20, 0.60), (0.23, 0.54), (0.19, 0.47),
        (0.27, 0.46), (0.29, 0.39), (0.40, 0.45), (0.36, 0.30),
        (0.45, 0.33),
    ]
    d.polygon([(S * x, S * y) for x, y in pts_norm], fill=CRIMSON, outline=NAVY, width=lw)
    finalize(im, 'icon_can_maple_white.png')


def draw_bra_christ():
    im, d, S = make_base_circle(MINT)
    lw = int(S * 0.014)
    # Sky backdrop
    d.ellipse([S * 0.14, S * 0.14, S * 0.86, S * 0.86], fill=(232, 248, 240, 255))
    # Tropical green Rio Sugarloaf hill
    d.chord([S * 0.22, S * 0.55, S * 0.78, S * 0.96], start=180, end=360, fill=MINT_DARK, outline=NAVY, width=lw)
    # Statue Pedestal
    d.rectangle([S * 0.44, S * 0.60, S * 0.56, S * 0.76], fill=(215, 224, 232, 255), outline=NAVY, width=int(lw * 0.9))
    # Christ Redeemer Outstretched Arms + Robe
    d.polygon([(S * 0.25, S * 0.38), (S * 0.75, S * 0.38), (S * 0.75, S * 0.44), (S * 0.55, S * 0.45), (S * 0.56, S * 0.60), (S * 0.44, S * 0.60), (S * 0.45, S * 0.45), (S * 0.25, S * 0.44)], fill=WHITE, outline=NAVY, width=lw)
    # Head + Gold Halo
    hr = S * 0.042
    d.ellipse([S * 0.50 - hr, S * 0.30 - hr, S * 0.50 + hr, S * 0.30 + hr], fill=WHITE, outline=NAVY, width=int(lw * 0.9))
    finalize(im, 'icon_bra_christ_white.png')


def draw_arg_glacier():
    im, d, S = make_base_circle(SKY)
    lw = int(S * 0.015)
    d.ellipse([S * 0.14, S * 0.14, S * 0.86, S * 0.86], fill=(225, 242, 255, 255))
    # Argentine Sun of May top right
    sr = S * 0.075
    d.ellipse([S * 0.68 - sr, S * 0.30 - sr, S * 0.68 + sr, S * 0.30 + sr], fill=GOLD, outline=GOLD_DARK, width=int(lw * 0.7))
    # Blue Patagonian Glacier Wall & Peaks
    d.polygon([(S * 0.18, S * 0.72), (S * 0.35, S * 0.34), (S * 0.50, S * 0.52), (S * 0.64, S * 0.38), (S * 0.82, S * 0.72)], fill=SKY, outline=NAVY, width=lw)
    d.polygon([(S * 0.35, S * 0.34), (S * 0.43, S * 0.55), (S * 0.27, S * 0.55)], fill=WHITE)
    d.polygon([(S * 0.64, S * 0.38), (S * 0.72, S * 0.57), (S * 0.56, S * 0.57)], fill=WHITE)
    # Deep Lake beneath glacier
    d.chord([S * 0.16, S * 0.62, S * 0.84, S * 0.86], start=0, end=180, fill=SKY_DARK, outline=NAVY, width=lw)
    finalize(im, 'icon_arg_glacier_white.png')


def draw_chl_moai():
    im, d, S = make_base_circle(CORAL)
    lw = int(S * 0.015)
    # Volcanic island silhouette backdrop
    d.chord([S * 0.20, S * 0.62, S * 0.80, S * 0.90], start=180, end=360, fill=MINT_DARK, outline=NAVY, width=lw)
    # Iconic Easter Island Moai Head silhouette
    moai = [
        (S * 0.38, S * 0.25), (S * 0.60, S * 0.25),
        (S * 0.63, S * 0.74), (S * 0.36, S * 0.74),
        (S * 0.38, S * 0.55), (S * 0.30, S * 0.53), (S * 0.36, S * 0.38),
    ]
    d.polygon(moai, fill=(138, 152, 168, 255), outline=NAVY, width=lw)
    # Brow ridge & Ear detail
    d.line([(S * 0.35, S * 0.36), (S * 0.52, S * 0.36)], fill=NAVY, width=int(S * 0.024))
    d.rounded_rectangle([S * 0.54, S * 0.38, S * 0.59, S * 0.54], radius=S * 0.015, fill=(110, 124, 140, 255), outline=NAVY, width=int(lw * 0.75))
    finalize(im, 'icon_chl_moai_white.png')


def draw_per_machupicchu():
    im, d, S = make_base_circle(GOLD)
    lw = int(S * 0.015)
    d.ellipse([S * 0.14, S * 0.14, S * 0.86, S * 0.86], fill=(235, 248, 244, 255))
    # Huayna Picchu dramatic spire behind
    d.polygon([(S * 0.36, S * 0.66), (S * 0.60, S * 0.24), (S * 0.82, S * 0.66)], fill=(62, 134, 96, 255), outline=NAVY, width=lw)
    # Green Terraces left foreground
    d.polygon([(S * 0.18, S * 0.74), (S * 0.34, S * 0.48), (S * 0.68, S * 0.74)], fill=MINT_DARK, outline=NAVY, width=lw)
    # Stone Inca Ruins stepped wall
    d.polygon([(S * 0.27, S * 0.74), (S * 0.33, S * 0.58), (S * 0.45, S * 0.58), (S * 0.47, S * 0.64), (S * 0.60, S * 0.64), (S * 0.62, S * 0.74)], fill=(205, 198, 178, 255), outline=NAVY, width=int(lw * 0.9))
    finalize(im, 'icon_per_machupicchu_white.png')


if __name__ == '__main__':
    draw_clock()
    draw_distance()
    draw_globe()
    draw_can_maple()
    draw_bra_christ()
    draw_arg_glacier()
    draw_chl_moai()
    draw_per_machupicchu()
