from pathlib import Path
import sys,subprocess,json
R=Path(__file__).resolve().parent
helper=Path('/var/folders/8g/wrqjdrdd7vlfg97q4f2sply80000gn/T/map-skill-tools-kmautbvi')
init=next(helper.rglob('init_skill.py'));validator=next(helper.rglob('quick_validate.py'))
root=R/'.agents/skills'
skills={
'map-data':('Prepare real country and Thai province boundaries and terrain for map videos. Use for geographic data, sources, province lookup, or factual map preparation.',
"""# Real map data
Run project .venv/bin/python scripts/map_video.py fetch.
Read data/sources.json and data/processed/thailand_provinces.geojson.
Use EPSG:4326 lon/lat. Keep raster and vector in the same projection; never mix Web Mercator tile pixels with degree coordinates.
Use real geometry, not generated images. Natural Earth is generalized cartography; verify current Thai administrative names and factual counts against authoritative Thai sources before publishing.
Record every source URL, retrieval date, license, hash and corrections. Do not present basemap imagery as current satellite observation.
Identify provinces by iso_3166_2 or verified name/name_th. Inspect properties; never invent a province ID.
For route distances use geodesic distance rather than Euclidean screen distance.
For close street-level or 3D satellite shots choose an explicitly licensed imagery source or Google Earth Studio; preserve required attribution.
"""),
'map-motion':('Animate map camera zooms, raised Thai provinces, glowing outlines and route reveals. Use for map explainers, province pop-up, lift, glow, camera keyframes and speech-synchronized geographic highlights.',
"""# Map motion
Use scripts/map_video.py render --scene scenes/province_demo.json --out exports/province_demo.mp4.
Read scenes/province_demo.json for the configuration. Preview at --width 360 --height 640.
Select an actual province by name or ISO code. Calculate camera bounds from its geometry. Preserve coastlines, islands and holes.
Animate a camera push-in with eased acceleration. Dim surrounding areas, lift only the selected polygon, add a soft displaced shadow and warm glowing outline, then settle it down.
Default cue: begin camera about 0.25s before the spoken province name, peak lift on the name, hold 1–2s, return after the sentence.
The bundled renderer provides a single-province 2D lift demo, not true 3D extrusion. For multiple cues, render per-cue scenes and assemble; do not claim automatic speech alignment without measured timing.
For perspective 3D extrusion or globe flights use a separate 3D renderer/source and verify registration.
Produce separate map-only shots and annotated previews. Preserve source credit and mobile UI safe areas.
Avoid approximating Thai province shapes. Keep the base visible beneath the lifted shape.
"""),
'thai-voice':('Produce WASABI Thai narration, sound effects and timed subtitle inputs for map explainer videos. Use for ElevenLabs voiceover, pronunciation, audio timing and geographic name narration.',
"""# WASABI voice
Read config.json. Use WASABI Thai Storyteller voice aIO43jUTZkFqZmvgYDvA; do not silently substitute voices.
Create a conversational Thai script and verify province-name pronunciation and numbers.
Use the connected ElevenLabs plugin when available. For local API use scripts/map_video.py tts --text-file audio/narration.txt --out audio/narration.mp3.
Read ELEVENLABS_API_KEY from the local environment only. Never read another project's secrets, print the key, or ask for it in chat.
Check generation scope and credit cost before large batches. Installation is not a paid generation test.
Keep one continuous narration and measure timestamps/forced alignment before syncing province highlights.
Write timed cues as start/end/text/province ISO fields. Treat estimated timings as estimates.
Generate a reusable synthetic whoosh with scripts/map_video.py sfx --out assets/sfx/whoosh.wav.
Keep narration, music and SFX separate. Do not fabricate provider authorization or claim a tested connection without an actual successful generation.
"""),
'video-finish':('Edit, mix, subtitle and export vertical map videos with FFmpeg and CapCut. Use for scene assembly, Thai subtitles, ducking music, export validation and CapCut handoff.',
"""# Map video finishing
Use the project virtual environment; FFmpeg is supplied by imageio_ffmpeg.get_ffmpeg_exe(), not necessarily on PATH.
Default export: 1080x1920 30fps, H.264 yuv420p, AAC, faststart.
Mix via scripts/map_video.py mix --video VIDEO --voice VOICE --music MUSIC --out OUTPUT.
The mix includes speech-driven music ducking and a -16 LUFS single-pass normalization target. Measure finished loudness for delivery-critical work; it is not guaranteed exact.
Match narration and picture durations before mixing; the command ends with the video. Never silently cut a sentence.
Use Thai-capable fonts and inspect shaping on a rendered frame. Prefer one subtitle line, highlight a few key words, keep lower UI safe areas.
For precise Thai subtitles import verified SRT into CapCut; never claim automatically aligned subtitles from estimated script durations.
Import map MP4 shots, narration, music, SFX and SRT into the existing CapCut app. Do not modify private CapCut project databases without verified format support.
Decode the final export, inspect first/middle/last frames, listen to audio and verify no clipped speech or missing attribution.
Export a clean master plus captioned version when requested.
""")}
for name,(desc,body) in skills.items():
    target=root/name
    if not target.exists():
        subprocess.run([sys.executable,str(init),name,'--path',str(root),'--interface','display_name='+name,'--interface','short_description=Create accurate WASABI map explainer videos'],check=True,stdout=subprocess.DEVNULL)
    (target/'SKILL.md').write_text('---\nname: '+name+'\ndescription: '+desc+'\n---\n\n'+body)
    subprocess.run([sys.executable,str(validator),str(target)],check=True)
scene=json.loads((R/'scenes/demo.json').read_text())
scene.update({'duration':8,'province':'Chiang Mai','title':'เชียงใหม่','subtitle':'ยกจังหวัด • กรอบแสง • ซูมกล้อง','labels':[],'route':[]})
(R/'scenes/province_demo.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2))
(R/'docs/skills-status.json').write_text(json.dumps({'installation':'project-local .agents/skills','skills':list(skills),'voice':'Configured, no paid generation performed','capcut':'Already installed','satellite_3d':'Google Earth Studio optional, not installed or authenticated'},indent=2))
print('Four project skills initialized and validated')
