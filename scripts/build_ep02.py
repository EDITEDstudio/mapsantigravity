"""Episode 02: เงินเดือน 20,000 บาท อยู่จังหวัดไหนเหลือเงินเยอะที่สุด?
Anti-Jitter & Ultra-Smooth Architecture:
1. Monotonic PCHIP Cubic Hermite Camera Spline (C1 continuous velocity, zero stop-and-go jerk, zero overshoot)
2. Sub-pixel cropped EXTENT terrain with BICUBIC resampling (zero texel crawling/shimmer)
3. Sub-pixel AFFINE province 3D lift + smooth float edges (zero 1px integer stepping)
4. Measured millisecond-exact micro-turn timing from audio/ep02_salary_20k_timing.json
5. Step-by-step Frameless Ledger with 8 crisp white-circle icons (Salary -> Room -> Transit -> Food -> Net Savings)
"""
from pathlib import Path
import argparse, ctypes, json, math, subprocess, time
import multiprocessing as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

R = Path(__file__).resolve().parents[1]
Image.MAX_IMAGE_PIXELS = 300_000_000


def ff():
    return imageio_ffmpeg.get_ffmpeg_exe()


def get_kanit(size, weight='bold'):
    return (float(size), str(weight))


class _CoreTextEngine:
    """macOS CoreText + CoreGraphics shaper for crisp OpenType Thai tone-mark stacking."""
    def __init__(self):
        cf = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        ct = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreText.framework/CoreText')
        cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')

        c_void_p = ctypes.c_void_p
        c_size_t = ctypes.c_size_t
        c_double = ctypes.c_double
        c_int = ctypes.c_int

        cf.CFStringCreateWithCString.restype = c_void_p
        cf.CFStringCreateWithCString.argtypes = [c_void_p, ctypes.c_char_p, ctypes.c_uint32]
        cf.CFRelease.argtypes = [c_void_p]
        cf.CFDictionaryCreateMutable.restype = c_void_p
        cf.CFDictionaryCreateMutable.argtypes = [c_void_p, ctypes.c_long, c_void_p, c_void_p]
        cf.CFDictionarySetValue.argtypes = [c_void_p, c_void_p, c_void_p]
        cf.CFAttributedStringCreate.restype = c_void_p
        cf.CFAttributedStringCreate.argtypes = [c_void_p, c_void_p, c_void_p]

        cg.CGDataProviderCreateWithFilename.restype = c_void_p
        cg.CGDataProviderCreateWithFilename.argtypes = [ctypes.c_char_p]
        cg.CGFontCreateWithDataProvider.restype = c_void_p
        cg.CGFontCreateWithDataProvider.argtypes = [c_void_p]
        cg.CGColorSpaceCreateDeviceRGB.restype = c_void_p
        cg.CGBitmapContextCreate.restype = c_void_p
        cg.CGBitmapContextCreate.argtypes = [c_void_p, c_size_t, c_size_t, c_size_t, c_size_t, c_void_p, ctypes.c_uint32]
        cg.CGContextRelease.argtypes = [c_void_p]
        cg.CGContextSetTextDrawingMode.argtypes = [c_void_p, c_int]
        cg.CGContextSetRGBFillColor.argtypes = [c_void_p, c_double, c_double, c_double, c_double]
        cg.CGContextSetRGBStrokeColor.argtypes = [c_void_p, c_double, c_double, c_double, c_double]
        cg.CGContextSetLineWidth.argtypes = [c_void_p, c_double]
        cg.CGContextSetLineJoin.argtypes = [c_void_p, c_int]
        cg.CGContextSetTextPosition.argtypes = [c_void_p, c_double, c_double]

        ct.CTFontCreateWithGraphicsFont.restype = c_void_p
        ct.CTFontCreateWithGraphicsFont.argtypes = [c_void_p, c_double, c_void_p, c_void_p]
        ct.CTFontGetCapHeight.restype = c_double
        ct.CTFontGetCapHeight.argtypes = [c_void_p]
        ct.CTLineCreateWithAttributedString.restype = c_void_p
        ct.CTLineCreateWithAttributedString.argtypes = [c_void_p]
        ct.CTLineGetTypographicBounds.restype = c_double
        ct.CTLineGetTypographicBounds.argtypes = [c_void_p, ctypes.POINTER(c_double), ctypes.POINTER(c_double), ctypes.POINTER(c_double)]
        ct.CTLineDraw.argtypes = [c_void_p, c_void_p]

        self.cf = cf
        self.ct = ct
        self.cg = cg
        self.c_double = c_double
        self.kCTFontAttributeName = c_void_p.in_dll(ct, 'kCTFontAttributeName')
        self.kCTForegroundColorFromContextAttributeName = c_void_p.in_dll(ct, 'kCTForegroundColorFromContextAttributeName')
        self.kCFBooleanTrue = c_void_p.in_dll(cf, 'kCFBooleanTrue')
        self.kKeys = c_void_p.in_dll(cf, 'kCFTypeDictionaryKeyCallBacks')
        self.kVals = c_void_p.in_dll(cf, 'kCFTypeDictionaryValueCallBacks')
        self.cs = cg.CGColorSpaceCreateDeviceRGB()

        self.cgfonts = {}
        self.ctfonts = {}
        self.sprite_cache = {}

    def _get_ctfont(self, size, weight):
        key = (round(float(size), 2), weight)
        if key in self.ctfonts:
            return self.ctfonts[key]
        if weight not in self.cgfonts:
            font_file = {
                'regular': 'Kanit-Regular.ttf',
                'medium': 'Kanit-Medium.ttf',
                'semi_bold': 'Kanit-SemiBold.ttf',
                'bold': 'Kanit-Bold.ttf',
                'extra_bold': 'Kanit-ExtraBold.ttf'
            }.get(weight, 'Kanit-Bold.ttf')
            fpath = R / 'assets/fonts' / font_file
            bpath = str(fpath if fpath.exists() else '/System/Library/Fonts/Supplemental/SukhumvitSet.ttc').encode('utf-8')
            prov = self.cg.CGDataProviderCreateWithFilename(bpath)
            self.cgfonts[weight] = self.cg.CGFontCreateWithDataProvider(prov)
            self.cf.CFRelease(prov)
        ctfont = self.ct.CTFontCreateWithGraphicsFont(self.cgfonts[weight], float(size), None, None)
        cap_h = self.ct.CTFontGetCapHeight(ctfont)
        self.ctfonts[key] = (ctfont, cap_h)
        return self.ctfonts[key]

    def _make_line(self, text, size, weight):
        ctfont, cap_h = self._get_ctfont(size, weight)
        attrs = self.cf.CFDictionaryCreateMutable(None, 2, self.kKeys, self.kVals)
        self.cf.CFDictionarySetValue(attrs, self.kCTFontAttributeName, ctfont)
        self.cf.CFDictionarySetValue(attrs, self.kCTForegroundColorFromContextAttributeName, self.kCFBooleanTrue)
        s = self.cf.CFStringCreateWithCString(None, text.encode('utf-8'), 0x08000100)
        astring = self.cf.CFAttributedStringCreate(None, s, attrs)
        line = self.ct.CTLineCreateWithAttributedString(astring)
        self.cf.CFRelease(astring)
        self.cf.CFRelease(s)
        self.cf.CFRelease(attrs)
        asc = self.c_double()
        desc = self.c_double()
        lead = self.c_double()
        tw = self.ct.CTLineGetTypographicBounds(line, ctypes.byref(asc), ctypes.byref(desc), ctypes.byref(lead))
        return line, tw, asc.value, desc.value, cap_h

    def measure_width(self, text, font_spec):
        if not text:
            return 0.0
        size, weight = font_spec
        line, tw, _, _, _ = self._make_line(text, size, weight)
        self.cf.CFRelease(line)
        return tw

    def get_sprite(self, text, font_spec, fill_rgb, stroke_w):
        size, weight = font_spec
        key = (text, round(float(size), 2), weight, fill_rgb, int(stroke_w))
        if key in self.sprite_cache:
            return self.sprite_cache[key]
        if len(self.sprite_cache) > 1500:
            self.sprite_cache.clear()

        line, tw, asc, desc, cap_h = self._make_line(text, size, weight)
        sw = max(1, int(stroke_w))
        sh_off = max(2, sw)
        pad_x = sw + sh_off + 6
        pad_top = sw + int(size * 0.48) + 6
        pad_bot = sw + sh_off + int(size * 0.36) + 6

        W = max(4, int(math.ceil(tw + 2 * pad_x + 2)))
        H = max(4, int(math.ceil(asc + desc + pad_top + pad_bot + 2)))
        base_y_from_bot = pad_bot + desc
        base_y_from_top = H - base_y_from_bot
        mid_y = base_y_from_top - cap_h * 0.42

        buf = np.zeros((H, W, 4), dtype=np.uint8)
        ctx = self.cg.CGBitmapContextCreate(buf.ctypes.data, W, H, 8, W * 4, self.cs, 1)
        self.cg.CGContextSetLineJoin(ctx, 1)
        self.cg.CGContextSetLineWidth(ctx, sw * 2.0)

        # 1. Soft directional drop shadow
        self.cg.CGContextSetRGBStrokeColor(ctx, 0.0, 0.0, 0.0, 150.0 / 255.0)
        self.cg.CGContextSetRGBFillColor(ctx, 0.0, 0.0, 0.0, 150.0 / 255.0)
        self.cg.CGContextSetTextDrawingMode(ctx, 2)
        self.cg.CGContextSetTextPosition(ctx, pad_x + sh_off * 0.5, base_y_from_bot - sh_off)
        self.ct.CTLineDraw(line, ctx)

        # 2. Dark outline stroke
        self.cg.CGContextSetRGBStrokeColor(ctx, 10.0 / 255.0, 18.0 / 255.0, 28.0 / 255.0, 230.0 / 255.0)
        self.cg.CGContextSetTextDrawingMode(ctx, 1)
        self.cg.CGContextSetTextPosition(ctx, pad_x, base_y_from_bot)
        self.ct.CTLineDraw(line, ctx)

        # 3. Crisp color fill
        self.cg.CGContextSetRGBFillColor(ctx, fill_rgb[0] / 255.0, fill_rgb[1] / 255.0, fill_rgb[2] / 255.0, 1.0)
        self.cg.CGContextSetTextDrawingMode(ctx, 0)
        self.cg.CGContextSetTextPosition(ctx, pad_x, base_y_from_bot)
        self.ct.CTLineDraw(line, ctx)

        self.cg.CGContextRelease(ctx)
        self.cf.CFRelease(line)

        spr = Image.frombytes('RGBa', (W, H), buf.tobytes()).convert('RGBA')
        res = (spr, float(pad_x), float(tw), float(mid_y))
        self.sprite_cache[key] = res
        return res


