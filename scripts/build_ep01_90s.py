"""Episode 01 (90s Extended World Edition): ประเทศไทยมีรายได้รวมเท่าไหร่?
Updated Requirements:
1. Font: Kanit (loopless/modern Thai sans-serif)
2. Frameless: No top/bottom boxes or cards
3. Opening Title: Bold hook with highlighted keyword colors
4. Sentences appear one-by-one and disappear cleanly (fade-in / hold / fade-out)
5. World Map: High-res globe/world terrain (8100x4050) with deep blue ocean
6. Dynamic Motion: Zooming in from space, panning between regions, zooming in/out
7. Animated running numbers (Odometer counter effect)
8. Audio: Clean voiceover only (no background music)
"""
from pathlib import Path
import argparse, json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

R = Path(__file__).resolve().parents[1]
Image.MAX_IMAGE_PIXELS = 300_000_000

def ff():
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_kanit(size, weight='bold'):
    font_file = {
        'regular': 'Kanit-Regular.ttf',
        'medium': 'Kanit-Medium.ttf',
        'semi_bold': 'Kanit-SemiBold.ttf',
        'bold': 'Kanit-Bold.ttf',
        'extra_bold': 'Kanit-ExtraBold.ttf'
    }.get(weight, 'Kanit-Bold.ttf')
    font_path = R / 'assets/fonts' / font_file
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/SukhumvitSet.ttc', size, index=5)

def rings(g):
    if g['type'] == 'Polygon':
        return g['coordinates']
    if g['type'] == 'MultiPolygon':
        return [r for p in g['coordinates'] for r in p]
    return []

def ease(x):
    x = max(0.0, min(1.0, float(x)))
    return x * x * (3.0 - 2.0 * x)

def interp_camera(t, waypoints, w, h):
    for i in range(len(waypoints) - 1):
        t0, cx0, cy0, s0 = waypoints[i]
        t1, cx1, cy1, s1 = waypoints[i + 1]
        if t0 <= t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 0
            cx = cx0 + (cx1 - cx0) * u
            cy = cy0 + (cy1 - cy0) * u
            span = s0 + (s1 - s0) * u
            sh = span
            sw = sh * (w / h)
            return [cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2]
    _, cx, cy, span = waypoints[-1]
    sh = span
    sw = sh * (w / h)
    return [cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2]

def draw_shadowed_text(d, pos, text, font, fill, shadow_fill=(0, 0, 0, 220), radius=2, anchor='mm'):
    x, y = pos
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                d.text((x + dx, y + dy), text, font=font, fill=shadow_fill, anchor=anchor)
    d.text((x, y), text, font=font, fill=fill, anchor=anchor)

