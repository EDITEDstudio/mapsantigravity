"""Generate crisp 4x-supersampled white-circle icons for EP06 (Travel, Currency & 5 Country Landmarks):
- icon_airplane_white.png (round-trip flight ticket)
- icon_exchange_white.png (currency exchange rate)
- icon_passport_white.png (passport & boarding pass for Top 5 hook/CTA)
- icon_che_alps_white.png (Switzerland: Matterhorn + Swiss peak flag)
- icon_vnm_nonla_white.png (Vietnam: Non La hat & steaming Pho bowl)
- icon_twn_boba_white.png (Taiwan: Boba bubble milk tea)
- icon_chn_panda_white.png (China: Giant Panda & bamboo)
- icon_jpn_fuji_white.png (Japan: Mount Fuji, Rising Sun & Torii)
"""
from pathlib import Path
import math
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
SKY = (76, 166, 232, 255)
SKY_DARK = (42, 118, 182, 255)
WHITE = (255, 255, 255, 255)
GRAY_LIGHT = (232, 238, 244, 255)


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


def rot_pt(pt, cx, cy, angle_deg):
    rad = math.radians(angle_deg)
    dx, dy = pt[0] - cx, pt[1] - cy
    return (cx + dx * math.cos(rad) - dy * math.sin(rad),
            cy + dx * math.sin(rad) + dy * math.cos(rad))


def draw_airplane():
    im, d, S = make_base_circle(SKY)
    # Dashed flight arc beneath plane
    for i in range(6):
        u0 = i * 0.14
        u1 = u0 + 0.08
        x0, y0 = S * (0.20 + 0.45 * u0), S * (0.72 - 0.18 * math.sin(u0 * math.pi))
        x1, y1 = S * (0.20 + 0.45 * u1), S * (0.72 - 0.18 * math.sin(u1 * math.pi))
        d.line([(x0, y0), (x1, y1)], fill=MINT_DARK, width=int(S * 0.016))

    # Draw crisp stylized airplane pointing up-right (-35 deg)
    cx, cy = S * 0.52, S * 0.46
    ang = -35.0
    lw = int(S * 0.014)

    # Wings (wide swept silhouette)
    wing_pts = [
        (cx - S * 0.04, cy - S * 0.04),
        (cx - S * 0.14, cy - S * 0.27),
        (cx - S * 0.03, cy - S * 0.27),
        (cx + S * 0.10, cy - S * 0.04),
        (cx + S * 0.10, cy + S * 0.04),
        (cx - S * 0.03, cy + S * 0.27),
        (cx - S * 0.14, cy + S * 0.27),
        (cx - S * 0.04, cy + S * 0.04),
    ]
    d.polygon([rot_pt(p, cx, cy, ang) for p in wing_pts], fill=SKY, outline=NAVY, width=lw)

    # Tail stabilizer
    tail_pts = [
        (cx - S * 0.22, cy - S * 0.02),
        (cx - S * 0.28, cy - S * 0.12),
        (cx - S * 0.21, cy - S * 0.12),
        (cx - S * 0.15, cy - S * 0.02),
        (cx - S * 0.15, cy + S * 0.02),
        (cx - S * 0.21, cy + S * 0.12),
        (cx - S * 0.28, cy + S * 0.12),
        (cx - S * 0.22, cy + S * 0.02),
    ]
    d.polygon([rot_pt(p, cx, cy, ang) for p in tail_pts], fill=CORAL, outline=NAVY, width=lw)

    # Fuselage
    fuse_pts = [
        (cx - S * 0.25, cy - S * 0.035),
        (cx + S * 0.18, cy - S * 0.045),
        (cx + S * 0.29, cy),
        (cx + S * 0.18, cy + S * 0.045),
        (cx - S * 0.25, cy + S * 0.035),
    ]
    d.polygon([rot_pt(p, cx, cy, ang) for p in fuse_pts], fill=GRAY_LIGHT, outline=NAVY, width=lw)

    # Cockpit window
    win_pts = [
        (cx + S * 0.15, cy - S * 0.025),
        (cx + S * 0.22, cy),
        (cx + S * 0.15, cy + S * 0.025),
    ]
    d.polygon([rot_pt(p, cx, cy, ang) for p in win_pts], fill=NAVY_SOFT)

    finalize(im, 'icon_airplane_white.png')


