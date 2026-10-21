"""User BGM + original voiced dialogue blips; no synthesized drone layer."""
from pathlib import Path
import json, subprocess, wave
import numpy as np
SR=44100
BGM_CUES=[('01-uneasy.mp3',0,64),('02-names.mp3',64,136),('03-listening.mp3',136,184)]

def render_audio(duration,pages,root):
    n=int(duration*SR)
    music=np.zeros((n,2),np.float32)
    voice=np.zeros(n,np.float32)
    report=[]
    for filename,start,end in BGM_CUES:
        end=min(end,duration)
        if start>=end:continue
        # Read from each supplied track's beginning, preserve stereo and pitch.
        data=subprocess.run(['ffmpeg','-v','error','-i',str(root/'assets/bgm'/filename),'-t',str(end-start),'-f','f32le','-acodec','pcm_f32le','-ar',str(SR),'-ac','2','pipe:1'],capture_output=True,check=True).stdout
        clip=np.frombuffer(data,dtype='<f4').reshape(-1,2).copy()
        assert len(clip)>=int((end-start-.1)*SR),f'BGM too short: {filename}'
        rms=float(np.sqrt(np.mean(clip**2)))
        gain=min(3,.095/max(rms,.001))
        clip*=gain
        length=len(clip)
        fade=min(int(.45*SR),length)
        clip[:fade]*=np.linspace(0,1,fade)[:,None]
        fadeout=min(int(.65*SR),length)
        clip[-fadeout:]*=np.linspace(1,0,fadeout)[:,None]
        off=int(start*SR);clip=clip[:n-off]
        music[off:off+len(clip)]+=clip
        report.append(dict(file=filename,start=start,end=end,source_in=0,gain=round(gain,4)))

    def place(start,samples):
        off=round(start*SR)
        if off>=n:return
        length=min(len(samples),n-off)
        voice[off:off+length]+=samples[:length]

    def blip(ch,p):
        # A pitched pulse through three vocal resonances, not a piercing key beep.
        emph='駆除' in p['text']
        whisper='──' in p['text'] or 'ころせない' in p['text']
        base=112 if emph else 148 if whisper else {'soil':132,'sugina':154,'pea':146,'beetle':176,'fly':163,'worm':118}.get(p.get('subject'),136)
        f0=base*2**(((ord(ch)%7)-3)/36)
        length=.046 if whisper else .055
        t=np.arange(int(SR*length))/SR
        phase=2*np.pi*f0*(t+.0009*(1-np.exp(-t/.012)))
        signal=np.zeros_like(t)
        for h in range(1,27):
            f=f0*h
            # Formants vary slightly by kana for a small talking-voice texture.
            f1=520+(ord(ch)%4)*85;f2=1250+(ord(ch)%5)*110
            weight=(.10*np.exp(-((f-220)/160)**2)+np.exp(-((f-f1)/220)**2)+.45*np.exp(-((f-f2)/350)**2))/h**.35
            signal+=weight*np.sin(h*phase)
        signal/=max(np.max(np.abs(signal)),.001)
        # Fast but smooth edges avoid digital clicks; a faint downwards pitch gives body.
        env=np.minimum(1,t/.003)*np.minimum(1,(length-t)/.009)*np.exp(-t*14)
        return (signal*env*(.12 if whisper else .19 if emph else .15)).astype(np.float32)

    events=[]
    duck=np.ones(n,np.float32)
    for p in pages:
        if p['start']>=214:continue  # ending remains completely silent
        for ch,offset in zip(p['text'],p['reveal_times']):
            if ch.isspace() or ch in '。、─「」':continue
            start=p['start']+offset
            if start>=duration:continue
            place(start,blip(ch,p));events.append(dict(time=round(start,6),char=ch))
            lo=max(0,int((start-.018)*SR));hi=min(n,int((start+.13)*SR))
            # Light music ducking keeps voice audible without swallowing the new BGM.
            tt=np.arange(hi-lo)/SR
            envelope=.22*np.minimum(1,tt/.018)*np.minimum(1,(len(tt)/SR-tt)/.065)
            duck[lo:hi]=np.minimum(duck[lo:hi],1-envelope)
        if '駆除' in p['text'] or 'とって' in p['text']:
            hits=[0] if '駆除' in p['text'] else [off for ch,off in zip(p['text'],p['reveal_times']) if ch=='と']
            for offset in hits:
                t=np.arange(int(.09*SR))/SR
                place(p['start']+offset,(np.sin(2*np.pi*91*t)+.3*np.sin(2*np.pi*697*t))*np.exp(-t*55)*.11)
    # Retain the first cut's short original interlude, with no continuous bass/drone.
    for time in np.arange(184,min(duration,214),.5):
        f=[523.251,659.255,783.991,659.255,587.33,659.255,440,392][round((time-184)*2)%8]
        t=np.arange(int(.26*SR))/SR
        envelope=np.minimum(1,t/.008)*np.minimum(1,(.26-t)/.045)*np.exp(-t*8)
        melody=np.tanh(3*np.sin(2*np.pi*f*t))*.075*envelope
        kick=np.sin(2*np.pi*(48*t+.875*(1-np.exp(-t/.025))))*np.exp(-t*23)*.17
        off=int(time*SR);length=min(len(t),n-off)
        music[off:off+length]+=(melody+kick)[:length,None]
    # Directed silences are keyed to the actual last revealed glyph.
    quiet=[]
    def quiet_between(start,end,level=0):
        lo=max(0,round(start*SR));hi=min(n,round(end*SR))
        if hi<=lo:return
        fade=min(round(.055*SR),(hi-lo)//3)
        gain=np.full(hi-lo,level,dtype=np.float32)
        if fade:
            gain[:fade]=np.linspace(1,level,fade)
            gain[-fade:]=np.linspace(level,1,fade)
        music[lo:hi]*=gain[:,None]
        quiet.append(dict(start=round(start,4),end=round(end,4),level=level))
    quiet_between(0,1.5)
    for p in pages:
        if p.get('music_silence'):
            quiet_between(p['start']+p['reveal_times'][-1]+.10,p['end'])
        if '── ちがう。' in p['text']:
            quiet_between(p['start']-.30,p['start']+p['reveal_times'][-1]+.15)
        if p['text'].startswith('ごおくねん。'):
            quiet_between(p['start'],p['start']+.65)
    mixed=music*duck[:,None]+voice[:,None]
    # Whole-track gain only; no hard clipping and no loudness jumps between sections.
    peak=float(np.max(np.abs(mixed)))
    final_gain=min(1,.89/max(peak,.001));mixed*=final_gain
    with wave.open(str(root/'output/soundtrack.wav'),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes((mixed*32767).astype('<i2').tobytes())
    (root/'output/audio-cues.json').write_text(json.dumps(dict(sample_rate=SR,channels=2,bgm=report,voice_events=events,peak_before_gain=peak,final_gain=final_gain,drone_layer=False,directed_silences=quiet),ensure_ascii=False,indent=2))
    return mixed
