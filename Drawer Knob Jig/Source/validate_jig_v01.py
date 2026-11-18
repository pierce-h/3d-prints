"""Slice the saved drawer jig and record material, nozzle and support checks."""
from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from build_jig_v01 import OUT, STEM

TEMP = Path('/tmp/drawer-knob-jig-v01')
BAMBU = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def slice_project():
    target = TEMP/'full'; target.mkdir(parents=True,exist_ok=True)
    with (TEMP/'slicing.log').open('w') as log:
        run = subprocess.run([BAMBU,'--datadir',str(TEMP/'profile'),'--debug','1',
            '--arrange','0','--orient','0','--slice','1','--export-3mf','sliced.3mf',
            '--outputdir',str(target),str(OUT/(STEM+'.3mf'))],stdout=log,stderr=subprocess.STDOUT)
    assert run.returncode == 0, TEMP/'slicing.log'
    result = json.loads((target/'result.json').read_text())
    assert result['return_code'] == 0
    assert len(result['sliced_plates']) == 1
    plate = result['sliced_plates'][0]
    assert not plate['warning_message'], plate['warning_message']
    assert len(plate['objects']) == 1
    assert len(plate['filaments']) == 1 and plate['filaments'][0]['filament_id'] == 'GFG01'
    with ZipFile(target/'sliced.3mf') as z:
        info = z.read('Metadata/slice_info.config'); root = ET.fromstring(info)
        nozzles = root.findall('plate/nozzle')
        assert len(nozzles) == 1 and nozzles[0].get('extruder_id') == '2'
        assert root.find('plate/filament').get('type') == 'PETG'
        gc = z.read(next(n for n in z.namelist() if n.endswith('.gcode'))).decode()
    assert '; FEATURE: Support' not in gc
    assert 'M140 S70' in gc and 'M104 S245' in gc
    dest = OUT/'Validation/full'; dest.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(target/'result.json',dest/'slicing.json')
    shutil.copyfile(TEMP/'slicing.log',dest/'slicing.log')
    (dest/'slice_info.config').write_bytes(info)
    summary = dict(project=STEM+'.3mf',return_code=0,warnings=plate['warning_message'],
                   seconds=plate['total_predication'],grams=plate['filaments'][0]['total_used_g'],
                   material='Bambu PETG Translucent',extruder='right / 2',support_toolpaths=False,
                   print_status='Prepared and sliced only; no print sent.')
    (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


def finalize():
    assert json.loads((OUT/'Validation/full/summary.json').read_text())['return_code'] == 0
    hashes = {str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in OUT.iterdir() if p.suffix in ('.3mf','.stl','.png')}
    (OUT/'Validation/archive_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--slice',action='store_true')
    parser.add_argument('--finalize',action='store_true')
    args = parser.parse_args()
    if args.slice: slice_project()
    if args.finalize: finalize()
