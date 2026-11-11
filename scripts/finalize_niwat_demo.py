from pathlib import Path
import json,subprocess,sys
import imageio_ffmpeg
R=Path(__file__).resolve().parents[1];ff=imageio_ffmpeg.get_ffmpeg_exe()
timing=json.loads((R/'audio/demo_niwat_timing.json').read_text())
scene=json.loads((R/'scenes/province_demo.json').read_text())
scene['duration']=max(8,timing['durationSec']+.5)
scene['subtitles']=[{'start':x['startSec'],'end':x['endSec'],'text':x['text']} for x in timing['turns']]
scene['subtitle']=''
scene['lift_start']=max(.5,timing['turns'][0]['endSec']-.7)
scene['zoom_duration']=scene['lift_start']+.2
(R/'scenes/niwat_demo.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2))
subprocess.run([sys.executable,str(R/'scripts/map_video.py'),'render','--scene',str(R/'scenes/niwat_demo.json'),'--width','1080','--height','1920','--out',str(R/'exports/map_demo_niwat_silent.mp4')],check=True)
cmd=[ff,'-y','-i',str(R/'exports/map_demo_niwat_silent.mp4'),'-i',str(R/'audio/demo_niwat_timed.mp3'),'-stream_loop','-1','-i',str(R/'assets/music/demo_original.wav'),'-i',str(R/'assets/sfx/whoosh.wav'),'-filter_complex',f"[1:a]apad,asplit=2[v][sc];[2:a]volume=0.5[m];[m][sc]sidechaincompress=threshold=0.015:ratio=8:attack=15:release=250[duck];[3:a]volume=0.25,adelay={round(scene['lift_start']*1000)}|{round(scene['lift_start']*1000)}[s];[v][duck][s]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]",'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(R/'exports/DEMO_เชียงใหม่_เสียงจากSkillเดิม.mp4')]
subprocess.run(cmd,check=True,stderr=(R/'exports/niwat-mix.log').open('w'))
subprocess.run([ff,'-v','error','-i',str(R/'exports/DEMO_เชียงใหม่_เสียงจากSkillเดิม.mp4'),'-f','null','-'],check=True)
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(R/'audio/demo_niwat.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(scene['subtitles']))+'\n')
print('Original thai-neural-tts skill used successfully; timed Niwat export decode-checked')
