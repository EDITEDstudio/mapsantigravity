from pathlib import Path
import json, subprocess, sys
R=Path(__file__).resolve().parent
for d in ['scripts','data/raw','data/processed','assets/fonts','assets/music','assets/sfx','audio','scenes','exports','docs','tests']:
    (R/d).mkdir(parents=True,exist_ok=True)
(R/'.gitignore').write_text('.venv/\n.env\n__pycache__/\ndata/raw/\ndata/processed/\nexports/\naudio/\n*.log\n.DS_Store\n')
(R/'requirements.txt').write_text('pillow\nnumpy\nrequests\npyshp\nimageio-ffmpeg\nelevenlabs\npyyaml\n')
(R/'config.json').write_text(json.dumps({'voice_id':'aIO43jUTZkFqZmvgYDvA','voice_name':'WASABI Thai Storyteller','model_id':'eleven_v3','width':1080,'height':1920,'fps':30},ensure_ascii=False,indent=2))
(R/'.env.example').write_text('ELEVENLABS_API_KEY=\n# Set locally; never paste a secret into chat or commit it.\n')
(R/'scenes/demo.json').write_text(json.dumps({'duration':6,'title':'THAILAND','subtitle':'แผนที่จริง • ทดสอบระบบโมชั่น','camera_start':[93,0,112,26],'camera_end':[96,4,109,22],'highlight':'THA','route':[[100.5018,13.7563],[100.5692,14.3532]],'labels':[{'lon':100.5018,'lat':13.7563,'text':'กรุงเทพฯ'},{'lon':102.5,'lat':18,'text':'ลาว'}]},ensure_ascii=False,indent=2))
(R/'AGENTS.md').write_text("""# คลิปแผนที่ — WASABI
Use the project-local skills under .agents/skills. Read the relevant SKILL.md before work.
Use .venv/bin/python and scripts/map_video.py. Do not modify global Python.
Follow map-data -> map-motion -> thai-voice -> video-finish.
Use actual geographic data, never image-generation for borders or factual labels.
Distinguish simulations from factual events. Fact-check numbers and current boundaries.
Default 1080x1920, 30fps. Preview at 360x640 first; render full resolution after review.
Use the configured WASABI voice. Never choose a substitute silently.
Keep secrets in environment variables only; never print them or copy from unrelated projects.
Do not claim a paid API works until an authorized generation succeeds.
Save sources, licenses, retrieval date and hashes in data/sources.json.
Keep footage, narration, music, SFX and subtitle files separate for CapCut import.
Before delivery decode-check the export and inspect representative frames.
This is a local Codex project installation, not a ChatGPT-wide personal skill installation.
""")
(R/'docs/เริ่มต้น.md').write_text("""# คลิปแผนที่
เปิดโฟลเดอร์นี้ใน Codex แล้วสั่ง: ใช้ชุดทำคลิปแผนที่ สร้างสตอรี่บอร์ดเรื่อง ... 60 วินาที
Skills อยู่ใน .agents/skills และมี AGENTS.md ชี้ขั้นตอนทำงาน
1. เตรียมข้อมูล: .venv/bin/python scripts/map_video.py fetch
2. ทดลองโมชั่น: .venv/bin/python scripts/map_video.py render --scene scenes/demo.json --width 360 --height 640 --out exports/demo.mp4
3. เสียง: .venv/bin/python scripts/map_video.py tts --text-file audio/narration.txt --out audio/narration.mp3
   ต้องตั้ง ELEVENLABS_API_KEY ใน Terminal ก่อน ไม่ต้องส่งคีย์ในแชท
   หรือสร้างเสียงผ่าน ElevenLabs ที่เชื่อมใน ChatGPT แล้วนำ MP3 มาไว้ใน audio
4. ผสมเสียง: .venv/bin/python scripts/map_video.py mix --video exports/demo.mp4 --voice audio/narration.mp3 --out exports/final.mp4
   เพิ่ม --music assets/music/track.wav ได้
5. เปิด CapCut ที่ติดตั้งแล้ว นำ MP4, เสียง, SRT เข้าโปรเจกต์และจัดจังหวะ
FFmpeg เป็น binary ภายใน imageio-ffmpeg ไม่ได้ติดตั้งเป็นคำสั่งส่วนกลาง
Natural Earth เป็นแผนที่ภูมิประเทศจริงเชิงแผนที่ ไม่ใช่ภาพดาวเทียมสด
หากต้องการบินกล้องโลก 3D/ภาพดาวเทียมละเอียด ใช้ Google Earth Studio เป็นแหล่งช็อตเพิ่มเติม
อย่าใช้ภาพ Google โดยตัดเครดิตออก ตรวจสิทธิ์และเงื่อนไขก่อนใช้
ข้อมูลจังหวัด Natural Earth เป็นข้อมูลทำแผนที่ทั่วไป ต้องตรวจชื่อ/จำนวน/ความทันสมัยก่อนเผยแพร่
เสียงพากย์ ElevenLabs ถูกตั้งชื่อและ voice ID แล้ว แต่ยังไม่ทดสอบสร้างแบบเสียเครดิต
""")
print('Project structure ready')
