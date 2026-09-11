#!/usr/bin/env python3
"""Render res/drawable-nodpi/preview.png from the Layout A geometry.

Mirrors res/raw/watchface.xml element-for-element so the picker thumbnail
matches the face, and so the layout can be eyeballed without a device.
Preview state: 10:08:32, Fri 11, 72%, 8412 steps, not charging.
"""
from PIL import Image, ImageDraw, ImageFont
import math, os

S = 480; C = 240
BG="#0A0A0B"; INK="#F2F2F0"; DIM="#8C8F93"; TRACK="#2A2D31"; ACCENT="#4A9EDB"
F = "watchface/src/main/res/font"
D = "watchface/src/main/res/drawable-nodpi"
def font(n, s): return ImageFont.truetype(f"{F}/{n}.ttf", s)

img = Image.new("RGBA", (S, S), (0,0,0,0)); d = ImageDraw.Draw(img)
d.ellipse([0,0,S-1,S-1], fill=BG)

def tint(name, box, color):
    m = Image.open(f"{D}/{name}.png").split()[-1].resize((box[2],box[3]), Image.LANCZOS)
    lay = Image.new("RGBA",(box[2],box[3]), color); lay.putalpha(m)
    img.alpha_composite(lay,(box[0],box[1]))

def track_text(s, f, x, y, w, h, fill, ls=0.0, align="CENTER"):
    """letterSpacing-aware straight text inside a box (em units, like WFF)."""
    sp = ls * f.size
    widths = [f.getlength(ch) + sp for ch in s]
    tw = sum(widths) - sp
    cx = x + (w - tw)/2 if align=="CENTER" else (x + w - tw if align=="END" else x)
    a, dsc = f.getmetrics(); by = y + (h - (a+dsc))/2 + a
    for ch, cw in zip(s, widths):
        d.text((cx, by), ch, font=f, fill=fill, anchor="ls"); cx += cw
    return tw

def curved(segs, r, mid_deg, ls_list):
    """Text along an arc, centred on mid_deg (0 deg = 12 o'clock, clockwise)."""
    items=[]
    for (s, f, col, ls) in segs:
        for ch in s: items.append((ch, f, col, f.getlength(ch) + ls*f.size))
    total = sum(w for *_ , w in items)
    a = mid_deg - math.degrees(total/2/r)
    for ch, f, col, w in items:
        ac = a + math.degrees(w/2/r)
        g = Image.new("RGBA", (int(f.size*2.2), int(f.size*2.2)), (0,0,0,0))
        gd = ImageDraw.Draw(g); gd.text((g.width/2, g.height/2), ch, font=f, fill=col, anchor="mm")
        g = g.rotate(-ac, resample=Image.BICUBIC)
        px = C + r*math.sin(math.radians(ac)); py = C - r*math.cos(math.radians(ac))
        img.alpha_composite(g, (int(px-g.width/2), int(py-g.height/2)))
        a += math.degrees(w/r)

def arc(r, a0, a1, width, color):
    bb=[C-r, C-r, C+r, C+r]
    d.arc(bb, a0-90, a1-90, fill=color, width=width)

# chrome
tint("track_minute",(0,0,S,S), TRACK if False else "#3E4247")
tint("track_hour",(0,0,S,S), "#6A6E73")
d.rectangle([239,10,240,31], fill=ACCENT)
sa = math.radians(32*6)
d.ellipse([C+222*math.sin(sa)-4, C-222*math.cos(sa)-4, C+222*math.sin(sa)+4, C-222*math.cos(sa)+4], fill=ACCENT)

# slot 0 + hairline
track_text("FRIDAY 11", font("archivo_semibold",23), 0, 64, 480, 30, INK, 0.16)
d.rectangle([166,106,313,106], fill=TRACK)

# time, colon-centred
tb = font("archivo_bold",100)
track_text("10", tb, 0,118,223,116, INK, -0.04, "END")
track_text(":",  tb, 223,118,34,116, DIM)
track_text("08", tb, 257,118,223,116, INK, -0.04, "START")

# arcs: steps 84%, battery 72%
arc(196,240,300,8,TRACK); arc(196,240,240+60*0.84,8,ACCENT)
arc(196, 60,120,8,TRACK); arc(196, 60, 60+60*0.72,8,ACCENT)
fm, fb = font("archivo_medium",13), font("archivo_bold",19)
f12, f14 = font("archivo_semibold",12), font("archivo_bold",14)
curved([("STEPS ",fm,DIM,0.108),("8412",fb,INK,0)], 176, 270, None)
curved([("BATT ",fm,DIM,0.108),("72%",fb,INK,0)], 176, 90, None)
curved([("ALM ",f12,DIM,0.133),("07:30",f14,INK,0)], 198, 315, None)
curved([("TMR ",f12,DIM,0.133),("12:00",f14,INK,0)], 198, 45, None)

# slot 1 forecast
for (i,(x,g,t,h)) in enumerate([(157,"wx_clear","18",11),(221,"wx_partly","17",12),(285,"wx_rain","15",13)]):
    tint(f"{g}_i",(x+6,248,26,26), INK); tint(f"{g}_a",(x+6,248,26,26), ACCENT)
    track_text(f"{t}°", font("archivo_bold",17), x,276,38,22, INK)
    track_text(str(h), font("archivo_medium",11), x,298,38,14, DIM, 0.1)

# slot 6 minor row + slot 7 tile
lf, vf = font("archivo_medium",14), font("archivo_bold",19)
lw = sum(lf.getlength(ch)+0.14*14 for ch in "SUNSET"); vw = vf.getlength("20:41")
x0 = C-(lw+9+vw)/2
track_text("SUNSET", lf, int(x0),334,int(lw),26, DIM, 0.14, "START")
track_text("20:41",  vf, int(x0+lw+9),334,int(vw),26, INK, 0, "START")
d.rounded_rectangle([216,366,263,413], radius=14, outline=TRACK, width=1)
tint("tile_wallet",(214,364,52,52), ACCENT)

img.save(f"{D}/preview.png", optimize=True)
print("preview.png", img.size, os.path.getsize(f"{D}/preview.png"), "bytes")
