"""Render actual CAD with Bambu Studio and arrange two mounting views."""
from pathlib import Path
from zipfile import ZipFile
import json
import subprocess
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from build_holder import write_project

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v06-essential-storage'
TEMP = Path('/tmp/ptr18-v06')
BAMBU = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
with ZipFile(OUT/'PTR18_Hanger_v06_Essential_Storage_TEST_FIT.3mf') as z:
    settings = json.loads(z.read('Metadata/project_settings.config'))
settings['filament_colour'] = ['#8BBAD2'] * len(settings['filament_colour'])
mesh = trimesh.load(OUT/'Validation/PTR18_Hanger_v06_Essential_Storage_TEST_FIT_installed.stl', force='mesh')
pose = np.array([[1,0,0,175], [0,0,-1,187.25], [0,1,0,57], [0,0,0,1]],float)
display = TEMP/'installed-preview.3mf'
write_project(display, [('Display only', mesh, pose)], settings, 'Display pose; not a print project.')
views = []
for label, rotation in [('overview', 0), ('hook', -30)]:
    target = TEMP/('mounted-'+label)
    target.mkdir(parents=True, exist_ok=True)
    cmd = [BAMBU, '--datadir', str(TEMP/('mounted-profile-'+label)), '--debug', '1',
           '--arrange','0','--orient','0','--rotate-x',str(rotation),'--ensure-on-bed',
           '--export-png','1','--camera-view','0','--outputdir',str(target),str(display)]
    with (TEMP/('mounted-'+label+'.log')).open('w') as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
    im = Image.open(target/'plate_1_0.png').convert('RGBA')
    views.append(im.crop(im.getbbox()))

canvas = Image.new('RGB',(1400,850),'#f3f5f7')
draw = ImageDraw.Draw(canvas)
font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
bold_path = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(size,bold=False): return ImageFont.truetype(bold_path if bold else font_path,size)
draw.text((55,35),'PTR-18+ French cleat holder',font=font(42,True),fill='#19384a')
draw.text((57,92),'Revision 06  |  Cutout hook and drop-in storage',font=font(23),fill='#526875')
for im,x,title in zip(views,(50,725),('Storage shelf','Triangle support')):
    draw.rounded_rectangle((x,155,x+625,655),radius=18,fill='white')
    draw.text((x+26,175),title,font=font(25,True),fill='#254454')
    scale=min(565/im.width,385/im.height)
    im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    canvas.paste(im,(x+(625-im.width)//2,240+(385-im.height)//2),im)
draw.text((60,695),'Only the ten measured attachments',font=font(25,True),fill='#254454')
draw.text((60,735),'2 tall pins + 2 short pins + 6 screws + Allen key',font=font(23),fill='#526875')
draw.text((735,695),'Broad hook supports the cutout',font=font(25,True),fill='#254454')
draw.text((735,735),'Fence channel sized for 430 x 20 x 10 mm',font=font(23),fill='#526875')
draw.text((60,800),'Print the fit samples first. Physical fit and loaded strength are unverified.',font=font(21),fill='#526875')
canvas.save(OUT/'Mounted_Preview.png')
