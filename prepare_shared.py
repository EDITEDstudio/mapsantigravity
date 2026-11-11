from pathlib import Path
import subprocess,sys,json
R=Path(__file__).resolve().parent
# Share one instruction set and one skill tree across compatible clients.
g=R/'GEMINI.md'
if not g.exists():g.symlink_to('AGENTS.md')
legacy=R/'.agent';legacy.mkdir(exist_ok=True)
if not (legacy/'skills').exists():(legacy/'skills').symlink_to('../.agents/skills')
(R/'คลิปแผนที่.code-workspace').write_text(json.dumps({'folders':[{'path':'.'}],'settings':{'python.defaultInterpreterPath':'${workspaceFolder}/.venv/bin/python'}},ensure_ascii=False,indent=2))
helper=Path('/var/folders/8g/wrqjdrdd7vlfg97q4f2sply80000gn/T/map-skill-tools-kmautbvi')
init=next(helper.rglob('init_skill.py'));valid=next(helper.rglob('quick_validate.py'))
name='map-content-strategy';target=R/'.agents/skills'/name
if not target.exists():subprocess.run([sys.executable,str(init),name,'--path',str(target.parent),'--interface','short_description=Plan Thai economics and geography map content'],check=True,stdout=subprocess.DEVNULL)
(target/'SKILL.md').write_text("""---
name: map-content-strategy
description: Plan Thai-first financial education, economic principles and economic geography videos using maps. Use for channel names, content pillars, research, hooks, episode planning and Thailand-to-world expansion.
---
# Map content strategy
Read docs/ชื่อช่องและแผนคอนเทนต์.md and the latest user choices.
Use four pillars: economic geography, everyday money, economic principles, Thailand-versus-world.
Start with Thailand and expand through trade routes or comparisons relevant to Thai viewers.
Use one precise question per episode and 2–3 causal mechanisms. Distinguish correlation from causation.
Draft a 60–90s story with hook, map context, zoomed evidence, comparison, answer and specific CTA.
Use BOT, NESDC, NSO, Customs and Ministry of Commerce primary data; record year and definition.
For international comparisons use compatible years, units, price bases and population denominators.
Use illustrative household budgets only when clearly labeled; do not present invented data as statistics.
Keep financial education separate from individualized investment recommendations.
Create an original script and visual identity. The reference channel supplies craft inspiration, not footage or a script to copy.
Keep proposed names and logo concepts pending review; do not finalize branding before the user chooses.
""")
subprocess.run([sys.executable,str(valid),str(target)],check=True)
(R/'docs/Antigravityทดสอบ.md').write_text("""# การใช้โฟลเดอร์เดียวกัน
โฟลเดอร์หลัก: /Users/macintosh/Desktop/คลิปแผนที่
เปิด คลิปแผนที่.code-workspace ใน Antigravity IDE หรือเปิดโฟลเดอร์นี้ใน Codex
Skills จริงอยู่ .agents/skills และมี .agent/skills เป็นลิงก์รองรับรุ่นเก่า
GEMINI.md อ้างไฟล์ AGENTS.md เดียวกัน ไม่มีสำเนาคำสั่งแยกที่อาจล้าสมัย
เอกสารผู้ผลิต: https://antigravity.google/docs/skills
ส่ง prompt ทดสอบผ่านคำสั่ง chat ของ Antigravity IDE แล้ว
ผลผ่านต้องมี exports/antigravity_test.mp4 และ docs/antigravity-test-result.md ที่ Antigravity สร้างจริง
เพียงเปิดโฟลเดอร์หรือส่ง prompt สำเร็จยังไม่ถือว่า agent ทดสอบผ่าน
ถ้าติด login/workspace trust/อนุมัติ command ให้ผู้ใช้จัดการในแอป ไม่ปิดระบบอนุมัติ
""")
print('Shared workspace, compatibility links and content skill ready')
