"""Episode 06: 5 อันดับประเทศที่คนไทยอยากไปเที่ยวมากที่สุด (ค่าเดินทาง + ค่าเงิน + พื้นผิวธงชาติ)
Architecture:
1. Monotonic PCHIP Cubic Hermite Camera Spline (smooth continental & regional pans, zero stop-and-go jerk)
2. 16K Land-Bled Terrain + Natural Earth 10m Vector Ocean Masking (zero coastal staircasing even at 4K deep zoom)
3. In-place Flat Geo-Anchored Country Surfaces Filled with Crisp Vector National Flags + Glowing Borders
4. macOS CoreText + CoreGraphics OpenType Kanit shaper (perfect Thai vowel + tone-mark stacking, cached sprites)
5. Step-by-step Travel & FX Rows + 5 Country Landmark White-Circle Icons + Flight Time / 1,000 THB Pills + Top-5 Outro Table
"""
from pathlib import Path
import argparse, ctypes, json, math, subprocess, time
import multiprocessing as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
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

        # Shadow
        self.cg.CGContextSetRGBStrokeColor(ctx, 0.0, 0.0, 0.0, 150.0 / 255.0)
        self.cg.CGContextSetRGBFillColor(ctx, 0.0, 0.0, 0.0, 150.0 / 255.0)
        self.cg.CGContextSetTextDrawingMode(ctx, 2)
        self.cg.CGContextSetTextPosition(ctx, pad_x + sh_off * 0.5, base_y_from_bot - sh_off)
        self.ct.CTLineDraw(line, ctx)

        # Stroke
        self.cg.CGContextSetRGBStrokeColor(ctx, 10.0 / 255.0, 18.0 / 255.0, 28.0 / 255.0, 230.0 / 255.0)
        self.cg.CGContextSetTextDrawingMode(ctx, 1)
        self.cg.CGContextSetTextPosition(ctx, pad_x, base_y_from_bot)
        self.ct.CTLineDraw(line, ctx)

        # Fill
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
        target_im.alpha_composite(spr.crop(src_box), dest=(ix0, iy0))
    else:
        sub = spr.crop(src_box)
        r, g, b, a = sub.split()
        a = a.point(lambda v: int(v * a_eff))
        sub.putalpha(a)
        target_im.alpha_composite(sub, dest=(ix0, iy0))


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


def star_pts(cx, cy, r_outer, r_inner=None, points=5, rot_deg=-90.0):
    if r_inner is None:
        r_inner = r_outer * 0.382
    pts = []
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        ang = math.radians(rot_deg + i * (180.0 / points))
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def draw_flag_emblem(fd, code, xyp_fn, box):
    """Draw crisp vector national flag pattern into RGBA flag canvas `fd` using geographic xyp_fn."""
    deg_w = box[2] - box[0]
    if code == 'CHE':
        # Swiss Red base + crisp white center square-armed cross
        fd.rectangle([0, 0, fd.im.size[0], fd.im.size[1]], fill=(214, 38, 28, 232))
        cx, cy = xyp_fn((8.21, 46.81))
        px_per_deg = fd.im.size[0] / deg_w
        arm = 0.62 * px_per_deg
        thick = 0.21 * px_per_deg
        fd.rectangle([cx - thick, cy - arm, cx + thick, cy + arm], fill=(255, 255, 255, 248))
        fd.rectangle([cx - arm, cy - thick, cx + arm, cy + thick], fill=(255, 255, 255, 248))

    elif code == 'VNM':
        # Vietnam Crimson base + crisp bright 5-point gold star over Northern Delta
        fd.rectangle([0, 0, fd.im.size[0], fd.im.size[1]], fill=(218, 37, 29, 232))
        cx, cy = xyp_fn((105.55, 21.30))
        px_per_deg = fd.im.size[0] / deg_w
        r_out = 1.15 * px_per_deg
        fd.polygon(star_pts(cx, cy, r_out, r_out * 0.382, points=5, rot_deg=-90.0), fill=(255, 222, 0, 250))

    elif code == 'TWN':
        # Taiwan Crimson base + upper-left Navy Canton + crisp 12-ray White Sun
        fd.rectangle([0, 0, fd.im.size[0], fd.im.size[1]], fill=(230, 16, 26, 232))
        px_per_deg = fd.im.size[0] / deg_w
        x_cut, y_cut = xyp_fn((121.32, 23.65))
        if x_cut > 0 and y_cut > 0:
            fd.rectangle([0, 0, x_cut, y_cut], fill=(0, 14, 148, 244))
        cx, cy = xyp_fn((120.88, 24.42))
        r_ray = 0.40 * px_per_deg
        r_in = 0.20 * px_per_deg
        r_disc = 0.165 * px_per_deg
        fd.polygon(star_pts(cx, cy, r_ray, r_in, points=12, rot_deg=-90.0), fill=(255, 255, 255, 250))
        fd.ellipse([cx - r_disc, cy - r_disc, cx + r_disc, cy + r_disc], fill=(0, 14, 148, 244))
        r_core = 0.135 * px_per_deg
        fd.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=(255, 255, 255, 250))

    elif code == 'CHN':
        # China Crimson base + 1 large + 4 small gold stars safely inside Xinjiang/Qinghai
        fd.rectangle([0, 0, fd.im.size[0], fd.im.size[1]], fill=(222, 41, 16, 230))
        px_per_deg = fd.im.size[0] / deg_w
        cx, cy = xyp_fn((84.8, 39.2))
        r_big = 3.1 * px_per_deg
        fd.polygon(star_pts(cx, cy, r_big, r_big * 0.382, points=5, rot_deg=-90.0), fill=(255, 222, 0, 250))
        sub_stars = [
            (90.0, 41.6),
            (91.8, 39.4),
            (91.8, 36.4),
            (90.0, 34.2),
        ]
        r_sm = 1.12 * px_per_deg
        for slon, slat in sub_stars:
            sx, sy = xyp_fn((slon, slat))
            ang = math.degrees(math.atan2(cy - sy, cx - sx))
            fd.polygon(star_pts(sx, sy, r_sm, r_sm * 0.382, points=5, rot_deg=ang), fill=(255, 222, 0, 250))

    elif code == 'JPN':
        # Japan Pure Crisp Off-White base + vibrant Crimson Hinomaru Sun centered cleanly inside Honshu
        fd.rectangle([0, 0, fd.im.size[0], fd.im.size[1]], fill=(248, 250, 252, 238))
        cx, cy = xyp_fn((138.15, 36.25))
        px_per_deg = fd.im.size[0] / deg_w
        r_sun = 1.05 * px_per_deg
        fd.ellipse([cx - r_sun, cy - r_sun, cx + r_sun, cy + r_sun], fill=(188, 0, 45, 250))