_CT_ENGINE = None


def _ct():
    global _CT_ENGINE
    if _CT_ENGINE is None:
        _CT_ENGINE = _CoreTextEngine()
    return _CT_ENGINE


def measure_text_width(text, font_spec):
    return _ct().measure_width(text, font_spec)


def rings(g):
    if g['type'] == 'Polygon':
        return g['coordinates']
    if g['type'] == 'MultiPolygon':
        return [r for p in g['coordinates'] for r in p]
    return []


def smootherstep(x):
    x = max(0.0, min(1.0, float(x)))
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def hex_rgba(hex_str, alpha=255):
    h = hex_str.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(max(0, min(255, alpha))))


def compute_pchip_tangents(ts, ys):
    """Fritsch-Carlson monotonic cubic Hermite tangents: C1 smooth, zero overshoot."""
    n = len(ts)
    if n < 2:
        return [0.0] * n
    h = [ts[i + 1] - ts[i] for i in range(n - 1)]
    delta = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    d = [0.0] * n
    for i in range(1, n - 1):
        if delta[i - 1] * delta[i] > 0:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            d[i] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i])
        else:
            d[i] = 0.0
    d[0] = delta[0]
    if n > 2 and d[0] * delta[0] <= 0:
        d[0] = 0.0
    d[-1] = delta[-1]
    if n > 2 and d[-1] * delta[-1] <= 0:
        d[-1] = 0.0
    return d


class SmoothCameraSpline:
    def __init__(self, waypoints):
        self.ts = [wp[0] for wp in waypoints]
        self.cxs = [wp[1] for wp in waypoints]
        self.cys = [wp[2] for wp in waypoints]
        self.spans = [wp[3] for wp in waypoints]
        self.dx = compute_pchip_tangents(self.ts, self.cxs)
        self.dy = compute_pchip_tangents(self.ts, self.cys)
        self.ds = compute_pchip_tangents(self.ts, self.spans)

    def _eval_dim(self, t, vals, tangs):
        if t <= self.ts[0]:
            return vals[0]
        if t >= self.ts[-1]:
            return vals[-1]
        for i in range(len(self.ts) - 1):
            t0, t1 = self.ts[i], self.ts[i + 1]
            if t0 <= t <= t1:
                h = t1 - t0
                u = (t - t0) / h
                u2 = u * u
                u3 = u2 * u
                h00 = 2 * u3 - 3 * u2 + 1
                h10 = u3 - 2 * u2 + u
                h01 = -2 * u3 + 3 * u2
                h11 = u3 - u2
                return h00 * vals[i] + h10 * h * tangs[i] + h01 * vals[i + 1] + h11 * h * tangs[i + 1]
        return vals[-1]

    def box(self, t, w, h):
        cx = self._eval_dim(t, self.cxs, self.dx)
        cy = self._eval_dim(t, self.cys, self.dy)
        span = self._eval_dim(t, self.spans, self.ds)
        sh = span
        sw = sh * (w / h)
        return [cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2]


