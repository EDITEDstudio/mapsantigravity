"""Local real-data map animation, province lift/glow, voiceover and finishing."""
from pathlib import Path
import argparse,json,math,subprocess,sys,zipfile,hashlib,datetime,os,wave
import requests,numpy as np,shapefile,imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
R=Path(__file__).resolve().parents[1]
Image.MAX_IMAGE_PIXELS=300_000_000
def ff():return imageio_ffmpeg.get_ffmpeg_exe()
def fetch():
    raw=R/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    sources=[
      ('countries','https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip'),
      ('provinces','https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip'),
      ('terrain','https://naciscdn.org/naturalearth/10m/raster/NE1_LR_LC_SR.zip')]
    manifest=[]
    for name,url in sources:
        target=raw/(name+'.zip')
        if not target.exists():
            print('Downloading',name,flush=True)
            with requests.get(url,stream=True,timeout=(20,180)) as res:
                res.raise_for_status()
                tmp=target.with_suffix('.part')
                with tmp.open('wb') as out:
                    for chunk in res.iter_content(1024*1024):out.write(chunk)
                tmp.rename(target)
        folder=raw/name;folder.mkdir(exist_ok=True)
        with zipfile.ZipFile(target) as z:z.extractall(folder)
        manifest.append(dict(name=name,url=url,license='Public Domain',retrieved=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    (R/'data/sources.json').write_text(json.dumps(manifest,indent=2))
    countries=[]
    for sr in shapefile.Reader(str(next((raw/'countries').glob('*.shp'))),encoding='utf-8').iterShapeRecords():
        p=sr.record.as_dict()
        if p.get('ADM0_A3') in ['THA','MMR','LAO','KHM','VNM','MYS','CHN']:
            countries.append({'type':'Feature','properties':p,'geometry':sr.shape.__geo_interface__})
    provinces=[]
    for sr in shapefile.Reader(str(next((raw/'provinces').glob('*.shp'))),encoding='utf-8').iterShapeRecords():
        p=sr.record.as_dict()
        if p.get('adm0_a3')=='THA':
            provinces.append({'type':'Feature','properties':p,'geometry':sr.shape.__geo_interface__})
    for name,features in [('countries',countries),('thailand_provinces',provinces)]:
        (R/('data/processed/'+name+'.geojson')).write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False))
    print('Downloaded real terrain and boundaries; Thai province features:',len(provinces),flush=True)
def rings(g):
    if g['type']=='Polygon':return g['coordinates']
    if g['type']=='MultiPolygon':return [r for p in g['coordinates'] for r in p]
    raise ValueError('Polygon geometry required')
