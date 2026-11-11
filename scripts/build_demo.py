from pathlib import Path
import subprocess,sys,json,wave
import numpy as np
import imageio_ffmpeg
R=Path(__file__).resolve().parents[1];py=sys.executable;tool=R/'scripts/map_video.py'
s=json.loads((R/'scenes/province_demo.json').read_text())
s['subtitles']=[{'start':0,'end':2.2,'text':'ลองซูมเข้าไปที่เชียงใหม่'},{'start':2.2,'end':4,'text':'แล้วดูว่าภูมิประเทศ'},{'start':4,'end':8,'text':'เชื่อมโยงกับเศรษฐกิจอย่างไร'}]
(R/'scenes/province_demo.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
p=tool;s=p.read_text();s=s.replace("s.get('subtitle',''),font=font", "next((c['text'] for c in s.get('subtitles',[]) if c['start']<=t<c['end']),s.get('subtitle','')),font=font")
p.write_text(s)
subprocess.run([py,str(tool),'sfx','--out',str(R/'assets/sfx/whoosh.wav')],check=True)
sr=48000;t=np.arange(sr*8)/sr
envelope=np.minimum(1,t/.4)*np.minimum(1,(8-t)/.7)
music=sum(np.sin(2*np.pi*f*t)*.018 for f in [130.81,164.81,196,261.63])*envelope
with wave.open(str(R/'assets/music/demo_original.wav'),'w') as f:
 f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((music*32767).astype('<i2').tobytes())
subprocess.run([py,str(tool),'render','--scene',str(R/'scenes/province_demo.json'),'--width','1080','--height','1920','--out',str(R/'exports/map_demo_1080p_silent.mp4')],check=True)
ff=imageio_ffmpeg.get_ffmpeg_exe()
cmd=[ff,'-y','-i',str(R/'exports/map_demo_1080p_silent.mp4'),'-i',str(R/'audio/demo_wasabi.mp3'),'-i',str(R/'assets/music/demo_original.wav'),'-i',str(R/'assets/sfx/whoosh.wav'),'-filter_complex','[1:a]apad,asplit=2[v][sc];[2:a]volume=0.5[m];[m][sc]sidechaincompress=threshold=0.015:ratio=8:attack=15:release=250[duck];[3:a]volume=0.25,adelay=1100|1100[s];[v][duck][s]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(R/'exports/map_demo_1080p_with_voice.mp4')]
subprocess.run(cmd,check=True,stderr=(R/'exports/audio-mix.log').open('w'))
subprocess.run([ff,'-v','error','-i',str(R/'exports/map_demo_1080p_with_voice.mp4'),'-f','null','-'],check=True)
for name,sec in [('start',.2),('lift',3),('end',7.6)]:
 subprocess.run([ff,'-y','-ss',str(sec),'-i',str(R/'exports/map_demo_1080p_with_voice.mp4'),'-frames:v','1','-vf','scale=360:640',str(R/f'exports/check_{name}.jpg')],check=True,stderr=subprocess.DEVNULL)
(R/'audio/demo_estimated.srt').write_text('1\n00:00:00,000 --> 00:00:02,200\nลองซูมเข้าไปที่เชียงใหม่\n\n2\n00:00:02,200 --> 00:00:04,000\nแล้วดูว่าภูมิประเทศ\n\n3\n00:00:04,000 --> 00:00:08,000\nเชื่อมโยงกับเศรษฐกิจอย่างไร\n')
print('Full HD video + WASABI voice + music + whoosh exported and decode-checked')
