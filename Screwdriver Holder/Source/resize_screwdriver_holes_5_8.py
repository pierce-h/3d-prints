"""Rebuild the selected screwdriver openings with an exact 5/8-inch diameter.

Default: change the four left positions on both shelves to straight bores.
--max-everywhere also reduces the six other upper recesses to the same diameter,
while preserving their original smaller through-bores and recess centers/depths.
Dependencies: numpy, trimesh, manifold3d.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import manifold3d as mf
import numpy as np
import trimesh

from enlarge_screwdriver_holes import ROOT, SOURCE, MEMBER, NS, SEGMENTS, fit_ring

DIAMETER = 25.4 * 5 / 8


def cylinder(center, z0, z1, radius):
    return mf.Manifold.cylinder(z1 - z0, radius, circular_segments=SEGMENTS).translate(
        (float(center[0]), float(center[1]), z0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-everywhere', action='store_true')
    args = parser.parse_args()
    name = ('Screwdriver_Holder_5-8in_Max' if args.max_everywhere
            else 'Screwdriver_Holder_v02_5-8in_Holes')
    output_dir = ROOT / 'Revisions' / ('unpublished-max-5-8-inch' if args.max_everywhere
                                     else 'v02-left-holes-5-8-inch')
    (output_dir / 'Validation').mkdir(parents=True, exist_ok=True)
    destination = output_dir / (name + '.3mf')
    original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with ZipFile(SOURCE) as archive:
        entries = archive.infolist()
        original = {e.filename: archive.read(e.filename) for e in entries}
    tree = ET.fromstring(original[MEMBER])
    vertices = np.array([[float(e.get(k)) for k in ('x', 'y', 'z')]
                         for e in tree.findall('.//m:vertex', NS)])
    faces = np.array([[int(e.get(k)) for k in ('v1', 'v2', 'v3')]
                      for e in tree.findall('.//m:triangle', NS)])
    source_mesh = trimesh.Trimesh(vertices, faces, process=False)
    source_solid = mf.Manifold(mf.Mesh64(vertices, faces.astype(np.uint64)))
    assert source_solid.status() == mf.Error.NoError
    floor = float(vertices[np.argmin(abs(vertices[:, 2] - 38.2125)), 2])
    top = float(vertices[:, 2].max())
    fillers, cutters, changes = [], [], []
    for x in (-80., -40., 0., 40., 80.):
        for y in (-28.5025, 10.5015):
            selected = x < -20
            if not selected and not args.max_everywhere:
                continue
            recess_center, recess_diameter = fit_ring(vertices, floor, (x+.5, y-.5), 10.502)
            fillers.append(cylinder(recess_center, floor, top, 11.))
            changes.append(dict(feature='fill original upper recess', center_mm=recess_center.tolist(),
                                original_diameter_mm=recess_diameter, z_mm=[floor, top]))
            if selected:
                for label, ring_z, z0, z1 in (
                    ('lower straight bore', -12.5004997, -12.61, -7.39),
                    ('upper straight bore', 32.4995003, 32.39, top+.1),
                ):
                    center, old_diameter = fit_ring(vertices, ring_z, (x, y), 5.)
                    cutters.append(cylinder(center, z0, z1, DIAMETER / 2))
                    changes.append(dict(feature=label, center_mm=center.tolist(), diameter_mm=DIAMETER,
                                        original_through_diameter_mm=old_diameter, z_mm=[z0, z1]))
            else:
                cutters.append(cylinder(recess_center, floor, top+.1, DIAMETER / 2))
                changes.append(dict(feature='reduced upper recess', center_mm=recess_center.tolist(),
                                    diameter_mm=DIAMETER, z_mm=[floor, top]))
    filled = mf.Manifold.batch_boolean([source_solid] + fillers, mf.OpType.Add)
    result = mf.Manifold.batch_boolean([filled] + cutters, mf.OpType.Subtract)
    assert result.status() == mf.Error.NoError
    rendered = result.to_mesh64()
    mesh = trimesh.Trimesh(np.array(rendered.vert_properties)[:, :3],
                           np.array(rendered.tri_verts), process=False)
    assert mesh.is_watertight and mesh.is_winding_consistent
    assert mesh.body_count == 1 and mesh.euler_number == source_mesh.euler_number
    assert np.allclose(mesh.bounds, source_mesh.bounds, atol=1e-7)
    assert np.min(mesh.area_faces) > 1e-10
    added = result - source_solid
    removed = source_solid - result
    # Boolean envelope checks prevent any additions/removals outside the intended features.
    assert (added - mf.Manifold.batch_boolean(fillers, mf.OpType.Add)).volume() < 1e-6
    assert (removed - mf.Manifold.batch_boolean(cutters, mf.OpType.Add)).volume() < 1e-6
    vlines = ['     <vertex x="%.10g" y="%.10g" z="%.10g"/>' % tuple(v)
              for v in mesh.vertices]
    flines = ['     <triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f)
              for f in mesh.faces]
    mesh_xml = '<mesh>\n    <vertices>\n' + '\n'.join(vlines)
    mesh_xml += '\n    </vertices>\n    <triangles>\n' + '\n'.join(flines)
    mesh_xml += '\n    </triangles>\n   </mesh>'
    changed = dict(original)
    changed[MEMBER] = re.sub(r'<mesh>.*?</mesh>', mesh_xml,
                            original[MEMBER].decode(), flags=re.S).encode()
    config = original['Metadata/model_settings.config'].decode()
    config = re.sub(r'face_count="\d+"', f'face_count="{len(mesh.faces)}"', config)
    changed['Metadata/model_settings.config'] = config.replace(
        'Screwdriver Holder FC (3).stl', name + '.stl').encode()
    with ZipFile(destination, 'w') as archive:
        for entry in entries:
            archive.writestr(entry, changed[entry.filename])
    mesh.export(output_dir / (name + '.stl'))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == original_hash
    report = dict(source=SOURCE.name, output=destination.name, source_sha256=original_hash,
                  diameter_inches=5/8, diameter_mm=DIAMETER,
                  scope='maximum everywhere' if args.max_everywhere else 'eight selected holes only',
                  selected_positions=['1B', '1F', '2B', '2F'], changes=changes,
                  source_volume_mm3=source_solid.volume(), final_volume_mm3=result.volume(),
                  added_volume_mm3=added.volume(), removed_volume_mm3=removed.volume(),
                  final_vertices=len(mesh.vertices), final_triangles=len(mesh.faces),
                  watertight=bool(mesh.is_watertight), winding_consistent=bool(mesh.is_winding_consistent),
                  connected_bodies=mesh.body_count, bounds_mm=mesh.bounds.tolist(),
                  project_settings_identical=changed['Metadata/project_settings.config'] == original['Metadata/project_settings.config'],
                  placement_identical=changed['3D/3dmodel.model'] == original['3D/3dmodel.model'])
    (output_dir / 'Validation' / 'geometry.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('output','scope','diameter_mm','final_triangles',
        'watertight','winding_consistent','connected_bodies','project_settings_identical',
        'placement_identical')}, indent=2))


if __name__ == '__main__':
    main()
