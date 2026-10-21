"""Original pixel cinema. Offline, deterministic, no remote assets required."""
from pathlib import Path
import argparse, re, json, math, subprocess, wave
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
(ROOT/'timeline.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2))
font=ImageFont.truetype(FONT,19); small=ImageFont.truetype(FONT,10); titlefont=ImageFont.truetype(FONT,36)
# Hand-authored sprite patterns, exported separately for reuse.
SPRITES={
'person':['...hhh...','..hhhhh..','...ss....','..sssss..','...ss....','..bbbbb..','.bbbbbbb.','.sbbbbb s'.replace(' ',''),'..bbbbb..','..ppppp..','..pp.pp..','..pp.pp..','.kkk.kkk.'],
'plant':['...g...','..gg.g.','g.gg.g.','.gggg..','...g...','..gggg.','.g.g...','...g...'],
'beetle':['..k.k..','...k...','..rrrr.','.rkrkrr','krrrrrk','.rkrkr.','..kkkk.'],
'worm':['.......','pp.....','.pp..pp','..pppp.','.......'],
'fly':['ww...ww','.wwwww.','..kyk..','.kykyk.','..kyk..','...k...']}
colors={'h':'#453c36','s':'#dec9a4','b':'#b7bcb1','p':'#ad817b','k':'#292e35','g':'#83a676','r':'#c77164','w':'#cdd8c6','y':'#cfb778'}
def sprite(im,name,x,y,scale=2):
 d=ImageDraw.Draw(im)
 for yy,row in enumerate(SPRITES[name]):
  for xx,c in enumerate(row):
   if c in colors:d.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=colors[c])
for name in SPRITES:
 im=Image.new('RGBA',(40,40));sprite(im,name,2,2,2);im.save(ROOT/'assets'/f'{name}.png')
def frame(t):
 im=Image.new('RGB',(640,360),'#080c12');d=ImageDraw.Draw(im)
 # restrained stars and distant mountain silhouettes
 for i in range(48):
  x=(i*127+23)%640;y=(i*43+9)%140
  c=int(75+35*math.sin(t*.5+i));d.point((x,y), fill=(c,c,c+12))
 d.polygon([(0,171),(80,128),(137,162),(219,116),(306,173),(390,132),(490,165),(570,121),(640,152),(640,210),(0,210)],fill='#121a21')
 living=t<42 or t>=64; green=t>=157
 ground='#343b2b' if green else '#302922'
 if 45<t<64:ground='#8c918c'
 d.rectangle((0,196,639,237),fill=ground)
 for i in range(95):
  x=(i*83+8)%640;y=200+(i*17)%35;d.rectangle((x,y,x+2,y+1),fill='#544637' if living else '#afb2a9')
 if living:
  for i in range(20):
   x=(i*67+13)%640
   sprite(im,'plant',x,182+(i%3)*3,2 if green else 1)
   if green:d.line((x+6,205,x+2+(i%4)*3,224),fill='#7c7251',width=1)
 # spotlight / protagonist
 d.ellipse((284,190,350,201),fill='#857b5a' if t<34 or t>=214 else '#535644')
 sprite(im,'person',307,164+int(math.sin(t*2)*.7),2)
 if 64<=t<113:
  n=min(4,int((t-64)/7))
  sprite(im,['plant','plant','beetle','fly','worm'][n],393,151+int(math.sin(t*2)*2),4)
 if 184<=t<214:
  # wordless original interlude: seed -> roots -> pollination -> seed
  p=(t-184)/30
  d.text((34,35),'土から、また。',font=font,fill='#c6d7ae')
  for i in range(7):sprite(im,'fly',80+i*74+int(math.sin(t+i)*10),120+int(math.cos(t*.8+i)*18),2)
  for i in range(8):d.line((40+i*80,214,50+i*80,235),fill='#9ea67b',width=2)
 if t<8:
  # Establish title gradually, then hold before dialogue.
  d.text((230,80),'ここにいる',font=titlefont,fill='#e3e3d3')
  d.text((237,131),'土と、名前と、わたしたち。',font=small,fill='#97a28f')
 page=next((p for p in pages if p['start']<=t<p['end']),None)
 if page:
  d.rectangle((24,245,615,343),fill='#080b10',outline='#dce2d5',width=2)
  d.rectangle((28,249,611,339),outline='#404944')
  d.text((36,230),page['chapter'],font=small,fill='#a6b897')
  elapsed=t-page['start']; chars=int(elapsed*20)+1; idx=0
  for row,line in enumerate(page['text'].split('\n')):
   for col,ch in enumerate(line):
    if idx>=chars:break
    dx=dy=0
    if page['effect']=='wave':dy=math.sin(t*4+idx*.65)*1.5
    elif page['effect']=='shake' and elapsed<.55:dx=math.sin(t*60+idx)*2;dy=math.cos(t*49+idx)*2
    d.text((44+col*19+dx,256+row*25+dy),ch,font=font,fill='#f0eee1');idx+=1
  if elapsed>len(page['text'])/20 and int(t*2)%2:d.polygon([(594,325),(602,325),(598,329)],fill='#bacaad')
 elif 184<=t<214:
  d.text((36,269),'INTERLUDE  /  めぐる',font=font,fill='#dce2cd')
  d.text((36,306),'くさ が かれて、つち に なって、また。',font=small,fill='#9caa92')
 if t>228:
  im=Image.blend(im,Image.new('RGB',im.size),min(1,(t-228)/2))
 return im
