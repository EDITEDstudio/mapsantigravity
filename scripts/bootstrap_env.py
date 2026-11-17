#!/usr/bin/env python3
"""Turnkey bootstrap for คลิปแผนที่-antigravity on a fresh machine.

Creates .venv, installs locked dependencies (including imageio-ffmpeg and edge-tts),
fetches Natural Earth 10m datasets, builds GeoJSON and terrain caches under data/ & work/,
and optionally regenerates Thai Neural TTS voiceover + timing files under audio/.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]

EPISODE_AUDIO_SPECS = [
    ("ep01_thailand_revenue", "audio/ep01_thailand_revenue_dialogue.json", "audio/ep01_thailand_revenue_voice.mp3", "audio/ep01_thailand_revenue_timing.json"),
    ("ep01_90s", "audio/ep01_90s_dialogue.json", "audio/ep01_90s_voice.mp3", "audio/ep01_90s_timing.json"),
    ("ep02_salary_20k", "audio/ep02_salary_20k_dialogue.json", "audio/ep02_salary_20k_voice.mp3", "audio/ep02_salary_20k_timing.json"),
    ("ep06_top5_travel", "audio/ep06_top5_travel_dialogue.json", "audio/ep06_top5_travel_voice.mp3", "audio/ep06_top5_travel_timing.json"),
    ("ep07_longest_flights", "audio/ep07_longest_flights_dialogue.json", "audio/ep07_longest_flights_voice.mp3", "audio/ep07_longest_flights_timing.json"),
    ("demo_niwat_timed", "audio/demo_dialogue.json", "audio/demo_niwat_timed.mp3", "audio/demo_niwat_timing.json"),
]

OCEAN_RGB = (14, 35, 54)


def ensure_dirs() -> None:
    for rel in ("data/raw", "data/processed", "work", "audio", "exports", "tests"):
        (R / rel).mkdir(parents=True, exist_ok=True)


def venv_python() -> Path:
    return R / ".venv/bin/python"


def _venv_ready(py_bin: Path) -> bool:
    if not py_bin.exists():
        return False
    probe = subprocess.run(
        [str(py_bin), "-c", "import PIL, numpy, requests, shapefile, imageio_ffmpeg, edge_tts, yaml"],
        capture_output=True,
    )
    return probe.returncode == 0


def ensure_venv_and_reexec(no_lock: bool) -> None:
    """Ensure .venv exists with required packages and run remaining steps inside it."""
    py_bin = venv_python()
    if not _venv_ready(py_bin):
        if not py_bin.exists():
            print(f"[1/5] Creating virtual environment at {R / '.venv'}...", flush=True)
            subprocess.run([sys.executable, "-m", "venv", str(R / ".venv")], check=True)
        req_file = R / ("requirements.txt" if no_lock or not (R / "requirements-lock.txt").exists() else "requirements-lock.txt")
        print(f"[1/5] Installing Python packages from {req_file.name}...", flush=True)
        subprocess.run([str(py_bin), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(py_bin), "-m", "pip", "install", "-r", str(req_file)], check=True)
    if Path(sys.executable).resolve() != py_bin.resolve():
        os.execv(str(py_bin), [str(py_bin), str(Path(__file__).resolve()), *sys.argv[1:]])


def ensure_fetch(force: bool = False) -> None:
    needed = [
        R / "data/raw/countries/ne_10m_admin_0_countries.shp",
        R / "data/raw/provinces/ne_10m_admin_1_states_provinces.shp",
        R / "data/raw/terrain/NE1_LR_LC_SR.tif",
        R / "data/processed/countries.geojson",
        R / "data/processed/thailand_provinces.geojson",
    ]
    if not force and all(p.exists() for p in needed):
        print("[2/5] Natural Earth 10m raw & Thailand GeoJSON already present.", flush=True)
        return
    print("[2/5] Fetching Natural Earth 10m datasets via map_video.py fetch...", flush=True)
    subprocess.run([sys.executable, str(R / "scripts/map_video.py"), "fetch"], cwd=R, check=True)


def build_world_countries_geojson(force: bool = False) -> None:
    out_path = R / "data/processed/world_countries.geojson"
    if out_path.exists() and not force:
        print(f"[3/5] {out_path.relative_to(R)} already present.", flush=True)
        return
    import shapefile

    shp_path = next((R / "data/raw/countries").glob("*.shp"))
    print(f"[3/5] Building {out_path.relative_to(R)} from {shp_path.name}...", flush=True)
    features = []
    for sr in shapefile.Reader(str(shp_path), encoding="utf-8").iterShapeRecords():
        rec = sr.record.as_dict()
        features.append({
            "type": "Feature",
            "properties": {
                "name": rec.get("NAME") or rec.get("ADMIN") or "",
                "adm0_a3": rec.get("ADM0_A3") or "",
            },
            "geometry": sr.shape.__geo_interface__,
        })
    out_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False), encoding="utf-8")
    print(f"      Wrote {len(features)} country features.", flush=True)


def _rasterize_land_mask(size: tuple[int, int], shp_path: Path):
    import shapefile
    from PIL import Image, ImageDraw

    w, h = size
    land = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(land)

    def to_xy(pt):
        return ((pt[0] + 180.0) / 360.0 * w, (90.0 - pt[1]) / 180.0 * h)

    for sr in shapefile.Reader(str(shp_path), encoding="utf-8").iterShapeRecords():
        geom = sr.shape.__geo_interface__
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            if len(poly[0]) >= 3:
                draw.polygon([to_xy(p) for p in poly[0]], fill=255)
            for hole in poly[1:]:
                if len(hole) >= 3:
                    draw.polygon([to_xy(p) for p in hole], fill=0)
    return land


def build_terrain_caches(force: bool = False) -> None:
    p_th = R / "work/cached_terrain.png"
    p_blue = R / "work/cached_world_terrain_blue_ocean.png"
    p_16k = R / "work/cached_world_terrain_16k_landbleed.png"

    targets = [p_th, p_blue, p_16k]
    if not force and all(p.exists() for p in targets):
        print("[4/5] All terrain caches under work/ already present.", flush=True)
        return

    from PIL import Image, ImageEnhance, ImageFilter

    Image.MAX_IMAGE_PIXELS = 300_000_000
    tif_path = next((R / "data/raw/terrain").glob("*.tif"))
    shp_path = next((R / "data/raw/countries").glob("*.shp"))
    print(f"[4/5] Building terrain caches from {tif_path.name}...", flush=True)

    raw = Image.open(tif_path).convert("RGB")
    rw, rh = raw.size  # 16200 x 8100

    if force or not p_th.exists():
        geo = [85, -5, 120, 32]
        crop_box = (
            int((geo[0] + 180) / 360 * rw),
            int((90 - geo[3]) / 180 * rh),
            int((geo[2] + 180) / 360 * rw),
            int((90 - geo[1]) / 180 * rh),
        )
        th = raw.crop(crop_box)
        th = ImageEnhance.Color(th).enhance(1.4)
        th = ImageEnhance.Brightness(th).enhance(0.64)
        th.save(p_th, optimize=False)
        th.close()
        print(f"      Saved {p_th.relative_to(R)} ({rw} crop)", flush=True)

    if force or any(not p.exists() for p in (p_blue, p_16k)):
        enhanced_16k = ImageEnhance.Brightness(ImageEnhance.Color(raw).enhance(1.25)).enhance(0.70)
        raw.close()

        if force or not p_blue.exists():
            w8 = enhanced_16k.resize((8100, 4050), Image.Resampling.LANCZOS)
            land_8k = _rasterize_land_mask((8100, 4050), shp_path)
            ocean_8k = Image.new("RGB", (8100, 4050), OCEAN_RGB)
            blue_8k = Image.composite(w8, ocean_8k, land_8k)
            blue_8k.save(p_blue, optimize=False)
            blue_8k.close()
            ocean_8k.close()
            land_8k.close()
            w8.close()
            print(f"      Saved {p_blue.relative_to(R)}", flush=True)

        if force or not p_16k.exists():
            land_16k = _rasterize_land_mask((rw, rh), shp_path)
            ocean_16k = Image.new("RGB", (rw, rh), OCEAN_RGB)
            bled = enhanced_16k.filter(ImageFilter.MaxFilter(5))
            land_core = land_16k.filter(ImageFilter.MinFilter(3))
            merged = Image.composite(enhanced_16k, bled, land_core)
            bled.close()
            land_core.close()
            final_16k = Image.composite(merged, ocean_16k, land_16k)
            merged.close()
            ocean_16k.close()
            land_16k.close()
            final_16k.save(p_16k, optimize=False)
            final_16k.close()
            print(f"      Saved {p_16k.relative_to(R)}", flush=True)

        enhanced_16k.close()
    else:
        raw.close()


def ensure_audio_assets(skip_audio: bool = False, force_audio: bool = False) -> None:
    if skip_audio:
        print("[5/5] Skipping TTS audio synthesis (--skip-audio).", flush=True)
        return

    tts_cli = R / ".agents/skills/thai-neural-tts/scripts/tts_cli.py"
    generated = 0
    for ep_name, dlg_rel, mp3_rel, timing_rel in EPISODE_AUDIO_SPECS:
        dlg_path = R / dlg_rel
        mp3_path = R / mp3_rel
        timing_path = R / timing_rel
        if not dlg_path.exists():
            continue
        if not force_audio and mp3_path.exists() and timing_path.exists():
            continue
        print(f"[5/5] Synthesizing {ep_name} via Niwat Neural TTS...", flush=True)
        subprocess.run(
            [sys.executable, str(tts_cli), "dialogue", str(dlg_path), "-o", str(mp3_path), "-t", str(timing_path)],
            cwd=R,
            check=True,
        )
        generated += 1

    # Generate demo_wasabi.mp3 + demo_niwat.mp3 from audio/narration.txt if missing
    narr_txt = R / "audio/narration.txt"
    if narr_txt.exists():
        for fname in ("audio/demo_niwat.mp3", "audio/demo_wasabi.mp3"):
            out_mp3 = R / fname
            if force_audio or not out_mp3.exists():
                print(f"[5/5] Synthesizing {fname} from audio/narration.txt...", flush=True)
                subprocess.run(
                    [sys.executable, str(R / "scripts/map_video.py"), "tts", "--engine", "edge", "--text-file", str(narr_txt), "--out", str(out_mp3)],
                    cwd=R,
                    check=True,
                )
                generated += 1

    if generated == 0:
        print("[5/5] All episode voiceovers & timing JSONs already present.", flush=True)


def verify_readiness() -> int:
    import imageio_ffmpeg

    checks = {
        ".venv python": venv_python().exists(),
        "imageio-ffmpeg": Path(imageio_ffmpeg.get_ffmpeg_exe()).exists(),
        "data/processed/countries.geojson": (R / "data/processed/countries.geojson").exists(),
        "data/processed/thailand_provinces.geojson": (R / "data/processed/thailand_provinces.geojson").exists(),
        "data/processed/world_countries.geojson": (R / "data/processed/world_countries.geojson").exists(),
        "work/cached_terrain.png": (R / "work/cached_terrain.png").exists(),
        "work/cached_world_terrain_blue_ocean.png": (R / "work/cached_world_terrain_blue_ocean.png").exists(),
        "work/cached_world_terrain_16k_landbleed.png": (R / "work/cached_world_terrain_16k_landbleed.png").exists(),
    }
    for _, _, mp3_rel, timing_rel in EPISODE_AUDIO_SPECS:
        checks[mp3_rel] = (R / mp3_rel).exists()
        checks[timing_rel] = (R / timing_rel).exists()

    print("\n=== Environment Readiness Summary ===")
    missing = []
    for k, ok in checks.items():
        status = "OK" if ok else "MISSING"
        print(f"  [{status:7s}] {k}")
        if not ok:
            missing.append(k)
    print("\nReady scripts after bootstrap: scripts/map_video.py, build_ep01.py, build_ep01_90s.py, build_ep02.py, build_ep06.py, build_ep07.py, render_4k60.py")
    print("Planned specs (dialogue.json uses 'segments', supported natively by tts_cli.py; build_ep03..05.py not yet authored): episodes/EP03..EP05")
    return 1 if missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Python venv, GeoJSON, terrain caches, and TTS audio.")
    parser.add_argument("--no-lock", action="store_true", help="Install from requirements.txt instead of requirements-lock.txt")
    parser.add_argument("--force", action="store_true", help="Rebuild GeoJSON and terrain cache PNGs even if present")
    parser.add_argument("--force-audio", action="store_true", help="Regenerate TTS MP3s and timing JSONs even if present")
    parser.add_argument("--skip-audio", action="store_true", help="Skip downloading/synthesizing TTS audio (for offline setup)")
    parser.add_argument("--check-only", action="store_true", help="Verify existing environment without modifying files")
    args = parser.parse_args()

    ensure_dirs()
    if args.check_only:
        if not venv_python().exists():
            print("[MISSING] .venv/bin/python — run: python3 scripts/bootstrap_env.py")
            return 1
        if Path(sys.executable).resolve() != venv_python().resolve():
            os.execv(str(venv_python()), [str(venv_python()), str(Path(__file__).resolve()), *sys.argv[1:]])
        return verify_readiness()

    ensure_venv_and_reexec(no_lock=args.no_lock)
    ensure_fetch(force=args.force)
    build_world_countries_geojson(force=args.force)
    build_terrain_caches(force=args.force)
    ensure_audio_assets(skip_audio=args.skip_audio, force_audio=args.force_audio)
    return verify_readiness()


if __name__ == "__main__":
    raise SystemExit(main())