def draw_crisp_text(target_im, pos, text, font, fill_rgba, alpha_scale=1.0, stroke_w=2, anchor='mm'):
    if not text:
        return
    a_eff = (fill_rgba[3] / 255.0) * float(alpha_scale)
    if a_eff <= 0.01:
        return
    spr, pad_x, tw, mid_y = _ct().get_sprite(text, font, fill_rgba[:3], stroke_w)
    x, y = pos
    if anchor == 'mm':
        x0 = int(round(x - (pad_x + tw * 0.5)))
    elif anchor == 'lm':
        x0 = int(round(x - pad_x))
    elif anchor == 'rm':
        x0 = int(round(x - (pad_x + tw)))
    else:
        x0 = int(round(x - (pad_x + tw * 0.5)))
    y0 = int(round(y - mid_y))

    ix0 = max(0, x0)
    iy0 = max(0, y0)
    ix1 = min(target_im.width, x0 + spr.width)
    iy1 = min(target_im.height, y0 + spr.height)
    if ix1 <= ix0 or iy1 <= iy0:
        return

    src_box = (ix0 - x0, iy0 - y0, ix1 - x0, iy1 - y0)
    if a_eff >= 0.995:
        target_im.alpha_composite(spr, dest=(ix0, iy0), source=src_box[:2]) if (ix1 - x0 == spr.width and iy1 - y0 == spr.height) else target_im.alpha_composite(spr.crop(src_box), dest=(ix0, iy0))
    else:
        sub = spr.crop(src_box)
        r, g, b, a = sub.split()
        a = a.point(lambda v: int(v * a_eff))
        sub.putalpha(a)
        target_im.alpha_composite(sub, dest=(ix0, iy0))


def bezier_arc(p0, p1, progress, steps=40, lift_deg=0.42):
    mx = (p0[0] + p1[0]) / 2.0
    my = (p0[1] + p1[1]) / 2.0
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dist = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / dist, dx / dist
    if ny < 0:
        nx, ny = -nx, -ny
    ctrl = (mx + nx * dist * lift_deg, my + ny * dist * lift_deg)
    pts = []
    n_pts = max(2, int(steps * progress))
    for i in range(n_pts + 1):
        u = min(progress, i / steps)
        x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * ctrl[0] + u ** 2 * p1[0]
        y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * ctrl[1] + u ** 2 * p1[1]
        pts.append((x, y))
    return pts


def draw_province_lift(im, provinces_list, lift, xy, w, h, fill_rgb=(255, 191, 47), edge_rgb=(255, 225, 90)):
    """Sub-pixel smooth 3D province lift using floating-point AFFINE texture shift."""
    if lift <= 0.01:
        return im
    mask = Image.new('L', (w, h))
    md = ImageDraw.Draw(mask)
    fdx = 10.0 * w / 1080.0 * lift
    fdy = -38.0 * h / 1920.0 * lift

    # Float polygon directly at lifted position (smooth continuous edge movement)
    lifted_mask = Image.new('L', (w, h))
    lmd = ImageDraw.Draw(lifted_mask)
    shadow_mask = Image.new('L', (w, h))
    smd = ImageDraw.Draw(shadow_mask)
    sdx = fdx + 12.0 * w / 1080.0 * lift
    sdy = fdy + 22.0 * h / 1920.0 * lift

    for f in provinces_list:
        polys = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
        for poly in polys:
            lmd.polygon([(xy(p)[0] + fdx, xy(p)[1] + fdy) for p in poly[0]], fill=255)
            smd.polygon([(xy(p)[0] + sdx, xy(p)[1] + sdy) for p in poly[0]], fill=255)
            for hole in poly[1:]:
                lmd.polygon([(xy(p)[0] + fdx, xy(p)[1] + fdy) for p in hole], fill=0)
                smd.polygon([(xy(p)[0] + sdx, xy(p)[1] + sdy) for p in hole], fill=0)

    blur_r = max(2, w // 90)
    sh_layer = Image.composite(
        Image.new('RGBA', (w, h), (0, 0, 0, int(175 * lift))),
        Image.new('RGBA', (w, h)),
        shadow_mask.filter(ImageFilter.GaussianBlur(blur_r))
    )
    im = Image.alpha_composite(im, sh_layer)

    # Sub-pixel AFFINE shift of underlying terrain so texture never jumps in 1px steps
    lifted_tex = im.transform((w, h), Image.Transform.AFFINE, (1.0, 0.0, -fdx, 0.0, 1.0, -fdy), Image.Resampling.BILINEAR)
    lifted_tex = Image.alpha_composite(im, lifted_tex)
    im = Image.composite(lifted_tex, im, lifted_mask)

    tint = Image.new('RGBA', (w, h), (*fill_rgb, int(85 * lift)))
    im = Image.alpha_composite(im, Image.composite(tint, Image.new('RGBA', (w, h)), lifted_mask))

    edge = Image.new('RGBA', (w, h))
    ed = ImageDraw.Draw(edge)
    for f in provinces_list:
        for ring in rings(f['geometry']):
            ed.line([(xy(p)[0] + fdx, xy(p)[1] + fdy) for p in ring], fill=(*edge_rgb, int(250 * lift)), width=max(2, w // 180))
    im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 100))))
    im = Image.alpha_composite(im, edge)
    return im


