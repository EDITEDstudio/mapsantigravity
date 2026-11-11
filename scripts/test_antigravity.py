from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1]
prompt="""Use the shared workspace /Users/macintosh/Desktop/คลิปแผนที่. Read AGENTS.md and activate the map-motion skill in .agents/skills/map-motion/SKILL.md. Run the existing command with no source modifications: .venv/bin/python scripts/map_video.py render --scene scenes/province_demo.json --width 360 --height 640 --out exports/antigravity_test.mp4. Do not install software, change permissions, access credentials or use paid services. Write docs/antigravity-test-result.md with the skill you used, actual command, result and file path. If you cannot execute because approval or authentication is required, say exactly that and do not claim success."""
try:
 p=subprocess.run([str(R/'tools/agy'),'-p',prompt,'--print-timeout','90s','--output-format','json'],cwd=R,capture_output=True,text=True,timeout=120)
 text=p.stdout+'\n'+p.stderr
 if any(x in text.lower() for x in ['sign in','log in','oauth','authentication required','not authenticated','authorize this','login required']):
  summary={'exit_code':p.returncode,'status':'Authentication or sign-in required; no login attempted','execution_verified':False}
 else:
  summary={'exit_code':p.returncode,'response':text[-12000:],'execution_verified':(R/'exports/antigravity_test.mp4').exists() and (R/'docs/antigravity-test-result.md').exists()}
except subprocess.TimeoutExpired:
 summary={'status':'CLI did not finish within 120 seconds; execution not verified','execution_verified':False}
(R/'docs/antigravity-cli-test.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
