#!/usr/bin/env python3
"""Structural checks on the watch face. Asserts attribute values, not substrings."""
import re, os, glob, struct, sys
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont

WF="watchface/src/main/res/raw/watchface.xml"
FD="watchface/src/main/res/font"; DD="watchface/src/main/res/drawable-nodpi"
SF="watchface/src/main/res/values/strings.xml"
rows=[]; FAIL=[]; UNK=[]
def chk(n, ok, det=""):
    t="PASS" if ok is True else ("FAIL" if ok is False else "UNKNOWN")
    if ok is False: FAIL.append(n)
    if ok is None: UNK.append(n)
    rows.append(f"{t:8} {n}" + (f"  -- {det}" if det and ok is not True else ""))

root=ET.parse(WF).getroot(); src=open(WF).read()
strings={m for m in re.findall(r'<string name="(\w+)"', open(SF).read())}
def grp(name):
    for g in root.iter("Group"):
        if g.get("name")==name: return g
    return None
A, Cc = grp("layout_a"), grp("layout_c")

# ---------- vocabulary ----------
ELEM={"WatchFace","Metadata","UserConfigurations","ListConfiguration","ListOption","Scene",
 "Group","Variant","Condition","Expressions","Expression","Compare","Default","PartText","Text",
 "TextCircular","Font","Template","Parameter","Upper","DigitalClock","TimeText","PartImage",
 "Image","PartDraw","Rectangle","RoundRectangle","Ellipse","Arc","Fill","Stroke","Transform",
 "Launch","ComplicationSlot","BoundingBox","Complication","DefaultProviderPolicy"}
ATTR={"WatchFace":{"width","height","clipShape"},"Metadata":{"key","value"},
 "UserConfigurations":set(),
 "ListConfiguration":{"id","displayName","screenReaderText","defaultValue","icon"},
 "ListOption":{"id","displayName","screenReaderText","icon"},"Scene":{"backgroundColor"},
 "Group":{"name","x","y","width","height","alpha"},"Variant":{"mode","target","value"},
 "Condition":set(),"Expressions":set(),"Expression":{"name"},"Compare":{"expression"},
 "Default":set(),"PartText":{"name","x","y","width","height"},
 "Text":{"align","verticalAlign"},
 "TextCircular":{"centerX","centerY","width","height","startAngle","endAngle","direction","align","verticalAlign"},
 "Font":{"family","size","color","weight","letterSpacing"},"Template":set(),
 "Parameter":{"expression"},"Upper":set(),
 "DigitalClock":{"name","x","y","width","height"},
 "TimeText":{"format","hourFormat","align","verticalAlign","x","y","width","height"},
 "PartImage":{"name","x","y","width","height","tintColor"},"Image":{"resource"},
 "PartDraw":{"name","x","y","width","height","pivotX","pivotY","angle"},
 "Rectangle":{"x","y","width","height"},
 "RoundRectangle":{"x","y","width","height","cornerRadiusX","cornerRadiusY"},
 "Ellipse":{"centerX","centerY","width","height"},
 "Arc":{"centerX","centerY","width","height","startAngle","endAngle","direction"},
 "Fill":{"color"},"Stroke":{"color","width"},"Transform":{"target","value","mode"},
 "Launch":{"target"},"ComplicationSlot":{"slotId","supportedTypes","x","y","width","height"},
 "BoundingBox":{"x","y","width","height"},"Complication":{"type"},
 "DefaultProviderPolicy":{"defaultSystemProvider","defaultSystemProviderType"}}
be=sorted({e.tag for e in root.iter() if e.tag not in ELEM})
ba=sorted({f"{e.tag}@{a}" for e in root.iter() if e.tag in ELEM for a in e.attrib if a not in ATTR[e.tag]})
chk("all elements traced to WFF reference docs", not be, str(be))
chk("all attributes traced to WFF reference docs", not ba, str(ba))