def get_ep02_config():
    timing = json.loads((R / 'audio/ep02_salary_20k_timing.json').read_text(encoding='utf-8'))
    turns = timing['turns']
    duration = timing['durationSec'] + 1.2  # ~97.64s

    # Camera waypoints: notice cy is nudged slightly north (+0.08*span) so provinces sit
    # comfortably in the middle-lower clear window (y = 0.42..0.74h) BELOW the top ledger!
    waypoints = [
        (0.0,   100.60, 15.20, 56.0),   # Overview from Asia/Globe
        (4.0,   100.80, 14.50, 22.0),   # Glide down to Thailand
        (7.2,   100.63, 13.95,  3.2),   # Smooth arrival into Bangkok
        (15.5,  100.65, 13.92,  2.5),   # Gentle zoom drift while deducting BKK ledger
        (24.2,  100.68, 13.90,  2.3),   # Finish BKK deduction
        (26.5,  101.28, 13.35,  3.1),   # Smooth glide across to Chon Buri
        (35.0,  101.26, 13.32,  2.6),   # Gentle drift during Chon Buri ledger
        (43.8,  101.24, 13.30,  2.4),   # Finish Chon Buri deduction
        (46.2,  102.47, 16.75,  4.0),   # Smooth flight north-east to Khon Kaen
        (55.0,  102.50, 16.72,  3.4),   # Gentle drift during Khon Kaen ledger
        (63.8,  102.52, 16.70,  3.2),   # Finish Khon Kaen deduction
        (66.5,   98.84, 19.75,  7.6),   # Smooth sweep north-west to Chiang Mai
        (75.0,   98.86, 19.72,  7.2),   # Gentle drift during Chiang Mai ledger
        (84.0,   98.88, 19.70,  6.8),   # Finish Chiang Mai deduction
        (86.8,  100.80, 16.40, 16.5),   # Pull back smoothly to show all 4 cities
        (92.0,  100.85, 16.30, 15.6),   # Gentle hold drift during insight
        (duration, 100.50, 16.00, 36.0) # Smooth zoom-out toward Southeast Asia
    ]

    # Exact city ledgers tied directly to measured audio turn timestamps!
    cities_ledger = [
        {
            'name': 'กรุงเทพมหานคร',
            't_start': turns[1]['startSec'], 't_end': turns[5]['endSec'] + 0.15,
            't_salary': turns[1]['startSec'],
            't_room': turns[2]['startSec'], 't_room_end': turns[2]['endSec'],
            't_transit': turns[3]['startSec'], 't_transit_end': turns[3]['endSec'],
            't_food': turns[4]['startSec'], 't_food_end': turns[4]['endSec'],
            't_rem': turns[5]['startSec'],
            'room_cost': 5500, 'room_lbl': 'ค่าเช่าหอพัก',
            'transit_cost': 2800, 'transit_lbl': 'ค่ารถไฟฟ้า / เดินทาง', 'transit_icon': 'bts',
            'food_cost': 6000, 'food_lbl': 'ค่าอาหารเฉลี่ย',
            'net_rem': 5700, 'net_col': '#ff7b7b'
        },
        {
            'name': 'ชลบุรี (โซนนิคมฯ)',
            't_start': turns[6]['startSec'], 't_end': turns[10]['endSec'] + 0.15,
            't_salary': turns[6]['startSec'],
            't_room': turns[7]['startSec'], 't_room_end': turns[7]['endSec'],
            't_transit': turns[8]['startSec'], 't_transit_end': turns[8]['endSec'],
            't_food': turns[9]['startSec'], 't_food_end': turns[9]['endSec'],
            't_rem': turns[10]['startSec'],
            'room_cost': 3800, 'room_lbl': 'ค่าเช่าห้องพัก',
            'transit_cost': 800, 'transit_lbl': 'รถรับส่งพนักงาน / เดินทาง', 'transit_icon': 'bus',
            'food_cost': 5500, 'food_lbl': 'ค่าอาหารเฉลี่ย',
            'net_rem': 9900, 'net_col': '#58d5b5'
        },
        {
            'name': 'ขอนแก่น (อันดับ 1)',
            't_start': turns[11]['startSec'], 't_end': turns[15]['endSec'] + 0.15,
            't_salary': turns[11]['startSec'],
            't_room': turns[12]['startSec'], 't_room_end': turns[12]['endSec'],
            't_transit': turns[13]['startSec'], 't_transit_end': turns[13]['endSec'],
            't_food': turns[14]['startSec'], 't_food_end': turns[14]['endSec'],
            't_rem': turns[15]['startSec'],
            'room_cost': 3000, 'room_lbl': 'ค่าเช่าหอพัก',
            'transit_cost': 1200, 'transit_lbl': 'มอเตอร์ไซค์ / น้ำมัน', 'transit_icon': 'motorbike',
            'food_cost': 4500, 'food_lbl': 'ค่าอาหารเฉลี่ย',
            'net_rem': 11300, 'net_col': '#ffd44d'
        },
        {
            'name': 'เชียงใหม่',
            't_start': turns[16]['startSec'], 't_end': turns[20]['endSec'] + 0.15,
            't_salary': turns[16]['startSec'],
            't_room': turns[17]['startSec'], 't_room_end': turns[17]['endSec'],
            't_transit': turns[18]['startSec'], 't_transit_end': turns[18]['endSec'],
            't_food': turns[19]['startSec'], 't_food_end': turns[19]['endSec'],
            't_rem': turns[20]['startSec'],
            'room_cost': 4200, 'room_lbl': 'ค่าเช่าที่พัก',
            'transit_cost': 2000, 'transit_lbl': 'ค่าเดินทาง / รถส่วนตัว', 'transit_icon': 'car',
            'food_cost': 5200, 'food_lbl': 'ค่าอาหารเฉลี่ย',
            'net_rem': 8600, 'net_col': '#ffd44d'
        }
    ]

    # Exact timed subtitles matching every single spoken turn!
    subtitles = []
    sub_highlights = [
        ('#ffffff', '#ffd44d'),  # 0: Hook
        ('#ffffff', '#ffd44d'),  # 1: BKK salary
        ('#ffffff', '#ff7b7b'),  # 2: BKK room
        ('#ffffff', '#ff7b7b'),  # 3: BKK transit
        ('#ffffff', '#ff7b7b'),  # 4: BKK food
        ('#ffffff', '#ff7b7b'),  # 5: BKK net
        ('#ffffff', '#58d5b5'),  # 6: Chon salary
        ('#ffffff', '#58d5b5'),  # 7: Chon room
        ('#ffffff', '#58d5b5'),  # 8: Chon transit
        ('#ffffff', '#58d5b5'),  # 9: Chon food
        ('#ffffff', '#58d5b5'),  # 10: Chon net
        ('#ffffff', '#ffd44d'),  # 11: KK salary
        ('#ffffff', '#ffd44d'),  # 12: KK room
        ('#ffffff', '#ffd44d'),  # 13: KK transit
        ('#ffffff', '#ffd44d'),  # 14: KK food
        ('#ffffff', '#ffd44d'),  # 15: KK net
        ('#ffffff', '#ffd44d'),  # 16: CM salary
        ('#ffffff', '#ffd44d'),  # 17: CM room
        ('#ffffff', '#ffd44d'),  # 18: CM transit
        ('#ffffff', '#ffd44d'),  # 19: CM food
        ('#ffffff', '#ffd44d'),  # 20: CM net
        ('#ffffff', '#58d5b5'),  # 21: Insight
        ('#ffd44d', '#ffffff'),  # 22: CTA
    ]

    # Pre-split long sentences cleanly into 1 or 2 crisp lines
    pretty_lines = [
        [('ถ้าเงินเดือน 20,000 บาทเท่ากัน อยู่จังหวัดไหนเหลือเยอะสุด?', '#ffffff'), ('มาเทียบ 4 เมืองใหญ่ทั่วไทยกันครับ', '#ffd44d')],
        [('เริ่มที่ กรุงเทพมหานคร ตั้งต้นเงินเดือน 20,000 บาท', '#ffffff')],
        [('หักค่าเช่าหอพักเฉลี่ย 5,500 บาท', '#ff7b7b')],
        [('ค่ารถไฟฟ้าและเดินทางอีก 2,800 บาท', '#ff7b7b')],
        [('บวกค่าอาหารเฉลี่ย 6,000 บาท', '#ff7b7b')],
        [('จะเหลือเงินเก็บเพียงเดือนละ 5,700 บาทเท่านั้นครับ', '#ff7b7b')],
        [('ต่อมา ชลบุรี โซนนิคมอุตสาหกรรม จากเงินเดือน 20,000 บาท', '#ffffff')],
        [('ค่าเช่าห้องลดลงเหลือราว 3,800 บาท', '#58d5b5')],
        [('โรงงานมีรถรับส่ง ค่าเดินทางเพิ่มแค่ราว 800 บาท', '#58d5b5')],
        [('บวกค่าอาหารประมาณ 5,500 บาท', '#58d5b5')],
        [('เงินเหลือเก็บจึงพุ่งขึ้นเป็น 9,900 บาทต่อเดือนเลยครับ', '#58d5b5')],
        [('ขยับขึ้นภาคอีสานที่ ขอนแก่น เงินเดือน 20,000 บาทเท่ากัน', '#ffffff')],
        [('ค่าเช่าหอพักเฉลี่ยอยู่แค่ราว 3,000 บาท', '#ffd44d')],
        [('ขับมอเตอร์ไซค์คล่องตัว ค่าน้ำมันราว 1,200 บาท', '#ffd44d')],
        [('ส่วนค่าอาหารเฉลี่ยเพียง 4,500 บาท', '#ffd44d')],
        [('ทำให้เหลือเงินเก็บทะลุ 11,300 บาท สูงสุดใน 4 เมืองนี้เลยครับ', '#ffd44d')],
        [('ปิดท้ายที่ เชียงใหม่ เมืองยอดฮิต จากเงินเดือน 20,000 บาท', '#ffffff')],
        [('ค่าเช่าที่พักดีดตัวตามดีมานด์ อยู่ที่ราว 4,200 บาท', '#ffd44d')],
        [('และเพราะไม่มีขนส่งสาธารณะครอบคลุม', '#ffffff'), ('ค่าเดินทางจึงขยับไปราว 2,000 บาท', '#ffd44d')],
        [('บวกค่าอาหารเฉลี่ย 5,200 บาท', '#ffd44d')],
        [('เหลือเงินเก็บสุทธิอยู่ที่ราว 8,600 บาทครับ', '#ffd44d')],
        [('จะเห็นว่าเงินเดือนเท่ากัน ไม่ได้แปลว่าเหลือเงินเท่ากัน', '#ffffff'), ('เพราะค่าที่อยู่และระบบขนส่งคือตัวแปรสำคัญ', '#58d5b5')],
        [('แล้วตอนนี้คุณอยู่จังหวัดไหน เหลือเก็บเดือนละกี่บาท?', '#ffd44d'), ('คอมเมนต์มาแชร์กันได้เลยครับ', '#ffffff')],
    ]

    for idx, tr in enumerate(turns):
        subtitles.append({
            'start': tr['startSec'],
            'end': tr['endSec'],
            'lines': pretty_lines[idx]
        })

    return duration, waypoints, cities_ledger, subtitles, turns