def draw_country_flag_lift(im, feat, code, lift, xy, box, w, h, edge_rgb=(255, 225, 90)):
    """Sub-pixel flat country surface anchored in-place and filled with its crisp vector national flag."""
    if lift <= 0.01 or feat is None:
        return im
    bb = feat['bbox']
    if bb[2] < box[0] - 1.0 or bb[0] > box[2] + 1.0 or bb[3] < box[1] - 1.0 or bb[1] > box[3] + 1.0:
        return im

    country_mask = Image.new('L', (w, h))
    cmd = ImageDraw.Draw(country_mask)

    g = feat['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        cmd.polygon([xy(p) for p in poly[0]], fill=255)
        for hole in poly[1:]:
            cmd.polygon([xy(p) for p in hole], fill=0)

    # 1. Vector Flag Surface clipped cleanly inside the real country boundary (no 3D lift/shadow)
    flag_canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flag_canvas)
    draw_flag_emblem(fd, code, xy, box)
    if lift < 0.99:
        r, g_c, b_c, a_c = flag_canvas.split()
        a_c = a_c.point(lambda v: int(v * lift))
        flag_canvas.putalpha(a_c)

    clipped_flag = Image.composite(flag_canvas, Image.new('RGBA', (w, h)), country_mask)
    im = Image.alpha_composite(im, clipped_flag)

    # 2. Crisp bright outline glow edge along the exact geographic border
    edge = Image.new('RGBA', (w, h))
    ed = ImageDraw.Draw(edge)
    for ring in rings(g):
        ed.line([xy(p) for p in ring], fill=(*edge_rgb, int(250 * lift)), width=max(2, w // 190))
    im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 110))))
    im = Image.alpha_composite(im, edge)
    return im


def bezier_arc(p0, p1, progress, steps=48, lift_deg=0.34):
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


def build_ring_index(features):
    indexed = []
    for f in features:
        f_rings = rings(f['geometry'])
        ring_list = []
        minx, miny, maxx, maxy = 999.0, 999.0, -999.0, -999.0
        for r in f_rings:
            xs = [p[0] for p in r]
            ys = [p[1] for p in r]
            rbb = (min(xs), min(ys), max(xs), max(ys))
            ring_list.append({'pts': r, 'bbox': rbb})
            minx, miny = min(minx, rbb[0]), min(miny, rbb[1])
            maxx, maxy = max(maxx, rbb[2]), max(maxy, rbb[3])
        g = f['geometry']
        raw_polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        poly_list = []
        for poly in raw_polys:
            oxs = [p[0] for p in poly[0]]
            oys = [p[1] for p in poly[0]]
            poly_list.append({'outer': poly[0], 'holes': poly[1:], 'bbox': (min(oxs), min(oys), max(oxs), max(oys))})
        indexed.append({'properties': f['properties'], 'geometry': f['geometry'], 'rings_bbox': ring_list, 'polys_bbox': poly_list, 'bbox': (minx, miny, maxx, maxy)})
    return indexed


def paste_icon_alpha(bg_im, icon_im, cx, cy, target_size, alpha_scale=1.0):
    if alpha_scale <= 0.02:
        return
    ic = icon_im.resize((target_size, target_size), Image.Resampling.LANCZOS)
    if alpha_scale < 0.99:
        r, g, b, a = ic.split()
        a = a.point(lambda p: int(p * alpha_scale))
        ic.putalpha(a)
    px, py = int(round(cx - target_size / 2)), int(round(cy - target_size / 2))
    bg_im.alpha_composite(ic, (px, py))