# ---------- configuration wiring ----------
uc=root.find("UserConfigurations")
ucs={c.get("id"):c for c in uc.findall("ListConfiguration")}
chk("UserConfigurations declares layout and numerals",
    set(ucs)=={"layout","numerals"}, str(sorted(ucs)))
scl=[e for e in root.find("Scene") if e.tag=="ListConfiguration"][0]
chk("Scene ListConfiguration is the layout selector", scl.get("id")=="layout", scl.get("id"))
chk("layout: declared options == used options",
    [o.get("id") for o in ucs["layout"]]==[o.get("id") for o in scl]==["a","c"])
chk("numerals: six options in HANDOFF section 3 order",
    [o.get("id") for o in ucs["numerals"]]==["archivo","barlow","saira","jet","bebas","playfair"],
    str([o.get("id") for o in ucs["numerals"]]))
chk("every defaultValue is a declared option",
    all(c.get("defaultValue") in [o.get("id") for o in c] for c in ucs.values()),
    str({k:v.get("defaultValue") for k,v in ucs.items()}))
ms=[v for c in ucs.values() for e in (c,*c) for k,v in e.attrib.items()
    if k in ("displayName","screenReaderText") and v not in strings]
chk("all editor labels resolve in strings.xml", not ms, str(sorted(set(ms))))
mi=[e.get("icon") for c in ucs.values() for e in (c,*c)
    if e.get("icon") and not os.path.exists(f"{DD}/{e.get('icon')}.png")]
chk("all ListOption icons exist as drawables", not mi, str(mi))
# every numerals option must be reachable from an expression in the scene
cfgref=set(re.findall(r'\[CONFIGURATION\.numerals\] == "(\w+)"', src))
opts={o.get("id") for o in ucs["numerals"]}
chk("five numerals options branch by expression, the sixth is the Default",
    cfgref==opts-{"playfair"}, f"branched={sorted(cfgref)} declared={sorted(opts)}")

# ---------- resources ----------
imgs=sorted({e.get("resource") for e in root.iter("Image")})
chk(f"all {len(imgs)} Image resources exist",
    not [r for r in imgs if not os.path.exists(f"{DD}/{r}.png")],
    str([r for r in imgs if not os.path.exists(f"{DD}/{r}.png")]))
fams=sorted({e.get("family") for e in root.iter("Font") if e.get("family")})
mf=[f for f in fams if f!="SYNC_TO_DEVICE" and not os.path.exists(f"{FD}/{f}.ttf")]
chk(f"all {len(fams)} Font families exist in res/font", not mf, str(mf))
bad=[]
for n,w in {"archivo_medium":500,"archivo_semibold":600,"archivo_bold":700}.items():
    t=TTFont(f"{FD}/{n}.ttf", lazy=True)
    if t['OS/2'].usWeightClass!=w: bad.append(f"{n}={t['OS/2'].usWeightClass}")
    if t.sfntVersion not in ("\x00\x01\x00\x00","true"): bad.append(f"{n} not TTF")
chk("Archivo UI weights 500/600/700 correct and real TTF", not bad, str(bad))

# ---------- data sources ----------
VER={"BATTERY_PERCENT","BATTERY_IS_LOW","BATTERY_CHARGING_STATUS","STEP_COUNT","STEP_PERCENT",
     "DAY","DAY_OF_WEEK_F","SECOND","HOUR_0_23","COMPLICATION.TEXT","COMPLICATION.TITLE"}
toks=set(re.findall(r'\[([A-Z0-9_.]+)\]', src)); wx={t for t in toks if t.startswith("WEATHER.")}
chk("non-weather tokens verified in SourceType ref", toks-wx<=VER, f"unverified={sorted(toks-wx-VER)}")
chk("weather tokens match WEATHER.HOURS.<1-8>.<FIELD>",
    all(re.fullmatch(r'WEATHER\.HOURS\.[1-8]\.(CONDITION|TEMPERATURE)',t) for t in wx),
    str([t for t in wx if not re.fullmatch(r'WEATHER\.HOURS\.[1-8]\.(CONDITION|TEMPERATURE)',t)]))