def build_ring_index(features):
    """Attach per-ring bounding boxes so off-screen islands are skipped in O(1)."""
    out = []
    for f in features:
        ring_list = []
        for r in rings(f['geometry']):
            xs = [p[0] for p in r]
            ys = [p[1] for p in r]
            ring_list.append({
                'pts': r,
                'bbox': [min(xs), min(ys), max(xs), max(ys)]
            })
        if ring_list:
            f_copy = dict(f)
            f_copy['rings_bbox'] = ring_list
            f_copy['bbox'] = [
                min(rb['bbox'][0] for rb in ring_list),
                min(rb['bbox'][1] for rb in ring_list),
                max(rb['bbox'][2] for rb in ring_list),
                max(rb['bbox'][3] for rb in ring_list),
            ]
            out.append(f_copy)
    return out


def paste_icon_alpha(im, icon, cx, cy, sz, alpha_scale):
    if alpha_scale <= 0.02:
        return
    resized = icon.resize((sz, sz), Image.Resampling.LANCZOS)
    if alpha_scale < 0.99:
        r_c, g_c, b_c, a_c = resized.split()
        a_c = a_c.point(lambda a: int(a * alpha_scale))
        resized = Image.merge('RGBA', (r_c, g_c, b_c, a_c))
    im.paste(resized, (int(cx - sz / 2), int(cy - sz / 2)), resized)