def get_ep06_config():
    timing = json.loads((R / 'audio/ep06_top5_travel_timing.json').read_text(encoding='utf-8'))
    turns = timing['turns']
    duration = timing['durationSec'] + 1.2

    # Smooth PCHIP camera waypoints: Thailand -> Switzerland (Europe) -> Vietnam -> Taiwan -> China -> Japan -> Overview!
    waypoints = [
        (0.0,                        100.5, 16.0, 58.0),    # Overview Asia/Thailand
        (turns[0]['endSec'] - 0.5,   98.0,  22.0, 74.0),    # Rise up to continental view
        (turns[1]['startSec'] + 1.4, 8.21,  47.65, 11.8),   # Land smoothly in Switzerland (Europe!)
        (turns[2]['endSec'],         8.21,  47.62, 11.0),   # Hold Switzerland during ticket cost
        (turns[3]['endSec'],         8.21,  47.60, 10.6),   # Hold Switzerland during CHF rate
        (turns[4]['startSec'] + 1.5, 105.8, 18.60, 34.5),   # Sweep back east across Eurasia to Vietnam
        (turns[5]['endSec'],         105.8, 18.55, 34.0),   # Hold Vietnam ticket cost
        (turns[6]['endSec'],         105.8, 18.50, 33.5),   # Hold Vietnam VND rate
        (turns[7]['startSec'] + 1.4, 121.03, 24.30, 9.2),   # Glide northeast to Taiwan
        (turns[8]['endSec'],         121.03, 24.28, 8.6),   # Hold Taiwan ticket cost
        (turns[9]['endSec'],         121.03, 24.26, 8.3),   # Hold Taiwan TWD rate
        (turns[10]['startSec'] + 1.6, 104.2, 43.80, 86.0),  # Pull out smoothly across China
        (turns[11]['endSec'],         104.5, 43.60, 84.0),  # Hold China ticket cost
        (turns[12]['endSec'],         104.8, 43.40, 82.0),  # Hold China CNY rate
        (turns[13]['startSec'] + 1.5, 136.6, 42.50, 35.5),  # Sweep east to #1 Japan
        (turns[14]['endSec'],         136.8, 42.35, 34.2),  # Hold Japan ticket cost
        (turns[15]['endSec'],         137.0, 42.20, 33.5),  # Hold Japan JPY rate
        (turns[16]['startSec'] + 1.8, 118.0, 29.00, 96.0),  # Pull back cleanly to East+SE Asia with Japan well inside frame
        (duration,                    121.5, 27.50, 94.0),  # Frame Thailand + Vietnam + Taiwan + China + all of Japan!
    ]

    countries_cards = [
        {
            'code': 'CHE',
            'rank_tag': 'อันดับ 5 • ประเทศในฝันยุโรป',
            'name': 'สวิตเซอร์แลนด์ (Switzerland)',
            'short_name': 'สวิตเซอร์แลนด์',
            'icon': 'che_alps',
            't_start': turns[1]['startSec'], 't_end': turns[3]['endSec'] + 0.15,
            't_flight': turns[2]['startSec'], 't_flight_end': turns[2]['endSec'],
            't_fx': turns[3]['startSec'], 't_fx_end': turns[3]['endSec'],
            'flight_val': '25,000 - 45,000 บ.',
            'flight_time': '~11.5 ชม.',
            'fx_lbl': 'ค่าเงินฟรังก์สวิส (CHF)',
            'fx_prefix': '1 CHF ≈ ', 'fx_target': 40.50, 'fx_dec': 2, 'fx_suffix': ' บาท',
            'fx_short': '1 CHF ≈ 40.50 บ.',
            'thb_1000': '1,000 บ. ≈ 24.7 CHF',
            'col': '#ff7b7b', 'edge_rgb': (255, 165, 165),
        },
        {
            'code': 'VNM',
            'rank_tag': 'อันดับ 4 • ใกล้ไทยคุ้มสุด',
            'name': 'เวียดนาม (Vietnam)',
            'short_name': 'เวียดนาม',
            'icon': 'vnm_nonla',
            't_start': turns[4]['startSec'], 't_end': turns[6]['endSec'] + 0.15,
            't_flight': turns[5]['startSec'], 't_flight_end': turns[5]['endSec'],
            't_fx': turns[6]['startSec'], 't_fx_end': turns[6]['endSec'],
            'flight_val': '3,500 - 7,000 บ.',
            'flight_time': '~1.5-2 ชม.',
            'fx_lbl': 'ค่าเงินดองเวียดนาม (VND)',
            'fx_prefix': '100 VND ≈ ', 'fx_target': 0.14, 'fx_dec': 2, 'fx_suffix': ' บาท',
            'fx_short': '100 VND ≈ 0.14 บ.',
            'thb_1000': '1,000 บ. ≈ 714,000 ดอง',
            'col': '#ffd44d', 'edge_rgb': (255, 225, 90),
        },
        {
            'code': 'TWN',
            'rank_tag': 'อันดับ 3 • ฟรีวีซ่าสตรีทฟู้ด',
            'name': 'ไต้หวัน (Taiwan)',
            'short_name': 'ไต้หวัน',
            'icon': 'twn_boba',
            't_start': turns[7]['startSec'], 't_end': turns[9]['endSec'] + 0.15,
            't_flight': turns[8]['startSec'], 't_flight_end': turns[8]['endSec'],
            't_fx': turns[9]['startSec'], 't_fx_end': turns[9]['endSec'],
            'flight_val': '6,000 - 11,000 บ.',
            'flight_time': '~3.5 ชม.',
            'fx_lbl': 'ค่าเงินดอลลาร์ไต้หวัน (TWD)',
            'fx_prefix': '1 TWD ≈ ', 'fx_target': 1.05, 'fx_dec': 2, 'fx_suffix': ' บาท',
            'fx_short': '1 TWD ≈ 1.05 บ.',
            'thb_1000': '1,000 บ. ≈ 952 TWD',
            'col': '#63b3ed', 'edge_rgb': (130, 210, 255),
        },
        {
            'code': 'CHN',
            'rank_tag': 'อันดับ 2 • ฟรีวีซ่ามาแรงสุด',
            'name': 'ประเทศจีน (China)',
            'short_name': 'จีน',
            'icon': 'chn_panda',
            't_start': turns[10]['startSec'], 't_end': turns[12]['endSec'] + 0.15,
            't_flight': turns[11]['startSec'], 't_flight_end': turns[11]['endSec'],
            't_fx': turns[12]['startSec'], 't_fx_end': turns[12]['endSec'],
            'flight_val': '7,000 - 14,000 บ.',
            'flight_time': '~3.5-4.5 ชม.',
            'fx_lbl': 'ค่าเงินหยวนจีน (CNY)',
            'fx_prefix': '1 CNY ≈ ', 'fx_target': 5.05, 'fx_dec': 2, 'fx_suffix': ' บาท',
            'fx_short': '1 CNY ≈ 5.05 บ.',
            'thb_1000': '1,000 บ. ≈ 198 CNY',
            'col': '#ffd44d', 'edge_rgb': (255, 225, 90),
        },
        {
            'code': 'JPN',
            'rank_tag': 'อันดับ 1 • แชมป์ในใจคนไทย',
            'name': 'ญี่ปุ่น (Japan)',
            'short_name': 'ญี่ปุ่น',
            'icon': 'jpn_fuji',
            't_start': turns[13]['startSec'], 't_end': turns[15]['endSec'] + 0.15,
            't_flight': turns[14]['startSec'], 't_flight_end': turns[14]['endSec'],
            't_fx': turns[15]['startSec'], 't_fx_end': turns[15]['endSec'],
            'flight_val': '11,000 - 22,000 บ.',
            'flight_time': '~6 ชม.',
            'fx_lbl': 'ค่าเงินเยนญี่ปุ่น (JPY)',
            'fx_prefix': '100 JPY ≈ ', 'fx_target': 21.30, 'fx_dec': 2, 'fx_suffix': ' บาท',
            'fx_short': '100 JPY ≈ 21.30 บ.',
            'thb_1000': '1,000 บ. ≈ 4,695 JPY',
            'col': '#58d5b5', 'edge_rgb': (255, 120, 140),
        },
    ]

    sub_lines = [
        [('5 อันดับประเทศที่คนไทยอยากไปเที่ยวมากที่สุด', '#ffffff'), ('บินกี่บาท และค่าเงินต่างจากไทยแค่ไหน?', '#ffd44d')],
        [('อันดับ 5 สวิตเซอร์แลนด์ แชมป์ในฝันยุโรป', '#ffd44d')],
        [('ตั๋วไป-กลับจากไทย เฉลี่ย 25,000 - 45,000 บาท', '#ffffff')],
        [('ใช้เงินฟรังก์สวิส: 1 CHF ≈ 40.50 บาท', '#ff8a8a')],
        [('อันดับ 4 เวียดนาม เพื่อนบ้านใกล้ไทยบินแป๊บเดียว', '#ffd44d')],
        [('ตั๋วไป-กลับ เริ่มต้นราว 3,500 - 7,000 บาท', '#ffffff')],
        [('ใช้เงินดอง: 100 VND ≈ 0.14 บาท (1,000 บ. ได้ 7 แสน)', '#58d5b5')],
        [('อันดับ 3 ไต้หวัน ฟรีวีซ่า สวรรค์สตรีทฟู้ด', '#63b3ed')],
        [('ตั๋วไป-กลับ เฉลี่ย 6,000 - 11,000 บาท', '#ffffff')],
        [('ใช้เงินดอลลาร์ไต้หวัน: 1 TWD ≈ 1.05 บาท', '#58d5b5')],
        [('อันดับ 2 ประเทศจีน มาแรงสุดหลังฟรีวีซ่าถาวร', '#ffd44d')],
        [('ตั๋วไป-กลับเมืองฮิต เฉลี่ย 7,000 - 14,000 บาท', '#ffffff')],
        [('ใช้เงินหยวน: 1 CNY ≈ 5.05 บาทครับ', '#ffd44d')],
        [('และอันดับ 1 ตลอดกาลในใจคนไทย: ญี่ปุ่น!', '#58d5b5')],
        [('ตั๋วไป-กลับ เฉลี่ยประมาณ 11,000 - 22,000 บาท', '#ffffff')],
        [('ใช้เงินเยน: 100 JPY ≈ 21.30 บาท ช้อปฟิน!', '#58d5b5')],
        [('ค่าตั๋วและค่าเงินต่างกันมหาศาล', '#ffffff'), ('ตั้งแต่ทริปประหยัดหลักพัน ยันยุโรปหลักหมื่น', '#ffd44d')],
        [('ใน 5 ประเทศนี้ คุณอยากบินไปประเทศไหนที่สุด?', '#ffd44d'), ('คอมเมนต์บอกกันหน่อยนะครับ!', '#ffffff')],
    ]

    subtitles = []
    for i, tr in enumerate(turns):
        subtitles.append({
            'start': tr['startSec'],
            'end': tr['endSec'] + 0.15,
            'lines': sub_lines[i],
        })

    return duration, waypoints, countries_cards, subtitles, turns