tb=[f"{(t.text or '').strip()!r}" for t in root.iter("Template")
    if len(re.findall(r'%[sd]', t.text or "")) != len(t.findall("Parameter"))]
chk("Template placeholders == Parameter count", not tb, str(tb))

# ---------- geometry, per layout ----------
def box(e): return tuple(float(e.get(k)) for k in ("x","y","width","height"))
def find(g, tag, pred): return [e for e in g.iter(tag) if pred(e)]

W,H=int(root.get("width")),int(root.get("height"))
chk("design space is 480x480", (W,H)==(480,480), f"{W}x{H}")
oob=[]
for e in root.iter():
    if e.tag in ("PartText","PartImage","PartDraw","Group","DigitalClock","Rectangle",
                 "RoundRectangle","ComplicationSlot","BoundingBox","TimeText"):
        try: x,y,w,h=box(e)
        except (TypeError,ValueError): continue
        if x<0 or y<0 or x+w>W or y+h>H: oob.append(f"{e.tag} {x},{y} {w}x{h}")
chk("no element outside the 480x480 space", not oob, str(oob))
rr=[f"r={float(e.get('width'))/2}" for e in root.iter("TextCircular") if float(e.get("width"))/2>200]
chk("curved text radius <= 200 (section 2 safe circle)", not rr, str(rr))

# HANDOFF section 5 / 6 exact values
from fontTools.ttLib import TTFont as _TT
NUM={"archivo":("archivo_bold",-0.04,700),"barlow":("barlow_condensed_medium",0.01,500),
     "saira":("saira_semibold",-0.02,600),"jet":("jetbrains_mono_semibold",-0.02,600),
     "bebas":("bebas_neue_regular",0.01,400),"playfair":("playfair_display_semibold",-0.015,600)}
def clocks(g):
    out=[]
    for dc in g.iter("DigitalClock"):
        tts=list(dc.iter("TimeText")); f=list(tts[0].iter("Font"))[0]
        out.append((box(dc), float(f.get("size")), f.get("family"),
                    float(f.get("letterSpacing")), box(tts[0]), box(tts[1])))
    return out
def colon_adv(fam,size):
    t=_TT(f"{FD}/{fam}.ttf", lazy=True)
    return t['hmtx'][t.getBestCmap()[ord(':')]][0]/t['head'].unitsPerEm*size
for tag,g,y,h,size in (("A",A,118,116,100),("C",Cc,162,109,96),("AOD",grp("ambient"),160,120,104)):
    cl=clocks(g)
    chk(f"{tag}: six numeral variants of the clock", len(cl)==6, f"{len(cl)}")
    chk(f"{tag}: every variant at y {y}, height {h}, size {size}",
        all(b[1]==y and b[3]==h and sz==size for b,sz,*_ in cl),
        str(sorted({(b[1],b[3],sz) for b,sz,*_ in cl})))
    chk(f"{tag}: families and tracking match HANDOFF section 3",
        {(fam,ls) for _,_,fam,ls,_,_ in cl}=={(v[0],v[1]) for v in NUM.values()},
        str(sorted({(fam,ls) for _,_,fam,ls,_,_ in cl})))
    bad=[]
    for _,sz,fam,_,hh,mm in cl:
        ca=colon_adv(fam,sz); want_end=round(240-ca/2,1); want_start=round(240+ca/2,1)
        if abs(hh[0]+hh[2]-want_end)>0.05: bad.append(f"{fam} hh ends {hh[0]+hh[2]} want {want_end}")
        if abs(mm[0]-want_start)>0.05: bad.append(f"{fam} mm starts {mm[0]} want {want_start}")
        if abs((hh[0]+hh[2]+mm[0])/2-240)>0.05: bad.append(f"{fam} colon not centred on 240")
    chk(f"{tag}: colon box is each font's own advance, centred on x 240", not bad, str(bad))
