"""Save v01 geometry with its left (hole-bank) end on the build plate.

Run orientation trial slices first under /tmp/bench-orientation-comparison.
No mesh or print settings are changed in the 3MF; only placement and labels.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
V01 = ROOT / 'Revisions' / 'v01-welded'
OUT = ROOT / 'Revisions' / 'v02-side-print'
TRIAL = Path('/tmp/bench-orientation-comparison')
NAME = 'Bench_Cookie_Organizer_v02_Side_Print'
OLD_NAME = 'Bench_Cookie_Organizer_v01_Welded'
CORE = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
MATRIX = np.array([[0, 0, 1, 200.5], [1, 0, 0, 115],
                   [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)


def main():
    validation = OUT / 'Validation'
    validation.mkdir(parents=True, exist_ok=True)
    with ZipFile(V01 / (OLD_NAME + '.3mf')) as z:
        data = {n: z.read(n) for n in z.namelist()}
    original_model = data['3D/3dmodel.model']
    original_settings = data['Metadata/project_settings.config']
    model = original_model.decode()
    transform = ' '.join('%.12g' % v for v in
                         np.r_[MATRIX[:3, :3].T.ravel(), MATRIX[:3, 3]])
    model, n = re.subn(r'(<build><item objectid="1" transform=")[^"]+',
                       lambda m: m[1] + transform, model)
    assert n == 1
    model = model.replace(OLD_NAME, NAME)
    data['3D/3dmodel.model'] = model.encode()
    data['Metadata/model_settings.config'] = data['Metadata/model_settings.config'].replace(
        OLD_NAME.encode(), NAME.encode())
    png = (TRIAL / 'y0-down' / 'render' / 'plate_1_11.png').read_bytes()
    for name in ('Metadata/plate_1.png', 'Metadata/plate_1_small.png',
                 'Metadata/plate_no_light_1.png', 'Auxiliaries/.thumbnails/thumbnail_3mf.png'):
        data[name] = png
    project = OUT / (NAME + '.3mf')
    with ZipFile(project, 'w', ZIP_DEFLATED) as z:
        for name, value in data.items():
            z.writestr(name, value)
    (OUT / 'Preview.png').write_bytes(png)

    original = trimesh.load(V01 / 'Validation' / 'holder_installed.stl',
                            force='mesh', process=False)
    mesh = original.copy()
    mesh.apply_transform(MATRIX)
    mesh.export(OUT / (NAME + '.stl'), file_type='stl_ascii')
    reread = trimesh.load(OUT / (NAME + '.stl'), force='mesh')
    assert reread.is_watertight and reread.is_winding_consistent and reread.body_count == 1
    assert np.allclose(reread.bounds, [[74.5, 97, 0], [275.5, 213, 222]])
    with ZipFile(project) as z:
        root = ET.fromstring(z.read('3D/3dmodel.model'))
        original_root = ET.fromstring(original_model)
        assert ET.tostring(root.find('.//m:mesh', CORE)) == ET.tostring(
            original_root.find('.//m:mesh', CORE))
        assert z.read('Metadata/project_settings.config') == original_settings
        assert len(root.findall('.//m:object', CORE)) == 1

    comparison = {}
    for label, path in (
        ('upright', V01 / 'Validation' / 'slicing_holder.json'),
        ('left_hole_bank_end_down', TRIAL / 'y0-down' / 'result.json'),
        ('right_open_bay_end_down', TRIAL / 'y222-down' / 'result.json')):
        result = json.loads(path.read_text())
        assert result['return_code'] == 0
        plate = result['sliced_plates'][0]
        assert not plate['warning_message']
        comparison[label] = dict(seconds=plate['total_predication'],
            total_filament_g=plate['filaments'][0]['total_used_g'],
            support_and_interface_seconds=sum(plate['feature_type_times'].get(k, 0)
                for k in ('Support', 'Support interface')))
        shutil.copyfile(path, validation / ('slicing_' + label + '.json'))
    report = dict(status='Geometry unchanged; all three orientations slice successfully. Physical print untested.',
        selected='left_hole_bank_end_down', transformation=MATRIX.tolist(),
        print_bounds_mm=reread.bounds.tolist(), installed_dimensions_width_depth_height_mm=[222, 116, 201],
        geometry_identical_to_v01=True, process_settings_identical_to_v01=True,
        watertight=bool(reread.is_watertight), consistent_winding=bool(reread.is_winding_consistent),
        connected_bodies=reread.body_count, comparison=comparison)
    (validation / 'orientation_comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (project, OUT / (NAME + '.stl'), OUT / 'Preview.png')}
    (validation / 'archive_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