def render_frame(t, w, h, terrain, countries, tha_country, flag_feats, icons, fonts, cam_spline, countries_cards, subtitles, turns, duration):
    box = cam_spline.box(t, w, h)

    def xy(p):
        return (
            (p[0] - box[0]) / (box[2] - box[0]) * w,
            (box[3] - p[1]) / (box[3] - box[1]) * h
        )

    # 1. Sub-pixel cropped 16K terrain background + 10m Vector Ocean/Land Mask (razor-sharp coastlines!)
    fx0 = (box[0] + 180.0) / 360.0 * terrain.width
    fy0 = (90.0 - box[3]) / 180.0 * terrain.height
    fx1 = (box[2] + 180.0) / 360.0 * terrain.width
    fy1 = (90.0 - box[1]) / 180.0 * terrain.height

    cx0 = max(0, int(math.floor(fx0)) - 3)
    cy0 = max(0, int(math.floor(fy0)) - 3)
    cx1 = min(terrain.width, int(math.ceil(fx1)) + 3)
    cy1 = min(terrain.height, int(math.ceil(fy1)) + 3)

    im = Image.new('RGBA', (w, h), (14, 35, 54, 255))
    if cx1 > cx0 and cy1 > cy0:
        cropped = terrain.crop((cx0, cy0, cx1, cy1))
        sub_reg = (fx0 - cx0, fy0 - cy0, fx1 - cx0, fy1 - cy0)
        terrain_rgba = cropped.transform((w, h), Image.Transform.EXTENT, sub_reg, Image.Resampling.BICUBIC).convert('RGBA')
        land_mask = Image.new('L', (w, h), 0)
        lmd = ImageDraw.Draw(land_mask)
        for c in countries:
            bb = c['bbox']
            if bb[2] < box[0] or bb[0] > box[2] or bb[3] < box[1] or bb[1] > box[3]:
                continue
            for pb in c['polys_bbox']:
                pbb = pb['bbox']
                if pbb[2] < box[0] or pbb[0] > box[2] or pbb[3] < box[1] or pbb[1] > box[3]:
                    continue
                lmd.polygon([xy(p) for p in pb['outer']], fill=255)
                for hole in pb['holes']:
                    lmd.polygon([xy(p) for p in hole], fill=0)
        im = Image.composite(terrain_rgba, im, land_mask)

    d = ImageDraw.Draw(im)

    # 2. Country outlines
    for c in countries:
        code = c['properties'].get('adm0_a3')
        if code in ('THA', 'CHE', 'VNM', 'TWN', 'CHN', 'JPN'):
            continue
        bb = c['bbox']
        if bb[2] < box[0] or bb[0] > box[2] or bb[3] < box[1] or bb[1] > box[3]:
            continue
        for rb in c['rings_bbox']:
            rbb = rb['bbox']
            if rbb[2] < box[0] or rbb[0] > box[2] or rbb[3] < box[1] or rbb[1] > box[3]:
                continue
            d.line([xy(p) for p in rb['pts']], fill=(220, 235, 228, 80), width=max(1, w // 450))

    # 3. Thailand highlight (origin hub!)
    if tha_country:
        edge = Image.new('RGBA', (w, h))
        ed = ImageDraw.Draw(edge)
        for rb in tha_country['rings_bbox']:
            rbb = rb['bbox']
            if rbb[2] < box[0] or rbb[0] > box[2] or rbb[3] < box[1] or rbb[1] > box[3]:
                continue
            ed.line([xy(p) for p in rb['pts']], fill=(88, 213, 181, 210), width=max(2, w // 220))
        im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 120))))
        im = Image.alpha_composite(im, edge)

    # 4. Flat Flag-Filled Countries (anchored in-place on real map borders)
    outro_start = turns[16]['startSec']
    for cc in countries_cards:
        code = cc['code']
        feat = flag_feats.get(code)
        ts, te = cc['t_start'] - 0.35, cc['t_end'] + 0.35
        if ts <= t <= te:
            fade_a = smootherstep((t - ts) / 0.85) * (1.0 - smootherstep((t - (te - 0.85)) / 0.85))
            im = draw_country_flag_lift(im, feat, code, fade_a, xy, box, w, h, edge_rgb=cc['edge_rgb'])
        elif t >= outro_start - 0.4:
            # Re-illuminate all 5 flagged countries flat on the map during Outro!
            out_a = smootherstep((t - (outro_start - 0.4)) / 0.9) * (1.0 - smootherstep((t - (duration - 1.2)) / 0.8))
            if out_a > 0.05:
                im = draw_country_flag_lift(im, feat, code, 0.55 * out_a, xy, box, w, h, edge_rgb=cc['edge_rgb'])

    # 5. Animated Bezier Flight Routes from Thailand -> Destination Coast/City Hubs (avoiding flag center emblems)
    tha_hub = (100.55, 13.75)
    route_layer = Image.new('RGBA', (w, h))
    rd = ImageDraw.Draw(route_layer)
    targets_hubs = {
        'CHE': (9.45, 46.75),
        'VNM': (108.25, 16.05),
        'TWN': (120.30, 22.62),
        'CHN': (116.40, 39.90),
        'JPN': (135.50, 34.69),
    }
    for cc in countries_cards:
        r_start = cc['t_start'] - 0.6
        r_end = cc['t_start'] + 1.3
        if t >= r_start:
            prog = smootherstep((t - r_start) / (r_end - r_start))
            active_fade = 1.0 if t <= cc['t_end'] + 0.5 else (0.68 if t >= outro_start - 0.4 else 0.25)
            end_fade = 1.0 - smootherstep((t - (duration - 1.2)) / 0.8) if t > duration - 1.2 else 1.0
            alpha = int(225 * active_fade * end_fade)
            if alpha > 5:
                col_rgb = hex_rgba(cc['col'])[:3]
                arc_pts = [xy(pt) for pt in bezier_arc(tha_hub, targets_hubs[cc['code']], prog)]
                rd.line(arc_pts, fill=(*col_rgb, alpha), width=max(2, w // 225))
                if len(arc_pts) >= 2 and 0.02 < prog < 0.99:
                    hx, hy = arc_pts[-1]
                    px0, py0 = arc_pts[-2]
                    ang = math.atan2(hy - py0, hx - px0)
                    sz = max(7.0, w / 46.0)
                    plane_poly = [
                        (hx + sz * 1.15 * math.cos(ang), hy + sz * 1.15 * math.sin(ang)),
                        (hx + sz * 0.70 * math.cos(ang + 2.45), hy + sz * 0.70 * math.sin(ang + 2.45)),
                        (hx - sz * 0.25 * math.cos(ang), hy - sz * 0.25 * math.sin(ang)),
                        (hx + sz * 0.70 * math.cos(ang - 2.45), hy + sz * 0.70 * math.sin(ang - 2.45)),
                    ]
                    rd.polygon(plane_poly, fill=(255, 255, 255, alpha), outline=(10, 22, 34, alpha))
                elif prog >= 0.99:
                    hx, hy = arc_pts[-1]
                    rad = max(3, w // 120)
                    rd.ellipse([hx - rad, hy - rad, hx + rad, hy + rad], fill=(*col_rgb, alpha), outline=(255, 255, 255, alpha))
    im = Image.alpha_composite(im, route_layer)

    # 6. Summary Floating Labels on Outro Turn 16 (before Top-5 summary table dims map in Turn 17)
    turn17_start = turns[17]['startSec']
    if outro_start - 0.2 <= t < turn17_start + 0.55:
        p_fade = smootherstep((t - (outro_start - 0.2)) / 0.7) * (1.0 - smootherstep((t - (turn17_start - 0.1)) / 0.6))
        if p_fade > 0.02:
            pd = ImageDraw.Draw(im)
            pin_specs = [
                ((108.25, 16.05), '#4 เวียดนาม', '#ffd44d', 1),
                ((120.30, 22.62), '#3 ไต้หวัน', '#63b3ed', 1),
                ((116.40, 39.90), '#2 จีน', '#ffd44d', -1),
                ((135.50, 34.69), '#1 ญี่ปุ่น', '#58d5b5', 1),
            ]
            for coord, plbl, pcol, ydir in pin_specs:
                px, py = xy(coord)
                if 0 < px < w and 0 < py < h:
                    r_dot = max(4, w // 125)
                    pd.ellipse([px - r_dot, py - r_dot, px + r_dot, py + r_dot], fill=hex_rgba(pcol, 255 * p_fade), outline=(255, 255, 255, int(255 * p_fade)), width=max(1, w // 360))
                    draw_crisp_text(im, (px, py + ydir * max(14, h // 48)), plbl, fonts['pin'], hex_rgba(pcol, 255), alpha_scale=p_fade, stroke_w=max(1, w // 240))
            # Directional pointer for #5 Switzerland (west off-screen Europe, clear of China's stars)
            che_x, che_y = int(w * 0.045), int(h * 0.565)
            che_txt = "← #5 สวิตเซอร์แลนด์ (ยุโรป)"
            tw_c = measure_text_width(che_txt, fonts['pill'])
            pad_px = max(8, int(w * 0.022))
            pill_h = max(20, int(h * 0.036))
            ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            ovd = ImageDraw.Draw(ov)
            ovd.rounded_rectangle([che_x, che_y - pill_h // 2, che_x + tw_c + pad_px * 2, che_y + pill_h // 2], radius=pill_h // 2, fill=(14, 28, 42, int(215 * p_fade)), outline=(255, 123, 123, int(230 * p_fade)), width=max(1, w // 320))
            im = Image.alpha_composite(im, ov)
            draw_crisp_text(im, (che_x + pad_px, che_y), che_txt, fonts['pill'], hex_rgba('#ff8a8a'), alpha_scale=p_fade, stroke_w=max(1, w // 280), anchor='lm')

    # 7. Opening Title Hook (Turn 0)
    if t < turns[0]['endSec'] + 0.3:
        fade = smootherstep(t / 0.45) * (1.0 - smootherstep((t - (turns[0]['endSec'] - 0.5)) / 0.7))
        if fade > 0.02:
            title_y = int(h * 0.145)
            paste_icon_alpha(im, icons['passport'], w / 2, title_y - int(h * 0.062), max(36, int(w * 0.13)), fade)
            draw_crisp_text(im, (w / 2, title_y), "พิกัดเงิน • รอบโลกน่ารู้", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=fade, stroke_w=max(2, w // 220))
            draw_crisp_text(im, (w / 2, title_y + int(h * 0.048)), "5 ประเทศน่าเที่ยวที่สุด", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=fade, stroke_w=max(2, w // 180))
            draw_crisp_text(im, (w / 2, title_y + int(h * 0.098)), "ค่าตั๋ว & ค่าเงินเทียบบาท", fonts['title_big'], hex_rgba('#ffffff'), alpha_scale=fade, stroke_w=max(2, w // 180))

    # 8. Country Travel & Currency Cards with Landmark + White-Circle Icons + Practical Pills
    active_cc = next((c for c in countries_cards if c['t_start'] <= t <= c['t_end']), None)
    if active_cc:
        cfade = smootherstep((t - active_cc['t_start']) / 0.38) * (1.0 - smootherstep((t - (active_cc['t_end'] - 0.42)) / 0.42))
        if cfade > 0.02:
            # Rank badge + Country Name with paired White-Circle Landmark Icon
            draw_crisp_text(im, (w / 2, int(h * 0.058)), active_cc['rank_tag'], fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=cfade, stroke_w=max(2, w // 220))
            lm_sz = max(30, int(w * 0.105))
            gap_lm = max(6, int(w * 0.02))
            name_w = measure_text_width(active_cc['name'], fonts['city_hdr'])
            total_hdr_w = lm_sz + gap_lm + name_w
            start_hdr_x = (w - total_hdr_w) / 2.0
            hdr_y = int(h * 0.108)
            paste_icon_alpha(im, icons[active_cc['icon']], start_hdr_x + lm_sz / 2.0, hdr_y, lm_sz, cfade)
            draw_crisp_text(im, (start_hdr_x + lm_sz + gap_lm, hdr_y), active_cc['name'], fonts['city_hdr'], hex_rgba('#ffffff'), alpha_scale=cfade, stroke_w=max(2, w // 180), anchor='lm')

            row_icon_sz = max(30, int(w * 0.102))

            # Row 1: Flight Ticket Cost (y = 0.184h)
            if t >= active_cc['t_flight']:
                f_in = smootherstep((t - active_cc['t_flight']) / 0.35)
                f_alpha = min(cfade, f_in)
                if f_alpha > 0.02:
                    sy = int((1.0 - f_in) * h * 0.015)
                    ry1 = int(h * 0.184) + sy
                    paste_icon_alpha(im, icons['airplane'], int(w * 0.185), ry1, row_icon_sz, f_alpha)
                    draw_crisp_text(im, (int(w * 0.28), ry1 - int(h * 0.016)), "ตั๋วเครื่องบินไป-กลับ (เฉลี่ย)", fonts['bal_lbl'], hex_rgba('#b8e6ff'), alpha_scale=f_alpha, stroke_w=max(1, w // 240), anchor='lm')
                    draw_crisp_text(im, (int(w * 0.28), ry1 + int(h * 0.017)), active_cc['flight_val'], fonts['bal_num'], hex_rgba('#ffd44d'), alpha_scale=f_alpha, stroke_w=max(2, w // 180), anchor='lm')

            # Row 2: Currency Exchange Rate + Compact Practical Pills (Flight Time & 1,000 THB Power)
            if t >= active_cc['t_fx']:
                x_in = smootherstep((t - active_cc['t_fx']) / 0.35)
                x_alpha = min(cfade, x_in)
                if x_alpha > 0.02:
                    sy = int((1.0 - x_in) * h * 0.015)
                    ry2 = int(h * 0.262) + sy
                    prog_fx = smootherstep((t - active_cc['t_fx']) / min(1.8, active_cc['t_fx_end'] - active_cc['t_fx']))
                    val_cur = active_cc['fx_target'] * prog_fx
                    fx_txt = f"{active_cc['fx_prefix']}{val_cur:.{active_cc['fx_dec']}f}{active_cc['fx_suffix']}"
                    paste_icon_alpha(im, icons['exchange'], int(w * 0.185), ry2, row_icon_sz, x_alpha)
                    draw_crisp_text(im, (int(w * 0.28), ry2 - int(h * 0.016)), active_cc['fx_lbl'], fonts['bal_lbl'], hex_rgba('#9ef0d8'), alpha_scale=x_alpha, stroke_w=max(1, w // 240), anchor='lm')
                    draw_crisp_text(im, (int(w * 0.28), ry2 + int(h * 0.017)), fx_txt, fonts['bal_num'], hex_rgba(active_cc['col']), alpha_scale=x_alpha, stroke_w=max(2, w // 180), anchor='lm')

                    # Row 3: Dual compact informative pills (Flight time + 1,000 THB purchasing power)
                    ry3 = int(h * 0.324) + sy
                    p1_txt = f"บิน {active_cc['flight_time']}"
                    p2_txt = active_cc['thb_1000']
                    pw1 = measure_text_width(p1_txt, fonts['pill'])
                    pw2 = measure_text_width(p2_txt, fonts['pill'])
                    ppad = max(8, int(w * 0.024))
                    pgap = max(6, int(w * 0.02))
                    ph = max(20, int(h * 0.033))
                    tot_pw = (pw1 + ppad * 2) + pgap + (pw2 + ppad * 2)
                    px_start = (w - tot_pw) / 2.0
                    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                    ovd = ImageDraw.Draw(ov)
                    ovd.rounded_rectangle([px_start, ry3 - ph // 2, px_start + pw1 + ppad * 2, ry3 + ph // 2], radius=ph // 2, fill=(14, 30, 46, int(205 * x_alpha)), outline=(184, 230, 255, int(210 * x_alpha)), width=max(1, w // 340))
                    px2 = px_start + pw1 + ppad * 2 + pgap
                    col_rgb = hex_rgba(active_cc['col'])[:3]
                    ovd.rounded_rectangle([px2, ry3 - ph // 2, px2 + pw2 + ppad * 2, ry3 + ph // 2], radius=ph // 2, fill=(14, 30, 46, int(205 * x_alpha)), outline=(*col_rgb, int(220 * x_alpha)), width=max(1, w // 340))
                    im = Image.alpha_composite(im, ov)
                    draw_crisp_text(im, (px_start + ppad, ry3), p1_txt, fonts['pill'], hex_rgba('#b8e6ff'), alpha_scale=x_alpha, stroke_w=max(1, w // 320), anchor='lm')
                    draw_crisp_text(im, (px2 + ppad, ry3), p2_txt, fonts['pill'], hex_rgba(active_cc['col']), alpha_scale=x_alpha, stroke_w=max(1, w // 320), anchor='lm')

    # 9. Outro Header + Screenshot-Ready Top-5 Summary Comparison Card (Turn 17)
    elif t >= outro_start - 0.1:
        ofade = smootherstep((t - outro_start) / 0.45) * (1.0 - smootherstep((t - (duration - 1.2)) / 0.8))
        if ofade > 0.02:
            if t < turn17_start:
                cy_top = int(h * 0.145)
                paste_icon_alpha(im, icons['passport'], w / 2, cy_top - int(h * 0.055), max(34, int(w * 0.12)), ofade)
                draw_crisp_text(im, (w / 2, cy_top), "สรุป 5 ประเทศยอดฮิตคนไทย", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=ofade, stroke_w=max(2, w // 220))
                draw_crisp_text(im, (w / 2, cy_top + int(h * 0.045)), "ตั้งแต่งบหลักพัน ยันยุโรป!", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=ofade, stroke_w=max(2, w // 180))
            else:
                card_a = smootherstep((t - turn17_start) / 0.55) * (1.0 - smootherstep((t - (duration - 1.2)) / 0.8))
                # Soft dark scrim over map so Top-5 summary table pops cleanly
                if card_a > 0.02:
                    scrim = Image.new('RGBA', (w, h), (8, 18, 28, int(135 * card_a)))
                    im = Image.alpha_composite(im, scrim)
                cy_top = int(h * 0.118)
                paste_icon_alpha(im, icons['passport'], w / 2, cy_top - int(h * 0.046), max(30, int(w * 0.10)), ofade)
                draw_crisp_text(im, (w / 2, cy_top), "ปักหมุดทริปหน้าของคุณ!", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=ofade, stroke_w=max(2, w // 220))
                draw_crisp_text(im, (w / 2, cy_top + int(h * 0.042)), "สรุป 5 อันดับ น่าเที่ยวที่สุด", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=ofade, stroke_w=max(2, w // 180))

                if card_a > 0.02:
                    cx0_b, cx1_b = int(w * 0.055), int(w * 0.945)
                    cy0_b, cy1_b = int(h * 0.220), int(h * 0.745)
                    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                    ovd = ImageDraw.Draw(ov)
                    ovd.rounded_rectangle([cx0_b, cy0_b, cx1_b, cy1_b], radius=max(10, int(w * 0.038)), fill=(12, 26, 40, int(218 * card_a)), outline=(88, 213, 181, int(200 * card_a)), width=max(1, w // 270))
                    # Row dividers (#1 -> #5 top to bottom)
                    ranked = list(reversed(countries_cards))
                    row_h = (cy1_b - cy0_b) / len(ranked)
                    for idx_r in range(1, len(ranked)):
                        ry_div = int(cy0_b + idx_r * row_h)
                        ovd.line([(cx0_b + int(w * 0.04), ry_div), (cx1_b - int(w * 0.04), ry_div)], fill=(255, 255, 255, int(42 * card_a)), width=max(1, w // 360))
                    im = Image.alpha_composite(im, ov)

                    ic_tbl_sz = max(24, int(w * 0.088))
                    for idx_r, rcc in enumerate(ranked):
                        row_st = turn17_start + idx_r * 0.14
                        ra = card_a * smootherstep((t - row_st) / 0.35)
                        if ra <= 0.02:
                            continue
                        ry_c = cy0_b + (idx_r + 0.5) * row_h
                        rank_num = idx_r + 1
                        # Landmark icon
                        paste_icon_alpha(im, icons[rcc['icon']], cx0_b + int(w * 0.095), ry_c, ic_tbl_sz, ra)
                        # Rank & Name
                        draw_crisp_text(im, (cx0_b + int(w * 0.175), ry_c - int(row_h * 0.15)), f"#{rank_num} {rcc['short_name']}", fonts['tbl_name'], hex_rgba(rcc['col']), alpha_scale=ra, stroke_w=max(1, w // 260), anchor='lm')
                        draw_crisp_text(im, (cx0_b + int(w * 0.175), ry_c + int(row_h * 0.20)), f"บิน {rcc['flight_time']} • {rcc['thb_1000']}", fonts['pill'], hex_rgba('#b8d4ea'), alpha_scale=ra, stroke_w=max(1, w // 340), anchor='lm')
                        # Right column: Ticket cost + FX rate
                        draw_crisp_text(im, (cx1_b - int(w * 0.04), ry_c - int(row_h * 0.15)), rcc['flight_val'], fonts['tbl_val'], hex_rgba('#ffd44d'), alpha_scale=ra, stroke_w=max(1, w // 260), anchor='rm')
                        draw_crisp_text(im, (cx1_b - int(w * 0.04), ry_c + int(row_h * 0.20)), rcc['fx_short'], fonts['pill'], hex_rgba('#9ef0d8'), alpha_scale=ra, stroke_w=max(1, w // 340), anchor='rm')

    # 10. Subtitles (Measured CoreText Kanit)
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
    draw_crisp_text(im, (w * 0.5, h * 0.95), "อ้างอิง: Klook, Skyscanner & ธปท. (2026) • แผนที่: Natural Earth", fonts['footer'], (210, 230, 245, 200), alpha_scale=1.0, stroke_w=max(1, w // 360))
    return im


def load_resources(w):
    t16k = R / 'work/cached_world_terrain_16k_landbleed.png'
    terrain = Image.open(t16k if t16k.exists() else (R / 'work/cached_world_terrain_blue_ocean.png')).convert('RGB')
    countries = build_ring_index(json.loads((R / 'data/processed/world_countries.geojson').read_text(encoding='utf-8'))['features'])
    tha_country = next((c for c in countries if c['properties'].get('adm0_a3') == 'THA'), None)
    flag_feats = {
        code: next((c for c in countries if c['properties'].get('adm0_a3') == code), None)
        for code in ('CHE', 'VNM', 'TWN', 'CHN', 'JPN')
    }
    icons = {
        'airplane': Image.open(R / 'assets/graphics/icon_airplane_white.png').convert('RGBA'),
        'exchange': Image.open(R / 'assets/graphics/icon_exchange_white.png').convert('RGBA'),
        'passport': Image.open(R / 'assets/graphics/icon_passport_white.png').convert('RGBA'),
        'che_alps': Image.open(R / 'assets/graphics/icon_che_alps_white.png').convert('RGBA'),
        'vnm_nonla': Image.open(R / 'assets/graphics/icon_vnm_nonla_white.png').convert('RGBA'),
        'twn_boba': Image.open(R / 'assets/graphics/icon_twn_boba_white.png').convert('RGBA'),
        'chn_panda': Image.open(R / 'assets/graphics/icon_chn_panda_white.png').convert('RGBA'),
        'jpn_fuji': Image.open(R / 'assets/graphics/icon_jpn_fuji_white.png').convert('RGBA'),
    }
    fonts = {
        'badge': get_kanit(max(11, w // 28), weight='semi_bold'),
        'title_big': get_kanit(max(18, w // 16), weight='extra_bold'),
        'city_hdr': get_kanit(max(15, w // 21), weight='extra_bold'),
        'bal_lbl': get_kanit(max(10, w // 33), weight='semi_bold'),
        'bal_num': get_kanit(max(16, w // 18), weight='extra_bold'),
        'pill': get_kanit(max(9, w // 39), weight='semi_bold'),
        'tbl_name': get_kanit(max(12, w // 26), weight='extra_bold'),
        'tbl_val': get_kanit(max(11, w // 29), weight='bold'),
        'pin': get_kanit(max(10, w // 34), weight='bold'),
        'footer': get_kanit(max(9, w // 42), weight='medium'),
    }
    return terrain, countries, tha_country, flag_feats, icons, fonts


def worker_render_chunk(worker_id, start_frame, end_frame, w, h, fps, out_chunk, check_points=None):
    duration, waypoints, countries_cards, subtitles, turns = get_ep06_config()
    cam_spline = SmoothCameraSpline(waypoints)
    terrain, countries, tha_country, flag_feats, icons, fonts = load_resources(w)

    use_vt = (w >= 1080)
    vcodec_args = ['-c:v', 'h264_videotoolbox', '-b:v', '42M', '-bf', '0'] if use_vt else ['-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-bf', '0']
    cmd = [
        ff(), '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
        '-r', str(fps), '-i', '-', '-an', *vcodec_args,
        '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
        '-movflags', '+faststart', str(out_chunk)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=(R / f'work/ep06_worker_{worker_id}.log').open('w'))
    t_start = time.time()

    try:
        for idx in range(start_frame, end_frame):
            t = idx / fps
            im = render_frame(t, w, h, terrain, countries, tha_country, flag_feats, icons, fonts, cam_spline, countries_cards, subtitles, turns, duration)

            if check_points:
                for sec, label in check_points:
                    if idx == round(sec * fps):
                        im.convert('RGB').save(R / f'work/check_ep06_{label}.jpg')

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
    voice_path = R / 'audio/ep06_top5_travel_voice.mp3'
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
    subprocess.run(cmd, check=True, stderr=(R / 'exports/mix_ep06.log').open('w'))
    subprocess.run([ff_bin, '-v', 'error', '-i', str(output_path), '-f', 'null', '-'], check=True)
    print(f"Verified & Saved: {output_path}", flush=True)


def run_test_flags():
    w, h = 360, 640
    duration, waypoints, countries_cards, subtitles, turns = get_ep06_config()
    cam_spline = SmoothCameraSpline(waypoints)
    terrain, countries, tha_country, flag_feats, icons, fonts = load_resources(w)
    check_points = [
        (2.5, '00_hook'),
        (turns[3]['endSec'] - 0.4, '01_che_switzerland'),
        (turns[6]['endSec'] - 0.4, '02_vnm_vietnam'),
        (turns[9]['endSec'] - 0.4, '03_twn_taiwan'),
        (turns[12]['endSec'] - 0.4, '04_chn_china'),
        (turns[15]['endSec'] - 0.4, '05_jpn_japan'),
        (turns[16]['startSec'] + 1.8, '06_outro_asia'),
        (turns[17]['startSec'] + 2.2, '07_outro_table'),
    ]
    for sec, label in check_points:
        im = render_frame(sec, w, h, terrain, countries, tha_country, flag_feats, icons, fonts, cam_spline, countries_cards, subtitles, turns, duration)
        outp = R / f'work/check_ep06_{label}.jpg'
        im.convert('RGB').save(outp)
        print('Saved test frame:', outp)


def run_build(mode='preview'):
    if mode == 'test_flags':
        run_test_flags()
        return

    duration, _, _, _, turns = get_ep06_config()
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
        (2.5, '00_hook'),
        (turns[3]['endSec'] - 0.4, '01_che_switzerland'),
        (turns[6]['endSec'] - 0.4, '02_vnm_vietnam'),
        (turns[9]['endSec'] - 0.4, '03_twn_taiwan'),
        (turns[12]['endSec'] - 0.4, '04_chn_china'),
        (turns[15]['endSec'] - 0.4, '05_jpn_japan'),
        (turns[16]['startSec'] + 1.8, '06_outro_asia'),
        (turns[17]['startSec'] + 2.2, '07_outro_table'),
    ]

    silent_out = R / f'exports/EP06_TOP5_TRAVEL_{tag}_silent.mp4'
    final_out = R / f'exports/EP06_TOP5_TRAVEL_{tag}_voice_only.mp4'
    silent_out.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Building EP06 ({w}x{h} @ {fps}fps, {total_frames} frames, {num_workers} workers) ===", flush=True)
    t0 = time.time()

    chunk_size = math.ceil(total_frames / num_workers)
    procs = []
    chunk_paths = []
    for i in range(num_workers):
        sf = i * chunk_size
        ef = min(total_frames, (i + 1) * chunk_size)
        if sf >= total_frames:
            break
        cpath = R / f'work/ep06_chunk_{i}.mp4'
        chunk_paths.append(cpath)
        p = mp.Process(target=worker_render_chunk, args=(i, sf, ef, w, h, fps, cpath, check_points))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
        if p.exitcode != 0:
            raise RuntimeError(f"Worker failed with exitcode {p.exitcode}")

    concat_txt = R / 'work/ep06_chunks.txt'
    concat_txt.write_text('\n'.join(f"file {cp.name}" for cp in chunk_paths))
    subprocess.run([ff(), '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_txt), '-c', 'copy', str(silent_out)], check=True)

    print(f"Video track complete in {time.time() - t0:.1f}s -> {silent_out}", flush=True)
    mix_audio_clean(silent_out, final_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['test_flags', 'preview', '1080p', '4k'], default='preview')
    args = parser.parse_args()
    run_build(args.mode)
