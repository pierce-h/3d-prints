"""Render exported cabinet-knob-jig meshes and a dimensioned placement diagram.

Previews use actual STL surfaces. Usage diagrams are labeled schematics,
showing one chosen corner per door, viewed from its front.
"""
from pathlib import Path
import sys
import math
import numpy as np
import trimesh
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Revisions/v01-corner-jig'
sys.path.insert(0,str(ROOT.parent/'Pliers Holder/Source'))
from render_previews import page,panel,paste_mesh,font,INK,MUTED,ACCENT

SIDE=31.75
END=63.5
FRAME=63.5
PLATE_W=70.
PLATE_H=90.
BORE=5.05
WOOD='#eee4d3'
PANEL='#faf7f1'
JIG='#a9c9d6'
JIG_LINE='#37697f'
ORANGE='#c47935'


def centered(d,xy,text,size=24,bold=False,fill=INK):
    x,y=xy; f=font(size,bold)
    d.text((x-d.textlength(text,font=f)/2,y),text,font=f,fill=fill)


def arrow(d,a,b,fill=ACCENT,width=3,head=10,both=False):
    a=np.array(a,float);b=np.array(b,float)
    d.line([tuple(a),tuple(b)],fill=fill,width=width)
    u=(b-a)/np.linalg.norm(b-a);v=np.array([-u[1],u[0]])
    def tip(p,sign):
        pts=[p,p-sign*u*head+v*head*.42,p-sign*u*head-v*head*.42]
        d.polygon([tuple(t) for t in pts],fill=fill)
    tip(b,1)
    if both:tip(a,-1)


def dashed(d,a,b,fill=MUTED,width=2,step=12):
    a=np.array(a,float);b=np.array(b,float)
    n=max(1,int(np.linalg.norm(b-a)/step))
    for i in range(0,n,2):
        d.line([tuple(a+(b-a)*i/n),tuple(a+(b-a)*min(i+1,n)/n)],fill=fill,width=width)


def cross(d,c,r=8,color=JIG_LINE):
    x,y=c;d.ellipse((x-r,y-r,x+r,y+r),fill='white',outline=color,width=3)
    d.line([(x-r-5,y),(x+r+5,y)],fill=color,width=2)
    d.line([(x,y-r-5),(x,y+r+5)],fill=color,width=2)


def actual_preview():
    a=trimesh.load(OUT/'Validation/Jig_A_Installed.stl',force='mesh')
    b=trimesh.load(OUT/'Validation/Jig_B_Installed.stl',force='mesh')
    # Proper rotation from build coordinates: the exposed drill face is Z=0.
    # Rotating 180 degrees around X shows that face without reflecting left/right.
    front_rotation=np.diag([1.,-1.,-1.,1.])
    a.apply_transform(front_rotation);b.apply_transform(front_rotation)
    im,d=page('Cabinet knob drilling jig',
              '1¼″ from the side  /  2½″ from the end  /  3⁄16″ drill bit',
              (1800,1220))
    for x,mesh,title,uses in [
        (55,a,'A — one identification groove','Top-left or bottom-right corner'),
        (925,b,'B — two identification grooves','Top-right or bottom-left corner')]:
        panel(d,(x,170,820,690),title)
        d.text((x+30,230),'Drill-entry side shown',font=font(25),fill=MUTED)
        paste_mesh(im,mesh,(x+60,280,700,450),eye=(.35,.65,1.7))
        centered(d,(x+410,765),uses,27,True,ACCENT)
        centered(d,(x+410,806),'The opposite face and edge stops sit against the door.',21,False,MUTED)
    panel(d,(55,890,1690,235),'Two mirrored jigs, one print plate')
    d.text((90,950),'The flat face between the stops rests against the door; the stops touch its outer edges.',
           font=font(29),fill=INK)
    d.text((90,1001),'Doors: ¾″–13⁄16″ thick  /  Edge stops: 10 mm deep  /  Printed guide: nominal 5.05 mm',
           font=font(27),fill=MUTED)
    d.text((90,1052),'Use one guide at the chosen corner. Printed guide fit and accuracy need a scrap test.',
           font=font(27),fill=MUTED)
    d.text((65,1160),'v01 · Actual CAD surfaces · All-plastic guide · Physical fit untested',font=font(24),fill=MUTED)
    im.save(OUT/'Preview.png')


def mini_door(d,box,corner,jig):
    x,y,w,h=box
    d.rounded_rectangle((x,y,x+w,y+h),6,fill=WOOD,outline='#b4a68e',width=2)
    s=.92
    f=FRAME*s
    d.rectangle((x+f,y+f,x+w-f,y+h-f),fill=PANEL,outline='#c8baa2',width=2)
    # Diagram scale intentionally enlarged around the frame corner, labeled schematic.
    sx=1 if 'left' in corner else -1
    sy=1 if 'top' in corner else -1
    ox=x if sx==1 else x+w
    oy=y if sy==1 else y+h
    jw,jh=PLATE_W*s,PLATE_H*s
    bx=(ox,ox+sx*jw);by=(oy,oy+sy*jh)
    d.rectangle((min(bx),min(by),max(bx),max(by)),fill=JIG,outline=JIG_LINE,width=3)
    d.line([(ox-sx*3,oy),(ox-sx*3,oy+sy*jh)],fill=JIG_LINE,width=6)
    d.line([(ox,oy-sy*3),(ox+sx*jw,oy-sy*3)],fill=JIG_LINE,width=6)
    hx=ox+sx*SIDE*s;hy=oy+sy*END*s
    cross(d,(hx,hy),6)
    centered(d,(x+w/2,y+h+15),f'Jig {jig} · {corner}',23,True,INK)


