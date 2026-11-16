"""Episode 07: 5 อันดับประเทศที่บินจากไทยนานที่สุด! (ระยะทาง + เวลาบิน + พื้นผิวธงชาติ)
Architecture:
1. Monotonic PCHIP Cubic Hermite Camera Spline (Thailand -> North America -> South America -> Americas Overview)
2. 16K Land-Bled Terrain + Natural Earth 10m Vector Ocean Masking with per-polygon `polys_bbox` culling
3. In-place Flat Geo-Anchored Country Surfaces Filled with Crisp Vector National Flags (CAN, BRA, ARG, CHL, PER)
4. macOS CoreText + CoreGraphics OpenType Kanit shaper (perfect Thai vowel + tone-mark stacking, cached sprites)
5. Flight Hours & Distance Odometer Counters + Landmark Icons + Airplane Routes + Top-5 Outro Comparison Card
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

        self.cg.CGContextSetRGBStrokeColor(ctx, 0.0, 0.0, 0.0, 150.0 / 255.0)
        self.cg.CGContextSetRGBFillColor(ctx, 0.0, 0.0, 0.0, 150.0 / 255.0)
        self.cg.CGContextSetTextDrawingMode(ctx, 2)
        self.cg.CGContextSetTextPosition(ctx, pad_x + sh_off * 0.5, base_y_from_bot - sh_off)
        self.ct.CTLineDraw(line, ctx)

        self.cg.CGContextSetRGBStrokeColor(ctx, 10.0 / 255.0, 18.0 / 255.0, 28.0 / 255.0, 230.0 / 255.0)
        self.cg.CGContextSetTextDrawingMode(ctx, 1)
        self.cg.CGContextSetTextPosition(ctx, pad_x, base_y_from_bot)
        self.ct.CTLineDraw(line, ctx)

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


def draw_flag_emblem(fd, code, xy_fn, box):
    """Draw crisp vector national flag pattern for CAN, BRA, ARG, CHL, PER."""
    deg_w = box[2] - box[0]
    px_per_deg = fd.im.size[0] / deg_w
    W, H = fd.im.size

    if code == 'CAN':
        # Red-White-Red vertical bands + centered Crimson 11-point Maple Leaf
        fd.rectangle([0, 0, W, H], fill=(216, 6, 33, 232))
        x_l, _ = xy_fn((-113.5, 56.0))
        x_r, _ = xy_fn((-79.5, 56.0))
        if x_r > x_l and x_r > 0 and x_l < W:
            fd.rectangle([max(0, x_l), 0, min(W, x_r), H], fill=(248, 250, 252, 240))
        cx, cy = xy_fn((-96.5, 55.5))
        s = 13.5 * px_per_deg
        leaf_norm = [
            (0.0, -0.50), (0.09, -0.30), (0.24, -0.35), (0.18, -0.09),
            (0.36, -0.18), (0.39, -0.06), (0.52, -0.05), (0.45, 0.08),
            (0.50, 0.17), (0.22, 0.21), (0.27, 0.31), (0.04, 0.26),
            (0.04, 0.50), (-0.04, 0.50), (-0.04, 0.26), (-0.27, 0.31),
            (-0.22, 0.21), (-0.50, 0.17), (-0.45, 0.08), (-0.52, -0.05),
            (-0.39, -0.06), (-0.36, -0.18), (-0.18, -0.09), (-0.24, -0.35),
            (-0.09, -0.30),
        ]
        fd.polygon([(cx + x * s, cy + y * s) for x, y in leaf_norm], fill=(216, 6, 33, 250))

    elif code == 'BRA':
        # Forest Green + Gold Diamond + Royal Blue Celestial Disc + White Curved Sash
        fd.rectangle([0, 0, W, H], fill=(0, 156, 59, 234))
        cx, cy = xy_fn((-52.5, -12.5))
        dx, dy = 13.5 * px_per_deg, 10.5 * px_per_deg
        fd.polygon([(cx, cy - dy), (cx + dx, cy), (cx, cy + dy), (cx - dx, cy)], fill=(255, 223, 0, 246))
        r_blue = 5.4 * px_per_deg
        fd.ellipse([cx - r_blue, cy - r_blue, cx + r_blue, cy + r_blue], fill=(0, 39, 118, 250))
        # Subtle curved white equatorial band across globe
        band_w = max(2, int(0.85 * px_per_deg))
        pts_band = []
        for k in range(25):
            u = -1.0 + 2.0 * (k / 24.0)
            bx = cx + u * r_blue * 0.94
            by = cy + u * r_blue * 0.18 - math.cos(u * 1.15) * r_blue * 0.22
            pts_band.append((bx, by))
        fd.line(pts_band, fill=(255, 255, 255, 246), width=band_w)

    elif code == 'ARG':
        # Sky Blue - White - Sky Blue horizontal bands + Golden Sun of May
        fd.rectangle([0, 0, W, H], fill=(116, 172, 223, 232))
        _, y_top = xy_fn((-63.6, -32.2))
        _, y_bot = xy_fn((-63.6, -42.2))
        if y_bot > y_top and y_bot > 0 and y_top < H:
            fd.rectangle([0, max(0, y_top), W, min(H, y_bot)], fill=(248, 250, 252, 244))
        cx, cy = xy_fn((-64.0, -37.2))
        r_ray = 2.9 * px_per_deg
        r_in = 1.65 * px_per_deg
        r_core = 1.4 * px_per_deg
        fd.polygon(star_pts(cx, cy, r_ray, r_in, points=16, rot_deg=-90.0), fill=(246, 180, 14, 250))
        fd.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=(246, 180, 14, 252), outline=(180, 118, 0, 235), width=max(1, W // 360))

    elif code == 'CHL':
        # White upper half + Crimson lower half + Blue upper-left Canton centered neatly over N. Chile
        _, y_split = xy_fn((-70.5, -34.5))
        if y_split > 0:
            fd.rectangle([0, 0, W, min(H, y_split)], fill=(248, 250, 252, 240))
        if y_split < H:
            fd.rectangle([0, max(0, y_split), W, H], fill=(213, 43, 30, 236))
        x_can, y_can_bot = xy_fn((-68.7, -28.0))
        if x_can > 0 and y_can_bot > 0:
            fd.rectangle([0, 0, min(W, x_can), min(H, y_can_bot)], fill=(0, 57, 166, 248))
        cx, cy = xy_fn((-69.8, -23.5))
        r_st = 1.45 * px_per_deg
        fd.polygon(star_pts(cx, cy, r_st, r_st * 0.382, points=5, rot_deg=-90.0), fill=(255, 255, 255, 252))

    elif code == 'PER':
        # Vertical Crimson - White - Crimson bands
        fd.rectangle([0, 0, W, H], fill=(217, 16, 35, 234))
        x_l, _ = xy_fn((-76.9, -9.2))
        x_r, _ = xy_fn((-73.1, -9.2))
        if x_r > x_l and x_r > 0 and x_l < W:
            fd.rectangle([max(0, x_l), 0, min(W, x_r), H], fill=(248, 250, 252, 244))


def draw_country_flag_flat(im, feat, code, fade_a, xy, box, w, h, edge_rgb=(255, 225, 90)):
    """Sub-pixel flat country surface anchored in-place and filled with its crisp vector national flag."""
    if fade_a <= 0.01 or feat is None:
        return im
    bb = feat['bbox']
    if bb[2] < box[0] - 1.0 or bb[0] > box[2] + 1.0 or bb[3] < box[1] - 1.0 or bb[1] > box[3] + 1.0:
        return im

    country_mask = Image.new('L', (w, h))
    cmd = ImageDraw.Draw(country_mask)
    for pb in feat['polys_bbox']:
        pbb = pb['bbox']
        if pbb[2] < box[0] - 1.0 or pbb[0] > box[2] + 1.0 or pbb[3] < box[1] - 1.0 or pbb[1] > box[3] + 1.0:
            continue
        cmd.polygon([xy(p) for p in pb['outer']], fill=255)
        for hole in pb['holes']:
            cmd.polygon([xy(p) for p in hole], fill=0)

    flag_canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flag_canvas)
    draw_flag_emblem(fd, code, xy, box)
    if fade_a < 0.99:
        r, g_c, b_c, a_c = flag_canvas.split()
        a_c = a_c.point(lambda v: int(v * fade_a))
        flag_canvas.putalpha(a_c)

    clipped_flag = Image.composite(flag_canvas, Image.new('RGBA', (w, h)), country_mask)
    im = Image.alpha_composite(im, clipped_flag)

    edge = Image.new('RGBA', (w, h))
    ed = ImageDraw.Draw(edge)
    for rb in feat['rings_bbox']:
        rbb = rb['bbox']
        if rbb[2] < box[0] - 1.0 or rbb[0] > box[2] + 1.0 or rbb[3] < box[1] - 1.0 or rbb[1] > box[3] + 1.0:
            continue
        ed.line([xy(p) for p in rb['pts']], fill=(*edge_rgb, int(250 * fade_a)), width=max(2, w // 190))
    im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 110))))
    im = Image.alpha_composite(im, edge)
    return im


def bezier_arc(p0, p1, progress, steps=56, lift_deg=0.22, ctrl_override=None):
    """Smooth great-circle-like curved route arc arching gracefully northward across Atlantic."""
    if ctrl_override is not None:
        ctrl = ctrl_override
    else:
        mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
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


def get_ep07_config():
    timing = json.loads((R / 'audio/ep07_longest_flights_timing.json').read_text(encoding='utf-8'))
    turns = timing['turns']
    duration = timing['durationSec'] + 1.2

    # Smooth PCHIP camera waypoints: Thailand -> High Eurasian/Atlantic arc -> Canada -> Brazil -> Argentina -> Chile -> Peru -> All Americas!
    waypoints = [
        (0.0,                        100.5,  15.0,  58.0),    # Hook: Thailand & Southeast Asia
        (turns[0]['endSec'] - 0.5,    52.0,  34.0,  112.0),   # Rise high panning west across Eurasia
        (turns[1]['startSec'] + 1.6, -96.5,  55.5,  122.0),   # Arrive in Canada (mainland & maple leaf framed cleanly below cards)
        (turns[2]['endSec'],         -96.5,  55.2,  120.0),   # Hold Canada flight hours
        (turns[3]['endSec'],         -96.5,  55.0,  118.0),   # Hold Canada distance & airfare
        (turns[4]['startSec'] + 1.6, -53.5,  -6.5,  86.0),    # Sweep southeast to #4 Brazil
        (turns[5]['endSec'],         -53.5,  -6.7,  84.5),    # Hold Brazil flight hours
        (turns[6]['endSec'],         -53.5,  -6.9,  83.5),    # Hold Brazil distance & airfare
        (turns[7]['startSec'] + 1.4, -63.6, -31.8,  72.0),    # Glide southwest to #3 Argentina
        (turns[8]['endSec'],         -63.6, -32.0,  71.0),    # Hold Argentina flight hours
        (turns[9]['endSec'],         -63.6, -32.2,  70.0),    # Hold Argentina distance & airfare
        (turns[10]['startSec'] + 1.4,-71.3, -29.2,  84.0),    # Slide west across Andes to #2 Chile
        (turns[11]['endSec'],        -71.3, -29.4,  83.0),    # Hold Chile flight hours
        (turns[12]['endSec'],        -71.3, -29.6,  82.0),    # Hold Chile distance & airfare
        (turns[13]['startSec'] + 1.5,-75.0,  -6.0,  44.0),    # Zoom crisp north along Andes to #1 Peru (Antipodes!)
        (turns[14]['endSec'],        -75.0,  -6.1,  43.0),    # Hold Peru flight hours
        (turns[15]['endSec'],        -75.0,  -6.2,  42.0),    # Hold Peru 19,714 km distance
        (turns[16]['startSec'] + 1.8,-74.0,   6.0, 162.0),    # Pull out to frame ALL 5 countries (Canada down to Chile/Argentina clear of bottom subtitle!)
        (duration,                   -75.0,   5.0, 160.0),    # Hold Americas panorama behind Top-5 summary table
    ]

    countries_cards = [
        {
            'code': 'CAN',
            'rank_tag': 'อันดับ 5 • แชมป์บินตรงนานที่สุด',
            'name': 'แคนาดา (Canada)',
            'short_name': 'แคนาดา',
            'icon': 'can_maple',
            't_start': turns[1]['startSec'], 't_end': turns[3]['endSec'] + 0.15,
            't_hours': turns[2]['startSec'], 't_hours_end': turns[2]['endSec'],
            't_dist': turns[3]['startSec'], 't_dist_end': turns[3]['endSec'],
            'hours_lbl': 'เวลาบินตรง (Air Canada)',
            'hours_prefix': '13.5 - ', 'hours_target': 15.5, 'hours_dec': 1, 'hours_suffix': ' ชม.',
            'hours_short': '13.5-15.5 ชม.',
            'dist_km': 11799,
            'ticket_pill': 'ตั๋ว 32,000 - 52,000 บ.',
            'mode_pill': 'บินตรงไม่แวะพัก (YVR)',
            'col': '#ff7b7b', 'edge_rgb': (255, 145, 145),
        },
        {
            'code': 'BRA',
            'rank_tag': 'อันดับ 4 • ประตูสู่อเมริกาใต้',
            'name': 'บราซิล (Brazil)',
            'short_name': 'บราซิล',
            'icon': 'bra_christ',
            't_start': turns[4]['startSec'], 't_end': turns[6]['endSec'] + 0.15,
            't_hours': turns[5]['startSec'], 't_hours_end': turns[5]['endSec'],
            't_dist': turns[6]['startSec'], 't_dist_end': turns[6]['endSec'],
            'hours_lbl': 'เวลารวมต่อเครื่อง (GRU)',
            'hours_prefix': '24.0 - ', 'hours_target': 28.0, 'hours_dec': 1, 'hours_suffix': ' ชม.',
            'hours_short': '24-28 ชม.',
            'dist_km': 16418,
            'ticket_pill': 'ตั๋ว 48,000 - 75,000 บ.',
            'mode_pill': 'ไม่มีบินตรง • ต่อ 1-2 ต่อ',
            'col': '#58d5b5', 'edge_rgb': (115, 235, 195),
        },
        {
            'code': 'ARG',
            'rank_tag': 'อันดับ 3 • เวลาต่างจากไทย -10 ชม.',
            'name': 'อาร์เจนตินา (Argentina)',
            'short_name': 'อาร์เจนตินา',
            'icon': 'arg_glacier',
            't_start': turns[7]['startSec'], 't_end': turns[9]['endSec'] + 0.15,
            't_hours': turns[8]['startSec'], 't_hours_end': turns[8]['endSec'],
            't_dist': turns[9]['startSec'], 't_dist_end': turns[9]['endSec'],
            'hours_lbl': 'เวลารวมต่อเครื่อง (EZE)',
            'hours_prefix': '26.0 - ', 'hours_target': 32.0, 'hours_dec': 1, 'hours_suffix': ' ชม.',
            'hours_short': '26-32 ชม.',
            'dist_km': 16884,
            'ticket_pill': 'ตั๋ว 52,000 - 80,000 บ.',
            'mode_pill': 'ไม่มีบินตรง • ข้ามแอตแลนติก',
            'table_mode': 'ไม่มีบินตรง • ต่อ 1-2 ต่อ',
            'col': '#63b3ed', 'edge_rgb': (130, 210, 255),
        },
        {
            'code': 'CHL',
            'rank_tag': 'อันดับ 2 • แนวยาวริมแอนดีส',
            'name': 'ชิลี (Chile)',
            'short_name': 'ชิลี',
            'icon': 'chl_moai',
            't_start': turns[10]['startSec'], 't_end': turns[12]['endSec'] + 0.15,
            't_hours': turns[11]['startSec'], 't_hours_end': turns[11]['endSec'],
            't_dist': turns[12]['startSec'], 't_dist_end': turns[12]['endSec'],
            'hours_lbl': 'เวลารวมต่อเครื่อง (SCL)',
            'hours_prefix': '26.0 - ', 'hours_target': 35.0, 'hours_dec': 1, 'hours_suffix': ' ชม.',
            'hours_short': '26-35 ชม.',
            'dist_km': 17653,
            'ticket_pill': 'ตั๋ว 55,000 - 85,000 บ.',
            'mode_pill': 'ไม่มีบินตรง • ต่อ 1-2 ต่อ',
            'col': '#ff8a8a', 'edge_rgb': (255, 165, 165),
        },
        {
            'code': 'PER',
            'rank_tag': 'อันดับ 1 • ตรงข้ามขั้วโลกของไทย!',
            'name': 'เปรู (Peru)',
            'short_name': 'เปรู',
            'icon': 'per_machupicchu',
            't_start': turns[13]['startSec'], 't_end': turns[15]['endSec'] + 0.15,
            't_hours': turns[14]['startSec'], 't_hours_end': turns[14]['endSec'],
            't_dist': turns[15]['startSec'], 't_dist_end': turns[15]['endSec'],
            'hours_lbl': 'เวลารวมต่อเครื่อง (LIM)',
            'hours_prefix': '28.0 - ', 'hours_target': 37.0, 'hours_dec': 1, 'hours_suffix': ' ชม.',
            'hours_short': '28-37 ชม.',
            'dist_km': 19714,
            'ticket_pill': 'ตั๋ว 55,000 - 90,000 บ.',
            'mode_pill': 'Antipodes ของไทย!',
            'col': '#ffd44d', 'edge_rgb': (255, 225, 90),
        },
    ]

    sub_lines = [
        [('ประเทศไหนที่บินจากไทยนานที่สุด?', '#ffffff'), ('ไล่จากแชมป์บินตรง สู่จุดไกลสุดขอบโลก!', '#ffd44d')],
        [('อันดับ 5 แคนาดา: แชมป์บินตรงนานสุดจากไทย', '#ff8a8a')],
        [('บินตรงรวดเดียว กรุงเทพฯ–แวนคูเวอร์ 13.5–15.5 ชม.', '#ffffff')],
        [('ระยะทาง ~11,799 กม. • ตั๋วเฉลี่ย 32,000–52,000 บ.', '#ffd44d')],
        [('อันดับ 4 บราซิล: ประตูสู่อเมริกาใต้ ไม่มีบินตรง', '#58d5b5')],
        [('ต่อเครื่องตะวันออกกลาง/ยุโรป รวม 24–28 ชม.', '#ffffff')],
        [('ระยะทาง ~16,418 กม. • ตั๋วเฉลี่ย 48,000–75,000 บ.', '#ffd44d')],
        [('อันดับ 3 อาร์เจนตินา: เวลาต่างจากไทย 10 ชม. เต็ม', '#63b3ed')],
        [('บินข้ามแอตแลนติกพร้อมรอต่อเครื่อง 26–32 ชม.', '#ffffff')],
        [('ระยะทาง ~16,884 กม. • ตั๋วเฉลี่ย 52,000–80,000 บ.', '#ffd44d')],
        [('อันดับ 2 ชิลี: แนวยาวริมแอนดีสฝั่งแปซิฟิก', '#ff8a8a')],
        [('ต่อเครื่อง 1–2 ต่อ ใช้เวลารวม 26–35 ชม.', '#ffffff')],
        [('ระยะทาง ~17,653 กม. • ตั๋วเฉลี่ย 55,000–85,000 บ.', '#ffd44d')],
        [('อันดับ 1 ไกลสุด & นานสุดจากไทย: เปรู!', '#ffd44d')],
        [('จุดตรงข้ามขั้วโลกของกรุงเทพฯ ใช้เวลา 28–37 ชม.!', '#ffffff')],
        [('ระยะทาง ~19,714 กม. • ตั๋วเฉลี่ย 55,000–90,000 บ.', '#58d5b5')],
        [('จากบินตรง 15 ชม. สู่เส้นทางมาราธอนเกือบ 2 วันข้ามโลก', '#ffd44d')],
        [('เคยนั่งเครื่องบินนานสุดกี่ ชม.? อยากไปประเทศไหนที่สุด?', '#ffd44d'), ('คอมเมนต์มาเล่ากันหน่อยนะครับ!', '#ffffff')],
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

    # 1. Sub-pixel cropped 16K terrain background + 10m Vector Ocean/Land Mask
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
        if code in ('THA', 'CAN', 'BRA', 'ARG', 'CHL', 'PER'):
            continue
        bb = c['bbox']
        if bb[2] < box[0] or bb[0] > box[2] or bb[3] < box[1] or bb[1] > box[3]:
            continue
        for rb in c['rings_bbox']:
            rbb = rb['bbox']
            if rbb[2] < box[0] or rbb[0] > box[2] or rbb[3] < box[1] or rbb[1] > box[3]:
                continue
            d.line([xy(p) for p in rb['pts']], fill=(220, 235, 228, 75), width=max(1, w // 450))

    # 3. Thailand highlight (origin!)
    if tha_country:
        tbb = tha_country['bbox']
        if not (tbb[2] < box[0] or tbb[0] > box[2] or tbb[3] < box[1] or tbb[1] > box[3]):
            edge = Image.new('RGBA', (w, h))
            ed = ImageDraw.Draw(edge)
            for rb in tha_country['rings_bbox']:
                rbb = rb['bbox']
                if rbb[2] < box[0] or rbb[0] > box[2] or rbb[3] < box[1] or rbb[1] > box[3]:
                    continue
                ed.line([xy(p) for p in rb['pts']], fill=(88, 213, 181, 210), width=max(2, w // 220))
            im = Image.alpha_composite(im, edge.filter(ImageFilter.GaussianBlur(max(2, w // 120))))
            im = Image.alpha_composite(im, edge)

    # 4. Flat Flag-Filled Countries (anchored in-place on real GeoJSON borders)
    outro_start = turns[16]['startSec']
    for cc in countries_cards:
        code = cc['code']
        feat = flag_feats.get(code)
        ts, te = cc['t_start'] - 0.35, cc['t_end'] + 0.35
        if ts <= t <= te:
            fade_a = smootherstep((t - ts) / 0.85) * (1.0 - smootherstep((t - (te - 0.85)) / 0.85))
            im = draw_country_flag_flat(im, feat, code, fade_a, xy, box, w, h, edge_rgb=cc['edge_rgb'])
        elif t >= outro_start - 0.4:
            out_a = smootherstep((t - (outro_start - 0.4)) / 0.9) * (1.0 - smootherstep((t - (duration - 1.2)) / 0.8))
            if out_a > 0.05:
                im = draw_country_flag_flat(im, feat, code, 0.72 * out_a, xy, box, w, h, edge_rgb=cc['edge_rgb'])

    # 5. Animated Long-Haul Flight Routes from Thailand (BKK) -> Hubs away from flag center emblems
    tha_hub = (100.75, 13.69)
    route_layer = Image.new('RGBA', (w, h))
    rd = ImageDraw.Draw(route_layer)
    targets_hubs = {
        'CAN': (-123.12, 49.28),  # Vancouver West Coast (clear of Maple Leaf at -96.5, 55.5)
        'BRA': (-46.63, -23.55),  # Sao Paulo SE coast (clear of celestial globe at -52.5, -12.5)
        'ARG': (-58.38, -34.60),  # Buenos Aires coast (east of Sun of May at -64.0, -37.2)
        'CHL': (-70.67, -33.45),  # Santiago central valley (south of blue canton/star at -23.5)
        'PER': (-77.04, -12.05),  # Lima coast (southwest edge cleanly inside red/white border)
    }
    for cc in countries_cards:
        r_start = cc['t_start'] - 0.6
        r_end = cc['t_start'] + 1.5
        if t >= r_start:
            prog = smootherstep((t - r_start) / (r_end - r_start))
            active_fade = 1.0 if t <= cc['t_end'] + 0.5 else (0.72 if t >= outro_start - 0.4 else 0.28)
            end_fade = 1.0 - smootherstep((t - (duration - 1.2)) / 0.8) if t > duration - 1.2 else 1.0
            alpha = int(225 * active_fade * end_fade)
            if alpha > 5:
                col_rgb = hex_rgba(cc['col'])[:3]
                ctrl_ov = (-10.0, 82.0) if cc['code'] == 'CAN' else None
                arc_pts = [xy(pt) for pt in bezier_arc(tha_hub, targets_hubs[cc['code']], prog, ctrl_override=ctrl_ov)]
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

    # 6. Summary Floating Pins on Outro Turn 16 (All 5 Americas Countries visible simultaneously!)
    turn17_start = turns[17]['startSec']
    if outro_start - 0.2 <= t < turn17_start + 0.55:
        p_fade = smootherstep((t - (outro_start - 0.2)) / 0.7) * (1.0 - smootherstep((t - (turn17_start - 0.1)) / 0.6))
        if p_fade > 0.02:
            pd = ImageDraw.Draw(im)
            ox_step = max(9, w // 36)
            oy_step = max(13, h // 48)
            pin_specs = [
                ((-96.50, 51.00), '#5 แคนาดา (15.5 ชม.)', '#ff8a8a', 0, oy_step, 'mm'),
                ((-46.63, -23.55), '#4 บราซิล (28 ชม.)', '#58d5b5', 0, oy_step, 'mm'),
                ((-58.38, -34.60), '#3 อาร์เจนตินา (32 ชม.)', '#63b3ed', ox_step, 0, 'lm'),
                ((-70.67, -33.45), '#2 ชิลี (35 ชม.)', '#ff8a8a', -ox_step, 0, 'rm'),
                ((-77.04, -12.05), '#1 เปรู (37 ชม.)', '#ffd44d', -ox_step, 0, 'rm'),
            ]
            for coord, plbl, pcol, dx_off, dy_off, anc in pin_specs:
                px, py = xy(coord)
                if 0 < px < w and 0 < py < h:
                    r_dot = max(4, w // 125)
                    pd.ellipse([px - r_dot, py - r_dot, px + r_dot, py + r_dot], fill=hex_rgba(pcol, 255 * p_fade), outline=(255, 255, 255, int(255 * p_fade)), width=max(1, w // 360))
                    tx = max(int(w * 0.04), min(int(w * 0.96), px + dx_off))
                    draw_crisp_text(im, (tx, py + dy_off), plbl, fonts['pin'], hex_rgba(pcol, 255), alpha_scale=p_fade, stroke_w=max(1, w // 240), anchor=anc)

    # 7. Opening Title Hook (Turn 0)
    if t < turns[0]['endSec'] + 0.3:
        fade = smootherstep(t / 0.45) * (1.0 - smootherstep((t - (turns[0]['endSec'] - 0.5)) / 0.7))
        if fade > 0.02:
            title_y = int(h * 0.145)
            paste_icon_alpha(im, icons['globe'], w / 2, title_y - int(h * 0.062), max(36, int(w * 0.13)), fade)
            draw_crisp_text(im, (w / 2, title_y), "พิกัดเงิน • รอบโลกน่ารู้", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=fade, stroke_w=max(2, w // 220))
            draw_crisp_text(im, (w / 2, title_y + int(h * 0.048)), "5 ประเทศที่บินนานที่สุด!", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=fade, stroke_w=max(2, w // 180))
            draw_crisp_text(im, (w / 2, title_y + int(h * 0.098)), "บินกี่ชั่วโมง & ไกลจากไทยกี่ กม.", fonts['title_big'], hex_rgba('#ffffff'), alpha_scale=fade, stroke_w=max(2, w // 180))

    # 8. Active Country Card (Landmark + Hours Odometer + Distance Odometer + Ticket/Mode Pills)
    active_cc = next((c for c in countries_cards if c['t_start'] <= t <= c['t_end']), None)
    if active_cc:
        cfade = smootherstep((t - active_cc['t_start']) / 0.38) * (1.0 - smootherstep((t - (active_cc['t_end'] - 0.42)) / 0.42))
        if cfade > 0.02:
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

            # Row 1: Flight Duration Hours with Odometer count-up
            if t >= active_cc['t_hours']:
                h_in = smootherstep((t - active_cc['t_hours']) / 0.35)
                h_alpha = min(cfade, h_in)
                if h_alpha > 0.02:
                    sy = int((1.0 - h_in) * h * 0.015)
                    ry1 = int(h * 0.184) + sy
                    prog_h = smootherstep((t - active_cc['t_hours']) / min(1.8, active_cc['t_hours_end'] - active_cc['t_hours']))
                    h_cur = active_cc['hours_target'] * prog_h
                    hrs_txt = f"{active_cc['hours_prefix']}{h_cur:.{active_cc['hours_dec']}f}{active_cc['hours_suffix']}"
                    paste_icon_alpha(im, icons['clock'], int(w * 0.185), ry1, row_icon_sz, h_alpha)
                    draw_crisp_text(im, (int(w * 0.28), ry1 - int(h * 0.016)), active_cc['hours_lbl'], fonts['bal_lbl'], hex_rgba('#b8e6ff'), alpha_scale=h_alpha, stroke_w=max(1, w // 240), anchor='lm')
                    draw_crisp_text(im, (int(w * 0.28), ry1 + int(h * 0.017)), hrs_txt, fonts['bal_num'], hex_rgba('#ffd44d'), alpha_scale=h_alpha, stroke_w=max(2, w // 180), anchor='lm')

            # Row 2: Great-Circle Distance (km) Odometer + Dual Ticket/Flight-Mode Pills
            if t >= active_cc['t_dist']:
                d_in = smootherstep((t - active_cc['t_dist']) / 0.35)
                d_alpha = min(cfade, d_in)
                if d_alpha > 0.02:
                    sy = int((1.0 - d_in) * h * 0.015)
                    ry2 = int(h * 0.262) + sy
                    prog_d = smootherstep((t - active_cc['t_dist']) / min(1.8, active_cc['t_dist_end'] - active_cc['t_dist']))
                    km_cur = int(round(active_cc['dist_km'] * prog_d))
                    dist_txt = f"{km_cur:,} กิโลเมตร"
                    paste_icon_alpha(im, icons['distance'], int(w * 0.185), ry2, row_icon_sz, d_alpha)
                    draw_crisp_text(im, (int(w * 0.28), ry2 - int(h * 0.016)), "ระยะทางเส้นตรงจากกรุงเทพฯ", fonts['bal_lbl'], hex_rgba('#9ef0d8'), alpha_scale=d_alpha, stroke_w=max(1, w // 240), anchor='lm')
                    draw_crisp_text(im, (int(w * 0.28), ry2 + int(h * 0.017)), dist_txt, fonts['bal_num'], hex_rgba(active_cc['col']), alpha_scale=d_alpha, stroke_w=max(2, w // 180), anchor='lm')

                    # Row 3: Dual Pills (Flight Mode + Round-Trip Ticket Range)
                    ry3 = int(h * 0.324) + sy
                    p1_txt = active_cc['mode_pill']
                    p2_txt = active_cc['ticket_pill']
                    pw1 = measure_text_width(p1_txt, fonts['pill'])
                    pw2 = measure_text_width(p2_txt, fonts['pill'])
                    ppad = max(8, int(w * 0.024))
                    pgap = max(6, int(w * 0.02))
                    ph = max(20, int(h * 0.033))
                    tot_pw = (pw1 + ppad * 2) + pgap + (pw2 + ppad * 2)
                    px_start = (w - tot_pw) / 2.0
                    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                    ovd = ImageDraw.Draw(ov)
                    ovd.rounded_rectangle([px_start, ry3 - ph // 2, px_start + pw1 + ppad * 2, ry3 + ph // 2], radius=ph // 2, fill=(14, 30, 46, int(205 * d_alpha)), outline=(184, 230, 255, int(210 * d_alpha)), width=max(1, w // 340))
                    px2 = px_start + pw1 + ppad * 2 + pgap
                    col_rgb = hex_rgba(active_cc['col'])[:3]
                    ovd.rounded_rectangle([px2, ry3 - ph // 2, px2 + pw2 + ppad * 2, ry3 + ph // 2], radius=ph // 2, fill=(14, 30, 46, int(205 * d_alpha)), outline=(*col_rgb, int(220 * d_alpha)), width=max(1, w // 340))
                    im = Image.alpha_composite(im, ov)
                    draw_crisp_text(im, (px_start + ppad, ry3), p1_txt, fonts['pill'], hex_rgba('#b8e6ff'), alpha_scale=d_alpha, stroke_w=max(1, w // 320), anchor='lm')
                    draw_crisp_text(im, (px2 + ppad, ry3), p2_txt, fonts['pill'], hex_rgba(active_cc['col']), alpha_scale=d_alpha, stroke_w=max(1, w // 320), anchor='lm')

    # 9. Outro Header + Screenshot-Ready Top-5 Summary Comparison Card (Turn 17)
    elif t >= outro_start - 0.1:
        ofade = smootherstep((t - outro_start) / 0.45) * (1.0 - smootherstep((t - (duration - 1.2)) / 0.8))
        if ofade > 0.02:
            if t < turn17_start:
                cy_top = int(h * 0.120)
                paste_icon_alpha(im, icons['globe'], w / 2, cy_top - int(h * 0.052), max(34, int(w * 0.115)), ofade)
                draw_crisp_text(im, (w / 2, cy_top), "สรุป 5 ประเทศบินไกลสุดจากไทย", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=ofade, stroke_w=max(2, w // 220))
                draw_crisp_text(im, (w / 2, cy_top + int(h * 0.044)), "15 ชม. ยัน 37 ชม. ข้ามซีกโลก!", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=ofade, stroke_w=max(2, w // 180))
            else:
                card_a = smootherstep((t - turn17_start) / 0.55) * (1.0 - smootherstep((t - (duration - 1.2)) / 0.8))
                if card_a > 0.02:
                    scrim = Image.new('RGBA', (w, h), (8, 18, 28, int(135 * card_a)))
                    im = Image.alpha_composite(im, scrim)
                cy_top = int(h * 0.118)
                paste_icon_alpha(im, icons['globe'], w / 2, cy_top - int(h * 0.046), max(30, int(w * 0.10)), ofade)
                draw_crisp_text(im, (w / 2, cy_top), "พิชิตระยะทางไกลสุดขอบโลก!", fonts['badge'], hex_rgba('#58d5b5'), alpha_scale=ofade, stroke_w=max(2, w // 220))
                draw_crisp_text(im, (w / 2, cy_top + int(h * 0.042)), "สรุป 5 อันดับ บินนานที่สุด", fonts['title_big'], hex_rgba('#ffd44d'), alpha_scale=ofade, stroke_w=max(2, w // 180))

                if card_a > 0.02:
                    cx0_b, cx1_b = int(w * 0.042), int(w * 0.958)
                    cy0_b, cy1_b = int(h * 0.220), int(h * 0.745)
                    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                    ovd = ImageDraw.Draw(ov)
                    ovd.rounded_rectangle([cx0_b, cy0_b, cx1_b, cy1_b], radius=max(10, int(w * 0.038)), fill=(12, 26, 40, int(218 * card_a)), outline=(88, 213, 181, int(200 * card_a)), width=max(1, w // 270))
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
                        paste_icon_alpha(im, icons[rcc['icon']], cx0_b + int(w * 0.090), ry_c, ic_tbl_sz, ra)
                        draw_crisp_text(im, (cx0_b + int(w * 0.165), ry_c - int(row_h * 0.15)), f"#{rank_num} {rcc['short_name']}", fonts['tbl_name'], hex_rgba(rcc['col']), alpha_scale=ra, stroke_w=max(1, w // 260), anchor='lm')
                        draw_crisp_text(im, (cx0_b + int(w * 0.165), ry_c + int(row_h * 0.20)), f"{rcc['dist_km']:,} กม. • {rcc.get('table_mode', rcc['mode_pill'])}", fonts['pill'], hex_rgba('#b8d4ea'), alpha_scale=ra, stroke_w=max(1, w // 340), anchor='lm')
                        draw_crisp_text(im, (cx1_b - int(w * 0.035), ry_c - int(row_h * 0.15)), rcc['hours_short'], fonts['tbl_val'], hex_rgba('#ffd44d'), alpha_scale=ra, stroke_w=max(1, w // 260), anchor='rm')
                        draw_crisp_text(im, (cx1_b - int(w * 0.035), ry_c + int(row_h * 0.20)), rcc['ticket_pill'], fonts['pill'], hex_rgba('#9ef0d8'), alpha_scale=ra, stroke_w=max(1, w // 340), anchor='rm')

    # 10. Subtitles
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
    draw_crisp_text(im, (w * 0.5, h * 0.95), "อ้างอิง: FlightConnections, Skyscanner, WGS84 (BKK) • แผนที่: Natural Earth", fonts['footer'], (210, 230, 245, 200), alpha_scale=1.0, stroke_w=max(1, w // 360))
    return im


def load_resources(w):
    t16k = R / 'work/cached_world_terrain_16k_landbleed.png'
    terrain = Image.open(t16k if t16k.exists() else (R / 'work/cached_world_terrain_blue_ocean.png')).convert('RGB')
    countries = build_ring_index(json.loads((R / 'data/processed/world_countries.geojson').read_text(encoding='utf-8'))['features'])
    tha_country = next((c for c in countries if c['properties'].get('adm0_a3') == 'THA'), None)
    flag_feats = {
        code: next((c for c in countries if c['properties'].get('adm0_a3') == code), None)
        for code in ('CAN', 'BRA', 'ARG', 'CHL', 'PER')
    }
    icons = {
        'clock': Image.open(R / 'assets/graphics/icon_clock_white.png').convert('RGBA'),
        'distance': Image.open(R / 'assets/graphics/icon_distance_white.png').convert('RGBA'),
        'globe': Image.open(R / 'assets/graphics/icon_globe_white.png').convert('RGBA'),
        'can_maple': Image.open(R / 'assets/graphics/icon_can_maple_white.png').convert('RGBA'),
        'bra_christ': Image.open(R / 'assets/graphics/icon_bra_christ_white.png').convert('RGBA'),
        'arg_glacier': Image.open(R / 'assets/graphics/icon_arg_glacier_white.png').convert('RGBA'),
        'chl_moai': Image.open(R / 'assets/graphics/icon_chl_moai_white.png').convert('RGBA'),
        'per_machupicchu': Image.open(R / 'assets/graphics/icon_per_machupicchu_white.png').convert('RGBA'),
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
        'pin': get_kanit(max(10, w // 36), weight='bold'),
        'footer': get_kanit(max(8, w // 46), weight='medium'),
    }
    return terrain, countries, tha_country, flag_feats, icons, fonts


def worker_render_chunk(worker_id, start_frame, end_frame, w, h, fps, out_chunk, check_points=None):
    duration, waypoints, countries_cards, subtitles, turns = get_ep07_config()
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
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=(R / f'work/ep07_worker_{worker_id}.log').open('w'))
    t_start = time.time()

    try:
        for idx in range(start_frame, end_frame):
            t = idx / fps
            im = render_frame(t, w, h, terrain, countries, tha_country, flag_feats, icons, fonts, cam_spline, countries_cards, subtitles, turns, duration)

            if check_points:
                for sec, label in check_points:
                    if idx == round(sec * fps):
                        im.convert('RGB').save(R / f'work/check_ep07_{label}.jpg')

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
    voice_path = R / 'audio/ep07_longest_flights_voice.mp3'
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
    subprocess.run(cmd, check=True, stderr=(R / 'exports/mix_ep07.log').open('w'))
    subprocess.run([ff_bin, '-v', 'error', '-i', str(output_path), '-f', 'null', '-'], check=True)
    print(f"Verified & Saved: {output_path}", flush=True)


def run_test_flags():
    w, h = 360, 640
    duration, waypoints, countries_cards, subtitles, turns = get_ep07_config()
    cam_spline = SmoothCameraSpline(waypoints)
    terrain, countries, tha_country, flag_feats, icons, fonts = load_resources(w)
    check_points = [
        (2.5, '00_hook'),
        (turns[3]['endSec'] - 0.4, '01_can_canada'),
        (turns[6]['endSec'] - 0.4, '02_bra_brazil'),
        (turns[9]['endSec'] - 0.4, '03_arg_argentina'),
        (turns[12]['endSec'] - 0.4, '04_chl_chile'),
        (turns[15]['endSec'] - 0.4, '05_per_peru'),
        (turns[16]['startSec'] + 1.8, '06_outro_americas'),
        (turns[17]['startSec'] + 2.2, '07_outro_table'),
    ]
    for sec, label in check_points:
        im = render_frame(sec, w, h, terrain, countries, tha_country, flag_feats, icons, fonts, cam_spline, countries_cards, subtitles, turns, duration)
        outp = R / f'work/check_ep07_{label}.jpg'
        im.convert('RGB').save(outp)
        print('Saved test frame:', outp)


def run_build(mode='preview'):
    if mode == 'test_flags':
        run_test_flags()
        return

    duration, _, _, _, turns = get_ep07_config()
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
        (turns[3]['endSec'] - 0.4, '01_can_canada'),
        (turns[6]['endSec'] - 0.4, '02_bra_brazil'),
        (turns[9]['endSec'] - 0.4, '03_arg_argentina'),
        (turns[12]['endSec'] - 0.4, '04_chl_chile'),
        (turns[15]['endSec'] - 0.4, '05_per_peru'),
        (turns[16]['startSec'] + 1.8, '06_outro_americas'),
        (turns[17]['startSec'] + 2.2, '07_outro_table'),
    ]

    silent_out = R / f'exports/EP07_LONGEST_FLIGHTS_{tag}_silent.mp4'
    final_out = R / f'exports/EP07_LONGEST_FLIGHTS_{tag}_voice_only.mp4'
    silent_out.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Building EP07 ({w}x{h} @ {fps}fps, {total_frames} frames, {num_workers} workers) ===", flush=True)
    t0 = time.time()

    chunk_size = math.ceil(total_frames / num_workers)
    procs = []
    chunk_paths = []
    for i in range(num_workers):
        sf = i * chunk_size
        ef = min(total_frames, (i + 1) * chunk_size)
        if sf >= total_frames:
            break
        cpath = R / f'work/ep07_chunk_{i}.mp4'
        chunk_paths.append(cpath)
        p = mp.Process(target=worker_render_chunk, args=(i, sf, ef, w, h, fps, cpath, check_points))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
        if p.exitcode != 0:
            raise RuntimeError(f"Worker failed with exitcode {p.exitcode}")

    concat_txt = R / 'work/ep07_chunks.txt'
    concat_txt.write_text('\n'.join(f"file {cp.name}" for cp in chunk_paths))
    subprocess.run([ff(), '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_txt), '-c', 'copy', str(silent_out)], check=True)

    print(f"Video track complete in {time.time() - t0:.1f}s -> {silent_out}", flush=True)
    mix_audio_clean(silent_out, final_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['test_flags', 'preview', '1080p', '4k'], default='preview')
    args = parser.parse_args()
    run_build(args.mode)
