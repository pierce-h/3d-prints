"""Actual mesh preview of the continuous two-socket cabinet mount."""
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import sys
import trimesh
from build_mount_v02 import ROOT,OUT,STEM
sys.path.insert(0,str(ROOT.parent/'Pliers Holder/Source'))
from render_previews import page,panel,paste_mesh,font,INK,MUTED,ACCENT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--embed',action='store_true')
    args=parser.parse_args()
    mesh=trimesh.load(OUT/'Validation/Mount_Installed.stl',force='mesh')
    im,d=page('Shark accessory mount — one piece',
        'One shared backplate  /  Two unchanged drop-in sockets  /  Two cabinet screws',
        (1800,1160))
    panel(d,(55,175,1690,530),'Continuous backplate joins both receivers')
    paste_mesh(im,mesh,(100,245,1600,385),eye=(.22,1.,1.4))
    d.text((95,650),'171 mm wide × 51.2 mm high × 51 mm deep',font=font(28,True),fill=ACCENT)
    panel(d,(55,735,1000,295),'Top view')
    paste_mesh(im,mesh,(85,794,940,195),eye=(.03,2.6,.3))
    panel(d,(1085,735,660,295),'Same socket spacing as v01')
    for y,line in [(809,'100 mm between socket centers'),(858,'153 mm between screw centers'),(907,'6.5 mm thick shared backplate')]:
        d.text((1120,y),line,font=font(26),fill=INK)
    d.text((65,1067),'v02 · Actual CAD geometry · Illustrative color · Accessory fit and spacing pending physical check',font=font(23),fill=MUTED)
    d.text((65,1106),'Receivers adapted from jverlenich’s IP1251 holder · CC BY-NC-SA 4.0',font=font(23),fill=MUTED)
    im.save(OUT/'Preview.png')
    if args.embed:
        path=OUT/(STEM+'.3mf')
        with ZipFile(path) as z:data={n:z.read(n) for n in z.namelist()}
        for n in ('Metadata/plate_1.png','Metadata/plate_no_light_1.png','Metadata/plate_1_small.png','Auxiliaries/.thumbnails/thumbnail_3mf.png'):
            data[n]=(OUT/'Preview.png').read_bytes()
        with ZipFile(path,'w',ZIP_DEFLATED) as z:
            for n,b in data.items():z.writestr(n,b)
    print(OUT/'Preview.png')


if __name__=='__main__':main()