def usage_diagram():
    im,d=page('Where the knob hole goes',
              'Door-front view  /  Choose one corner, opposite the hinges',
              (1800,1510))
    panel(d,(55,170,820,1190),'Position on a 2½″ stile and rail')
    # Bottom-left example with precise drawn scale, millimetres→pixels.
    scale=3.1;ox,oy=250,1000
    left=ox;right=805;top=390;bottom=oy
    d.rectangle((left,top,right,bottom),fill=WOOD,outline='#b4a68e',width=3)
    inner_x=ox+FRAME*scale;inner_y=oy-FRAME*scale
    d.rectangle((inner_x,top,right,inner_y),fill=PANEL,outline='#c8baa2',width=2)
    d.text((472,429),'Recessed panel',font=font(25),fill=MUTED)
    centered(d,(347,520),'Stile',27,True,MUTED)
    centered(d,(632,879),'Rail',27,True,MUTED)
    # Accurate actual body footprint, door-contact side projection.
    body=(ox,oy-PLATE_H*scale,ox+PLATE_W*scale,oy)
    overlay=Image.new('RGBA',im.size,(0,0,0,0));od=ImageDraw.Draw(overlay)
    od.rectangle(body,fill=(90,145,170,55),outline=JIG_LINE,width=3)
    im.paste(overlay,(0,0),overlay)
    d=ImageDraw.Draw(im)
    d.line([(ox-6,oy-PLATE_H*scale),(ox-6,oy+6),(ox+PLATE_W*scale,oy+6)],fill=JIG_LINE,width=10)
    hx=ox+SIDE*scale;hy=oy-END*scale
    cross(d,(hx,hy),BORE*scale/2)
    dashed(d,(hx,hy),(hx,1060),ACCENT)
    dashed(d,(ox,hy),(hx,hy),ACCENT)
    d.line([(ox,1020),(ox,1100)],fill=MUTED,width=2)
    d.line([(hx,1020),(hx,1100)],fill=MUTED,width=2)
    arrow(d,(ox,1080),(hx,1080),both=True)
    centered(d,((ox+hx)/2,1110),'1¼″',31,True,ACCENT)
    centered(d,((ox+hx)/2,1152),'31.75 mm',23,False,MUTED)
    # Vertical dimension outside the jig.
    dx=159
    d.line([(dx-15,hy),(ox-12,hy)],fill=MUTED,width=2)
    d.line([(dx-15,oy),(ox-12,oy)],fill=MUTED,width=2)
    arrow(d,(dx,hy),(dx,oy),both=True)
    d.text((90,(hy+oy)/2-35),'2½″',font=font(29,True),fill=ACCENT)
    d.text((81,(hy+oy)/2+7),'63.5',font=font(23),fill=MUTED)
    d.text((94,(hy+oy)/2+35),'mm',font=font(22),fill=MUTED)
    # Hole callout and clamp location.
    arrow(d,(665,650),(hx+11,hy-11),fill=ACCENT)
    d.text((526,590),'Knob screw center',font=font(27,True),fill=INK)
    d.text((526,628),'3⁄16″ clearance drill',font=font(25),fill=MUTED)
    cx,cy=ox+30*scale,oy-22*scale
    d.ellipse((cx-20,cy-20,cx+20,cy+20),outline=ORANGE,width=3)
    arrow(d,(648,1187),(cx+10,cy+13),fill=ORANGE)
    d.text((488,1192),'Clamp over solid frame,',font=font(24),fill=ORANGE)
    d.text((488,1227),'clear of the drill path.',font=font(24),fill=ORANGE)
    d.text((90,1291),'Example shown: bottom-left corner, Jig B.',font=font(24),fill=MUTED)

    panel(d,(905,170,840,1190),'Which jig to use')
    centered(d,(1325,239),'Base cabinets — top corners',29,True,INK)
    mini_door(d,(1015,309,245,300),'top-left','A')
    mini_door(d,(1390,309,245,300),'top-right','B')
    centered(d,(1325,741),'Upper cabinets — bottom corners',29,True,INK)
    mini_door(d,(1015,811,245,300),'bottom-left','B')
    mini_door(d,(1390,811,245,300),'bottom-right','A')
    centered(d,(1325,1210),'Rotate a jig 180° for its opposite corner.',25,False,MUTED)
    centered(d,(1325,1252),'One hole per door — these are four alternatives.',25,True,INK)
    centered(d,(1325,1295),'Corner examples are schematic.',22,False,MUTED)
    d.text((65,1400),'Clamp the jig and a scrap backer. Check the location and drill fit on scrap before drilling a finished door.',
           font=font(25),fill=MUTED)
    d.text((65,1443),'The 1¼″ side offset assumes the stile is actually 2½″ wide.',font=font(25),fill=MUTED)
    im.save(OUT/'Placement_Diagram.png')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    actual_preview()
    usage_diagram()
    print(OUT/'Preview.png')
    print(OUT/'Placement_Diagram.png')

if __name__=='__main__':main()