def draw_exchange():
    im, d, S = make_base_circle(GOLD)
    lw = int(S * 0.015)

    # Curved exchange arrows around top-right and bottom-left
    d.arc([S * 0.21, S * 0.21, S * 0.79, S * 0.79], start=210, end=330, fill=MINT_DARK, width=int(S * 0.022))
    d.arc([S * 0.21, S * 0.21, S * 0.79, S * 0.79], start=30, end=150, fill=GOLD_DARK, width=int(S * 0.022))

    # Arrowheads
    d.polygon([(S*0.77, S*0.33), (S*0.70, S*0.24), (S*0.67, S*0.37)], fill=MINT_DARK)
    d.polygon([(S*0.23, S*0.67), (S*0.30, S*0.76), (S*0.33, S*0.63)], fill=GOLD_DARK)

    # Back coin (Foreign currency / Mint)
    cx2, cy2, r2 = S * 0.61, S * 0.56, S * 0.165
    d.ellipse([cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2], fill=MINT, outline=NAVY, width=lw)
    d.ellipse([cx2 - r2 * 0.74, cy2 - r2 * 0.74, cx2 + r2 * 0.74, cy2 + r2 * 0.74], fill=MINT, outline=MINT_DARK, width=int(S * 0.008))
    f_fx = ImageFont.truetype(str(R / 'assets/fonts/Kanit-ExtraBold.ttf'), int(S * 0.19))
    d.text((cx2, cy2 - S * 0.01), "¥", font=f_fx, fill=WHITE, anchor='mm')

    # Front coin (Baht / Gold)
    cx1, cy1, r1 = S * 0.39, S * 0.44, S * 0.165
    d.ellipse([cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1], fill=GOLD, outline=NAVY, width=lw)
    d.ellipse([cx1 - r1 * 0.74, cy1 - r1 * 0.74, cx1 + r1 * 0.74, cy1 + r1 * 0.74], fill=GOLD, outline=GOLD_DARK, width=int(S * 0.008))
    d.text((cx1, cy1 - S * 0.01), "฿", font=f_fx, fill=NAVY, anchor='mm')

    finalize(im, 'icon_exchange_white.png')


def draw_passport():
    im, d, S = make_base_circle(MINT)
    lw = int(S * 0.015)

    # Boarding pass peeking out top-right
    bp_pts = [
        (S * 0.42, S * 0.23),
        (S * 0.76, S * 0.30),
        (S * 0.69, S * 0.62),
        (S * 0.35, S * 0.55),
    ]
    d.polygon(bp_pts, fill=GOLD, outline=NAVY, width=lw)

    # Passport cover front-left
    d.rounded_rectangle([S * 0.27, S * 0.29, S * 0.63, S * 0.75], radius=S * 0.035, fill=NAVY_SOFT, outline=NAVY, width=lw)
    # Spine detail
    d.line([(S * 0.32, S * 0.30), (S * 0.32, S * 0.74)], fill=NAVY, width=int(S * 0.012))
    # Gold globe emblem
    gx, gy, gr = S * 0.47, S * 0.49, S * 0.105
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], outline=GOLD, width=int(S * 0.014))
    d.ellipse([gx - gr * 0.52, gy - gr, gx + gr * 0.52, gy + gr], outline=GOLD, width=int(S * 0.010))
    d.line([(gx - gr, gy), (gx + gr, gy)], fill=GOLD, width=int(S * 0.010))
    # Gold label bar below globe
    d.rounded_rectangle([S * 0.37, S * 0.64, S * 0.57, S * 0.68], radius=S * 0.01, fill=GOLD)

    finalize(im, 'icon_passport_white.png')


