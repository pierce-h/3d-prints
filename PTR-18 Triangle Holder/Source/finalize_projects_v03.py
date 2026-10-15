"""Refresh Bambu previews and retain successful slicing results."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Revisions'/'v03-measured-attachments'
TEMP=Path('/tmp/ptr18-v03')

for name,stem,cam,preview in [
    ('main','PTR18_Hanger_v03_Measured_Attachments_TEST_FIT',11,'Print_Preview.png'),
    ('samples','PTR18_Fit_Check_Plate_v03',11,'Fit_Check_Preview.png'),
    ('pockets','Attachment_Pockets_Fit_v03',11,'Attachment_Pockets_Preview.png')]:
    result=json.loads((TEMP/name/'result.json').read_text())
    assert result['return_code']==0 and not result['sliced_plates'][0]['warning_message']
    png=(TEMP/('render-'+name)/('plate_1_'+str(cam)+'.png')).read_bytes()
    project=OUT/(stem+'.3mf')
    with ZipFile(project) as z: data={n:z.read(n) for n in z.namelist()}
    for n in ('Metadata/plate_1.png','Metadata/plate_no_light_1.png',
              'Metadata/plate_1_small.png','Auxiliaries/.thumbnails/thumbnail_3mf.png'):
        data[n]=png
    with ZipFile(project,'w',ZIP_DEFLATED) as z:
        for n,b in data.items():z.writestr(n,b)
    (OUT/preview).write_bytes(png)
    shutil.copyfile(TEMP/name/'result.json',OUT/'Validation'/('slicing_'+name+'.json'))
    shutil.copyfile(TEMP/(name+'.log'),OUT/'Validation'/('slicing_'+name+'.log'))
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()
        if p.suffix.lower() in ('.3mf','.stl','.png')}
(OUT/'Validation'/'archive_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('Project previews and slicing results saved.')
