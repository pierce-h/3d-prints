"""Independent exported-mesh checks; does not import the CAD builder."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v01-corner-jig'
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
    expected_corners = {'A': ['bottom-right', 'top-left'],
                        'B': ['bottom-left', 'top-right']}
    parts = {}
    meshes = {}
    for kind in ('A', 'B'):
        path = VAL / f'Jig_{kind}_Installed.stl'
        mesh = trimesh.load(path, force='mesh')
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert mesh.body_count == 1 and np.all(mesh.area_faces > 1e-9)
        close(mesh.extents, [74, 94, 20])
        meshes[kind] = mesh
        holes = []
        for z in (2, 5, 9):
            face = section(mesh, z)
            assert len(face.interiors) == 1
            opening = Polygon(face.interiors[0])
            bounds = np.array(opening.bounds)
            center = (bounds[:2] + bounds[2:]) / 2
            diameter = bounds[2:] - bounds[:2]
            close(center, [31.75 if kind == 'A' else 38.25, 63.5])
            close(diameter, [5.05, 5.05])
            holes.append(dict(z_mm=z, center_xy_mm=center.tolist(),
                              diameter_xy_mm=diameter.tolist()))
        center = np.array(holes[1]['center_xy_mm'])
        fences = section(mesh, 15)
        side = fences.intersection(LineString([(-20, center[1]), (100, center[1])]))
        end = fences.intersection(LineString([(center[0], -20), (center[0], 110)]))
        side_datum = side.bounds[2] if kind == 'A' else side.bounds[0]
        end_datum = end.bounds[3]
        close(side_datum, 0 if kind == 'A' else 70)
        close(end_datum, 0)
        close(abs(center[0] - side_datum), 31.75)
        close(center[1] - end_datum, 63.5)
        # Registration stops are supported directly on the broad printed plate.
        assert fences.difference(section(mesh, 9)).area < 1e-5
        close(section(mesh, 10.1).symmetric_difference(section(mesh, 19.9)).area, 0)
        # Contact face is Z=10, stop tips Z=20, so there is no door-thickness channel.
        faces = mesh.triangles[np.all(np.isclose(mesh.triangles[:, :, 2], 10), axis=1)]
        assert len(faces) > 0
        detail = next(p for p in geo['parts'] if p['name'] == kind)
        assert detail['door_corners'] == expected_corners[kind]
        transform = np.asarray(detail['print_transform'])
        close(transform[:3, :3], np.eye(3))
        placed = mesh.copy(); placed.apply_transform(transform)
        close(placed.bounds, detail['print_bounds'])
        assert np.all(placed.bounds[0] >= [3, 3, -1e-6])
        assert np.all(placed.bounds[1] <= [322, 307, 320])
        parts[kind] = dict(watertight=True, connected_bodies=1,
                           mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           bounds_mm=mesh.bounds.tolist(),
                           guide_sections=holes, side_offset_mm=31.75, end_offset_mm=63.5,
                           measured_side_datum_x_mm=float(side_datum),
                           measured_end_datum_y_mm=float(end_datum),
                           door_contact_z_mm=10, stop_depth_mm=10,
                           front_view_corners=expected_corners[kind],
                           identification='one groove' if kind == 'A' else 'two grooves')
    for z in (2, 5, 9, 15):
        reflected = affinity.scale(section(meshes['A'], z), xfact=-1, yfact=1, origin=(35, 0))
        assert reflected.symmetric_difference(section(meshes['B'], z)).area < 1e-3
    # The intentional second identification groove accounts for B's smaller volume.
    close(meshes['A'].volume - meshes['B'].volume, 9.6, tol=1e-3)
    project = OUT / geo['project']
    with ZipFile(project) as z:
        assert z.testzip() is None
        root = ET.fromstring(z.read('3D/3dmodel.model'))
        objects = root.findall(f'{CORE}resources/{CORE}object')
        assert len(objects) == 2 and len(root.findall(f'{CORE}build/{CORE}item')) == 2
        for kind, obj in zip(('A', 'B'), objects):
            verts = [[float(v.get(c)) for c in 'xyz'] for v in obj.findall(f'{CORE}mesh/{CORE}vertices/{CORE}vertex')]
            faces = [[int(t.get(c)) for c in ('v1', 'v2', 'v3')] for t in obj.findall(f'{CORE}mesh/{CORE}triangles/{CORE}triangle')]
            model = trimesh.Trimesh(verts, faces, process=True)
            assert model.is_watertight and model.body_count == 1
            close(model.bounds, meshes[kind].bounds)
            close(model.volume, meshes[kind].volume, tol=0.01)
        settings = json.loads(z.read('Metadata/project_settings.config'))
        assert settings['enable_support'] == '0'
        assert settings['filament_map'] == ['1'] and settings['filament_map_mode'] == 'Manual'
    job = Path('/tmp/cabinet-knob-jig-v01/full/sliced.3mf')
    with ZipFile(job) as z:
        gcode = z.read(next(n for n in z.namelist() if n.endswith('.gcode')))
        assert b'; FEATURE: Support' not in gcode
    summary = json.loads((VAL / 'full/summary.json').read_text())
    assert summary['return_code'] == 0 and not summary['warnings']
    report = dict(result='PASS', method='Independent sections of exported STL and direct 3MF inspection; no CAD-builder import.',
                  parts=parts,
                  mirror_geometry='A and B are mirrors except the intentional second identification groove on B.',
                  handedness_proof='Exposed drill face Z=0 faces the viewer. A proper 180-degree rotation about Y gives screen X=-model X and screen Y=model Y. A registers at bottom-right; B at bottom-left. In-plane 180-degree rotation gives the opposite upper corners.',
                  other_checks=dict(guide_axis_straight=True, one_hole_per_jig=True,
                                    printed_plate_thickness_mm=10, straight_guide_length_mm=9.5,
                                    entry_chamfer_depth_mm=0.5, support_toolpaths=False,
                                    print_orientation='Broad exposed face Z=0 on bed; stops rise upward',
                                    small_identification_recesses='2 mm-wide blind grooves require only short bridging over their roofs',
                                    both_parts_on_one_plate=True, printer='H2D', material='PLA', extruder='left'),
                  gcode_sha256=hashlib.sha256(gcode).hexdigest(),
                  limits=['Printed guide fit, accuracy and wear are not physically tested.',
                          'Proposed offsets should be checked on the actual door before drilling.',
                          'Printed hole diameter is 5.05 mm; the intended wood-drilling bit is 3/16 in (4.7625 mm).'])
    (VAL / 'independent_review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(result=report['result'], parts={k:v['front_view_corners'] for k,v in parts.items()},
                         support_toolpaths=False), indent=2))


if __name__ == '__main__':
    main()
