"""Independent drawer-jig review of exports; does not import CAD builder code."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v01-single-edge'
VAL = OUT / 'Validation'
CORE = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'


def section(mesh, z):
    cut = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    polygons = list(polygonize([
        LineString(cut.vertices[entity.points, :2]) for entity in cut.entities
    ]))
    return max(polygons, key=lambda p: p.area)


def close(actual, expected, tol=1e-4):
    assert np.allclose(actual, expected, atol=tol, rtol=0), (actual, expected)


def main():
    geo = json.loads((VAL / 'geometry.json').read_text())
    mesh_path = VAL / 'Jig_Local.stl'
    mesh = trimesh.load(mesh_path, force='mesh')
    assert mesh.is_watertight and mesh.is_winding_consistent
    assert mesh.body_count == 1 and np.all(mesh.area_faces > 1e-9)
    close(mesh.bounds, [[0, -4, 0], [80, 55, 20]])
    hole_sections = []
    expected_notch = Polygon([(38.5, 55), (40, 52), (41.5, 55)])
    expected_outer = box(0, -4, 80, 55).difference(expected_notch)
    for z in (0.75, 2, 5, 9):
        face = section(mesh, z)
        assert len(face.interiors) == 1
        opening = Polygon(face.interiors[0])
        bounds = np.array(opening.bounds)
        center = (bounds[:2] + bounds[2:]) / 2
        diameter = bounds[2:] - bounds[:2]
        close(center, [40, 31.75])
        close(diameter, [5.05, 5.05])
        assert Polygon(face.exterior).symmetric_difference(expected_outer).area < 1e-5
        hole_sections.append(dict(z_mm=z, center_xy_mm=center.tolist(),
                                  diameter_xy_mm=diameter.tolist()))
    face = section(mesh, 0.25)
    voids = [Polygon(ring) for ring in face.interiors]
    assert len(voids) == 3
    guide = min(voids, key=lambda p: p.centroid.distance(Point(40, 31.75)))
    close(np.array(guide.bounds)[2:] - np.array(guide.bounds)[:2], [5.55, 5.55])
    grooves = sorted([p for p in voids if p is not guide], key=lambda p: p.bounds[1])
    for groove, y0, y1 in zip(grooves, (4, 36.5), (27, 52)):
        close(groove.bounds, [39.7, y0, 40.3, y1])
        close(groove.centroid.x, 40)
    # These loops prove the single top fence remains a rectangle at every
    # sampled stop height; there are no side fences on the drawer face.
    for z in (10.1, 15, 19.9):
        fence = section(mesh, z)
        assert fence.symmetric_difference(box(0, -4, 80, 0)).area < 1e-5
        assert fence.difference(section(mesh, 9)).area < 1e-5
    fence = section(mesh, 15)
    datum = fence.intersection(LineString([(40, -20), (40, 80)])).bounds[3]
    close(datum, 0)
    close(hole_sections[1]['center_xy_mm'][1] - datum, 31.75)
    assert mesh.bounds[1, 1] < 63.5
    contact_faces = mesh.triangles[np.all(np.isclose(mesh.triangles[:, :, 2], 10), axis=1)]
    assert len(contact_faces) > 0
    project = OUT / geo['project']
    with ZipFile(project) as z:
        assert z.testzip() is None
        root = ET.fromstring(z.read('3D/3dmodel.model'))
        objects = root.findall(f'{CORE}resources/{CORE}object')
        items = root.findall(f'{CORE}build/{CORE}item')
        assert len(objects) == len(items) == 1
        obj = objects[0]
        verts = [[float(v.get(c)) for c in 'xyz'] for v in obj.findall(f'{CORE}mesh/{CORE}vertices/{CORE}vertex')]
        faces = [[int(t.get(c)) for c in ('v1', 'v2', 'v3')] for t in obj.findall(f'{CORE}mesh/{CORE}triangles/{CORE}triangle')]
        model = trimesh.Trimesh(verts, faces, process=True)
        assert model.is_watertight and model.is_winding_consistent and model.body_count == 1
        close(model.bounds, mesh.bounds)
        close(model.volume, mesh.volume, tol=0.01)
        values = np.array(list(map(float, items[0].get('transform').split())))
        transform = np.eye(4); transform[:3, :3] = values[:9].reshape(3, 3).T
        transform[:3, 3] = values[9:]
        close(transform[:3, :3], np.eye(3))
        close(transform, geo['print_transform'])
        placed = model.copy(); placed.apply_transform(transform)
        close(placed.bounds, [[130, 130.5, 0], [210, 189.5, 20]])
        exported = trimesh.load(OUT / (project.stem + '.stl'), force='mesh')
        close(placed.bounds, exported.bounds)
        close(placed.volume, exported.volume, tol=0.01)
        settings = json.loads(z.read('Metadata/project_settings.config'))
        assert settings['enable_support'] == '0'
        assert settings['printer_model'] == 'Bambu Lab H2D'
        assert settings['filament_map'] == ['2'] and settings['filament_map_mode'] == 'Manual'
        assert settings['master_extruder_id'] == '2' and settings['filament_type'] == ['PETG']
        brim = float(settings['brim_width'])
        conservative_bounds = placed.bounds[:, :2] + np.array([[-brim, -brim], [brim, brim]])
        assert np.all(conservative_bounds[0] >= [25, 0])
        assert np.all(conservative_bounds[1] <= [350, 310])
    job = Path('/tmp/drawer-knob-jig-v01/full/sliced.3mf')
    with ZipFile(job) as z:
        gcode = z.read(next(n for n in z.namelist() if n.endswith('.gcode')))
        assert b'; FEATURE: Support' not in gcode
        info = ET.fromstring(z.read('Metadata/slice_info.config'))
        nozzles = info.findall('plate/nozzle')
        assert len(nozzles) == 1 and nozzles[0].get('extruder_id') == '2'
        assert info.find('plate/filament').get('type') == 'PETG'
    summary = json.loads((VAL / 'full/summary.json').read_text())
    assert summary['return_code'] == 0 and not summary['warnings']
    report = dict(result='PASS',
                  method='Independent cross-sections of exported STL and direct 3MF/build-transform inspection; no CAD-builder import.',
                  mesh=dict(watertight=True, connected_bodies=1, bounds_local_mm=mesh.bounds.tolist(),
                            sha256=hashlib.sha256(mesh_path.read_bytes()).hexdigest()),
                  guide=dict(sections=hole_sections, offset_from_top_edge_mm=31.75,
                             straight_diameter_mm=5.05, intended_drill_bit_mm=4.7625,
                             plate_thickness_mm=10, straight_guide_length_mm=9.5,
                             entry_chamfer_depth_mm=0.5),
                  registration=dict(top_edge_datum_y_mm=0, top_fences=1, side_fences=0,
                                    fence_bounds_local_mm=[[0, -4, 10], [80, 0, 20]],
                                    drawer_contact_z_mm=10, stop_depth_mm=10),
                  horizontal_alignment=dict(notch_apex_xy_mm=[40, 52], notch_width_mm=3, notch_depth_mm=3,
                                            groove_x_mm=40, groove_width_mm=0.6, groove_depth_mm=0.5,
                                            groove_y_ranges_mm=[[4, 27], [36.5, 52]],
                                            all_align_with_guide_center=True,
                                            user_action='Align with a pencil line marking the drawer horizontal midpoint.'),
                  rail_fit=dict(user_confirmed_height_mm=63.5, contact_footprint_depth_mm=55,
                                clearance_before_recessed_panel_mm=8.5),
                  print=dict(printer='H2D', physical_nozzle='right / 2', material='PETG',
                             profile=settings['filament_settings_id'][0], supports=False,
                             slice_warnings=summary['warnings'], model_bounds_mm=placed.bounds.tolist(),
                             model_plus_brim_xy_bounds_mm=conservative_bounds.tolist(),
                             project_contains_one_object=True,
                             small_recesses='Narrow 0.6 mm engraved-line roofs bridge without support.'),
                  gcode_sha256=hashlib.sha256(gcode).hexdigest(),
                  limits=['Drawer jig has not been physically tested.',
                          'Horizontal placement depends on the user pencil centerline.',
                          'Printed guide fit, rail fit and finished-door placement should be checked before drilling.'])
    (VAL / 'independent_review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(result=report['result'], guide_center=[40, 31.75],
                         top_fences=1, side_fences=0, notch_apex=[40, 52],
                         supports=False, material='PETG', physical_nozzle='right / 2'), indent=2))


if __name__ == '__main__':
    main()
