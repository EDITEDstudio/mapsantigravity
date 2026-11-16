"""Episode 01: ประเทศไทยมีรายได้รวมเท่าไหร่?
Generates map motion, overlays, speech-sync, audio mix with ducking, and previews.
"""
from pathlib import Path
import argparse, json, math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import imageio_ffmpeg

R = Path(__file__).resolve().parents[1]
Image.MAX_IMAGE_PIXELS = 300_000_000

def ff():
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_font(size, weight='bold'):
    ttc_path = Path('/System/Library/Fonts/Supplemental/SukhumvitSet.ttc')
    if ttc_path.exists():
        idx_map = {
            'thin': 0, 'light': 1, 'text': 2, 'medium': 3, 'semi_bold': 4, 'bold': 5
        }
        return ImageFont.truetype(str(ttc_path), size, index=idx_map.get(weight, 5))
    
    # Fallbacks
    candidates = [
        Path('/Library/Fonts/Arial Unicode.ttf'),
        Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf'),
        Path('/System/Library/Fonts/Supplemental/Thonburi.ttc')
    ]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    raise RuntimeError('Thai capable font missing')

def rings(g):
    if g['type'] == 'Polygon':
        return g['coordinates']
    if g['type'] == 'MultiPolygon':
        return [r for p in g['coordinates'] for r in p]
    raise ValueError('Polygon geometry required')

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

def ensure_ambient_music():
    out = R / 'assets/music/ep01_ambient.wav'
    if out.exists():
        return
    sr = 48000
    duration = 31.5
    t = np.arange(int(sr * duration)) / sr
    chords = [
        (0.0, 7.5, [146.83, 174.61, 220.00, 293.66]),
        (7.5, 15.0, [116.54, 146.83, 174.61, 233.08]),
        (15.0, 22.5, [130.81, 164.81, 196.00, 261.63]),
        (22.5, 31.5, [146.83, 174.61, 220.00, 293.66])
    ]
    wave_out = np.zeros(len(t))
    for start_sec, end_sec, freqs in chords:
        mask = (t >= start_sec) & (t < end_sec)
        t_chord = t[mask] - start_sec
        dur = end_sec - start_sec
        env = np.minimum(1.0, t_chord / 0.8) * np.minimum(1.0, (dur - t_chord) / 0.8)
        chord_sig = np.zeros(len(t_chord))
        for f in freqs:
            chord_sig += 0.05 * np.sin(2 * np.pi * f * t_chord)
            chord_sig += 0.015 * np.sin(2 * np.pi * f * 2 * t_chord)
        wave_out[mask] += chord_sig * env
    master_env = np.minimum(1.0, t / 0.5) * np.minimum(1.0, (duration - t) / 1.5)
    wave_out = wave_out * master_env
    wave_out = wave_out / (np.max(np.abs(wave_out)) + 1e-6) * 0.40
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((wave_out * 32767).astype('<i2').tobytes())

def generate_srt(subtitles, srt_path):
    def stamp(sec):
        ms = round(sec * 1000)
        return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'
    lines = []
    for i, s in enumerate(subtitles):
        text_full = ' '.join(s['lines'])
        lines.append(f"{i + 1}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{text_full}\n")
    srt_path.write_text('\n'.join(lines), encoding='utf-8')

