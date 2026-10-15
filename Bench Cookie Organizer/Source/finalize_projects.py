"""Render current projects, refresh archive thumbnails, and collect slice checks.

Run build_welded_holder.py first. Slice main and spacer projects separately
with the Bambu Studio CLI (no --export-png in a --slice invocation).
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions' / 'v01-welded'
CLI = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def main():
    with tempfile.TemporaryDirectory(prefix='bench-cookie-preview-') as tempdir:
        temp = Path(tempdir)
        for stem, preview, slices in [
            ('Bench_Cookie_Organizer_v01_Welded','Preview.png','/tmp/bench-weld-slice'),
            ('Rear_Spacers_4x_v01','Rear_Spacers_Preview.png','/tmp/bench-spacers-slice')]:
            path = OUT / (stem+'.3mf')
            with ZipFile(path) as z:
                data = {n:z.read(n) for n in z.namelist()}
            display = dict(data)
            settings = json.loads(display['Metadata/project_settings.config'])
            settings['filament_colour'] = ['#8BBAD2']
            display['Metadata/project_settings.config'] = json.dumps(settings).encode()
            src = temp / (stem+'.3mf')
            with ZipFile(src,'w',ZIP_DEFLATED) as z:
                for n, v in display.items(): z.writestr(n,v)
            render = temp / stem
            render.mkdir()
            result = subprocess.run([CLI,'--datadir',str(temp/(stem+'-profile')),
                '--debug','1','--arrange','0','--orient','0','--export-png','1',
                '--camera-view','0','--outputdir',str(render),str(src)],
                capture_output=True,text=True,check=True)
            png = (render/'plate_1_0.png').read_bytes()
            (OUT/preview).write_bytes(png)
            data['Metadata/plate_1.png'] = png
            data['Metadata/plate_1_small.png'] = png
            data['Metadata/plate_no_light_1.png'] = png
            data['Auxiliaries/.thumbnails/thumbnail_3mf.png'] = png
            # Package-level thumbnail relation for viewers and recent-file lists.
            rel = ET.fromstring(data['_rels/.rels'])
            ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
            ET.register_namespace('', ns)
            if not any(e.get('Id') == 'rel-thumbnail' for e in rel):
                ET.SubElement(rel, '{'+ns+'}Relationship',
                    Target='/Metadata/plate_1.png', Id='rel-thumbnail',
                    Type='http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail')
            data['_rels/.rels'] = ET.tostring(rel, encoding='utf-8',xml_declaration=True)
            with ZipFile(path,'w',ZIP_DEFLATED) as z:
                for n,v in data.items():z.writestr(n,v)
            report = json.loads((Path(slices)/'result.json').read_text())
            assert report['return_code'] == 0, report
            suffix = 'holder' if stem.startswith('Bench_') else 'spacers'
            shutil.copyfile(Path(slices)/'result.json',OUT/'Validation'/f'slicing_{suffix}.json')
            (OUT/'Validation'/f'render_{suffix}.log').write_text(result.stdout+result.stderr)
            print(stem, 'rendered and slice success confirmed')


if __name__ == '__main__':
    main()