bad=[]
for sid,(fam,_,wt) in NUM.items():
    t=_TT(f"{FD}/{fam}.ttf", lazy=True)
    if t['OS/2'].usWeightClass!=wt: bad.append(f"{sid}={t['OS/2'].usWeightClass} want {wt}")
    if any(ord(c) not in t.getBestCmap() for c in "0123456789:"): bad.append(f"{sid} missing glyphs")
chk("all six numeral fonts carry 0-9 and : at the section 3 weight", not bad, str(bad))

def strip_y(g, size):
    for pt in g.iter("PartText"):
        fs=[f for f in pt.iter("Font") if f.get("size")==str(size)]
        if fs and any(u.tag=="Upper" for f in fs for u in f): return box(pt)[1]
chk("A: top strip y 64 at 23 px", strip_y(A,23)==64, str(strip_y(A,23)))
chk("C: top strip y 130 at 21 px", strip_y(Cc,21)==130, str(strip_y(Cc,21)))

def minor_y(g):
    for cs in g.iter("ComplicationSlot"):
        if cs.get("slotId")=="6":
            inner=[p for p in cs.iter("PartText")][0]
            return box(cs)[1]+box(inner)[1]
chk("A: minor row renders at y 334 (section 5)", minor_y(A)==334, str(minor_y(A)))
chk("C: minor row renders at y 326 (section 6)", minor_y(Cc)==326, str(minor_y(Cc)))

def tile_y(g):
    return [box(r)[1] for r in g.iter("RoundRectangle") if box(r)[2]==48][0]
chk("A: icon tile 48x48 at x 216 y 366", tile_y(A)==366 and
    [box(r)[0] for r in A.iter("RoundRectangle") if box(r)[2]==48][0]==216, str(tile_y(A)))
chk("C: icon tile 48x48 at x 216 y 358", tile_y(Cc)==358, str(tile_y(Cc)))
chk("both: tile corner radius 14",
    all(r.get("cornerRadiusX")=="14" for g in (A,Cc) for r in g.iter("RoundRectangle") if box(r)[2]==48))

def fc_y(g, icon_px):
    return sorted({box(p)[1] for p in g.iter("PartImage") if box(p)[2]==icon_px})
chk("A: forecast icons 26 px at y 248", fc_y(A,26)==[248.0], str(fc_y(A,26)))
chk("C: forecast icons 20 px at y 284", fc_y(Cc,20)==[284.0], str(fc_y(Cc,20)))

# arcs: A only
aarc=[(float(a.get("startAngle")), float(a.get("width"))/2) for a in A.iter("Arc")]
chk("A: arc gauges r 196, sweeps from 240 and 60",
    all(r==196 for _,r in aarc) and sorted({s for s,_ in aarc})==[60.0,240.0], str(aarc))
chk("A: arc fill clamped 0-1 (section 5)",
    len(re.findall(r'clamp\(\[(?:STEP|BATTERY)_PERCENT\] / 100, 0, 1\)', src))==3,
    str(len(re.findall(r'clamp\(', src))))
chk("C: no arc gauges - centre holds time only (section 6)", len(list(Cc.iter("Arc")))==0,
    f"{len(list(Cc.iter('Arc')))} arcs")

# rim angles
def mids(g):
    out={}
    for t in g.iter("TextCircular"):
        r=float(t.get("width"))/2; s,e=float(t.get("startAngle")),float(t.get("endAngle"))
        lbl=(list(t.iter("Font"))[0].text or "").strip()
        out.setdefault(lbl,(r,(s+e)/2 % 360, t.get("direction")))
    return out
ma, mc = mids(A), mids(Cc)
chk("A: rim ALM 315 / TMR 45 on r 198",
    ma.get("ALM",(0,0,0))[:2]==(198,315) and ma.get("TMR",(0,0,0))[:2]==(198,45), str(ma))
