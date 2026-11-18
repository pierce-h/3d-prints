"""Render the actual cabinet-mount mesh; color is illustrative."""
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import sys
import trimesh
from build_mount_v01 import ROOT, OUT, STEM
sys.path.insert(0, str(ROOT.parent/'Pliers Holder/Source'))
from render_previews import page, panel, paste_mesh, font, INK, MUTED, ACCENT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--embed',action='store_true')
    args=parser.parse_args()
    mesh=trimesh.load(OUT/'Validation/Mount_Installed.stl',force='mesh')
    second=mesh.copy();second.apply_translation((100,0,0))
    pair=trimesh.util.concatenate((mesh,second))
    im,d=page('Shark accessory cabinet mounts',
        'Two separate holders  /  Drop-in sockets  /  Choose the spacing to suit your cabinet',
        (1800,1250))
    panel(d,(55,175,1690,520),'Two identical holders — viewed from above and in front')
    paste_mesh(im,pair,(100,245,1600,385),eye=(.24,1.0,1.4))
    d.text((95,642),'Each: 71 mm wide × 51.2 mm high × 51 mm deep',font=font(28,True),fill=ACCENT)
    panel(d,(55,725,820,375),'Keyed socket opening')
    paste_mesh(im,mesh,(85,785,760,250),eye=(.05,2.6,.4))
    d.text((90,1053),'Original PowerDetect receiver geometry retained',font=font(23),fill=MUTED)
    panel(d,(905,725,840,375),'Cabinet attachment')
    d.text((940,803),'Two countersunk screw holes per holder',font=font(29,True),fill=INK)
    d.text((940,859),'53 mm between screw centers',font=font(27),fill=MUTED)
    d.text((940,911),'6.5 mm backing with a flat cabinet face',font=font(27),fill=MUTED)
    d.text((940,963),'Print one holder first to check accessory fit.',font=font(26),fill=ACCENT)
    d.text((65,1141),'v01 · Actual CAD geometry · Illustrative color · IP3251 physical fit pending',font=font(24),fill=MUTED)
    d.text((65,1184),'Receiver adapted from jverlenich’s IP1251 holder · CC BY-NC-SA 4.0',font=font(23),fill=MUTED)
    im.save(OUT/'Preview.png')
    single,d=page('One holder for the first fit check',
        'Same complete holder as the pair  /  Two cabinet screws  /  PLA, left nozzle',(1400,1000))
    panel(d,(55,175,1290,660),'Actual CAD geometry')
    paste_mesh(single,mesh,(110,245,1180,505),eye=(.25,1.0,1.4))
    d.text((90,780),'71 × 51.2 × 51 mm overall',font=font(28,True),fill=ACCENT)
    d.text((65,878),'v01 · IP3251 physical fit pending · No print sent',font=font(25),fill=MUTED)
    d.text((65,928),'Receiver: jverlenich · Modified cabinet backing · CC BY-NC-SA 4.0',font=font(23),fill=MUTED)
    single.save(OUT/'Single_Preview.png')
    if args.embed:
        for name,png in [(STEM,'Preview.png'),('Shark_Accessory_Mount_v01_Single_PLA_Left_TEST_FIT','Single_Preview.png')]:
            path=OUT/(name+'.3mf')
            with ZipFile(path) as z:data={n:z.read(n) for n in z.namelist()}
            for key in ('Metadata/plate_1.png','Metadata/plate_no_light_1.png','Metadata/plate_1_small.png','Auxiliaries/.thumbnails/thumbnail_3mf.png'):
                data[key]=(OUT/png).read_bytes()
            with ZipFile(path,'w',ZIP_DEFLATED) as z:
                for n,b in data.items():z.writestr(n,b)
    print(OUT/'Preview.png')


if __name__=='__main__':main()
