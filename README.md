# คลิปแผนที่ — WASABI (`mapsantigravity`)

โปรเจกต์ผลิตวิดีโอแนวตั้งแผนที่เศรษฐกิจไทยและโลก (9:16 Vertical, 4K60 / 1080p) พร้อมเสียงบรรยายไทย Neural TTS และคำบรรยาย

## ตั้งค่าเครื่องใหม่หลัง `git clone` (ทำรอบเดียว)

ไฟล์ขนาดใหญ่และไฟล์ที่สร้างอัตโนมัติ (`.venv/`, `data/raw/`, `data/processed/`, `work/`, `audio/*.mp3`, `exports/`) ถูกแยกออกผ่าน `.gitignore` ให้รันคำสั่งเดียวเพื่อติดตั้งและสร้างข้อมูลทั้งหมดให้พร้อมผลิตคลิป:

```bash
python3 scripts/bootstrap_env.py
```

สคริปต์ [`scripts/bootstrap_env.py`](scripts/bootstrap_env.py) จะดำเนินการให้อัตโนมัติ:
1. สร้าง `.venv/` และติดตั้งแพ็กเกจจาก `requirements-lock.txt` (รวม `imageio-ffmpeg` ที่ให้ binary `ffmpeg` โดยไม่ต้องลง `ffmpeg` บน `PATH` ส่วนกลาง)
2. ดาวน์โหลดแผนที่ Natural Earth 10m ผ่าน `scripts/map_video.py fetch` และสร้าง `data/processed/countries.geojson`, `data/processed/thailand_provinces.geojson`
3. สร้าง `data/processed/world_countries.geojson` (258 ประเทศ) สำหรับสคริปต์ระดับโลก
4. สร้างภาพแคชภูมิประเทศใน `work/` (`cached_terrain.png`, `cached_world_terrain.png`, `cached_world_terrain_blue_ocean.png`, `cached_world_terrain_16k_landbleed.png`)
5. สังเคราะห์เสียงพากย์ `th-TH-NiwatNeural` (`*_voice.mp3`) และไฟล์จังหวะ (`*_timing.json`) ใน `audio/` จากไฟล์ `*_dialogue.json` ที่มีอยู่ในรีโป (ข้ามขั้นนี้ได้ด้วย `--skip-audio` หรือตรวจความพร้อมด้วย `--check-only`)

## สถานะสคริปต์ตอน

| ตอน | สถานะ | หมายเหตุ |
|---|---|---|
| **Demo** | พร้อมรัน | `scripts/map_video.py` |
| **EP01 / EP01 90s / 4K60** | พร้อมรันหลัง bootstrap | `scripts/build_ep01.py`, `scripts/build_ep01_90s.py`, `scripts/render_4k60.py` |
| **EP02** | พร้อมรันหลัง bootstrap | `scripts/build_ep02.py` |
| **EP03–EP05** | แผนตอนพร้อมพัฒนา | มี `README.md`, `dialogue.json`, `scene_plan.json` ใน `episodes/` (`tts_cli.py` รองรับทั้งคีย์ `"segments"` และ `"turns"` แล้ว); ยังไม่มี `scripts/build_ep03.py`–`build_ep05.py` |
| **EP06 / EP07** | พร้อมรันหลัง bootstrap | `scripts/build_ep06.py`, `scripts/build_ep07.py` |

## ทดสอบความพร้อม

```bash
.venv/bin/python scripts/bootstrap_env.py --check-only
```