def worker_render_chunk(worker_id, start_frame, end_frame, w, h, fps, out_chunk, check_points=None):
    duration, waypoints, cities_ledger, subtitles, turns = get_ep02_config()
    cam_spline = SmoothCameraSpline(waypoints)

    terrain = Image.open(R / 'work/cached_world_terrain_blue_ocean.png').convert('RGB')
    countries = build_ring_index(json.loads((R / 'data/processed/world_countries.geojson').read_text(encoding='utf-8'))['features'])
    provinces = build_ring_index(json.loads((R / 'data/processed/thailand_provinces.geojson').read_text(encoding='utf-8'))['features'])

    tha_country = next((c for c in countries if c['properties'].get('adm0_a3') == 'THA'), None)
    bkk_prov = [p for p in provinces if p['properties'].get('name') == 'Bangkok Metropolis']
    chon_prov = [p for p in provinces if p['properties'].get('name') == 'Chon Buri']
    kk_prov = [p for p in provinces if p['properties'].get('name') == 'Khon Kaen']
    cm_prov = [p for p in provinces if p['properties'].get('name') == 'Chiang Mai']

    city_coords = {
        'bkk': (100.626, 13.720),
        'chon': (101.278, 13.094),
        'kk': (102.473, 16.348),
        'cm': (98.837, 18.701),
    }

    # Load all crisp white-circle icons
    icons = {
        'salary': Image.open(R / 'assets/graphics/icon_salary_white.png').convert('RGBA'),
        'room': Image.open(R / 'assets/graphics/icon_room_white.png').convert('RGBA'),
        'bts': Image.open(R / 'assets/graphics/icon_bts_white.png').convert('RGBA'),
        'bus': Image.open(R / 'assets/graphics/icon_bus_white.png').convert('RGBA'),
        'motorbike': Image.open(R / 'assets/graphics/icon_motorbike_white.png').convert('RGBA'),
        'car': Image.open(R / 'assets/graphics/icon_car_white.png').convert('RGBA'),
        'food': Image.open(R / 'assets/graphics/icon_food_white.png').convert('RGBA'),
        'savings': Image.open(R / 'assets/graphics/icon_savings_white.png').convert('RGBA'),
        'wallet': Image.open(R / 'assets/graphics/icon_salary_white.png').convert('RGBA'),
    }

    # Pre-cache fonts for speed
    fonts = {
        'badge': get_kanit(max(11, w // 28), weight='semi_bold'),
        'title_big': get_kanit(max(18, w // 16), weight='extra_bold'),
        'city_hdr': get_kanit(max(15, w // 20), weight='extra_bold'),
        'bal_lbl': get_kanit(max(10, w // 32), weight='semi_bold'),
        'bal_num': get_kanit(max(18, w // 16), weight='extra_bold'),
        'row_lbl': get_kanit(max(11, w // 28), weight='bold'),
        'row_amt': get_kanit(max(12, w // 25), weight='extra_bold'),
        'pin': get_kanit(max(10, w // 34), weight='bold'),
        'footer': get_kanit(max(9, w // 42), weight='medium'),
    }

    use_vt = (w >= 1080)
    # Use -bf 0 (zero B-frames) on hardware encode so chunk concat has zero DTS/PTS jump!
    vcodec_args = ['-c:v', 'h264_videotoolbox', '-b:v', '42M', '-bf', '0'] if use_vt else ['-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-bf', '0']
    cmd = [
        ff(), '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
        '-r', str(fps), '-i', '-', '-an', *vcodec_args,
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(out_chunk)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=(R / f'work/ep02_worker_{worker_id}.log').open('w'))
    t_start = time.time()

    try:
        for idx in range(start_frame, end_frame):
            t = idx / fps
            box = cam_spline.box(t, w, h)

            def xy(p):
                return (
                    (p[0] - box[0]) / (box[2] - box[0]) * w,
                    (box[3] - p[1]) / (box[3] - box[1]) * h
                )

            # Sub-pixel accurate terrain transform with BICUBIC (eliminates texel shimmer!)
            fx0 = (box[0] + 180.0) / 360.0 * terrain.width
            fy0 = (90.0 - box[3]) / 180.0 * terrain.height
            fx1 = (box[2] + 180.0) / 360.0 * terrain.width
            fy1 = (90.0 - box[1]) / 180.0 * terrain.height

            cx0 = max(0, int(math.floor(fx0)) - 3)
            cy0 = max(0, int(math.floor(fy0)) - 3)
            cx1 = min(terrain.width, int(math.ceil(fx1)) + 3)
            cy1 = min(terrain.height, int(math.ceil(fy1)) + 3)

            if cx1 <= cx0 or cy1 <= cy0:
                im = Image.new('RGBA', (w, h), (14, 35, 54, 255))
            else:
                cropped = terrain.crop((cx0, cy0, cx1, cy1))
                sub_reg = (fx0 - cx0, fy0 - cy0, fx1 - cx0, fy1 - cy0)
                im = cropped.transform((w, h), Image.Transform.EXTENT, sub_reg, Image.Resampling.BICUBIC).convert('RGBA')

            d = ImageDraw.Draw(im)

            # 1. Country Borders (ring-level bbox filtered!)
            for c in countries:
                if c['properties'].get('adm0_a3') == 'THA':
                    continue
                bb = c['bbox']
                if bb[2] < box[0] or bb[0] > box[2] or bb[3] < box[1] or bb[1] > box[3]:
                    continue
                for rb in c['rings_bbox']:
                    rbb = rb['bbox']
                    if rbb[2] < box[0] or rbb[0] > box[2] or rbb[3] < box[1] or rbb[1] > box[3]:
                        continue
                    d.line([xy(p) for p in rb['pts']], fill=(220, 235, 228, 85), width=max(1, w // 450))

            # 2. Provincial Borders (ring-level bbox filtered!)
            if box[3] - box[1] < 30.0:
                for f in provinces:
                    bb = f['bbox']
                    if bb[2] < box[0] or bb[0] > box[2] or bb[3] < box[1] or bb[1] > box[3]:
                        continue
                    for rb in f['rings_bbox']:
                        rbb = rb['bbox']
                        if rbb[2] < box[0] or rbb[0] > box[2] or rbb[3] < box[1] or rbb[1] > box[3]:
                            continue
                        d.line([xy(p) for p in rb['pts']], fill=(240, 248, 255, 70), width=max(1, w // 540))

            # 3. Thailand Glow Border
            if tha_country and t >= 1.5:
                tha_glow = smootherstep((t - 1.5) / 1.5) * (1.0 - smootherstep((t - (duration - 1.5)) / 1.2))
                if tha_glow > 0.02:
                    edge = Image.new('RGBA', (w, h))
                    ed = ImageDraw.Draw(edge)
                    for rb in tha_country['rings_bbox']:
                        rbb = rb['bbox']
                        if rbb[2] < box[0] or rbb[0] > box[2] or rbb[3] < box[1] or rbb[1] > box[3]:
                            continue
                        ed.line([xy(p) for p in rb['pts']], fill=(255, 219, 76, int(170 * tha_glow)), width=max(2, w // 220))
                    im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 110))))
                    im = Image.alpha_composite(im, edge)

            # 4. 3D Province Lifts (synchronized cleanly with each city's turns)
            lift_specs = [
                (bkk_prov, cities_ledger[0], (255, 115, 115), (255, 165, 165)),
                (chon_prov, cities_ledger[1], (88, 213, 181), (130, 245, 215)),
                (kk_prov, cities_ledger[2], (255, 191, 47), (255, 225, 90)),
                (cm_prov, cities_ledger[3], (255, 191, 47), (255, 225, 90)),
            ]
            for plist, cl, f_rgb, e_rgb in lift_specs:
                ts, te = cl['t_start'] - 0.3, cl['t_end'] + 0.3
                if ts <= t <= te:
                    lift = smootherstep((t - ts) / 0.9) * (1.0 - smootherstep((t - (te - 0.9)) / 0.9))
                    im = draw_province_lift(im, plist, lift, xy, w, h, fill_rgb=f_rgb, edge_rgb=e_rgb)

            # 5. Smooth Bezier Flight Route Arcs
            route_layer = Image.new('RGBA', (w, h))
            rd = ImageDraw.Draw(route_layer)
            routes = [
                (cities_ledger[0]['t_end'] - 0.3, cities_ledger[1]['t_start'] + 1.2, city_coords['bkk'], city_coords['chon'], (88, 213, 181)),
                (cities_ledger[1]['t_end'] - 0.3, cities_ledger[2]['t_start'] + 1.2, city_coords['chon'], city_coords['kk'], (255, 212, 77)),
                (cities_ledger[2]['t_end'] - 0.3, cities_ledger[3]['t_start'] + 1.2, city_coords['kk'], city_coords['cm'], (255, 212, 77)),
            ]
            for r_start, r_end, p0, p1, col in routes:
                if t >= r_start:
                    prog = smootherstep((t - r_start) / (r_end - r_start))
                    fade_out = 1.0 - smootherstep((t - (duration - 3.0)) / 1.8) if t > duration - 3.0 else 1.0
                    alpha = int(220 * fade_out)
                    if alpha > 5:
                        arc_pts = [xy(pt) for pt in bezier_arc(p0, p1, prog)]
                        rd.line(arc_pts, fill=(*col, alpha), width=max(2, w // 220))
                        if 0.02 < prog < 0.98:
                            hx, hy = arc_pts[-1]
                            rad = max(4, w // 100)
                            rd.ellipse([hx - rad, hy - rad, hx + rad, hy + rad], fill=(255, 255, 255, alpha))
            im = Image.alpha_composite(im, route_layer)

            # 6. Summary City Pins (turns 21-22)
            t_sum_start = turns[21]['startSec'] - 0.5
            if t_sum_start <= t <= duration - 0.5:
                pin_alpha = smootherstep((t - t_sum_start) / 0.8) * (1.0 - smootherstep((t - (duration - 2.0)) / 1.5))
                if pin_alpha > 0.02:
                    pd = ImageDraw.Draw(im)
                    pin_specs = [
                        (city_coords['bkk'], 'กทม. 5,700 บ.', '#ff7b7b', -1),
                        (city_coords['chon'], 'ชลบุรี 9,900 บ.', '#58d5b5', 1),
                        (city_coords['kk'], 'ขอนแก่น 11,300 บ.', '#ffd44d', -1),
                        (city_coords['cm'], 'เชียงใหม่ 8,600 บ.', '#ffd44d', 1),
                    ]
                    for coord, plabel, pcol, ydir in pin_specs:
                        px, py = xy(coord)
                        r_dot = max(4, w // 120)
                        pd.ellipse([px - r_dot, py - r_dot, px + r_dot, py + r_dot], fill=hex_rgba(pcol, 255 * pin_alpha), outline=(255, 255, 255, int(255 * pin_alpha)), width=max(1, w // 360))
                        draw_crisp_text(im, (px, py + ydir * max(14, h // 52)), plabel, fonts['pin'], hex_rgba(pcol, 255), alpha_scale=pin_alpha, stroke_w=max(1, w // 240))

            # 7. Opening Title Hook (Turn 0)
            if t < turns[0]['endSec'] + 0.3:
                fade = smootherstep(t / 0.45) * (1.0 - smootherstep((t - (turns[0]['endSec'] - 0.5)) / 0.7))
                if fade > 0.02:
                    title_y = int(h * 0.12)
                    draw_crisp_text(im, (w / 2, title_y), "พิกัดเงิน • การเงินใกล้ตัว", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=fade, stroke_w=max(2, w // 220))
                    draw_crisp_text(im, (w / 2, title_y + int(h * 0.048)), "เงินเดือน 20,000 บาท", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=fade, stroke_w=max(2, w // 180))
                    draw_crisp_text(im, (w / 2, title_y + int(h * 0.100)), "อยู่จังหวัดไหนเหลือเยอะสุด?", fonts['title_big'], hex_rgba('#ffffff'), alpha_scale=fade, stroke_w=max(2, w // 180))

            # 8. STEP-BY-STEP EXPENSE LEDGER WITH WHITE-CIRCLE ICONS
            active_city = next((c for c in cities_ledger if c['t_start'] <= t <= c['t_end']), None)
            if active_city:
                city_fade = smootherstep((t - active_city['t_start']) / 0.4) * (1.0 - smootherstep((t - (active_city['t_end'] - 0.45)) / 0.45))
                if city_fade > 0.02:
                    # Calculate LIVE running balance counting down cleanly as each expense hits!
                    bal = 20000.0
                    if t >= active_city['t_room']:
                        p = smootherstep((t - active_city['t_room']) / min(1.8, active_city['t_room_end'] - active_city['t_room']))
                        bal -= active_city['room_cost'] * p
                    if t >= active_city['t_transit']:
                        p = smootherstep((t - active_city['t_transit']) / min(1.8, active_city['t_transit_end'] - active_city['t_transit']))
                        bal -= active_city['transit_cost'] * p
                    if t >= active_city['t_food']:
                        p = smootherstep((t - active_city['t_food']) / min(1.6, active_city['t_food_end'] - active_city['t_food']))
                        bal -= active_city['food_cost'] * p

                    bal_int = int(round(bal))
                    is_final = (t >= active_city['t_rem'])

                    # Top City Title (y = 0.080 * h)
                    draw_crisp_text(im, (w / 2, int(h * 0.080)), active_city['name'], fonts['city_hdr'], hex_rgba('#ffffff'), alpha_scale=city_fade, stroke_w=max(2, w // 180))

                    # Row 0: Running Salary -> Remaining Balance (y = 0.145 * h)
                    bal_y = int(h * 0.145)
                    top_icon_sz = max(32, int(w * 0.115))
                    top_icon = icons['savings'] if is_final else icons['salary']
                    paste_icon_alpha(im, top_icon, int(w * 0.20), bal_y, top_icon_sz, city_fade)

                    bal_label = "เหลือเก็บสุทธิ/เดือน" if is_final else "เงินเดือนคงเหลือ"
                    bal_col = active_city['net_col'] if is_final else '#ffd44d'
                    draw_crisp_text(im, (int(w * 0.31), bal_y - int(h * 0.018)), bal_label, fonts['bal_lbl'], hex_rgba('#58d5b5' if not is_final else active_city['net_col']), alpha_scale=city_fade, stroke_w=max(1, w // 240), anchor='lm')
                    draw_crisp_text(im, (int(w * 0.31), bal_y + int(h * 0.018)), f"{bal_int:,} บาท", fonts['bal_num'], hex_rgba(bal_col), alpha_scale=city_fade, stroke_w=max(2, w // 180), anchor='lm')

                    # Expense Rows appearing sequentially below (y = 0.215h, 0.268h, 0.321h)
                    row_specs = [
                        (active_city['t_room'], icons['room'], active_city['room_lbl'], f"-{active_city['room_cost']:,} บ.", int(h * 0.215)),
                        (active_city['t_transit'], icons[active_city['transit_icon']], active_city['transit_lbl'], f"-{active_city['transit_cost']:,} บ.", int(h * 0.268)),
                        (active_city['t_food'], icons['food'], active_city['food_lbl'], f"-{active_city['food_cost']:,} บ.", int(h * 0.321)),
                    ]
                    row_icon_sz = max(24, int(w * 0.082))
                    for r_t, r_icon, r_lbl, r_amt, ry in row_specs:
                        if t >= r_t:
                            r_in = smootherstep((t - r_t) / 0.35)
                            r_alpha = min(city_fade, r_in)
                            if r_alpha > 0.02:
                                # Smooth upward slide-in (12px -> 0px)
                                slide_y = int((1.0 - r_in) * h * 0.016)
                                paste_icon_alpha(im, r_icon, int(w * 0.21), ry + slide_y, row_icon_sz, r_alpha)
                                draw_crisp_text(im, (int(w * 0.29), ry + slide_y), r_lbl, fonts['row_lbl'], hex_rgba('#eef5fb'), alpha_scale=r_alpha, stroke_w=max(1, w // 240), anchor='lm')
                                draw_crisp_text(im, (int(w * 0.87), ry + slide_y), r_amt, fonts['row_amt'], hex_rgba('#ff8a8a'), alpha_scale=r_alpha, stroke_w=max(2, w // 220), anchor='rm')

            # 9. Summary & CTA Top Header (Turns 21-22)
            elif t >= turns[21]['startSec'] - 0.1:
                if t < turns[22]['startSec']:
                    s_fade = smootherstep((t - turns[21]['startSec']) / 0.4) * (1.0 - smootherstep((t - (turns[21]['endSec'] - 0.3)) / 0.4))
                    if s_fade > 0.02:
                        cy_top = int(h * 0.145)
                        paste_icon_alpha(im, icons['savings'], w / 2, cy_top - int(h * 0.055), max(34, int(w * 0.12)), s_fade)
                        draw_crisp_text(im, (w / 2, cy_top), "สรุปเงินเหลือเก็บ (ฐาน 20,000 บ.)", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=s_fade, stroke_w=max(2, w // 220))
                        draw_crisp_text(im, (w / 2, cy_top + int(h * 0.045)), "ต่างกันสูงสุดเกือบ 2 เท่า!", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=s_fade, stroke_w=max(2, w // 180))
                elif t <= duration - 0.3:
                    c_fade = smootherstep((t - turns[22]['startSec']) / 0.4) * (1.0 - smootherstep((t - (duration - 1.2)) / 0.8))
                    if c_fade > 0.02:
                        cy_top = int(h * 0.145)
                        paste_icon_alpha(im, icons['salary'], w / 2, cy_top - int(h * 0.055), max(34, int(w * 0.12)), c_fade)
                        draw_crisp_text(im, (w / 2, cy_top), "แล้วชีวิตจริงของคุณล่ะ?", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=c_fade, stroke_w=max(2, w // 220))
                        draw_crisp_text(im, (w / 2, cy_top + int(h * 0.045)), "เหลือเก็บเดือนละกี่บาท?", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=c_fade, stroke_w=max(2, w // 180))

            # 10. Subtitles (Measured timing per spoken micro-turn)
            active_sub = next((s for s in subtitles if s['start'] <= t < s['end']), None)
            if active_sub:
                t_rel = t - active_sub['start']
                dur_sub = active_sub['end'] - active_sub['start']
                fade = 1.0
                if t_rel < 0.20:
                    fade = smootherstep(t_rel / 0.20)
                elif t_rel > dur_sub - 0.20:
                    fade = 1.0 - smootherstep((t_rel - (dur_sub - 0.20)) / 0.20)

                if fade > 0.02:
                    sub_y = int(h * 0.81) if len(active_sub['lines']) > 1 else int(h * 0.83)
                    font_sz = max(13, w // 24)
                    font_sub = get_kanit(font_sz, weight='bold')
                    max_lw = max(measure_text_width(ltxt, font_sub) for ltxt, _ in active_sub['lines'])
                    while font_sz > 9 and max_lw > w * 0.90:
                        font_sz -= 1
                        font_sub = get_kanit(font_sz, weight='bold')
                        max_lw = max(measure_text_width(ltxt, font_sub) for ltxt, _ in active_sub['lines'])

                    line_step = max(int(font_sz * 1.45), int(h * 0.036))
                    for line_idx, (line_txt, line_col) in enumerate(active_sub['lines']):
                        ly = sub_y + line_idx * line_step
                        draw_crisp_text(im, (w / 2, ly), line_txt, font_sub, hex_rgba(line_col), alpha_scale=fade, stroke_w=max(2, w // 200))

            # 11. Source Attribution Footer
            draw_crisp_text(im, (w * 0.5, h * 0.95), "งบจำลองอ้างอิงค่าครองชีพเฉลี่ย: NSO & พาณิชย์ • แผนที่: Natural Earth", fonts['footer'], (210, 230, 245, 200), alpha_scale=1.0, stroke_w=max(1, w // 360))

            if check_points:
                for sec, label in check_points:
                    if idx == round(sec * fps):
                        im.convert('RGB').save(R / f'work/check_ep02v2_{label}.jpg')

            proc.stdin.write(im.convert('RGB').tobytes())

            if (idx - start_frame) % 300 == 0 and idx > start_frame:
                elapsed = time.time() - t_start
                cur_fps = (idx - start_frame + 1) / elapsed
                print(f"[Worker {worker_id}] Frame {idx} ({cur_fps:.1f} FPS)", flush=True)

    finally:
        proc.stdin.close()
        code = proc.wait()

    if code != 0:
        raise RuntimeError(f"Worker {worker_id} FFmpeg failed with exit code {code}")


def mix_audio_clean(video_path, output_path):
    ff_bin = ff()
    voice_path = R / 'audio/ep02_salary_20k_voice.mp3'
    cmd = [
        ff_bin, '-y',
        '-i', str(video_path),
        '-i', str(voice_path),
        '-filter_complex', '[1:a]apad,loudnorm=I=-16:TP=-1.5:LRA=11[a]',
        '-map', '0:v:0',
        '-map', '[a]',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '256k',
        '-shortest',
        '-movflags', '+faststart',
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stderr=(R / 'exports/mix_ep02.log').open('w'))
    subprocess.run([ff_bin, '-v', 'error', '-i', str(output_path), '-f', 'null', '-'], check=True)
    print(f"Verified & Saved: {output_path}", flush=True)


def run_build(mode='preview'):
    duration, _, _, _, turns = get_ep02_config()
    if mode == 'preview':
        w, h, fps = 360, 640, 60
        tag = 'PREVIEW_360p60'
        num_workers = 4
    elif mode == '1080p':
        w, h, fps = 1080, 1920, 60
        tag = '1080p60'
        num_workers = 4
    else:
        w, h, fps = 2160, 3840, 60
        tag = '4K_60FPS'
        num_workers = 4

    total_frames = round(duration * fps)
    check_points = [
        (2.5, '00_title_overview'),
        (turns[4]['endSec'] - 0.3, '01_bangkok_ledger_all_rows'),
        (turns[10]['endSec'] - 0.5, '02_chonburi_ledger_final'),
        (turns[15]['endSec'] - 0.5, '03_khonkaen_ledger_final'),
        (turns[20]['endSec'] - 0.5, '04_chiangmai_ledger_final'),
        (turns[21]['startSec'] + 3.0, '05_summary_4cities'),
        (turns[22]['startSec'] + 2.5, '06_cta_zoomout')
    ]

    silent_out = R / f'exports/EP02_SALARY20K_{tag}_silent.mp4'
    final_out = R / f'exports/EP02_SALARY20K_{tag}_voice_only.mp4'
    silent_out.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Building EP02 v2 ({w}x{h} @ {fps}fps, {total_frames} frames, {num_workers} workers) ===", flush=True)
    t0 = time.time()

    chunk_size = math.ceil(total_frames / num_workers)
    procs = []
    chunk_paths = []
    for i in range(num_workers):
        sf = i * chunk_size
        ef = min(total_frames, (i + 1) * chunk_size)
        if sf >= total_frames:
            break
        cpath = R / f'work/ep02v2_chunk_{i}.mp4'
        chunk_paths.append(cpath)
        p = mp.Process(target=worker_render_chunk, args=(i, sf, ef, w, h, fps, cpath, check_points))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
        if p.exitcode != 0:
            raise RuntimeError(f"Worker failed with exitcode {p.exitcode}")

    concat_txt = R / 'work/ep02v2_chunks.txt'
    concat_txt.write_text('\n'.join(f"file {cp.name}" for cp in chunk_paths))
    subprocess.run([ff(), '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_txt), '-c', 'copy', str(silent_out)], check=True)

    print(f"Video track complete in {time.time() - t0:.1f}s -> {silent_out}", flush=True)
    mix_audio_clean(silent_out, final_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['preview', '1080p', '4k'], default='preview')
    args = parser.parse_args()
    run_build(args.mode)
