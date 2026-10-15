"""Refresh previews after running flatten_front.py and the Bambu CLI checks."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
import hashlib
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions' / 'v01-plain-front'
TEMP = Path('/tmp/tso-plain')
NAME = 'TSO_Tool_Holder_v01_Plain_Front'


def main():
    result = json.loads((TEMP / 'slice' / 'result.json').read_text())
    assert result['return_code'] == 0 and not result['sliced_plates'][0]['warning_message']
    png = (TEMP / 'render' / 'plate_1_10.png').read_bytes()
    webp = BytesIO()
    Image.open(BytesIO(png)).save(webp, format='WEBP', lossless=True)
    project = OUT / (NAME + '.3mf')
    with ZipFile(project) as z:
        archive = {n: z.read(n) for n in z.namelist()}
    # Bambu-generated selection/top views correspond to the final geometry.
    with ZipFile(TEMP / 'slice' / 'sliced.3mf') as z:
        for n in ('Metadata/top_1.png', 'Metadata/pick_1.png'):
            if n in z.namelist():
                archive[n] = z.read(n)
    for n in list(archive):
        if n.endswith('.png') and n not in ('Metadata/top_1.png', 'Metadata/pick_1.png'):
            archive[n] = png
        elif n.startswith('Auxiliaries/') and n.endswith('.webp'):
            archive[n] = webp.getvalue()
    with ZipFile(project, 'w', ZIP_DEFLATED) as z:
        for n, value in archive.items():
            z.writestr(n, value)
    (OUT / 'Preview.png').write_bytes(png)
    shutil.copyfile(TEMP / 'slice' / 'result.json', OUT / 'Validation' / 'slicing.json')
    shutil.copyfile(TEMP / 'slice.log', OUT / 'Validation' / 'slicing.log')
    shutil.copyfile(TEMP / 'render.log', OUT / 'Validation' / 'render.log')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (project, OUT / (NAME + '.stl'), OUT / 'Preview.png')}
    (OUT / 'Validation' / 'archive_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print('Final project previews and successful slice report saved.')


if __name__ == '__main__':
    main()