SR=22050

def audio(duration):
 a=np.zeros(int(duration*SR),dtype=np.float32)
 def add(start,length,freq,vol=.035,kind='sine'):
  off=int(start*SR);n=min(int(length*SR),len(a)-off)
  if n<=0:return
  tt=np.arange(n)/SR
  env=np.minimum(1,tt/.025)*np.minimum(1,(n/SR-tt)/.12)
  sig=np.sin(2*np.pi*freq*tt)
  if kind=='square':sig=np.tanh(sig*4)*.5
  if kind=='kick':sig=np.sin(2*np.pi*(48*tt+35*.025*(1-np.exp(-tt/.025))))*np.exp(-tt*16)
  a[off:off+n]+=sig*env*vol
 # Sparse original A minor / C major score, no borrowed melody.
 for start,end in [(0,34),(64,113),(142,184),(184,214)]:
  add(start,end-start,65.406,.035)
  for t in np.arange(start,end,2):
   chord=[220,261.626,329.628] if t<184 else [261.626,329.628,391.995]
   for f in chord:add(float(t),min(2.8,end-t),f,.009)
 for t in np.arange(184,213,.5):
  add(float(t),.24,48,.18,'kick')
  f=[523.251,659.255,783.991,659.255,587.33,659.255,440,392][int((t-184)*2)%8]
  add(float(t),.24,f,.035,'square')
 for t in [161,167,173,180]:add(t,.4,48,.12,'kick')
 for p in pages:
  # Keep chapter four, silence before the correction, and the ending entirely silent.
  if 113<=p['start']<142 or p['start']>=214:continue
  if '駆除' in p['text']:add(p['start'],.22,80,.11,'square')
  if 'とって' in p['text']:
   for k in range(3):add(p['start']+k*.45,.09,150,.09,'square')
  for i,c in enumerate(p['text']):
   if c.isspace() or c in '。、─「」':continue
   tm=p['start']+i/20
   if tm<p['end'] and not (113<=tm<142):add(tm,.033,640+(ord(c)%6)*70,.018,'square')
 peak=np.max(np.abs(a));a*=min(1,.8/max(peak,.001))
 with wave.open(str(OUT/'soundtrack.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((a*32767).astype('<i2').tobytes())
 return a
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--fps',type=int,default=12);args=ap.parse_args()
 duration=15 if args.preview else 230
 audio(duration)
 cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','640x360','-r',str(args.fps),'-i','pipe:0','-i',str(OUT/'soundtrack.wav'),'-vf','scale=1280:720:flags=neighbor','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',str(OUT/('preview.mp4' if args.preview else 'koko-ni-iru.mp4'))]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for n in range(duration*args.fps):
   p.stdin.write(frame(n/args.fps).tobytes())
   if n%(30*args.fps)==0:print(f'{n/args.fps:.0f}/{duration}s',flush=True)
 finally:p.stdin.close()
 if p.wait():raise SystemExit('ffmpeg failed')
 frame(89).resize((1280,720),Image.Resampling.NEAREST).save(OUT/'still.png')
 print('Rendered',duration,'seconds',flush=True)