def render_ep01(width=360, height=640, fps=30, output_name='ep01_preview.mp4'):
    ensure_ambient_music()
    timing_file = R / 'audio/ep01_thailand_revenue_timing.json'
    timing = json.loads(timing_file.read_text(encoding='utf-8'))
    duration = max(30.5, timing['durationSec'] + 0.6)

    # 2-line structured subtitles for optimal mobile legibility
    structured_subs = [
        {'start': 0.0, 'end': 4.584, 'lines': ['รู้ไหมครับว่า ในหนึ่งปี', 'ประเทศไทยของเรามีรายได้รวมเท่าไหร่กันแน่']},
        {'start': 4.934, 'end': 10.982, 'lines': ['ถ้าดูจาก GDP หรือมูลค่าเศรษฐกิจรวม', 'สภาพัฒน์ระบุว่าอยู่ที่ราว 18 ล้านล้านบาท']},
        {'start': 11.332, 'end': 17.332, 'lines': ['แต่ถ้าเป็นรายได้สุทธิที่รัฐบาลจัดเก็บเข้าคลัง', 'จะอยู่ที่ประมาณ 2.8 ล้านล้านบาทต่อปี']},
        {'start': 17.682, 'end': 24.234, 'lines': ['และที่น่าทึ่งคือ รายได้เหล่านี้กว่า 60%', 'กระจุกตัวอยู่แค่ในกรุงเทพฯ และภาคตะวันออกเท่านั้น']},
        {'start': 24.584, 'end': 29.600, 'lines': ['แล้วจังหวัดของคุณ สร้างรายได้เป็นอันดับที่เท่าไหร่?', 'คอมเมนต์บอกกันได้เลยครับ']}
    ]

    srt_path = R / 'audio/ep01_thailand_revenue.srt'
    generate_srt(structured_subs, srt_path)

    # Load geographical data
    countries = json.loads((R / 'data/processed/countries.geojson').read_text(encoding='utf-8'))['features']
    provinces = json.loads((R / 'data/processed/thailand_provinces.geojson').read_text(encoding='utf-8'))['features']
    tha_country = next((c for c in countries if c['properties'].get('ADM0_A3') == 'THA'), None)

    # Targets for lift (Bangkok + EEC)
    lift_target_names = ['Bangkok Metropolis', 'Rayong', 'Chon Buri', 'Chachoengsao']
    lift_provinces = [p for p in provinces if p['properties'].get('name') in lift_target_names]

    # Terrain
    cached_terrain_path = R / 'work/cached_terrain.png'
    if not cached_terrain_path.exists():
        raise RuntimeError('Run base terrain cache first: work/cached_terrain.png')
    terrain = Image.open(cached_terrain_path).convert('RGB')
    geo = [85, -5, 120, 32]

    # Camera waypoints
    waypoints = [
        (0.0,  102.0, 13.0, 24.5), # Regional overview
        (3.5,  101.0, 13.0, 16.5), # Frame Thailand nicely
        (10.5, 101.0, 13.0, 16.5), # Hold on Thailand
        (16.5, 100.8, 13.4, 11.5), # Drift toward Central / East
        (18.5, 101.1, 13.3, 4.6),  # Close-up on EEC & Bangkok
        (23.5, 101.1, 13.3, 4.6),  # Hold on EEC
        (26.0, 101.0, 13.0, 16.5), # Pull back to full Thailand
        (31.0, 101.0, 13.0, 16.5)  # Final hold
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
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=(R / 'exports/render_ep01.log').open('w'))

    lift_start = 17.68
    lift_end = 24.5
    sample_frames = {}

    print(f"Rendering Episode 1 ({w}x{h}, {duration:.1f}s, {total_frames} frames)...", flush=True)

    try:
        for i in range(total_frames):
            t = i / fps
            box = interp_camera(t, waypoints, w, h)

            def xy(p):
                return (
                    (p[0] - box[0]) / (box[2] - box[0]) * w,
                    (box[3] - p[1]) / (box[3] - box[1]) * h
                )

            region = (
                (box[0] - geo[0]) / (geo[2] - geo[0]) * terrain.width,
                (geo[3] - box[3]) / (geo[3] - geo[1]) * terrain.height,
                (box[2] - geo[0]) / (geo[2] - geo[0]) * terrain.width,
                (geo[3] - box[1]) / (geo[3] - geo[1]) * terrain.height
            )

            im = terrain.transform((w, h), Image.Transform.EXTENT, region, Image.Resampling.BILINEAR).convert('RGBA')
            d = ImageDraw.Draw(im)

            # 1. Neighboring countries borders
            for c in countries:
                if c['properties'].get('ADM0_A3') != 'THA':
                    for ring in rings(c['geometry']):
                        pts = [xy(p) for p in ring]
                        d.line(pts, fill=(220, 235, 228, 140), width=max(1, w // 450))

            # 2. Thailand provincial borders
            for f in provinces:
                for ring in rings(f['geometry']):
                    d.line([xy(p) for p in ring], fill=(240, 248, 255, 90), width=max(1, w // 540))

            # 3. Thailand country border outline glow (Active throughout)
            if tha_country:
                tha_glow = ease((t - 0.5) / 1.5) * (1 - ease((t - 29.5) / 1.0))
                if tha_glow > 0.05:
                    edge = Image.new('RGBA', (w, h))
                    ed = ImageDraw.Draw(edge)
                    for ring in rings(tha_country['geometry']):
                        ed.line([xy(p) for p in ring], fill=(255, 219, 76, int(180 * tha_glow)), width=max(2, w // 200))
                    im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 100))))
                    im = Image.alpha_composite(im, edge)

            # 4. Lifted Provinces (Bangkok + EEC)
            lift = 0.0
            if lift_start <= t <= lift_end:
                lift = ease((t - lift_start) / 0.8) * (1.0 - ease((t - (lift_end - 0.8)) / 0.8))

            if lift > 0.01:
                mask = Image.new('L', (w, h))
                md = ImageDraw.Draw(mask)
                for f in lift_provinces:
                    polygons = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
                    for poly in polygons:
                        md.polygon([xy(p) for p in poly[0]], fill=255)
                        for hole in poly[1:]:
                            md.polygon([xy(p) for p in hole], fill=0)

                dx = int(10 * w / 1080 * lift)
                dy = int(-45 * h / 1920 * lift)

                shifted = Image.new('L', (w, h))
                shifted.paste(mask, (dx, dy))

                shadow = Image.new('L', (w, h))
                shadow.paste(mask, (dx + int(10 * lift), dy + int(20 * lift)))
                im = Image.alpha_composite(
                    im,
                    Image.composite(
                        Image.new('RGBA', (w, h), (0, 0, 0, int(185 * lift))),
                        Image.new('RGBA', (w, h)),
                        shadow.filter(ImageFilter.GaussianBlur(max(3, w // 90)))
                    )
                )

                lifted = Image.new('RGBA', (w, h))
                lifted.paste(im, (dx, dy))
                im = Image.composite(lifted, im, shifted)

                tint = Image.new('RGBA', (w, h), (255, 191, 47, int(90 * lift)))
                im = Image.alpha_composite(im, Image.composite(tint, Image.new('RGBA', (w, h)), shifted))

                edge = Image.new('RGBA', (w, h))
                ed = ImageDraw.Draw(edge)
                for f in lift_provinces:
                    for ring in rings(f['geometry']):
                        ed.line([(xy(p)[0] + dx, xy(p)[1] + dy) for p in ring], fill=(255, 225, 90, int(255 * lift)), width=max(2, w // 160))
                im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 80))))
                im = Image.alpha_composite(im, edge)

            # Re-draw for UI elements
            d = ImageDraw.Draw(im)

            # 5. Top Header Card (Title & Series)
            header_y = int(h * 0.055)
            header_h = int(h * 0.082)
            d.rounded_rectangle((w * 0.05, header_y, w * 0.95, header_y + header_h), radius=max(8, w // 45), fill=(8, 18, 28, 225), outline=(255, 212, 77, 180), width=1)
            
            badge_font = get_font(max(10, w // 34), weight='bold')
            d.text((w * 0.5, header_y + header_h * 0.30), "พิกัดเงิน • ภูมิศาสตร์เศรษฐกิจ", font=badge_font, fill="#ffd44d", anchor="mm")
            
            title_font = get_font(max(13, w // 22), weight='bold')
            d.text((w * 0.5, header_y + header_h * 0.72), "ประเทศไทยมีรายได้รวมเท่าไหร่?", font=title_font, fill="#ffffff", anchor="mm")

            # 6. Dynamic Context / Stat Badges
            stat_card = None
            stat_sub = None
            if 4.93 <= t < 11.0:
                stat_card = "GDP รวมทั้งประเทศ: ~18 ล้านล้านบาท"
                stat_sub = "มูลค่าผลผลิตมวลรวมสินค้าและบริการ (สภาพัฒน์)"
            elif 11.0 <= t < 17.3:
                stat_card = "รายได้สุทธิรัฐบาลจัดเก็บ: ~2.8 ล้านล้านบาท/ปี"
                stat_sub = "ภาษีสรรพากร • สรรพสามิต • ศุลกากร • รัฐวิสาหกิจ"
            elif 17.3 <= t < 24.3:
                stat_card = "กทม. + ภาคตะวันออก: > 60% ของ GDP"
                stat_sub = "ระยอง ชลบุรี กทม. ศูนย์รวมอุตสาหกรรมและการเงิน"
            elif 24.3 <= t < 29.8:
                stat_card = "77 จังหวัดทั่วไทย"
                stat_sub = "จังหวัดของคุณสร้างรายได้อันดับไหน? คอมเมนต์เลย"

            if stat_card:
                sc_y = int(h * 0.16)
                sc_h = int(h * 0.070)
                d.rounded_rectangle((w * 0.05, sc_y, w * 0.95, sc_y + sc_h), radius=max(8, w // 45), fill=(10, 24, 38, 225), outline=(88, 213, 181, 190), width=1)
                d.text((w * 0.5, sc_y + sc_h * 0.35), stat_card, font=get_font(max(11, w // 25), weight='bold'), fill="#ffd44d", anchor="mm")
                if stat_sub:
                    d.text((w * 0.5, sc_y + sc_h * 0.74), stat_sub, font=get_font(max(9, w // 36), weight='medium'), fill="#edf3fa", anchor="mm")

            # 7. Subtitles (2 lines inside dark pill for ultra readability)
            active_sub = next((s for s in structured_subs if s['start'] <= t < s['end']), None)
            if active_sub:
                sub_lines = active_sub['lines']
                font_sz = max(13, w // 23)
                sub_font = get_font(font_sz, weight='bold')
                
                # Check line width and adjust size if needed
                max_lw = max(d.textlength(l, font=sub_font) for l in sub_lines)
                while font_sz > 10 and max_lw > w * 0.88:
                    font_sz -= 1
                    sub_font = get_font(font_sz, weight='bold')
                    max_lw = max(d.textlength(l, font=sub_font) for l in sub_lines)

                line_h = int(font_sz * 1.5)
                tot_h = len(sub_lines) * line_h
                sub_cy = int(h * 0.77)

                pad_x = int(w * 0.04)
                pad_y = int(h * 0.012)
                pill_box = (
                    w / 2 - max_lw / 2 - pad_x,
                    sub_cy - tot_h / 2 - pad_y,
                    w / 2 + max_lw / 2 + pad_x,
                    sub_cy + tot_h / 2 + pad_y
                )

                d.rounded_rectangle(pill_box, radius=max(8, w // 40), fill=(6, 15, 24, 225), outline=(255, 212, 77, 160), width=1)
                for line_idx, line_txt in enumerate(sub_lines):
                    ly = sub_cy - tot_h / 2 + line_idx * line_h + line_h / 2
                    d.text((w / 2, ly), line_txt, font=sub_font, fill="#ffffff", anchor="mm")

            # 8. Source Attribution Footer
            footer_font = get_font(max(10, w // 34), weight='bold')
            d.text((w * 0.5, h * 0.94), "ข้อมูล: สภาพัฒน์ (NESDC) • แผนที่: Natural Earth", font=footer_font, fill=(210, 230, 245, 220), anchor="mm")

            # Save representative check frames
            if abs(t - 2.0) < 1.0 / fps:
                sample_frames['intro'] = im.convert('RGB')
            elif abs(t - 8.0) < 1.0 / fps:
                sample_frames['gdp'] = im.convert('RGB')
            elif abs(t - 14.0) < 1.0 / fps:
                sample_frames['govt_revenue'] = im.convert('RGB')
            elif abs(t - 21.0) < 1.0 / fps:
                sample_frames['eec_lift'] = im.convert('RGB')
            elif abs(t - 27.0) < 1.0 / fps:
                sample_frames['cta'] = im.convert('RGB')

            proc.stdin.write(im.convert('RGB').tobytes())

            if i % 150 == 0:
                print(f"  Frame {i}/{total_frames} ({t:.1f}s)...", flush=True)

    finally:
        proc.stdin.close()
        code = proc.wait()

    if code != 0:
        raise RuntimeError('FFmpeg video encoding failed; inspect exports/render_ep01.log')

    (R / 'work').mkdir(exist_ok=True)
    for k, img in sample_frames.items():
        img.save(R / f'work/check_ep01_{k}.jpg')

    print(f"Video track rendered: {out_path}", flush=True)
    return out_path

def mix_audio(video_path, output_path, include_music=False):
    ff_bin = ff()
    voice_path = R / 'audio/ep01_thailand_revenue_voice.mp3'
    music_path = R / 'assets/music/ep01_ambient.wav'
    whoosh_path = R / 'assets/sfx/whoosh.wav'
    whoosh_delay_ms = 17700

    if include_music:
        cmd = [
            ff_bin, '-y',
            '-i', str(video_path),
            '-i', str(voice_path),
            '-i', str(music_path),
            '-i', str(whoosh_path),
            '-filter_complex',
            f"[1:a]apad,asplit=2[v][sc];"
            f"[2:a]volume=0.45[m];"
            f"[m][sc]sidechaincompress=threshold=0.018:ratio=8:attack=15:release=250[duck];"
            f"[3:a]volume=0.30,adelay={whoosh_delay_ms}|{whoosh_delay_ms}[s];"
            f"[v][duck][s]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
            '-map', '0:v',
            '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-movflags', '+faststart',
            str(output_path)
        ]
    else:
        cmd = [
            ff_bin, '-y',
            '-i', str(video_path),
            '-i', str(voice_path),
            '-filter_complex',
            '[1:a]apad,loudnorm=I=-16:TP=-1.5:LRA=11[a]',
            '-map', '0:v:0',
            '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-movflags', '+faststart',
            str(output_path)
        ]
    subprocess.run(cmd, check=True, stderr=(R / 'exports/mix_ep01.log').open('w'))
    subprocess.run([ff_bin, '-v', 'error', '-i', str(output_path), '-f', 'null', '-'], check=True)
    print(f"Final mixed video verified and saved: {output_path} (music={include_music})", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true', help='Render fast preview at 360x640')
    parser.add_argument('--full', action='store_true', help='Render full resolution at 1080x1920')
    parser.add_argument('--with-music', action='store_true', help='Include background music (default is voice only)')
    args = parser.parse_args()

    if args.preview:
        v_out = render_ep01(width=360, height=640, output_name='EP01_PREVIEW_ประเทศไทยมีรายได้เท่าไหร่_360p.mp4')
        final_out = R / 'exports/EP01_PREVIEW_ประเทศไทยมีรายได้เท่าไหร่_360p_with_sound.mp4'
        mix_audio(v_out, final_out, include_music=args.with_music)
        print("\n=== PREVIEW READY ===")
        print(f"File: {final_out}")
    elif args.full:
        v_out = render_ep01(width=1080, height=1920, output_name='EP01_FULL_ประเทศไทยมีรายได้เท่าไหร่_1080p.mp4')
        final_out = R / 'exports/EP01_FULL_ประเทศไทยมีรายได้เท่าไหร่_1080p.mp4'
        mix_audio(v_out, final_out, include_music=args.with_music)
        print("\n=== FULL 1080P EXPORT READY ===")
        print(f"File: {final_out}")
    else:
        print("Please specify --preview or --full")

if __name__ == '__main__':
    main()