def render_ep01_90s(width=360, height=640, fps=30, output_name='ep01_90s_world_360p.mp4'):
    timing_file = R / 'audio/ep01_90s_timing.json'
    timing = json.loads(timing_file.read_text(encoding='utf-8'))
    duration = max(93.5, timing['durationSec'] + 1.0)

    # 7 structured subtitles with fade in/out timing
    subtitles = [
        {
            'start': 0.0, 'end': 10.632,
            'lines': [
                ('รู้ไหมครับว่า ในหนึ่งปี ประเทศไทยมีรายได้เท่าไหร่?', '#ffffff'),
                ('ถ้าดูจาก GDP สภาพัฒน์ระบุว่าอยู่ที่ราว 18.5 ล้านล้านบาท', '#ffd44d')
            ]
        },
        {
            'start': 11.082, 'end': 21.234,
            'lines': [
                ('แต่ถ้าเป็นรายได้สุทธิที่รัฐบาลจัดเก็บเข้าคลัง', '#ffffff'),
                ('จะอยู่ที่ประมาณ 2.8 ล้านล้านบาทต่อปี จากภาษีและรัฐวิสาหกิจ', '#58d5b5')
            ]
        },
        {
            'start': 21.684, 'end': 39.324,
            'lines': [
                ('และที่น่าทึ่งคือ รายได้กว่า 60% กระจุกตัวแค่ กทม. และภาคตะวันออก', '#ffffff'),
                ('เฉพาะ กทม. และปริมณฑล สร้างสัดส่วนสูงถึง 46% ของ GDP', '#ffd44d')
            ]
        },
        {
            'start': 39.774, 'end': 55.566,
            'lines': [
                ('ถัดมาคือภาคตะวันออก ฐานการผลิตและท่าเรือแหลมฉบัง', '#ffffff'),
                ('และจังหวัดที่รายได้ต่อหัวสูงสุดในไทยคือ ระยอง (1 ล้านบาท/คน/ปี)', '#ffd44d')
            ]
        },
        {
            'start': 56.016, 'end': 70.680,
            'lines': [
                ('ในทางกลับกัน ภาคอีสานมีประชากรถึง 1 ใน 3 ของประเทศ', '#ffffff'),
                ('แต่สร้างสัดส่วน GDP รวมกันได้เพียงราว 10% เท่านั้น', '#58d5b5')
            ]
        },
        {
            'start': 71.130, 'end': 84.714,
            'lines': [
                ('ถ้าหารเฉลี่ยคนไทย 66 ล้านคน จะตกคนละ 270,000 บาท/ปี', '#ffd44d'),
                ('แต่ในความจริง เงินส่วนใหญ่อยู่ในระบบอุตสาหกรรมและบริษัทใหญ่', '#ffffff')
            ]
        },
        {
            'start': 85.164, 'end': 92.412,
            'lines': [
                ('แล้วคุณคิดว่า ควรพัฒนาทำเลไหนเพื่อกระจายรายได้?', '#ffd44d'),
                ('อยากให้ซูมจังหวัดไหนต่อ คอมเมนต์บอกกันได้เลยครับ', '#ffffff')
            ]
        }
    ]

    # Geographic data
    countries = json.loads((R / 'data/processed/world_countries.geojson').read_text(encoding='utf-8'))['features']
    provinces = json.loads((R / 'data/processed/thailand_provinces.geojson').read_text(encoding='utf-8'))['features']
    tha_country = next((c for c in countries if c['properties'].get('adm0_a3') == 'THA'), None)

    # Specific province selections
    bkk_provinces = [p for p in provinces if p['properties'].get('name') == 'Bangkok Metropolis']
    eec_provinces = [p for p in provinces if p['properties'].get('name') in ['Rayong', 'Chon Buri']]
    isan_names = [
        'Nakhon Ratchasima', 'Khon Kaen', 'Ubon Ratchathani', 'Udon Thani', 
        'Buri Ram', 'Surin', 'Si Sa Ket', 'Roi Et', 'Chaiyaphum', 'Sakon Nakhon', 
        'Kalasin', 'Maha Sarakham', 'Nakhon Phanom', 'Loei', 'Yasothon', 
        'Nong Khai', 'Bueng Kan', 'Amnat Charoen', 'Nong Bua Lam Phu', 'Mukdahan'
    ]
    isan_provinces = [p for p in provinces if p['properties'].get('name') in isan_names]

    # Icons
    icons = {
        'gdp': Image.open(R / 'assets/graphics/icon_gdp.png').convert('RGBA'),
        'treasury': Image.open(R / 'assets/graphics/icon_treasury.png').convert('RGBA'),
        'skyline': Image.open(R / 'assets/graphics/icon_skyline.png').convert('RGBA'),
        'industry': Image.open(R / 'assets/graphics/icon_industry.png').convert('RGBA'),
        'agriculture': Image.open(R / 'assets/graphics/icon_agriculture.png').convert('RGBA'),
        'wallet': Image.open(R / 'assets/graphics/icon_wallet.png').convert('RGBA')
    }

    world_terrain_path = R / 'work/cached_world_terrain_blue_ocean.png'
    if not world_terrain_path.exists():
        raise RuntimeError('Run world terrain cache first: work/cached_world_terrain_blue_ocean.png')
    terrain = Image.open(world_terrain_path).convert('RGB')

    # Dynamic Camera Waypoints (World Orbit -> Zoom-In -> Regional Panning -> Orbit Zoom-Out)
    waypoints = [
        (0.0,   100.0, 18.0, 110.0), # Space / World orbit view centered on Asia
        (3.8,   100.0, 18.0, 110.0), # Hold orbit view while title plays
        (6.5,   101.0, 13.0, 16.5),  # Rapid zoom-in plunge to Thailand
        (10.5,  101.0, 13.0, 16.5),  # Hold on Thailand
        (14.5,  100.8, 13.2, 13.0),  # Drift towards Central Thailand
        (20.5,  100.8, 13.2, 13.0),  # Hold
        (24.0,  100.5, 13.75, 2.5),  # Deep zoom punch-in to Bangkok
        (36.0,  100.5, 13.75, 2.5),  # Hold on Bangkok
        (40.5,  101.3, 12.8, 2.8),   # Smooth pan across to Eastern Seaboard / Rayong
        (52.5,  101.3, 12.8, 2.8),   # Hold on Rayong & Chon Buri
        (56.5,  103.2, 16.0, 8.0),   # Pull back & sweep up to Northeast (Isan)
        (67.5,  103.2, 16.0, 8.0),   # Hold on Isan
        (72.0,  101.0, 13.0, 16.5),  # Pull back to full Thailand
        (83.5,  101.0, 13.0, 16.5),  # Hold
        (88.0,  100.0, 15.0, 65.0),  # Zoom back out to continental / world view
        (93.5,  100.0, 15.0, 65.0)   # Final hold
    ]

    w, h = width, height
    total_frames = round(duration * fps)
    out_path = R / f'exports/{output_name}'
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ff(), '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
        '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(out_path)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=(R / 'exports/render_ep01_world.log').open('w'))

    sample_frames = {}

    print(f"Rendering World Edition ({w}x{h}, {duration:.1f}s, {total_frames} frames)...", flush=True)

    try:
        for i in range(total_frames):
            t = i / fps
            box = interp_camera(t, waypoints, w, h)

            def xy(p):
                return (
                    (p[0] - box[0]) / (box[2] - box[0]) * w,
                    (box[3] - p[1]) / (box[3] - box[1]) * h
                )

            # Map coordinates to world terrain texture [ -180..180, -90..90 ]
            region = (
                (box[0] + 180.0) / 360.0 * terrain.width,
                (90.0 - box[3]) / 180.0 * terrain.height,
                (box[2] + 180.0) / 360.0 * terrain.width,
                (90.0 - box[1]) / 180.0 * terrain.height
            )

            im = terrain.transform((w, h), Image.Transform.EXTENT, region, Image.Resampling.BILINEAR).convert('RGBA')
            d = ImageDraw.Draw(im)

            # 1. World Country Borders
            for c in countries:
                if c['properties'].get('adm0_a3') != 'THA':
                    for ring in rings(c['geometry']):
                        pts = [xy(p) for p in ring]
                        d.line(pts, fill=(220, 235, 228, 90), width=max(1, w // 450))

            # 2. Thailand Provincial Borders (when zoomed close enough)
            if box[3] - box[1] < 30.0:
                for f in provinces:
                    for ring in rings(f['geometry']):
                        d.line([xy(p) for p in ring], fill=(240, 248, 255, 75), width=max(1, w // 540))

            # 3. Thailand Country Border Glow (active from zoom-in onwards)
            if tha_country and t >= 5.0:
                tha_glow = ease((t - 5.0) / 1.5) * (1 - ease((t - 92.5) / 1.0))
                if tha_glow > 0.05:
                    edge = Image.new('RGBA', (w, h))
                    ed = ImageDraw.Draw(edge)
                    for ring in rings(tha_country['geometry']):
                        ed.line([xy(p) for p in ring], fill=(255, 219, 76, int(190 * tha_glow)), width=max(2, w // 200))
                    im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 100))))
                    im = Image.alpha_composite(im, edge)

            # 4. Province Lifts & Regional Highlights
            # A) Bangkok lift (23.5s - 37.5s)
            bkk_lift = 0.0
            if 23.5 <= t <= 37.5:
                bkk_lift = ease((t - 23.5) / 0.8) * (1.0 - ease((t - 36.7) / 0.8))
            if bkk_lift > 0.01:
                mask = Image.new('L', (w, h))
                md = ImageDraw.Draw(mask)
                for f in bkk_provinces:
                    polys = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
                    for poly in polys:
                        md.polygon([xy(p) for p in poly[0]], fill=255)
                        for hole in poly[1:]: md.polygon([xy(p) for p in hole], fill=0)
                dx = int(10 * w / 1080 * bkk_lift); dy = int(-45 * h / 1920 * bkk_lift)
                shifted = Image.new('L', (w, h)); shifted.paste(mask, (dx, dy))
                shadow = Image.new('L', (w, h)); shadow.paste(mask, (dx + int(10 * bkk_lift), dy + int(20 * bkk_lift)))
                im = Image.alpha_composite(im, Image.composite(Image.new('RGBA', (w, h), (0, 0, 0, int(185 * bkk_lift))), Image.new('RGBA', (w, h)), shadow.filter(ImageFilter.GaussianBlur(max(3, w // 90)))))
                lifted = Image.new('RGBA', (w, h)); lifted.paste(im, (dx, dy))
                im = Image.composite(lifted, im, shifted)
                tint = Image.new('RGBA', (w, h), (255, 191, 47, int(90 * bkk_lift)))
                im = Image.alpha_composite(im, Image.composite(tint, Image.new('RGBA', (w, h)), shifted))
                edge = Image.new('RGBA', (w, h)); ed = ImageDraw.Draw(edge)
                for f in bkk_provinces:
                    for ring in rings(f['geometry']):
                        ed.line([(xy(p)[0] + dx, xy(p)[1] + dy) for p in ring], fill=(255, 225, 90, int(255 * bkk_lift)), width=max(2, w // 160))
                im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 80))))
                im = Image.alpha_composite(im, edge)

            # B) Rayong & Chon Buri lift (40.5s - 53.5s)
            eec_lift = 0.0
            if 40.5 <= t <= 53.5:
                eec_lift = ease((t - 40.5) / 0.8) * (1.0 - ease((t - 52.7) / 0.8))
            if eec_lift > 0.01:
                mask = Image.new('L', (w, h))
                md = ImageDraw.Draw(mask)
                for f in eec_provinces:
                    polys = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
                    for poly in polys:
                        md.polygon([xy(p) for p in poly[0]], fill=255)
                        for hole in poly[1:]: md.polygon([xy(p) for p in hole], fill=0)
                dx = int(10 * w / 1080 * eec_lift); dy = int(-45 * h / 1920 * eec_lift)
                shifted = Image.new('L', (w, h)); shifted.paste(mask, (dx, dy))
                shadow = Image.new('L', (w, h)); shadow.paste(mask, (dx + int(10 * eec_lift), dy + int(20 * eec_lift)))
                im = Image.alpha_composite(im, Image.composite(Image.new('RGBA', (w, h), (0, 0, 0, int(185 * eec_lift))), Image.new('RGBA', (w, h)), shadow.filter(ImageFilter.GaussianBlur(max(3, w // 90)))))
                lifted = Image.new('RGBA', (w, h)); lifted.paste(im, (dx, dy))
                im = Image.composite(lifted, im, shifted)
                tint = Image.new('RGBA', (w, h), (255, 191, 47, int(90 * eec_lift)))
                im = Image.alpha_composite(im, Image.composite(tint, Image.new('RGBA', (w, h)), shifted))
                edge = Image.new('RGBA', (w, h)); ed = ImageDraw.Draw(edge)
                for f in eec_provinces:
                    for ring in rings(f['geometry']):
                        ed.line([(xy(p)[0] + dx, xy(p)[1] + dy) for p in ring], fill=(255, 225, 90, int(255 * eec_lift)), width=max(2, w // 160))
                im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 80))))
                im = Image.alpha_composite(im, edge)

            # C) Isan 20 Provinces Highlight (56.0s - 69.5s)
            isan_glow = 0.0
            if 56.0 <= t <= 69.5:
                isan_glow = ease((t - 56.0) / 0.8) * (1.0 - ease((t - 68.7) / 0.8))
            if isan_glow > 0.01:
                mask = Image.new('L', (w, h))
                md = ImageDraw.Draw(mask)
                for f in isan_provinces:
                    polys = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
                    for poly in polys:
                        md.polygon([xy(p) for p in poly[0]], fill=255)
                        for hole in poly[1:]: md.polygon([xy(p) for p in hole], fill=0)
                tint = Image.new('RGBA', (w, h), (88, 213, 181, int(45 * isan_glow)))
                im = Image.alpha_composite(im, Image.composite(tint, Image.new('RGBA', (w, h)), mask))
                edge = Image.new('RGBA', (w, h)); ed = ImageDraw.Draw(edge)
                for f in isan_provinces:
                    for ring in rings(f['geometry']):
                        ed.line([xy(p) for p in ring], fill=(88, 213, 181, int(190 * isan_glow)), width=max(1, w // 300))
                im = Image.alpha_composite(im, edge)

            d = ImageDraw.Draw(im)

            # 5. Opening Title Hook (0.0s - 4.5s) - Frameless with Highlights & Dropshadow
            if t < 4.8:
                fade = 1.0
                if t < 0.4: fade = ease(t / 0.4)
                elif t > 4.2: fade = 1.0 - ease((t - 4.2) / 0.6)
                
                title_y = int(h * 0.12)
                font_title_badge = get_kanit(max(11, w // 30), weight='semi_bold')
                font_title_main = get_kanit(max(20, w // 16), weight='extra_bold')
                
                shadow_alpha = int(230 * fade)
                draw_shadowed_text(d, (w / 2, title_y), "พิกัดเงิน • ภูมิศาสตร์เศรษฐกิจ", font_title_badge, "#58d5b5", shadow_fill=(0, 0, 0, shadow_alpha), radius=2)
                draw_shadowed_text(d, (w / 2, title_y + int(h * 0.045)), "ประเทศไทย", font_title_main, "#ffd44d", shadow_fill=(0, 0, 0, shadow_alpha), radius=3)
                draw_shadowed_text(d, (w / 2, title_y + int(h * 0.095)), "มีรายได้รวมเท่าไหร่?", font_title_main, "#ffffff", shadow_fill=(0, 0, 0, shadow_alpha), radius=3)

            # 6. Frameless Floating Running Numbers & Infographics
            floating_data = None
            if 4.8 <= t < 10.8:
                p = ease((t - 5.0) / 4.5)
                val = 18.5 * p
                floating_data = {
                    'icon': icons['gdp'],
                    'label': 'ผลิตภัณฑ์มวลรวมในประเทศ (GDP)',
                    'number': f"{val:.1f} ล้านล้านบาท",
                    'sub': 'มูลค่าผลผลิตมวลรวมสินค้าและบริการ (สภาพัฒน์)'
                }
            elif 11.2 <= t < 21.2:
                p = ease((t - 12.0) / 4.5)
                val = 2.8 * p
                floating_data = {
                    'icon': icons['treasury'],
                    'label': 'รายได้สุทธิรัฐบาลจัดเก็บเข้าคลัง',
                    'number': f"{val:.1f} ล้านล้านบาท/ปี",
                    'sub': 'ภาษีสรรพากร • สรรพสามิต • ศุลกากร • รัฐวิสาหกิจ'
                }
            elif 22.0 <= t < 39.5:
                p = ease((t - 23.5) / 5.0)
                val = int(46 * p)
                floating_data = {
                    'icon': icons['skyline'],
                    'label': 'กรุงเทพฯ และปริมณฑล',
                    'number': f"{val}% ของ GDP ทั้งประเทศ",
                    'sub': 'ศูนย์รวมสำนักงานใหญ่ สถาบันการเงิน และภาคบริการ'
                }
            elif 40.0 <= t < 55.5:
                p = ease((t - 42.0) / 5.5)
                val = int(1_040_000 * p)
                floating_data = {
                    'icon': icons['industry'],
                    'label': 'ระยอง • จังหวัดที่รวยที่สุดในไทย',
                    'number': f"{val:,} บาท/คน/ปี",
                    'sub': 'ฐานการผลิตปิโตรเคมี ยานยนต์ และท่าเรือแหลมฉบัง'
                }
            elif 56.0 <= t < 70.8:
                p = ease((t - 57.5) / 5.0)
                val_pop = int(33 * p); val_gdp = int(10 * p)
                floating_data = {
                    'icon': icons['agriculture'],
                    'label': 'ภาคอีสาน (20 จังหวัด)',
                    'number': f"ประชากร {val_pop}%  |  GDP เพียง {val_gdp}%",
                    'sub': 'พื้นที่ใหญ่ที่สุด แต่พึ่งพาเกษตรกรรมมูลค่าเพิ่มต่ำ'
                }
            elif 71.2 <= t < 84.8:
                p = ease((t - 72.5) / 5.0)
                val_year = int(270_000 * p); val_month = int(22_500 * p)
                floating_data = {
                    'icon': icons['wallet'],
                    'label': 'หารเฉลี่ยคนไทย 66 ล้านคน',
                    'number': f"{val_year:,} บ./ปี (เดือนละ {val_month:,} บ.)",
                    'sub': 'ความจริง: เงินส่วนใหญ่อยู่ในระบบอุตสาหกรรมและบริษัท'
                }
            elif 85.0 <= t < 92.8:
                floating_data = {
                    'icon': icons['gdp'],
                    'label': '77 จังหวัดทั่วไทย',
                    'number': 'จังหวัดคุณอยู่อันดับไหน?',
                    'sub': 'ควรพัฒนาทำเลไหนต่อ? คอมเมนต์แลกเปลี่ยนกันได้เลย'
                }

            if floating_data:
                center_y = int(h * 0.18)
                font_f_label = get_kanit(max(11, w // 30), weight='semi_bold')
                font_f_num = get_kanit(max(20, w // 16), weight='extra_bold')
                font_f_sub = get_kanit(max(9, w // 36), weight='medium')

                # Floating badge icon
                icon_img = floating_data['icon']
                icon_sz = max(36, int(w * 0.14))
                icon_resized = icon_img.resize((icon_sz, icon_sz), Image.Resampling.LANCZOS)
                im.paste(icon_resized, (int(w / 2 - icon_sz / 2), center_y - icon_sz - int(h * 0.015)), icon_resized)
                d = ImageDraw.Draw(im)

                draw_shadowed_text(d, (w / 2, center_y), floating_data['label'], font_f_label, "#58d5b5", radius=2)
                draw_shadowed_text(d, (w / 2, center_y + int(h * 0.045)), floating_data['number'], font_f_num, "#ffd44d", radius=3)
                draw_shadowed_text(d, (w / 2, center_y + int(h * 0.082)), floating_data['sub'], font_f_sub, "#d4e4f0", radius=2)

            # 7. Subtitles (Sentence by sentence, fades in and cleanly disappears)
            active_sub = next((s for s in subtitles if s['start'] <= t < s['end']), None)
            if active_sub:
                t_rel = t - active_sub['start']
                dur_sub = active_sub['end'] - active_sub['start']
                fade = 1.0
                if t_rel < 0.25: fade = ease(t_rel / 0.25)
                elif t_rel > dur_sub - 0.25: fade = 1.0 - ease((t_rel - (dur_sub - 0.25)) / 0.25)

                if fade > 0.05:
                    sub_y = int(h * 0.81)
                    font_sz = max(13, w // 24)
                    font_sub = get_kanit(font_sz, weight='bold')
                    max_lw = max(d.textlength(ltxt, font=font_sub) for ltxt, _ in active_sub['lines'])
                    while font_sz > 9 and max_lw > w * 0.90:
                        font_sz -= 1
                        font_sub = get_kanit(font_sz, weight='bold')
                        max_lw = max(d.textlength(ltxt, font=font_sub) for ltxt, _ in active_sub['lines'])

                    shadow_alpha = int(230 * fade)
                    line_step = max(int(font_sz * 1.45), int(h * 0.035))

                    for line_idx, (line_txt, line_col) in enumerate(active_sub['lines']):
                        ly = sub_y + line_idx * line_step
                        draw_shadowed_text(d, (w / 2, ly), line_txt, font_sub, line_col, shadow_fill=(0, 0, 0, shadow_alpha), radius=2)

            # 8. Source Attribution Footer (Clean frameless dropshadow)
            footer_font = get_kanit(max(9, w // 38), weight='medium')
            draw_shadowed_text(d, (w * 0.5, h * 0.95), "ข้อมูล: สภาพัฒน์ (NESDC) • แผนที่: Natural Earth", footer_font, (210, 230, 245, 200), shadow_fill=(0, 0, 0, 180), radius=1)

            # Save check frames
            check_points = [
                (2.5, '00_world_orbit_title'),
                (7.5, '01_zoom_thailand_gdp'),
                (16.0, '02_govt_revenue'),
                (30.0, '03_zoom_bkk_lift'),
                (47.0, '04_pan_rayong_lift'),
                (64.0, '05_sweep_isan_glow'),
                (78.0, '06_per_capita_average'),
                (89.0, '07_zoomout_world_cta')
            ]
            for sec, label in check_points:
                if abs(t - sec) < 1.0 / fps:
                    sample_frames[label] = im.convert('RGB')

            proc.stdin.write(im.convert('RGB').tobytes())

            if i % 300 == 0:
                print(f"  Frame {i}/{total_frames} ({t:.1f}s)...", flush=True)

    finally:
        proc.stdin.close()
        code = proc.wait()

    if code != 0:
        raise RuntimeError('FFmpeg encoding failed; inspect exports/render_ep01_world.log')

    (R / 'work').mkdir(exist_ok=True)
    for k, img in sample_frames.items():
        img.save(R / f'work/check_world_{k}.jpg')

    print(f"Video track rendered: {out_path}", flush=True)
    return out_path

def mix_audio_clean(video_path, output_path):
    ff_bin = ff()
    voice_path = R / 'audio/ep01_90s_voice.mp3'

    cmd = [
        ff_bin, '-y',
        '-i', str(video_path),
        '-i', str(voice_path),
        '-filter_complex', '[1:a]apad,loudnorm=I=-16:TP=-1.5:LRA=11[a]',
        '-map', '0:v:0',
        '-map', '[a]',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-movflags', '+faststart',
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stderr=(R / 'exports/mix_ep01_world.log').open('w'))
    subprocess.run([ff_bin, '-v', 'error', '-i', str(output_path), '-f', 'null', '-'], check=True)
    print(f"Final clean video saved: {output_path}", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true', help='Render fast preview at 360x640')
    parser.add_argument('--full', action='store_true', help='Render full resolution at 1080x1920')
    args = parser.parse_args()

    if args.preview:
        v_out = render_ep01_90s(width=360, height=640, output_name='EP01_WORLD_90S_PREVIEW_360p_silent.mp4')
        final_out = R / 'exports/EP01_WORLD_90S_PREVIEW_360p_voice_only.mp4'
        mix_audio_clean(v_out, final_out)
        print("\n=== WORLD 90S PREVIEW READY ===")
        print(f"File: {final_out}")
    elif args.full:
        v_out = render_ep01_90s(width=1080, height=1920, output_name='EP01_WORLD_90S_FULL_1080p_silent.mp4')
        final_out = R / 'exports/EP01_WORLD_90S_FULL_1080p.mp4'
        mix_audio_clean(v_out, final_out)
        print("\n=== FULL 1080P WORLD 90S READY ===")
        print(f"File: {final_out}")
    else:
        print("Please specify --preview or --full")

if __name__ == '__main__':
    main()
