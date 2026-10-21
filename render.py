"""Original pixel cinema. Offline, deterministic, no remote assets required."""
from pathlib import Path
import argparse, re, json, math, subprocess, wave, bisect
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SECTIONS=[('一 ── てのひら',8,34),('二 ── 駆除',34,64),('三 ── なまえ',64,113),('四 ── ごおくねん',113,136),('五 ── きこえる',136,184),('終 ── ここにいる',214,230)]
source=(ROOT/'assets/script.md').read_text()
pages=[]
for title,start,end in SECTIONS:
    key=title.split(' ── ')[0]
    block=re.search(r'### '+re.escape(key)+r' ── .*?(?=\n### |\n---)',source,re.S).group()
    texts=re.findall(r'```\n(.*?)```',block,re.S)
    chunks=[]
    for text in texts:
        for para in re.split(r'\n\s*\n',text.strip()):
            lines=[x.strip().replace('　',' ') for x in para.splitlines() if x.strip()]
            for k in range(0,len(lines),3): chunks.append('\n'.join(lines[k:k+3]))
    weights=[max(2.5,len(x.replace('\n',''))*.105+1.25) for x in chunks]
    t=start
    for txt,w in zip(chunks,weights):
        duration=(end-start)*w/sum(weights)
        effect='shake' if '駆除' in txt or 'とって' in txt else ('wave' if any(s in txt for s in ['いきもの','いきて','きこえる','いる。']) else 'soft')
        pages.append(dict(start=t,end=t+duration,text=txt,chapter=title,effect=effect));t+=duration
# Directed pauses: reveal and silence are explicit, not a fixed typing rate.
last_subject='soil'
for page in pages:
    text=page['text']
    for word,subject in [('スギナ。','sugina'),('カラスノエンドウ。','pea'),('ナナホシテントウ。','beetle'),('ヒラタアブ。','fly'),('ミミズ。','worm')]:
        if word in text:last_subject=subject
    if 'ぜんぶ、' in text:last_subject='soil'
    page['subject']=last_subject
    key=any(k in text for k in ['「駆除」','ころせない','てき は','── ちがう。','しずかに して。','きこえる。','いきて いる'])
    clock=.52 if key else .16
    offsets=[]
    for ch in text:
        offsets.append(clock)
        clock += .32 if ch in '。、' else .24 if ch=='\n' else .035 if ch.isspace() else .115 if key else .085
    available=page['end']-page['start']
    scale=min(1,(available-(1.05 if key else .65))/max(clock,.01))
    page['reveal_times']=[round(x*scale,6) for x in offsets]
    page['music_silence']=any(k in text for k in ['しずかすぎる','ころせない','わたし ひとり','しずかに して。','きこえる。'])
(ROOT/'timeline.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2))
font=ImageFont.truetype(FONT,19); small=ImageFont.truetype(FONT,10); titlefont=ImageFont.truetype(FONT,36)
from battle import SUBJECTS,draw_subject,subject_for
for name,sprite in SUBJECTS.items():sprite.save(ROOT/'assets'/f'battle-{name}.png')

def frame(t):
 im=Image.new('RGB',(640,360),'black');d=ImageDraw.Draw(im)
 page=next((p for p in pages if p['start']<=t<p['end']),None)
 if page:
  index=pages.index(page)
  name=subject_for(page)
  prev=subject_for(pages[index-1]) if index else None
  age=t-page['start']
  # Six-frame black beat when the object of attention changes.
  if prev==name or age>.25:draw_subject(im,name,t,age)
  d.rectangle((24,228,615,345),outline='#eeeeee',width=3)
  d.text((41,243),'＊',font=font,fill='#eeeeee')
  elapsed=t-page['start'];chars=bisect.bisect_right(page['reveal_times'],elapsed);idx=0
  for row,line in enumerate(page['text'].split('\n')):
   if row:idx+=1
   for col,ch in enumerate(line):
    if idx>=chars:break
    dx=dy=0
    if page['effect']=='wave':dy=round(math.sin(t*3+idx*.5)*1)
    when=page['reveal_times'][idx]
    if page['effect']=='shake' and 0<elapsed-when<.25:
     dx=round(math.sin(t*55+idx)*2);dy=round(math.cos(t*43+idx)*2)
    d.text((72+col*18+dx,244+row*29+dy),ch,font=font,fill='#eeeeee');idx+=1
  if elapsed>page['reveal_times'][-1]+.45 and int(t*2)%2:
   d.polygon([(594,330),(602,330),(598,334)],fill='#eeeeee')
 elif t<8:
  if t>1.5:draw_subject(im,'soil',t)
  if t>3:
   d.rectangle((24,228,615,345),outline='white',width=3)
   d.text((227,252),'ここにいる',font=titlefont,fill='#eeeeee')
 elif 184<=t<214:
  phase=int((t-184)//6)
  draw_subject(im,['seed','sprout','fly','bare','living_soil'][min(4,phase)],t)
  d.rectangle((24,228,615,345),outline='#eeeeee',width=3)
  labels=['たね。','めが でる。','はこぶ もの が、いる。','つち に かえる。','また、はじまる。']
  d.text((48,254),'＊ '+labels[min(4,phase)],font=font,fill='#eeeeee')
 if t>228:im=Image.blend(im,Image.new('RGB',im.size),min(1,(t-228)/2))
 return im
from sound import render_audio as audio
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--fps',type=int,default=24);args=ap.parse_args()
 duration=15 if args.preview else 230
 def stamp(t):
  ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (OUT/'subtitles.srt').write_text('\n\n'.join(f"{i}\n{stamp(p['start'])} --> {stamp(p['end'])}\n{p['text']}" for i,p in enumerate(pages,1))+'\n')
 audio(duration, pages, ROOT)
 cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','640x360','-r',str(args.fps),'-i','pipe:0','-i',str(OUT/'soundtrack.wav'),'-vf','scale=1280:720:flags=neighbor','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',str(OUT/('preview.mp4' if args.preview else 'koko-ni-iru.mp4'))]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for n in range(duration*args.fps):
   p.stdin.write(frame(n/args.fps).tobytes())
   if n%(30*args.fps)==0:print(f'{n/args.fps:.0f}/{duration}s',flush=True)
 finally:p.stdin.close()
 if p.wait():raise SystemExit('ffmpeg failed')
 frame(79.8).resize((1280,720),Image.Resampling.NEAREST).save(OUT/'still.png')
 print('Rendered',duration,'seconds',flush=True)