def font(size):
    candidates=list((R/'assets/fonts').glob('*.ttf'))+[Path('/Library/Fonts/Arial Unicode.ttf'),Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')]
    for p in candidates:
        if p.exists():return ImageFont.truetype(str(p),size)
    raise RuntimeError('Thai-capable font missing')
def ease(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def render(a):
    s=json.loads(Path(a.scene).read_text());w,h=a.width,a.height;duration=s.get('duration',6);fps=a.fps
    countries=json.loads((R/'data/processed/countries.geojson').read_text())['features']
    provinces=json.loads((R/'data/processed/thailand_provinces.geojson').read_text())['features']
    selected=None
    if s.get('province'):
        matches=[f for f in provinces if s['province'] in [f['properties'].get(k) for k in ['name','name_en','name_th','iso_3166_2']]]
        if len(matches)!=1:raise ValueError('Province not uniquely found: '+s['province'])
        selected=matches[0];print('Province:',selected['properties'].get('name'),flush=True)
    raster=Image.open(next((R/'data/raw/terrain').glob('*.tif'))).convert('RGB')
    # Crop once to Southeast Asia to keep animation memory and rendering cost bounded.
    geo=[85,-5,120,32]
    crop=(int((geo[0]+180)/360*raster.width),int((90-geo[3])/180*raster.height),int((geo[2]+180)/360*raster.width),int((90-geo[1])/180*raster.height))
    terrain=raster.crop(crop);raster.close()
    terrain=ImageEnhance.Color(terrain).enhance(1.4)
    terrain=ImageEnhance.Brightness(terrain).enhance(.64)
    land=Image.new('L',terrain.size);ld=ImageDraw.Draw(land)
    def landxy(p):return ((p[0]-geo[0])/(geo[2]-geo[0])*terrain.width,(geo[3]-p[1])/(geo[3]-geo[1])*terrain.height)
    for sr in shapefile.Reader(str(next((R/'data/raw/countries').glob('*.shp'))),encoding='utf-8').iterShapeRecords():
        if sr.shape.bbox[2]<geo[0] or sr.shape.bbox[0]>geo[2] or sr.shape.bbox[3]<geo[1] or sr.shape.bbox[1]>geo[3]:continue
        g=sr.shape.__geo_interface__
        polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for poly in polys:
            ld.polygon([landxy(p) for p in poly[0]],fill=255)
            for hole in poly[1:]:ld.polygon([landxy(p) for p in hole],fill=0)
    terrain=Image.composite(terrain,Image.new('RGB',terrain.size,'#155d75'),land)
    start=s['camera_start'];end=s['camera_end']
    def fit(b):
        cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2;sw=max(b[2]-b[0],(b[3]-b[1])*w/h);sh=sw*h/w
        return [cx-sw/2,cy-sh/2,cx+sw/2,cy+sh/2]
    start=fit(start);end=fit(end)
    if selected:
        pts=[p for r in rings(selected['geometry']) for p in r]
        cx=(min(p[0] for p in pts)+max(p[0] for p in pts))/2
        cy=(min(p[1] for p in pts)+max(p[1] for p in pts))/2
        span=max(max(p[0] for p in pts)-min(p[0] for p in pts),1.8)*2.4
        # Plate-carree camera: same lon/lat pixel scale; no mixed projections.
        end=[cx-span/2,cy-span*h/w/2,cx+span/2,cy+span*h/w/2]
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    cmd=[ff(),'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=(R/'exports/render.log').open('w'))
    still=None
    try:
      for i in range(round(duration*fps)):
        t=i/fps;u=ease((t-s.get('zoom_start',.15))/s.get('zoom_duration',1.3))
        box=[start[k]*(1-u)+end[k]*u for k in range(4)]
        def xy(p):return ((p[0]-box[0])/(box[2]-box[0])*w,(box[3]-p[1])/(box[3]-box[1])*h)
        region=((box[0]-geo[0])/(geo[2]-geo[0])*terrain.width,(geo[3]-box[3])/(geo[3]-geo[1])*terrain.height,(box[2]-geo[0])/(geo[2]-geo[0])*terrain.width,(geo[3]-box[1])/(geo[3]-geo[1])*terrain.height)
        im=terrain.transform((w,h),Image.Transform.EXTENT,region,Image.Resampling.BILINEAR).convert('RGBA')
        d=ImageDraw.Draw(im)
        for f in countries:
            for ring in rings(f['geometry']):
                pts2=[xy(p) for p in ring]
                d.line(pts2,fill=(220,235,228,180),width=max(1,w//450))
        if selected:
            for f in provinces:
                for ring in rings(f['geometry']):d.line([xy(p) for p in ring],fill=(240,245,240,100),width=1)
            lift=ease((t-s.get('lift_start',1.1))/.55)*(1-ease((t-duration+1)/.7))
            mask=Image.new('L',(w,h));md=ImageDraw.Draw(mask)
            # Render exterior and holes separately to preserve actual geometry.
            polygons=selected['geometry']['coordinates'] if selected['geometry']['type']=='MultiPolygon' else [selected['geometry']['coordinates']]
            for poly in polygons:
                md.polygon([xy(p) for p in poly[0]],fill=255)
                for hole in poly[1:]:md.polygon([xy(p) for p in hole],fill=0)
            dx,dy=int(8*w/1080*lift),int(-42*h/1920*lift)
            shifted=Image.new('L',(w,h));shifted.paste(mask,(dx,dy))
            shadow=Image.new('L',(w,h));shadow.paste(mask,(dx+int(8*lift),int(10*lift)))
            im=Image.alpha_composite(im,Image.composite(Image.new('RGBA',(w,h),(0,0,0,int(170*lift))),Image.new('RGBA',(w,h)),shadow.filter(ImageFilter.GaussianBlur(max(2,w/120)))))
            lifted=Image.new('RGBA',(w,h));lifted.paste(im,(dx,dy))
            im=Image.composite(lifted,im,shifted)
            tint=Image.new('RGBA',(w,h),(255,191,47,int(80*lift)))
            im=Image.alpha_composite(im,Image.composite(tint,Image.new('RGBA',(w,h)),shifted))
            edge=Image.new('RGBA',(w,h));ed=ImageDraw.Draw(edge)
            for ring in rings(selected['geometry']):
                ed.line([(xy(p)[0]+dx,xy(p)[1]+dy) for p in ring],fill=(255,215,78,int(255*lift)),width=max(2,w//180))
            im=Image.alpha_composite(im,edge.filter(ImageFilter.GaussianBlur(max(2,w/90))))
            im=Image.alpha_composite(im,edge)
        d=ImageDraw.Draw(im)
        route=s.get('route',[])
        if len(route)>1 and not selected:
            fraction=ease(t/duration);p0,p1=xy(route[0]),xy(route[-1])
            q=(p0[0]+(p1[0]-p0[0])*fraction,p0[1]+(p1[1]-p0[1])*fraction)
            d.line([p0,q],fill='#ffdb4c',width=max(2,w//140))
            d.ellipse((q[0]-4,q[1]-4,q[0]+4,q[1]+4),fill='white')
        for label in s.get('labels',[]):
            x,y=xy([label['lon'],label['lat']])
            d.text((x,y),label['text'],font=font(max(12,w//28)),fill='white',stroke_width=1,stroke_fill='#243b30',anchor='mm')
        d.rounded_rectangle((w*.05,h*.07,w*.95,h*.15),radius=8,fill=(4,17,26,200))
        d.text((w/2,h*.11),s.get('title','WASABI'),font=font(max(14,w//15)),fill='#ffdb4c',anchor='mm')
        caption=next((c['text'] for c in s.get('subtitles',[]) if c['start']<=t<c['end']),s.get('subtitle',''))
        size=max(12,w//24)
        while size>10 and d.textlength(caption,font=font(size))>w*.9:size-=1
        d.text((w/2,h*.80),caption,font=font(size),fill='white',stroke_width=max(1,w//540),stroke_fill='black',anchor='mm')
        d.text((w/2,h*.92),'Made with Natural Earth | WASABI',font=font(max(8,w//48)),fill='white',anchor='mm')
        if i==round(duration*fps*.65):still=im.convert('RGB');still.save(output.with_suffix('.jpg'))
        proc.stdin.write(im.convert('RGB').tobytes())
    finally:
        proc.stdin.close();code=proc.wait()
    if code:raise RuntimeError('FFmpeg failed; inspect exports/render.log')
    subprocess.run([ff(),'-v','error','-i',str(output),'-f','null','-'],check=True)
    print('Rendered and decode-checked:',output,flush=True)
def tts(a):
    if a.engine == "edge":
        subprocess.run([sys.executable,str(R/".agents/skills/thai-neural-tts/scripts/tts_cli.py"),"file",a.text_file,"-o",a.out,"-v","niwat","--rate","+3%"],check=True)
        return
    from elevenlabs import ElevenLabs
    if not os.environ.get('ELEVENLABS_API_KEY'):raise RuntimeError('Set ELEVENLABS_API_KEY locally or use the connected ElevenLabs plugin; do not paste secrets into chat.')
    c=json.loads((R/'config.json').read_text())
    audio=ElevenLabs().text_to_speech.convert(voice_id=c['voice_id'],text=Path(a.text_file).read_text(),model_id=c['model_id'],output_format='mp3_44100_128')
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    with open(a.out,'wb') as f:
        for chunk in audio:f.write(chunk)
    print('Speech saved:',a.out)
def sfx(a):
    sr=48000;t=np.arange(sr)/sr
    rng=np.random.default_rng(7);x=rng.normal(0,.15,len(t))*np.sin(np.pi*t)**3
    x+=.12*np.sin(2*np.pi*(500*t+700*t*t))*np.exp(-8*t)
    with wave.open(a.out,'w') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(x,-1,1)*32767).astype('<i2').tobytes())
def mix(a):
    cmd=[ff(),'-y','-i',a.video,'-i',a.voice]
    if a.music:
        cmd+=['-stream_loop','-1','-i',a.music]
        filt='[1:a]apad,asplit=2[v][sc];[2:a]volume=0.12[m];[m][sc]sidechaincompress=threshold=0.025:ratio=8:attack=20:release=300[duck];[v][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]'
    else:filt='[1:a]apad,loudnorm=I=-16:TP=-1.5:LRA=11[a]'
    cmd+=['-filter_complex',filt,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',a.out]
    subprocess.run(cmd,check=True)
def main():
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
    sp.add_parser('fetch')
    r=sp.add_parser('render');r.add_argument('--scene',required=True);r.add_argument('--out',required=True);r.add_argument('--width',type=int,default=1080);r.add_argument('--height',type=int,default=1920);r.add_argument('--fps',type=int,default=30)
    v=sp.add_parser('tts');v.add_argument('--engine',choices=['edge','elevenlabs'],default='edge');v.add_argument('--text-file',required=True);v.add_argument('--out',required=True)
    m=sp.add_parser('mix');m.add_argument('--video',required=True);m.add_argument('--voice',required=True);m.add_argument('--music');m.add_argument('--out',required=True)
    x=sp.add_parser('sfx');x.add_argument('--out',required=True)
    a=p.parse_args()
    if a.cmd=='fetch':fetch()
    elif a.cmd=='render':render(a)
    elif a.cmd=='tts':tts(a)
    elif a.cmd=='mix':mix(a)
    else:sfx(a)
if __name__=='__main__':main()