chk("A: arc readouts r 176 at 270 / 90",
    ma.get("STEPS",(0,0,0))[:2]==(176,270) and ma.get("BATT",(0,0,0))[:2]==(176,90), str(ma))
chk("C: four rim readouts r 198 at 315 / 45 / 225 / 135",
    all(mc.get(k,(0,0,0))[:2]==(198,v) for k,v in (("STP",315),("BAT",45),("ALM",225),("TMR",135))), str(mc))
chk("C: 225 and 135 use the reversed path (section 6)",
    mc.get("ALM",(0,0,""))[2]=="COUNTER_CLOCKWISE" and mc.get("TMR",(0,0,""))[2]=="COUNTER_CLOCKWISE",
    f"ALM={mc.get('ALM',('','',''))[2]} TMR={mc.get('TMR',('','',''))[2]}")

# ---------- tap targets (section 8) ----------
bad=[]
for p in root.iter():
    for l in p.findall("Launch"):
        try: x,y,w,h=box(p)
        except (TypeError,ValueError): bad.append(f"{p.tag} unbounded"); continue
        if w<44 or h<44: bad.append(f"{p.get('name')} {w}x{h} < 44")
        if (w,h)==(480,480): bad.append(f"{p.get('name')} captures the whole dial")
chk("every Launch sits on a bounded part of at least 44x44", not bad, str(bad))

# ---------- slot parity (section 10) ----------
sa={c.get("slotId") for c in A.iter("ComplicationSlot")}
sc={c.get("slotId") for c in Cc.iter("ComplicationSlot")}
chk("both layouts expose the same slot ids so assignments survive a switch",
    sa==sc=={"4","5","6"}, f"A={sorted(sa)} C={sorted(sc)}")

# ---------- palette ----------
TOK={"#ff0A0A0B","#ffF2F2F0","#ff8C8F93","#ff2A2D31","#ff3E4247","#ff6A6E73","#ff4A9EDB",
     "#ff8E9195","#ff5E6165","#ffE0A33A","#00000000"}
cols={c for c in re.findall(r'(?:color|tintColor|backgroundColor)="(#[0-9A-Fa-f]{6,8})"', src)}
chk("only Swiss + AOD + warn tokens used", cols<=TOK, f"stray={sorted(cols-TOK)}")

# ---------- ambient ----------
amb=grp("ambient")
chk("ambient group toggles alpha via Variant",
    amb.get("alpha")=="0" and any(v.get("mode")=="AMBIENT" and v.get("target")=="alpha"
                                  and v.get("value")=="255" for v in amb.findall("Variant")))
chk("both layouts and the status band go dark in ambient",
    all(any(v.get("mode")=="AMBIENT" and v.get("value")=="0" for v in g.findall("Variant"))
        for g in (A,Cc,grp("status_band"))))

# ---------- assets ----------
d=open(f"{DD}/preview.png","rb").read(33); w,h=struct.unpack('>II', d[16:24])
chk("preview.png is 480x480", (w,h)==(480,480), f"{w}x{h}")
for n in ("opt_layout_a","opt_layout_c"):
    dd=open(f"{DD}/{n}.png","rb").read(33); ow,oh=struct.unpack('>II', dd[16:24])
    chk(f"{n}.png <= 400x400 (editor icon limit)", ow<=400 and oh<=400, f"{ow}x{oh}")

fb=sum(os.path.getsize(p) for p in glob.glob(f"{FD}/*.ttf"))
db=sum(os.path.getsize(p) for p in glob.glob(f"{DD}/*.png"))
rows.append(f"INFO     assets: fonts {fb//1024} KiB, drawables {db//1024} KiB, "
            f"xml {os.path.getsize(WF)//1024} KiB")
print("\n".join(rows))
n=len(rows)-1
print(f"\n{n} checks: {n-len(FAIL)-len(UNK)} pass, {len(FAIL)} fail, {len(UNK)} unknown")
sys.exit(1 if FAIL else 0)
