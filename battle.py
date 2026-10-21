"""Original FC-era battle framing and hand-drawn ecological pixel subjects."""
import math
from PIL import Image,ImageDraw
INK='#eeeede'

def make_subject(name,green=False):
    im=Image.new('RGBA',(112,96));d=ImageDraw.Draw(im)
    w=INK;mid='#89897f';dark='#33332e';earth='#c4af87' if green else mid
    if name=='soil':
        # Palm presented toward the viewer; square-stepped contour and soil mound.
        d.polygon([(16,48),(23,48),(23,55),(31,58),(80,58),(88,50),(96,50),(96,57),(90,66),(78,73),(69,77),(65,91),(44,91),(42,78),(31,72),(21,65),(16,57)],fill=w)
        d.polygon([(28,50),(33,39),(41,35),(45,28),(55,31),(63,25),(69,34),(78,35),(84,47),(80,57),(35,57)],fill=earth)
        for x,y in [(37,44),(45,37),(55,45),(65,35),(75,46),(47,53),(65,53)]:d.rectangle((x,y,x+2,y+1),fill=dark)
        d.line([(34,65),(45,69),(66,68),(80,61)],fill=mid,width=2)
        d.line([(48,77),(59,73),(70,72)],fill=mid,width=2)
        if green:
            d.line((56,33,56,12),fill='#9cb989',width=2)
            d.polygon([(56,20),(44,13),(44,8),(52,9),(56,15)],fill='#9cb989')
            d.polygon([(57,16),(61,7),(70,7),(67,13)],fill='#9cb989')
    elif name=='sugina':
        for base,top in [(37,24),(56,8),(75,30)]:
            d.rectangle((base,top,base+2,78),fill=w)
            for y in range(top+9,75,9):
                span=min(14,(y-top)//2+5)
                d.line((base,y,base-span,y-9),fill=w,width=2)
                d.line((base+2,y,base+span,y-9),fill=w,width=2)
                d.rectangle((base-1,y+1,base+3,y+2),fill=mid)
        d.line([(25,81),(45,76),(58,82),(81,78)],fill=mid,width=2)
        for x in [38,57,76]:d.line([(x,80),(x-5,86),(x+2,90)],fill=mid)
    elif name=='pea':
        d.line([(50,83),(52,62),(59,39),(56,17)],fill=w,width=2)
        for x,y,flip in [(53,66,-1),(56,50,1),(58,34,-1),(56,22,1)]:
            d.line((x,y,x+flip*15,y-8),fill=w,width=2)
            for j in [1,2]:
                a=x+flip*j*7
                d.ellipse((a-5,y-15,a+3,y-7),fill=w)
        d.polygon([(66,42),(74,44),(73,64),(67,76),(62,73),(65,56)],outline=w)
        for y in [51,58,65]:d.rectangle((67,y,69,y+2),fill=mid)
        d.line([(57,17),(62,11),(69,13),(68,18),(64,17)],fill=w)
    elif name=='beetle':
        d.line([(48,30),(44,22),(40,22)],fill=w,width=2);d.line([(64,30),(68,22),(72,22)],fill=w,width=2)
        for y in [45,56,68]:
            d.line([(34,y),(26,y-4),(22,y+3)],fill=w,width=2);d.line([(78,y),(86,y-4),(90,y+3)],fill=w,width=2)
        d.ellipse((42,28,70,48),fill=w);d.ellipse((32,38,80,82),fill=w)
        d.line((56,40,56,81),fill=dark,width=2)
        # Seven black spots: one shared near the head, three per wing.
        for x,y in [(56,44),(43,49),(40,61),(47,73),(69,49),(72,61),(65,73)]:d.ellipse((x-3,y-3,x+3,y+3),fill=dark)
        d.rectangle((48,33,50,35),fill=dark);d.rectangle((62,33,64,35),fill=dark)
    elif name=='fly':
        d.ellipse((22,24,51,53),outline=w,width=2);d.ellipse((61,24,90,53),outline=w,width=2)
        d.line((29,28,47,46),fill=mid);d.line((83,28,65,46),fill=mid)
        for y in [48,59,69]:
            d.line([(46,y),(36,y+3),(32,y+10)],fill=w,width=2);d.line([(66,y),(76,y+3),(80,y+10)],fill=w,width=2)
        d.ellipse((45,26,67,44),fill=w);d.ellipse((44,42,68,79),fill=w)
        for y in [49,58,67]:d.rectangle((45,y,67,y+3),fill=dark)
        d.rectangle((48,31,51,34),fill=dark);d.rectangle((61,31,64,34),fill=dark)
    elif name=='worm':
        pts=[(19,65),(25,53),(36,49),(46,54),(51,65),(61,71),(73,66),(81,52),(89,45)]
        d.line(pts,fill=w,width=10)
        for x,y in pts[1:-1]:d.line((x-3,y-4,x+3,y+4),fill=mid,width=1)
        d.ellipse((84,40,93,49),fill=w)
    elif name=='planet':
        d.ellipse((24,14,88,78),outline=w,width=2)
        for poly in [[(39,19),(49,22),(47,32),(57,37),(51,48),(37,43),(31,31)],[(63,43),(77,37),(82,47),(74,59),(66,67),(61,59)]]:d.polygon(poly,fill=w)
        d.line((20,48,14,52),fill=mid);d.point((15,24),fill=w);d.point((98,38),fill=w)
    elif name=='bare':
        d.line([(19,58),(34,54),(48,57),(61,54),(80,56),(95,53)],fill=w,width=2)
        for x,y in [(30,65),(45,73),(69,67),(82,76)]:d.rectangle((x,y,x+3,y+1),fill=mid)
        d.line([(48,57),(53,64),(49,68),(58,74)],fill=mid)
    elif name in ['sprout','seed']:
        d.ellipse((47,68,65,82),fill=earth)
        if name=='sprout':
            d.line((56,72,56,35),fill=w,width=3)
            d.polygon([(55,49),(37,42),(32,29),(45,30),(55,39)],fill=w)
            d.polygon([(58,42),(60,27),(75,21),(79,26),(72,39)],fill=w)
            d.line([(55,79),(48,88),(40,89)],fill=mid);d.line([(57,79),(63,88),(72,90)],fill=mid)
    return im

SUBJECTS={k:make_subject(k) for k in ['soil','sugina','pea','beetle','fly','worm','planet','bare','sprout','seed']}
SUBJECTS['living_soil']=make_subject('soil',True)

def subject_for(p):
    text=p['text'];chapter=p['chapter']
    if chapter.startswith('一'):return 'soil'
    if chapter.startswith('二'):return 'bare' if any(k in text for k in ['とって','きれい','しずか']) else 'soil'
    if chapter.startswith('三'):return p.get('subject','soil')
    if chapter.startswith('四'):return 'planet'
    if chapter.startswith('五'):
        return 'bare' if any(k in text for k in ['あした','なおらない','ちがう','けが','はがしたく','でも あれ']) else 'living_soil'
    return 'living_soil'

def draw_subject(im,name,t,age=5):
    sprite=SUBJECTS[name]
    # A tiny idle movement; hold still for the very first moment of an encounter.
    bob=0 if age<.45 else round(math.sin(t*2.1)*1)
    if name=='fly':bob=round(math.sin(t*5)*2)
    scale=2
    sprite=sprite.resize((224,192),Image.Resampling.NEAREST)
    im.paste(sprite,(208,16+bob),sprite)
