"""Render the actual v09 CAD, refresh project thumbnails, and save slice evidence."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

from build_holder import write_project

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v09-enlarged-deeper-pockets'
TEMP = Path('/tmp/ptr18-v09')
MAIN = 'PTR18_Hanger_v09_Enlarged_Deeper_Pockets_PETG_Right_TEST_FIT'
BAMBU = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def run_render(project, label, camera, rotation=None):
    dest = TEMP / ('render-' + label)
    dest.mkdir(parents=True, exist_ok=True)
    command = [BAMBU, '--datadir', str(TEMP / (label + '-profile')), '--debug', '1',
               '--arrange', '0', '--orient', '0', '--export-png', '1',
               '--camera-view', str(camera), '--outputdir', str(dest), str(project)]
    if rotation is not None:
        command[-1:-1] = ['--rotate-x', str(rotation), '--ensure-on-bed']
    with (TEMP / (label + '.log')).open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    return dest / ('plate_1_' + str(camera) + '.png')


def render():
    with ZipFile(OUT / (MAIN + '.3mf')) as z:
        archive = {n: z.read(n) for n in z.namelist()}
    settings = json.loads(archive['Metadata/project_settings.config'])
    settings['filament_colour'] = ['#8BBAD2'] * len(settings['filament_colour'])
    archive['Metadata/project_settings.config'] = json.dumps(settings).encode()
    display = TEMP / 'print-display.3mf'
    with ZipFile(display, 'w', ZIP_DEFLATED) as z:
        for name, data in archive.items():
            z.writestr(name, data)
    print_image = run_render(display, 'print', 11)
    views = []
    mesh = trimesh.load(OUT / 'Validation' / (MAIN + '_installed.stl'), force='mesh')
    pose = np.array([[1,0,0,175], [0,0,-1,187.25], [0,1,0,57], [0,0,0,1]], float)
    project = TEMP / 'installed-display.3mf'
    write_project(project, [('Display only', mesh, pose)], settings,
                  'Wall-mounted CAD display only; not a print project.')
    for label, rotation in [('storage', 0), ('underside', -30)]:
        png = run_render(project, label, 0, rotation)
        im = Image.open(png).convert('RGBA')
        views.append(im.crop(im.getbbox()))
    return print_image, views


def preview(views):
    canvas = Image.new('RGB', (1400, 850), '#f3f5f7')
    d = ImageDraw.Draw(canvas)
    def font(size, bold=False):
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'
                                  + (' Bold' if bold else '') + '.ttf', size)
    d.text((45, 30), 'PTR-18+ French cleat holder', font=font(40, True), fill='#19384a')
    d.text((47, 87), 'Revision 09  |  Accepted pocket sizes, deeper screw storage',
           font=font(24), fill='#526875')
    for x, im, title in zip((45, 725), views, ('Storage shelf', 'Support and closed pocket bottoms')):
        d.rounded_rectangle((x, 145, x+630, 655), radius=18, fill='white')
        d.text((x+25, 168), title, font=font(25, True), fill='#254454')
        scale = min(565/im.width, 400/im.height)
        im = im.resize((round(im.width*scale), round(im.height*scale)), Image.Resampling.LANCZOS)
        canvas.paste(im, (x+(630-im.width)//2, 225+(400-im.height)//2), im)
    d.text((50, 685), '4 pin pockets: 11.8 mm diameter', font=font(25, True), fill='#254454')
    d.text((50, 725), 'Original 8 / 16 mm depths retained', font=font(23), fill='#526875')
    d.text((735, 685), '6 screw pockets: 8.8 mm diameter', font=font(25, True), fill='#254454')
    d.text((735, 725), 'Now 6 mm deep; heads sit 2 mm below top', font=font(23), fill='#526875')
    d.text((50, 790), 'New depth untested. Blue is for visibility; the saved project uses black PETG on the right nozzle.',
           font=font(21), fill='#526875')
    canvas.save(OUT / 'Mounted_Preview.png')


def finalize(print_image):
    result = json.loads((TEMP / 'main/result.json').read_text())
    assert result['return_code'] == 0 and not result['sliced_plates'][0]['warning_message']
    plate = result['sliced_plates'][0]
    assert len(plate['filaments']) == 1 and plate['filaments'][0]['id'] == 4
    with ZipFile(TEMP / 'main/sliced.3mf') as z:
        sliced = {n: z.read(n) for n in z.namelist()}
    info = ET.fromstring(sliced['Metadata/slice_info.config'])
    assert info.find('plate/nozzle').get('extruder_id') == '2'
    png = print_image.read_bytes()
    project = OUT / (MAIN + '.3mf')
    with ZipFile(project) as z:
        archive = {n: z.read(n) for n in z.namelist()}
    for name in ('Metadata/plate_1.png', 'Metadata/plate_no_light_1.png',
                 'Metadata/plate_1_small.png', 'Auxiliaries/.thumbnails/thumbnail_3mf.png'):
        archive[name] = png
    for name in ('Metadata/top_1.png', 'Metadata/pick_1.png'):
        if name in sliced:
            archive[name] = sliced[name]
    with ZipFile(project, 'w', ZIP_DEFLATED) as z:
        for name, data in archive.items():
            z.writestr(name, data)
    (OUT / 'Print_Preview.png').write_bytes(png)
    for src, dest in [('main/result.json', 'slicing.json'), ('main.log', 'slicing.log')]:
        shutil.copyfile(TEMP / src, OUT / 'Validation' / dest)
    (OUT / 'Validation/slice_info.config').write_bytes(sliced['Metadata/slice_info.config'])
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()
              if p.suffix in ('.3mf', '.stl', '.png')}
    (OUT / 'Validation/archive_hashes.json').write_text(json.dumps(hashes, indent=2)+'\n')
    geometry_file = OUT / 'Validation/geometry.json'
    geometry = json.loads(geometry_file.read_text())
    geometry['project_sha256'] = hashes[project.name]
    geometry_file.write_text(json.dumps(geometry, indent=2)+'\n')
    print(json.dumps(dict(total_seconds=plate['total_predication'],
                         filament_g=plate['filaments'][0]['total_used_g'],
                         nozzle='right', warnings=plate['warning_message']), indent=2))


if __name__ == '__main__':
    print_image, views = render()
    preview(views)
    finalize(print_image)
