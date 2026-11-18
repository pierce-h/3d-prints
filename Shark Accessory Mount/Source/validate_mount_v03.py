"""Check the saved clear-PETG/right-nozzle slice without sending a print."""
from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from build_mount_v03 import OUT,STEM

TEMP=Path('/tmp/shark-accessory-v03')
BAMBU='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def slice_project():
    target=TEMP/'full';target.mkdir(parents=True,exist_ok=True)
    with (target/'slicing.log').open('w') as log:
        run=subprocess.run([BAMBU,'--datadir',str(TEMP/'profile'),'--debug','1','--arrange','0',
            '--orient','0','--slice','1','--export-3mf','sliced.3mf','--outputdir',str(target),str(OUT/(STEM+'.3mf'))],stdout=log,stderr=subprocess.STDOUT)
    assert run.returncode==0,target/'slicing.log'
    result=json.loads((target/'result.json').read_text())
    assert result['return_code']==0 and len(result['sliced_plates'])==1
    plate=result['sliced_plates'][0]
    assert not plate['warning_message'] and len(plate['objects'])==1
    assert len(plate['filaments'])==1 and plate['filaments'][0]['filament_id']=='GFG01'
    with ZipFile(target/'sliced.3mf') as z:
        info=z.read('Metadata/slice_info.config');root=ET.fromstring(info)
        nozzles=root.findall('plate/nozzle')
        assert len(nozzles)==1 and nozzles[0].get('extruder_id')=='2'
        assert root.find('plate/filament').get('type')=='PETG'
        gc=z.read(next(n for n in z.namelist() if n.endswith('.gcode'))).decode()
    assert '; FEATURE: Support' not in gc
    assert 'M140 S70' in gc and 'M104 S245' in gc
    dest=OUT/'Validation/full';dest.mkdir(parents=True,exist_ok=True)
    for name in ('result.json','slicing.log'):
        shutil.copyfile(target/name,dest/('slicing.json' if name=='result.json' else name))
    (dest/'slice_info.config').write_bytes(info)
    summary=dict(project=STEM+'.3mf',return_code=0,warnings=plate['warning_message'],
        seconds=plate['total_predication'],grams=plate['filaments'][0]['total_used_g'],
        material='Bambu PETG Translucent, clear',extruder='right / 2',objects=1,support_toolpaths=False,
        print_status='Prepared and sliced only; no print sent.')
    (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--slice',action='store_true')
    parser.add_argument('--finalize',action='store_true')
    args=parser.parse_args()
    if args.slice:slice_project()
    if args.finalize:
        assert json.loads((OUT/'Validation/full/summary.json').read_text())['return_code']==0
        (OUT/'Validation/archive_hashes.json').write_text(json.dumps({STEM+'.3mf':hashlib.sha256((OUT/(STEM+'.3mf')).read_bytes()).hexdigest()},indent=2)+'\n')
