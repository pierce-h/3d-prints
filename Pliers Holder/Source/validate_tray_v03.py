"""Validate upright tray slices and embed final actual-CAD previews."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from build_tray_v03 import OUT, STEMS

TEMP=Path('/tmp/pliers-v03')
BAMBU='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def slice_project(label):
    target=TEMP/label;target.mkdir(parents=True,exist_ok=True)
    with (TEMP/(label+'.log')).open('w') as log:
        run=subprocess.run([BAMBU,'--datadir',str(TEMP/(label+'-profile')),'--debug','1',
            '--arrange','0','--orient','0','--slice','1','--export-3mf','sliced.3mf',
            '--outputdir',str(target),str(OUT/(STEMS[label]+'.3mf'))],stdout=log,stderr=subprocess.STDOUT)
    assert run.returncode==0,f'Slice failed: {TEMP/(label+".log")}'
    result=json.loads((target/'result.json').read_text());assert result['return_code']==0
    plate=result['sliced_plates'][0];assert not plate['warning_message'],plate['warning_message']
    assert len(plate['filaments'])==1 and plate['filaments'][0]['id']==1
    with ZipFile(target/'sliced.3mf') as z:
        info=z.read('Metadata/slice_info.config');root=ET.fromstring(info)
        nozzles=root.findall('plate/nozzle');assert len(nozzles)==1 and nozzles[0].get('extruder_id')=='1'
        assert root.find('plate/filament').get('type')=='PLA'
        gc=z.read(next(n for n in z.namelist() if n.endswith('.gcode'))).decode()
    support_present='; FEATURE: Support' in gc
    if label=='sample':assert not support_present
    else:assert support_present,'Expected support below rear cleats'
    dest=OUT/'Validation'/label;dest.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(target/'result.json',dest/'slicing.json')
    shutil.copyfile(TEMP/(label+'.log'),dest/'slicing.log')
    (dest/'slice_info.config').write_bytes(info)
    summary=dict(project=STEMS[label]+'.3mf',return_code=0,warnings=plate['warning_message'],
                 seconds=plate['total_predication'],grams=plate['filaments'][0]['total_used_g'],
                 material='Bambu PLA Basic',extruder='left / 1',support_toolpaths=support_present)
    (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


def finalize():
    for label,stem in STEMS.items():
        summary=json.loads((OUT/f'Validation/{label}/summary.json').read_text())
        assert summary['return_code']==0
        name='Fit_Sample_Preview.png' if label=='sample' else 'Print_Preview.png' if label=='full' else 'Section_Preview.png'
        png=(OUT/name).read_bytes();path=OUT/(stem+'.3mf')
        with ZipFile(path) as z:data={n:z.read(n) for n in z.namelist()}
        for key in ['Metadata/plate_1.png','Metadata/plate_no_light_1.png','Metadata/plate_1_small.png',
                    'Auxiliaries/.thumbnails/thumbnail_3mf.png']:data[key]=png
        with ZipFile(path,'w',ZIP_DEFLATED) as z:
            for key,value in data.items():z.writestr(key,value)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ('.3mf','.stl','.png')}
    (OUT/'Validation/archive_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--slice',choices=list(STEMS)+['all']);parser.add_argument('--finalize',action='store_true')
    args=parser.parse_args()
    if args.slice:
        for label in STEMS if args.slice=='all' else [args.slice]:slice_project(label)
    if args.finalize:finalize()
