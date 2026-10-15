"""Enlarge the confirmed four left positions on both screwdriver-holder shelves.

Dependencies: numpy, trimesh, manifold3d. Run with the original project unchanged.
The Bambu project settings, placement, and all unrelated geometry are retained.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Original" / "Screwdriver_Holder_FC.3mf"
OUTPUT_DIR = ROOT / "Revisions" / "v01-larger-left-holes"
NAME = "Screwdriver_Holder_v01_Larger_Left_Holes"
DEST = OUTPUT_DIR / (NAME + ".3mf")
NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
MEMBER = "3D/Objects/object_1.model"
THROUGH_DIAMETER = 16.35
RECESS_DIAMETER = 27.35
SEGMENTS = 256  # Maximum radial chord error is approximately 0.001 mm.


def fit_ring(vertices, z, guess, radius):
    distance = np.linalg.norm(vertices[:, :2] - guess, axis=1)
    ring = vertices[(np.abs(vertices[:, 2] - z) < 1e-4)
                    & (np.abs(distance - radius) < .08), :2]
    ring = np.unique(ring, axis=0)
    if len(ring) != 20:
        raise ValueError(f"Expected a 20-vertex source ring, found {len(ring)}")
    A = np.column_stack((2 * ring, np.ones(len(ring))))
    result = np.linalg.lstsq(A, np.square(ring).sum(axis=1), rcond=None)[0]
    center = result[:2]
    fitted_radius = np.sqrt(result[2] + np.square(center).sum())
    return center, 2 * fitted_radius


def main():
    (OUTPUT_DIR / "Validation").mkdir(parents=True, exist_ok=True)
    original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with ZipFile(SOURCE) as archive:
        original = {entry.filename: archive.read(entry.filename)
                    for entry in archive.infolist()}
        entries = archive.infolist()
    tree = ET.fromstring(original[MEMBER])
    vertices = np.array([[float(e.get(k)) for k in ("x", "y", "z")]
                         for e in tree.findall(".//m:vertex", NS)])
    faces = np.array([[int(e.get(k)) for k in ("v1", "v2", "v3")]
                      for e in tree.findall(".//m:triangle", NS)])
    source_mesh = trimesh.Trimesh(vertices, faces, process=False)
    source_solid = mf.Manifold(mf.Mesh64(vertices, faces.astype(np.uint64)))
    assert source_solid.status() == mf.Error.NoError
    assert source_mesh.is_watertight
    cutters, changes = [], []
    for x in (-80., -40.):
        for y in (-28.5025, 10.5015):
            for label, z_ring, z_start, z_end, guess, old_r, diameter in (
                ("lower through-hole", -12.5004997, -12.61, -7.39, (x, y), 5., THROUGH_DIAMETER),
                ("upper through-hole", 32.4995003, 32.39, 42.61, (x, y), 5., THROUGH_DIAMETER),
                ("upper recess", 38.2125015, 38.2125015, 42.61,
                 (x + .5, y - .5), 10.502, RECESS_DIAMETER),
            ):
                center, old_diameter = fit_ring(vertices, z_ring, guess, old_r)
                # Preserve the actual recess floor, not a rounded nominal depth.
                if label == "upper recess":
                    z_start = float(vertices[np.argmin(abs(vertices[:, 2] - z_ring)), 2])
                cutter = mf.Manifold.cylinder(z_end - z_start, diameter / 2,
                                              circular_segments=SEGMENTS)
                cutters.append(cutter.translate((float(center[0]), float(center[1]), z_start)))
                changes.append(dict(feature=label, center_mm=center.tolist(),
                                    original_measured_diameter_mm=old_diameter,
                                    final_nominal_diameter_mm=diameter,
                                    cutter_z_mm=[z_start, z_end]))
    result = mf.Manifold.batch_boolean([source_solid] + cutters, mf.OpType.Subtract)
    assert result.status() == mf.Error.NoError
    mesh64 = result.to_mesh64()
    mesh = trimesh.Trimesh(np.array(mesh64.vert_properties)[:, :3],
                           np.array(mesh64.tri_verts), process=False)
    assert mesh.is_watertight and mesh.is_winding_consistent
    assert mesh.body_count == 1 and mesh.euler_number == source_mesh.euler_number
    assert np.allclose(mesh.bounds, source_mesh.bounds, atol=1e-7)
    assert np.min(mesh.area_faces) > 1e-10
    assert (result - source_solid).volume() < 1e-6
    expected = source_solid - mf.Manifold.batch_boolean(cutters, mf.OpType.Add)
    assert abs(expected.volume() - result.volume()) < 1e-6
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
    config = config.replace('Screwdriver Holder FC (3).stl', NAME + '.stl')
    changed['Metadata/model_settings.config'] = config.encode()
    # Keep author, license, original source metadata, and print/filament settings.
    with ZipFile(DEST, 'w') as archive:
        for entry in entries:
            archive.writestr(entry, changed[entry.filename])
    mesh.export(OUTPUT_DIR / (NAME + '.stl'))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == original_hash
    report = dict(source=SOURCE.name, output=DEST.name,
                  source_sha256=original_hash, confirmed_positions=['1B', '1F', '2B', '2F'],
                  requested_diameter_increase_mm=6.35, changes=changes,
                  source_volume_mm3=source_solid.volume(), final_volume_mm3=result.volume(),
                  final_vertices=len(mesh.vertices), final_triangles=len(mesh.faces),
                  watertight=bool(mesh.is_watertight), winding_consistent=bool(mesh.is_winding_consistent),
                  connected_bodies=mesh.body_count, bounds_mm=mesh.bounds.tolist(),
                  project_settings_identical=changed['Metadata/project_settings.config'] == original['Metadata/project_settings.config'],
                  placement_identical=changed['3D/3dmodel.model'] == original['3D/3dmodel.model'])
    (OUTPUT_DIR / 'Validation' / 'geometry.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('output','source_volume_mm3','final_volume_mm3',
        'final_triangles','watertight','winding_consistent','connected_bodies',
        'project_settings_identical','placement_identical')}, indent=2))


if __name__ == '__main__':
    main()
