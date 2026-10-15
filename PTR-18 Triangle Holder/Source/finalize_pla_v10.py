"""Archive the successful PLA slice, its material mapping, and artifact hashes."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from prepare_pla_v10 import OUT, MAIN

TEMP = Path('/tmp/ptr18-v10')
result = json.loads((TEMP / 'main/result.json').read_text())
assert result['return_code'] == 0
plate = result['sliced_plates'][0]
assert not plate['warning_message']
assert len(plate['filaments']) == 1 and plate['filaments'][0]['id'] == 1
with ZipFile(TEMP / 'main/sliced.3mf') as z:
    info = z.read('Metadata/slice_info.config')
    root = ET.fromstring(info)
    assert root.find('plate/nozzle').get('extruder_id') == '2'
    gcode_name = next(n for n in z.namelist() if n.endswith('.gcode'))
    gcode = z.read(gcode_name).decode()
assert '; filament_type = PLA' in gcode
for src, dest in [('main/result.json', 'slicing.json'), ('main.log', 'slicing.log')]:
    shutil.copyfile(TEMP / src, OUT / 'Validation' / dest)
(OUT / 'Validation/slice_info.config').write_bytes(info)
settings = json.loads((OUT / 'Validation/settings.json').read_text())
settings['slicing'] = {
    'return_code': result['return_code'],
    'plate_warnings': plate['warning_message'],
    'active_filament_ids': [p['id'] for p in plate['filaments']],
    'extruder_id': '2',
    'gcode_filament_type_verified': 'PLA',
    'total_seconds': plate['total_predication'],
    'total_used_g': plate['filaments'][0]['total_used_g'],
}
(OUT / 'Validation/settings.json').write_text(json.dumps(settings, indent=2) + '\n')
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()
          if p.suffix in ('.3mf', '.stl', '.png')}
(OUT / 'Validation/archive_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
print(json.dumps(settings['slicing'], indent=2))
