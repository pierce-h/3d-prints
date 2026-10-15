"""v08: two small PETG attachment-pocket clearance tests.

Installed coordinates remain X along the shelf, Y up, Z toward the user.
The same side transform as the full hanger makes every pocket horizontal
during printing.  These tests do not change the full hanger.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np

from build_holder import CORE, box, cylinder_y, mesh_of, side_transform, union, write_project


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Revisions/v07-petg-matte-right-nozzle/PTR18_Hanger_v07_PETG_Matte_Right_TEST_FIT.3mf'
OUT = ROOT / 'Revisions/v08-clearance-test'
MAIN = 'PTR18_Attachment_Clearance_Test_v08_PETG_Right'
BANKS = [('A_Plus2mm', 2., 1, (155., 155.)),
         ('B_Plus3mm', 3., 2, (195., 155.))]


def bank_solid(increase, notch_count):
    positions = [
        dict(type='short pin', x=0., z=0., diameter=9.8 + increase, depth=8.),
        dict(type='tall pin', x=24., z=0., diameter=9.8 + increase, depth=16.),
        dict(type='small screw', x=48., z=0., diameter=6.8 + increase, depth=2.5),
    ]
    # The shelf matches the v04 test sample and the full holder's thickness.
    parts = [box((-12., 59., -12.), (60., 65., 12.))]
    for p in positions:
        if p['depth'] > 4:
            parts.append(cylinder_y(p['x'], p['z'], p['diameter'] + 6.,
                                    65. - p['depth'] - 3., 65.))
    # A two-millimetre-thick end foot gives a flat 19 x 24 mm bed contact
    # in the unchanged side print pose, without intersecting any cavity.
    parts.append(box((-12., 46., -12.), (-10., 65., 12.)))
    cavities = [cylinder_y(p['x'], p['z'], p['diameter'],
                           65. - p['depth'], 66.) for p in positions]
    # One or two opposite corner notches at the screw-pocket end identify
    # the bank after printing.  Each notch is 3 x 2 mm through the shelf.
    notches = [box((57., 58.9, 10.), (61., 65.1, 13.))]
    if notch_count == 2:
        notches.append(box((57., 58.9, -13.), (61., 65.1, -10.)))
    return union(parts) - union(cavities + notches), positions


def verify_bank(solid, positions):
    mesh = mesh_of(solid)
    assert solid.status() == mf.Error.NoError
    assert len(solid.decompose()) == 1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    section = mesh.section(plane_normal=[0, 1, 0], plane_origin=[0, 64., 0])
    openings = []
    for points in section.discrete:
        bounds = np.array([points.min(axis=0), points.max(axis=0)])
        width = np.ptp(bounds, axis=0)
        if width[0] < 14. and width[2] < 14.:
            openings.append(dict(center_XZ_mm=bounds.mean(axis=0)[[0, 2]].tolist(),
                                 diameter_XZ_mm=width[[0, 2]].tolist()))
    assert len(openings) == 3
    probes = []
    for p in positions:
        found = [o for o in openings if np.allclose(o['center_XZ_mm'], [p['x'], p['z']], atol=1e-6)]
        assert len(found) == 1 and np.allclose(found[0]['diameter_XZ_mm'], p['diameter'], atol=1e-6)
        floor_y = 65. - p['depth']
        cavity_probe = cylinder_y(p['x'], p['z'], p['diameter'] - .02, floor_y + .01, 65.1)
        floor_probe = cylinder_y(p['x'], p['z'], p['diameter'] - .02, floor_y - .5, floor_y - .01)
        blocked = float((solid ^ cavity_probe).volume())
        missing_floor = float((floor_probe - solid).volume())
        assert abs(blocked) < 1e-6 and abs(missing_floor) < 1e-6
        probes.append(dict(**p, floor_y_mm=floor_y,
                           floor_thickness_mm=3. if p['depth'] > 4. else 3.5,
                           cavity_obstruction_mm3=blocked,
                           missing_floor_probe_mm3=missing_floor))
    return mesh, openings, probes


def patch_project(path, extra_members):
    with ZipFile(path) as z:
        members = {n: z.read(n) for n in z.namelist()}
    ET.register_namespace('', CORE)
    root = ET.fromstring(members['3D/3dmodel.model'])
    for meta in root.findall(f'{{{CORE}}}metadata'):
        if meta.get('name') == 'CreationDate':
            meta.text = '2026-10-15'
    members['3D/3dmodel.model'] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    config = ET.fromstring(members['Metadata/model_settings.config'])
    for obj in config.findall('object'):
        obj.find("metadata[@key='extruder']").set('value', '4')
    plate = config.find('plate')
    ET.SubElement(plate, 'metadata', key='filament_maps', value='1 1 1 2')
    ET.SubElement(plate, 'metadata', key='filament_volume_maps', value='0 0 0 0')
    members['Metadata/model_settings.config'] = ET.tostring(config, encoding='utf-8', xml_declaration=True)
    members.update(extra_members)
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        for name, data in members.items():
            z.writestr(name, data)


def main():
    validation = OUT / 'Validation'
    validation.mkdir(parents=True, exist_ok=True)
    with ZipFile(BASE) as z:
        original_settings = json.loads(z.read('Metadata/project_settings.config'))
        extras = {n: z.read(n) for n in z.namelist()
                  if n.startswith('Metadata/filament_settings_') and n.endswith('.config')}
    settings = json.loads(json.dumps(original_settings))
    settings['outer_wall_speed'] = ['100' for _ in settings['outer_wall_speed']]
    settings['layer_height'] = '0.2'
    # Match the existing explicit plate override at global level too.
    settings['filament_map'] = ['1', '1', '1', '2']
    diff = list(settings['different_settings_to_system'])
    diff[0] = ';'.join(sorted(set(filter(None, diff[0].split(';'))) | {'outer_wall_speed'}))
    settings['different_settings_to_system'] = diff
    assert settings['filament_settings_id'][3] == 'Bambu PETG Matte @BBL H2D 0.4 nozzle'
    assert settings['filament_colour'][3] == '#000000'
    assert settings['physical_extruder_map'] == original_settings['physical_extruder_map']

    report = dict(
        revision='v08 clearance test; full holder unchanged',
        status='UNPRINTED: choose clearance by testing actual hardware body-first, threads up.',
        reference_project=str(BASE.relative_to(ROOT)),
        reference_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
        dimensions_mm=dict(shelf_length=72, shelf_width=24, shelf_thickness=6,
                           maximum_depth_with_boss=19, print_height=72,
                           flat_bed_contact=[19, 24], base_foot_thickness=2),
        hole_axis_installed=[0, 1, 0], hole_axis_print=[1, 0, 0],
        print_orientation='Same side transform as v07 full holder; holes horizontal.',
        settings_changes_from_v07={k: dict(before=original_settings.get(k), after=v)
                                  for k, v in settings.items() if original_settings.get(k) != v},
        filament=dict(slot=4, material=settings['filament_settings_id'][3],
                      color=settings['filament_colour'][3],
                      plate_mapping='1 1 1 2', physical_extruder_map=settings['physical_extruder_map'],
                      nozzle='right, as mapped by v07'),
        parts={})
    objects = []
    for name, increase, notch_count, center in BANKS:
        solid, positions = bank_solid(increase, notch_count)
        mesh, openings, probes = verify_bank(solid, positions)
        transform = side_transform(mesh, center)
        placed = mesh.copy()
        placed.apply_transform(transform)
        assert np.allclose(placed.bounds[0][2], 0.)
        assert np.all(placed.bounds[0] >= [25, 5, -1e-6])
        assert np.all(placed.bounds[1] <= [325, 305, 350])
        assert np.allclose(placed.extents, [19, 24, 72])
        mesh.export(validation / (name + '_installed.stl'), file_type='stl_ascii')
        placed.export(OUT / (name + '.stl'), file_type='stl_ascii')
        objects.append((name, mesh, transform))
        report['parts'][name] = dict(
            diameter_increase_mm=increase, notch_count=notch_count,
            notch_description='3 x 2 mm corner cuts through 6 mm shelf at screw-pocket end; '
                              + ('one +Z corner' if notch_count == 1 else 'both +/-Z corners'),
            notch_installed_X_range_mm=[57, 60],
            notch_installed_Z_ranges_mm=[[10, 12]] if notch_count == 1 else [[10, 12], [-12, -10]],
            pockets=probes, section_openings=openings,
            bounds_installed=mesh.bounds.tolist(), bounds_print=placed.bounds.tolist(),
            transform=transform.tolist(), volume_mm3=float(mesh.volume),
            triangles=len(mesh.faces), watertight=bool(mesh.is_watertight), bodies=int(mesh.body_count))
    path = OUT / (MAIN + '.3mf')
    write_project(path, objects, settings,
                  'Two small horizontal-hole fit banks for PTR-18 attachments: A (one corner notch) '
                  'increases original diameters by 2 mm; B (two corner notches) by 3 mm. '
                  'Short/tall/screw pocket depths remain 8/16/2.5 mm. Black PETG Matte, right nozzle, '
                  '0.20 mm layers, 100 mm/s outer walls. Full holder is unchanged.')
    patch_project(path, extras)
    with ZipFile(path) as z:
        assert z.testzip() is None
        cfg = ET.fromstring(z.read('Metadata/model_settings.config'))
        assert all(o.find("metadata[@key='extruder']").get('value') == '4' for o in cfg.findall('object'))
        assert cfg.find("plate/metadata[@key='filament_maps']").get('value') == '1 1 1 2'
        assert json.loads(z.read('Metadata/project_settings.config')) == settings
    report['project'] = path.name
    report['project_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (validation / 'geometry.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(project=str(path), parts={name: dict(
        diameters=[p['diameter'] for p in item['pockets']],
        depths=[p['depth'] for p in item['pockets']],
        print_bounds=item['bounds_print'], notch_count=item['notch_count'])
        for name, item in report['parts'].items()}), indent=2))


if __name__ == '__main__':
    main()