def draw_che_alps():
    im, d, S = make_base_circle(CORAL)
    lw = int(S * 0.015)
    # Sky backdrop circle
    d.ellipse([S * 0.14, S * 0.14, S * 0.86, S * 0.86], fill=(230, 242, 255, 255))
    # Back ridge (Alps)
    d.polygon([(S * 0.16, S * 0.72), (S * 0.36, S * 0.44), (S * 0.56, S * 0.72)], fill=(120, 148, 178, 255), outline=NAVY, width=lw)
    d.polygon([(S * 0.48, S * 0.72), (S * 0.68, S * 0.42), (S * 0.84, S * 0.72)], fill=(104, 134, 166, 255), outline=NAVY, width=lw)
    # Main Matterhorn peak
    peak = [(S * 0.24, S * 0.76), (S * 0.50, S * 0.28), (S * 0.76, S * 0.76)]
    d.polygon(peak, fill=(74, 102, 132, 255), outline=NAVY, width=lw)
    # Snow cap with zig-zag ridge
    snow = [(S * 0.50, S * 0.28), (S * 0.39, S * 0.49), (S * 0.46, S * 0.46), (S * 0.51, S * 0.52), (S * 0.56, S * 0.46), (S * 0.62, S * 0.50)]
    d.polygon(snow, fill=WHITE, outline=NAVY, width=int(lw * 0.8))
    # Swiss Cross crest bottom-center
    fx, fy, fr = S * 0.50, S * 0.67, S * 0.095
    d.rounded_rectangle([fx - fr, fy - fr, fx + fr, fy + fr], radius=S * 0.025, fill=(214, 38, 28, 255), outline=NAVY, width=int(lw * 0.9))
    d.rectangle([fx - fr * 0.22, fy - fr * 0.62, fx + fr * 0.22, fy + fr * 0.62], fill=WHITE)
    d.rectangle([fx - fr * 0.62, fy - fr * 0.22, fx + fr * 0.62, fy + fr * 0.22], fill=WHITE)
    finalize(im, 'icon_che_alps_white.png')


def draw_vnm_nonla():
    im, d, S = make_base_circle(GOLD)
    lw = int(S * 0.015)
    # Pho Bowl lower half
    d.chord([S * 0.25, S * 0.44, S * 0.75, S * 0.80], start=0, end=180, fill=(218, 37, 29, 255), outline=NAVY, width=lw)
    # Bowl rim & foot
    d.rounded_rectangle([S * 0.24, S * 0.59, S * 0.76, S * 0.64], radius=S * 0.015, fill=GOLD, outline=NAVY, width=lw)
    d.rounded_rectangle([S * 0.40, S * 0.77, S * 0.60, S * 0.82], radius=S * 0.01, fill=NAVY_SOFT, outline=NAVY, width=lw)
    # Non La (Vietnamese conical hat) perched/floating cleanly above bowl!
    hat = [(S * 0.18, S * 0.50), (S * 0.50, S * 0.23), (S * 0.82, S * 0.50)]
    d.polygon(hat, fill=(248, 205, 92, 255), outline=NAVY, width=lw)
    d.arc([S * 0.18, S * 0.44, S * 0.82, S * 0.54], start=0, end=180, fill=NAVY, width=lw)
    for k in (0.35, 0.50, 0.65):
        y_l = S * (0.23 + 0.27 * ((k - 0.23) / 0.27 if k > 0.23 else 0.5))
        d.line([(S * 0.50 - S * 0.14 * (k * 1.4), S * (0.30 + k * 0.25)),
                (S * 0.50 + S * 0.14 * (k * 1.4), S * (0.30 + k * 0.25))], fill=GOLD_DARK, width=int(S * 0.009))
    # Tiny gold star on hat crown & chopsticks
    d.line([(S * 0.56, S * 0.58), (S * 0.74, S * 0.45)], fill=NAVY, width=int(S * 0.014))
    d.line([(S * 0.61, S * 0.59), (S * 0.78, S * 0.49)], fill=NAVY, width=int(S * 0.014))
    finalize(im, 'icon_vnm_nonla_white.png')


def draw_twn_boba():
    im, d, S = make_base_circle(SKY)
    lw = int(S * 0.015)
    # Wide Coral Boba Straw tilting top-right
    straw = [(S * 0.53, S * 0.20), (S * 0.60, S * 0.20), (S * 0.52, S * 0.72), (S * 0.45, S * 0.72)]
    d.polygon(straw, fill=CORAL, outline=NAVY, width=lw)
    # Milk Tea Cup body (trapezoid)
    cup = [(S * 0.31, S * 0.38), (S * 0.69, S * 0.38), (S * 0.62, S * 0.79), (S * 0.38, S * 0.79)]
    d.polygon(cup, fill=(238, 198, 136, 255), outline=NAVY, width=lw)
    # Creamy foam top
    d.polygon([(S * 0.315, S * 0.38), (S * 0.685, S * 0.38), (S * 0.67, S * 0.47), (S * 0.33, S * 0.47)], fill=WHITE, outline=NAVY, width=int(lw * 0.8))
    # Lid dome & rim
    d.rounded_rectangle([S * 0.28, S * 0.33, S * 0.72, S * 0.39], radius=S * 0.025, fill=SKY, outline=NAVY, width=lw)
    # Boba Pearls inside bottom of cup
    for bx, by in [(0.42, 0.73), (0.50, 0.74), (0.57, 0.72), (0.45, 0.66), (0.54, 0.67)]:
        pr = S * 0.036
        d.ellipse([S * bx - pr, S * by - pr, S * bx + pr, S * by + pr], fill=(44, 28, 22, 255))
    finalize(im, 'icon_twn_boba_white.png')


