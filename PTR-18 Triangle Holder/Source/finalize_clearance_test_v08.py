"""Render the actual v08 CAD, refresh project thumbnails, and save slice evidence."""
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
OUT = ROOT / 'Revisions/v08-clearance-test'
TEMP = Path('/tmp/ptr18-v08')
MAIN = 'PTR18_Attachment_Clearance_Test_v08_PETG_Right'
BAMBU = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def run_render(project, label, camera):
    dest = TEMP / ('render-' + label)
    dest.mkdir(parents=True, exist_ok=True)
    command = [BAMBU, '--datadir', str(TEMP / (label + '-profile')), '--debug', '1',
               '--arrange', '0', '--orient', '0', '--export-png', '1',
               '--camera-view', str(camera), '--outputdir', str(dest), str(project)]
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
    for label in ('A_Plus2mm', 'B_Plus3mm'):
        mesh = trimesh.load(OUT / 'Validation' / (label + '_installed.stl'), force='mesh')
        center = mesh.bounds.mean(axis=0)
        # Display the pocket mouths facing upward. Printable orientation stays sideways.
        pose = np.array([[1, 0, 0, 175-center[0]], [0, 0, -1, 155+center[2]],
                         [0, 1, 0, -mesh.bounds[0, 1]], [0, 0, 0, 1]], float)
        project = TEMP / (label + '-display.3mf')
        write_project(project, [(label, mesh, pose)], settings, 'CAD display only; not print orientation.')
        png = run_render(project, label, 0)
        im = Image.open(png).convert('RGBA')
        views.append(im.crop(im.getbbox()))
    return print_image, views


def preview(views):
    canvas = Image.new('RGB', (1400, 900), '#f3f5f7')
    d = ImageDraw.Draw(canvas)
    def font(size, bold=False):
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'
                                  + (' Bold' if bold else '') + '.ttf', size)
    d.text((45, 30), 'PTR-18 attachment fit test', font=font(40, True), fill='#19384a')
    d.text((47, 87), 'Try the hardware in these samples before another full holder.',
           font=font(24), fill='#526875')
    cards = [('A  |  2 mm larger', 'One corner notch', 'Pin pockets: 11.8 mm', 'Screw pocket: 8.8 mm'),
             ('B  |  3 mm larger', 'Two corner notches', 'Pin pockets: 12.8 mm', 'Screw pocket: 9.8 mm')]
    for x, im, labels in zip((45, 725), views, cards):
        d.rounded_rectangle((x, 145, x+630, 700), radius=18, fill='white')
        d.text((x+25, 165), labels[0], font=font(30, True), fill='#254454')
        d.text((x+25, 207), labels[1], font=font(23), fill='#526875')
        scale = min(565/im.width, 320/im.height)
        im = im.resize((round(im.width*scale), round(im.height*scale)), Image.Resampling.LANCZOS)
        canvas.paste(im, (x+(630-im.width)//2, 258+(320-im.height)//2), im)
        d.text((x+25, 605), labels[2], font=font(26, True), fill='#254454')
        d.text((x+25, 646), labels[3], font=font(24), fill='#526875')
    d.text((50, 735), 'Each sample: short-pin pocket / tall-pin pocket / small-screw pocket',
           font=font(25, True), fill='#254454')
    d.text((50, 777), 'Pocket depths: 8 / 16 / 2.5 mm. Insert the bodies first, with threads up.',
           font=font(23), fill='#526875')
    d.text((50, 819), 'Prints on its side, matching the full holder. PETG Matte / right nozzle / 0.20 mm.',
           font=font(22), fill='#526875')
    d.text((50, 861), 'Blue shows the CAD clearly; the saved print uses black filament. Physical fit is untested.',
           font=font(19), fill='#526875')
    canvas.save(OUT / 'Preview.png')


def finalize(print_image):
    result = json.loads((TEMP / 'slice/result.json').read_text())
    assert result['return_code'] == 0 and not result['sliced_plates'][0]['warning_message']
    plate = result['sliced_plates'][0]
    assert len(plate['filaments']) == 1 and plate['filaments'][0]['id'] == 4
    with ZipFile(TEMP / 'slice/sliced.3mf') as z:
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
    for src, dest in [('slice/result.json', 'slicing.json'), ('slice.log', 'slicing.log')]:
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
