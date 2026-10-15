"""Render the actual revised CAD, refresh thumbnails, and archive the Bambu slice."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
import hashlib, json, shutil, subprocess
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Revisions/v01-32mm-center'
TEMP=Path('/tmp/caliper-edit')
NAME='Caliper_Holder_v01_32mm_Center'
BAMBU='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
ET.register_namespace('', NS['m'])
ET.register_namespace('p', 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06')

def render():
    with ZipFile(OUT/(NAME+'.3mf')) as z: archive={n:z.read(n) for n in z.namelist()}
    settings=json.loads(archive['Metadata/project_settings.config'])
    settings['filament_colour']=['#8BBAD2']
    archive['Metadata/project_settings.config']=json.dumps(settings).encode()
    for label,cam in [('print',11),('mounted',0)]:
        data=archive.copy()
        if label=='mounted':
            root=ET.fromstring(data['3D/3dmodel.model'])
            # Rigid display rotation only. Saved printable orientation is unaffected.
            root.find('m:build/m:item',NS).set('transform','0 -1 0 0 0 1 -1 0 0 175 160 47.5')
            data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        project=TEMP/(label+'-preview.3mf')
        with ZipFile(project,'w',ZIP_DEFLATED) as z:
            for n,b in data.items():z.writestr(n,b)
        dest=TEMP/('render-'+label);dest.mkdir(parents=True,exist_ok=True)
        cmd=[BAMBU,'--datadir',str(TEMP/('render-'+label+'-profile')),'--debug','1',
             '--arrange','0','--orient','0','--export-png','1','--camera-view',str(cam),
             '--outputdir',str(dest),str(project)]
        with (TEMP/('render-'+label+'.log')).open('w') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)

def preview():
    im=Image.open(TEMP/'render-mounted/plate_1_0.png').convert('RGBA')
    im=im.crop(im.getbbox())
    canvas=Image.new('RGB',(1320,810),'#f3f5f7');d=ImageDraw.Draw(canvas)
    def font(n,bold=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',n)
    d.text((45,32),'Caliper holder | 32 mm center opening',font=font(37,True),fill='#19384a')
    d.text((47,89),'Sized for your approximately 30 mm digital-caliper body',font=font(23),fill='#526875')
    for x,title in [(40,'Revised model'),(690,'Front detail')]:
        d.rounded_rectangle((x,145,x+590,650),radius=18,fill='white')
        d.text((x+25,165),title,font=font(25,True),fill='#254454')
    scale=min(490/im.width,400/im.height)
    im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    canvas.paste(im,(40+(590-im.width)//2,225+(400-im.height)//2),im)
    # Orthographic front detail, projected directly from the final mesh.
    mesh=trimesh.load(OUT/'Validation/widened_local.stl',force='mesh')
    scale=5.7;cx=985;cy=414
    def p(v):return (cx-v[2]*scale,cy-v[1]*scale)
    d.rectangle((cx-40*scale,cy-30*scale,cx+40*scale,cy+31*scale),fill='#d4e3ea')
    for tri in mesh.triangles:
        if tri[:,0].min()>=6.99999 and tri[:,0].max()>7.00001:
            d.polygon([p(v) for v in tri],fill='#79a5ba')
    geom=json.loads((OUT/'Validation/geometry.json').read_text())
    z0,z1=geom['new_inner_edges_z_mm'];x0=cx-z1*scale;x1=cx-z0*scale;y=cy+89
    d.line((x0,cy+17,x0,y+13),fill='#254454',width=2)
    d.line((x1,cy+17,x1,y+13),fill='#254454',width=2)
    d.line((x0,y,x1,y),fill='#254454',width=3)
    d.polygon([(x0,y),(x0+10,y-6),(x0+10,y+6)],fill='#254454')
    d.polygon([(x1,y),(x1-10,y-6),(x1-10,y+6)],fill='#254454')
    label='32 mm';bounds=d.textbbox((0,0),label,font=font(28,True));w=bounds[2]-bounds[0]
    d.text(((x0+x1-w)/2,y+19),label,font=font(28,True),fill='#19384a')
    d.text((55,686),'Before: 28.92 mm   →   Now: 32 mm',font=font(27,True),fill='#254454')
    d.text((55,730),'About 1 mm clearance per side. Backplate and French cleat unchanged.',font=font(23),fill='#526875')
    d.text((55,773),'Revision v01 | Physical fit of the revised opening is untested.',font=font(18),fill='#526875')
    canvas.save(OUT/'Preview.png')

def finalize():
    result=json.loads((TEMP/'slice/result.json').read_text())
    assert result['return_code']==0 and not result['sliced_plates'][0]['warning_message']
    png=(TEMP/'render-print/plate_1_11.png').read_bytes()
    project=OUT/(NAME+'.3mf')
    with ZipFile(project) as z:data={n:z.read(n) for n in z.namelist()}
    with ZipFile(TEMP/'slice/sliced.3mf') as z:
        for n in ('Metadata/top_1.png','Metadata/pick_1.png'):
            if n in z.namelist():data[n]=z.read(n)
    for n in list(data):
        if n.endswith('.png') and n not in ('Metadata/top_1.png','Metadata/pick_1.png'):data[n]=png
    # Older project photos remain in the archived original, not the revised model.
    for n in list(data):
        if n.startswith(('Auxiliaries/Model Pictures/','Auxiliaries/Profile Pictures/')):del data[n]
    with ZipFile(project,'w',ZIP_DEFLATED) as z:
        for n,b in data.items():z.writestr(n,b)
    (OUT/'Print_Preview.png').write_bytes(png)
    shutil.copyfile(TEMP/'slice/result.json',OUT/'Validation/slicing.json')
    shutil.copyfile(TEMP/'slice.log',OUT/'Validation/slicing.log')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ('.3mf','.stl','.png')}
    (OUT/'Validation/archive_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print('CAD previews and successful slicing result saved.')

if __name__=='__main__':
    render();preview();finalize()