def draw_chn_panda():
    im, d, S = make_base_circle(GOLD)
    lw = int(S * 0.016)
    # Bamboo stalks on left
    d.line([(S * 0.22, S * 0.76), (S * 0.22, S * 0.26)], fill=MINT_DARK, width=int(S * 0.032))
    d.polygon([(S * 0.22, S * 0.36), (S * 0.34, S * 0.28), (S * 0.28, S * 0.40)], fill=MINT)
    # Black Panda Ears
    for ex in (0.35, 0.65):
        er = S * 0.095
        d.ellipse([S * ex - er, S * 0.29 - er, S * ex + er, S * 0.29 + er], fill=NAVY)
    # White Panda Face
    d.ellipse([S * 0.28, S * 0.28, S * 0.72, S * 0.73], fill=WHITE, outline=NAVY, width=lw)
    # Iconic Eye Patches (tilted slightly inward)
    for ex, sign in [(0.41, -1), (0.59, 1)]:
        d.ellipse([S * ex - S * 0.068, S * 0.43, S * ex + S * 0.068, S * 0.56], fill=NAVY)
        d.ellipse([S * ex - S * 0.022, S * 0.47, S * ex + S * 0.022, S * 0.515], fill=WHITE)
    # Nose & Smile
    d.ellipse([S * 0.46, S * 0.56, S * 0.54, S * 0.61], fill=NAVY)
    d.arc([S * 0.43, S * 0.59, S * 0.57, S * 0.67], start=15, end=165, fill=NAVY, width=int(S * 0.014))
    # Cheek blushes
    d.ellipse([S * 0.33, S * 0.58, S * 0.39, S * 0.625], fill=(255, 165, 175, 220))
    d.ellipse([S * 0.61, S * 0.58, S * 0.67, S * 0.625], fill=(255, 165, 175, 220))
    finalize(im, 'icon_chn_panda_white.png')


def draw_jpn_fuji():
    im, d, S = make_base_circle((255, 107, 129, 255))
    lw = int(S * 0.015)
    # Rising Crimson Sun behind Fuji
    sr = S * 0.165
    d.ellipse([S * 0.50 - sr, S * 0.36 - sr, S * 0.50 + sr, S * 0.36 + sr], fill=(214, 38, 48, 255), outline=NAVY, width=int(lw * 0.8))
    # Mount Fuji conic trapezoid slope
    fuji = [(S * 0.19, S * 0.72), (S * 0.42, S * 0.39), (S * 0.58, S * 0.39), (S * 0.81, S * 0.72)]
    d.polygon(fuji, fill=SKY_DARK, outline=NAVY, width=lw)
    # Fuji snow cap
    snow = [(S * 0.42, S * 0.39), (S * 0.58, S * 0.39), (S * 0.65, S * 0.49), (S * 0.57, S * 0.46), (S * 0.50, S * 0.51), (S * 0.43, S * 0.46), (S * 0.35, S * 0.49)]
    d.polygon(snow, fill=WHITE, outline=NAVY, width=int(lw * 0.7))
    # Mini Vermilion Torii Gate foreground right/center
    gx = S * 0.50
    d.line([(gx - S * 0.11, S * 0.78), (gx - S * 0.11, S * 0.59)], fill=(230, 52, 42, 255), width=int(S * 0.028))
    d.line([(gx + S * 0.11, S * 0.78), (gx + S * 0.11, S * 0.59)], fill=(230, 52, 42, 255), width=int(S * 0.028))
    d.rounded_rectangle([gx - S * 0.18, S * 0.57, gx + S * 0.18, S * 0.605], radius=S * 0.01, fill=(230, 52, 42, 255), outline=NAVY, width=int(lw * 0.6))
    d.rectangle([gx - S * 0.13, S * 0.635, gx + S * 0.13, S * 0.658], fill=(230, 52, 42, 255))
    finalize(im, 'icon_jpn_fuji_white.png')


if __name__ == '__main__':
    draw_airplane()
    draw_exchange()
    draw_passport()
    draw_che_alps()
    draw_vnm_nonla()
    draw_twn_boba()
    draw_chn_panda()
    draw_jpn_fuji()
