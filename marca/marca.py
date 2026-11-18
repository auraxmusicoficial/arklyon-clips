import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
F="/home/claude/arklyon-clips/motor/fontes/"
PD=F+"Pricedown.otf"; AN=F+"Anton-Regular.ttf"
ROSA=(255,46,147); LAR=(255,128,48); SOL=(255,214,64); CIANO=(0,229,212); ROXO=(48,8,78); PRETO=(0,0,0); BR=(255,255,255)
def grad(w,h,cores):
    g=Image.new("RGB",(w,h)); d=ImageDraw.Draw(g); n=len(cores)-1
    for y in range(h):
        t=y/(h-1); k=min(int(t*n),n-1); u=t*n-k
        d.line([(0,y),(w,y)],fill=tuple(int(cores[k][j]+(cores[k+1][j]-cores[k][j])*u) for j in range(3)))
    return g
def texto(img,xy,txt,size,fill,font=PD,anchor="mm",stroke=None,sombra=True):
    f=ImageFont.truetype(font,size); d=ImageDraw.Draw(img); st=stroke or max(4,size//12); x,y=xy
    if sombra: d.text((x+size//14,y+size//14),txt,font=f,fill=PRETO,anchor=anchor,stroke_width=st,stroke_fill=PRETO)
    d.text((x,y),txt,font=f,fill=PRETO,anchor=anchor,stroke_width=st,stroke_fill=PRETO)
    if isinstance(fill,list):
        bb=d.textbbox((x,y),txt,font=f,anchor=anchor); m=Image.new("L",img.size,0)
        ImageDraw.Draw(m).text((x,y),txt,font=f,fill=255,anchor=anchor)
        g=grad(bb[2]-bb[0]+2,bb[3]-bb[1]+2,fill); c=Image.new("RGB",img.size); c.paste(g,(bb[0],bb[1])); img.paste(c,(0,0),m)
    else: d.text((x,y),txt,font=f,fill=fill,anchor=anchor)
def sol(img,cx,cy,r):
    s=grad(2*r,2*r,[SOL,LAR,ROSA]); m=Image.new("L",(2*r,2*r),0); dm=ImageDraw.Draw(m); dm.ellipse([0,0,2*r-1,2*r-1],fill=255)
    for i in range(7):  # faixas do sol synthwave
        y=int(r*1.05+i*r*0.13); h=max(3,int(r*0.025+i*r*0.012)); dm.rectangle([0,y,2*r,y+h],fill=0)
    img.paste(s,(cx-r,cy-r),m)
def palmeira(d,x,base,alt,esc=1.0,cor=(20,0,35)):
    topo=(x+int(40*esc),base-alt)
    pts=[]; 
    for i in range(21):
        t=i/20; pts.append((x+int(40*esc*t*t)-int(10*esc*(1-t)), base-int(alt*t)))
    for i in range(len(pts)-1): d.line([pts[i],pts[i+1]],fill=cor,width=max(6,int((18-10*i/20)*esc)))
    for ang in [-160,-130,-100,-60,-25,10,35]:
        a=math.radians(ang); L=int(150*esc)
        p=[topo]
        for k in range(1,9):
            t=k/8; p.append((topo[0]+int(L*t*math.cos(a)), topo[1]+int(L*t*math.sin(a))+int(60*esc*t*t)))
        for i in range(len(p)-1): d.line([p[i],p[i+1]],fill=cor,width=max(4,int(14*esc*(1-i/9))))
def grade(img,y0,w,h,cor=ROSA):
    d=ImageDraw.Draw(img,"RGBA")
    for i in range(14):
        y=y0+int(h*(i/13)**2); d.line([(0,y),(w,y)],fill=cor+(150,),width=3)
    for k in range(-20,21):
        d.line([(w//2+k*60,y0),(w//2+k*420,y0+h)],fill=cor+(120,),width=3)

# ---------- BANNER 2560x1440 (área segura central 1546x423) ----------
W,H=2560,1440; b=grad(W,H,[(20,0,40),(90,10,110),(255,70,160),(255,140,70)])
sol(b,W//2,640,330)
mar=grad(W,H-760,[(40,0,70),(10,0,25)]); b.paste(mar,(0,760)); grade(b,760,W,680)
d=ImageDraw.Draw(b)
for x,a,e in [(120,620,1.3),(330,480,1.0),(2150,560,1.2),(2380,700,1.4),(560,380,0.8),(1960,400,0.85)]:
    palmeira(d,x,780,a,e)
texto(b,(W//2,640),"HQ VAULT CLIPS",190,[BR,(255,235,245)])
texto(b,(W//2,790),"DAILY GTA 6 NEWS  •  SECRETS  •  TIPS",62,CIANO,font=AN,stroke=6)
texto(b,(W//2,870),"NEW VIDEO EVERY DAY",48,SOL,font=AN,stroke=5)
b.save("banner.jpg",quality=92)

# ---------- AVATAR 800x800 ----------
A=800; av=grad(A,A,[(60,5,95),(255,60,150),(255,140,60)])
sol(av,A//2,300,210)
da=ImageDraw.Draw(av,"RGBA"); da.rectangle([0,470,A,A],fill=(25,0,45,255)); grade(av,470,A,330)
# cofre
da=ImageDraw.Draw(av)
da.rounded_rectangle([190,190,610,560],radius=40,fill=(15,0,30),outline=CIANO,width=16)
da.rounded_rectangle([235,235,565,515],radius=24,outline=ROSA,width=10)
da.ellipse([470,330,540,400],outline=CIANO,width=10); da.line([(505,330),(505,400)],fill=CIANO,width=6); da.line([(470,365),(540,365)],fill=CIANO,width=6)
da.rectangle([240,560,300,600],fill=(15,0,30)); da.rectangle([500,560,560,600],fill=(15,0,30))
texto(av,(355,375),"HQ",170,[SOL,LAR,ROSA])
texto(av,(A//2,690),"VAULT CLIPS",92,BR)
m=Image.new("L",(A,A),0); ImageDraw.Draw(m).ellipse([0,0,A-1,A-1],fill=255)
av.save("avatar.jpg",quality=93)
prev=Image.new("RGB",(A,A),(255,255,255)); prev.paste(av,(0,0),m); prev.save("avatar_previa_redonda.jpg",quality=90)
# ---------- MARCA D'ÁGUA 150x150 (PNG com transparência) ----------
wm=av.resize((150,150),Image.LANCZOS).convert("RGBA"); mk=Image.new("L",(150,150),0); ImageDraw.Draw(mk).ellipse([0,0,149,149],fill=255)
wm.putalpha(mk); wm.save("watermark.png")
# prévia do banner: como fica no celular (faixa central)
b.crop(((W-1546)//2,(H-423)//2,(W+1546)//2,(H+423)//2)).save("banner_celular.jpg",quality=88)
