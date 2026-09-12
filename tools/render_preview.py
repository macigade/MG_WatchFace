#!/usr/bin/env python3
"""Render the picker thumbnail and the editor option icons from the shipped geometry.

Mirrors res/raw/watchface.xml element for element, so the images match the face
and the layout can be eyeballed without a device.

  preview.png     480x480  Layout A (the default option)
  opt_layout_a    200x200  editor icon
  opt_layout_c    200x200  editor icon

Preview state: 10:08:32, Fri 11, 72%, 8412 steps, not charging, not low.
"""
from PIL import Image, ImageDraw, ImageFont
import math, os, sys

S=480; C=240
BG="#0A0A0B"; INK="#F2F2F0"; DIM="#8C8F93"; TRACK="#2A2D31"; ACCENT="#4A9EDB"
FD="watchface/src/main/res/font"; DD="watchface/src/main/res/drawable-nodpi"
def fnt(n,s): return ImageFont.truetype(f"{FD}/{n}.ttf", s)

def build(layout):
    img=Image.new("RGBA",(S,S),(0,0,0,0)); d=ImageDraw.Draw(img)
    d.ellipse([0,0,S-1,S-1], fill=BG)

    def tint(name,box,color):
        m=Image.open(f"{DD}/{name}.png").split()[-1].resize((box[2],box[3]), Image.LANCZOS)
        lay=Image.new("RGBA",(box[2],box[3]),color); lay.putalpha(m)
        img.alpha_composite(lay,(box[0],box[1]))

    def txt(s,f,x,y,w,h,fill,ls=0.0,align="CENTER"):
        sp=ls*f.size; ws=[f.getlength(ch)+sp for ch in s]; tw=sum(ws)-sp
        cx = x+(w-tw)/2 if align=="CENTER" else (x+w-tw if align=="END" else x)
        a,dsc=f.getmetrics(); by=y+(h-(a+dsc))/2+a
        for ch,cw in zip(s,ws):
            d.text((cx,by),ch,font=f,fill=fill,anchor="ls"); cx+=cw
        return tw

    def curved(segs,r,mid,ccw=False):
        items=[(ch,f,col,f.getlength(ch)+ls*f.size) for (s,f,col,ls) in segs for ch in s]
        total=sum(w for *_,w in items)
        half=math.degrees(total/2/r)
        a = mid+half if ccw else mid-half
        for ch,f,col,w in items:
            step=math.degrees(w/r); ac = a-step/2 if ccw else a+step/2
            g=Image.new("RGBA",(int(f.size*2.4),)*2,(0,0,0,0))
            ImageDraw.Draw(g).text((g.width/2,g.height/2),ch,font=f,fill=col,anchor="mm")
            g=g.rotate(-(ac+180) if ccw else -ac, resample=Image.BICUBIC)
            px=C+r*math.sin(math.radians(ac)); py=C-r*math.cos(math.radians(ac))
            img.alpha_composite(g,(int(px-g.width/2),int(py-g.height/2)))
            a = a-step if ccw else a+step

    def arc(r,a0,a1,w,col):
        d.arc([C-r,C-r,C+r,C+r], a0-90, a1-90, fill=col, width=w)

    # chrome, identical in both layouts
    tint("track_minute",(0,0,S,S),"#3E4247"); tint("track_hour",(0,0,S,S),"#6A6E73")
    d.rectangle([239,10,240,31], fill=ACCENT)
    sa=math.radians(32*6)
    d.ellipse([C+222*math.sin(sa)-4,C-222*math.cos(sa)-4,C+222*math.sin(sa)+4,C-222*math.cos(sa)+4], fill=ACCENT)

    if layout=="a":
        txt("FRIDAY 11", fnt("archivo_semibold",23),0,64,480,30,INK,0.16)
        d.rectangle([166,106,313,106], fill=TRACK)
        tb=fnt("archivo_bold",100)
        txt("10",tb,0,118,223,116,INK,-0.04,"END"); txt(":",tb,223,118,34,116,DIM)
        txt("08",tb,257,118,223,116,INK,-0.04,"START")
        arc(196,240,300,8,TRACK); arc(196,240,240+60*0.84,8,ACCENT)
        arc(196,60,120,8,TRACK);  arc(196,60,60+60*0.72,8,ACCENT)
        fm,fb=fnt("archivo_medium",13),fnt("archivo_bold",19)
        f12,f14=fnt("archivo_semibold",12),fnt("archivo_bold",14)
        curved([("STEPS ",fm,DIM,0.108),("8412",fb,INK,0)],176,270)
        curved([("BATT ",fm,DIM,0.108),("72%",fb,INK,0)],176,90)
        curved([("ALM ",f12,DIM,0.133),("07:30",f14,INK,0)],198,315)
        curved([("TMR ",f12,DIM,0.133),("12:00",f14,INK,0)],198,45)
        for x,g,t,h in ((157,"wx_clear","18",11),(221,"wx_partly","17",12),(285,"wx_rain","15",13)):
            tint(f"{g}_i",(x+6,248,26,26),INK); tint(f"{g}_a",(x+6,248,26,26),ACCENT)
            txt(f"{t}°",fnt("archivo_bold",17),x,276,38,22,INK)
            txt(str(h),fnt("archivo_medium",11),x,298,38,14,DIM,0.1)
        lf,vf=fnt("archivo_medium",14),fnt("archivo_bold",19); my=334
        tile_y=366
    else:
        txt("FRIDAY 11", fnt("archivo_semibold",21),0,130,480,28,INK,0.16)
        tb=fnt("archivo_bold",96)
        txt("10",tb,0,162,224,109,INK,-0.04,"END"); txt(":",tb,224,162,32,109,DIM)
        txt("08",tb,256,162,224,109,INK,-0.04,"START")
        f13,f16=fnt("archivo_semibold",13),fnt("archivo_bold",16)
        curved([("STP ",f13,DIM,0.123),("8412",f16,INK,0)],198,315)
        curved([("BAT ",f13,DIM,0.123),("72%",f16,INK,0)],198,45)
        curved([("ALM ",f13,DIM,0.123),("07:30",f16,INK,0)],198,225,ccw=True)
        curved([("TMR ",f13,DIM,0.123),("12:00",f16,INK,0)],198,135,ccw=True)
        for x,g,t in ((174,"wx_clear","18"),(226,"wx_partly","17"),(278,"wx_rain","15")):
            tint(f"{g}_i",(x+4,284,20,20),INK); tint(f"{g}_a",(x+4,284,20,20),ACCENT)
            txt(f"{t}°",fnt("archivo_bold",15),x,306,28,20,INK)
        lf,vf=fnt("archivo_medium",12),fnt("archivo_bold",17); my=326
        tile_y=358

    lw=sum(lf.getlength(ch)+0.14*lf.size for ch in "SUNSET"); vw=vf.getlength("20:41")
    x0=C-(lw+9+vw)/2
    txt("SUNSET",lf,int(x0),my,int(lw),26,DIM,0.14,"START")
    txt("20:41",vf,int(x0+lw+9),my,int(vw),26,INK,0,"START")
    d.rounded_rectangle([216,tile_y,263,tile_y+47], radius=14, outline=TRACK, width=1)
    tint("tile_wallet",(214,tile_y-2,52,52),ACCENT)
    return img

a=build("a"); c=build("c")
a.save(f"{DD}/preview.png", optimize=True)
a.resize((200,200), Image.LANCZOS).save(f"{DD}/opt_layout_a.png", optimize=True)
c.resize((200,200), Image.LANCZOS).save(f"{DD}/opt_layout_c.png", optimize=True)
if "--sheet" in sys.argv:
    sh=Image.new("RGBA",(S*2+24,S),(24,24,26,255))
    sh.alpha_composite(a,(0,0)); sh.alpha_composite(c,(S+24,0)); sh.save("/tmp/layouts.png")
for f in ("preview.png","opt_layout_a.png","opt_layout_c.png"):
    print(f"{f:18} {os.path.getsize(DD+'/'+f):6} B")
