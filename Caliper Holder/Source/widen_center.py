"""Widen the central display-body clearance to 32 mm; retain the rear and settings."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import xml.etree.ElementTree as ET
import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Original/Caliper_Holder_for_French_Cleat_saved_2026-10-14_0948.3mf'
OUT = ROOT / 'Revisions/v01-32mm-center'
NAME = 'Caliper_Holder_v01_32mm_Center'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PRODUCTION = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
NS = {'m': CORE}

def mesh_of(solid):
    data = solid.to_mesh64()
    return trimesh.Trimesh(np.asarray(data.vert_properties)[:, :3], np.asarray(data.tri_verts), process=False)

def main():
    validation = OUT / 'Validation'
    validation.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as z:
        archive = {n: z.read(n) for n in z.namelist()}
    object_path = '3D/Objects/object_1.model'
    object_root = ET.fromstring(archive[object_path])
    obj = object_root.find('.//m:object[@id="1"]', NS)
    vertices = np.array([[float(e.get(a)) for a in 'xyz'] for e in obj.findall('.//m:vertex', NS)])
    faces = np.array([[int(e.get(a)) for a in ('v1', 'v2', 'v3')] for e in obj.findall('.//m:triangle', NS)], dtype=np.uint64)
    original_mesh = trimesh.Trimesh(vertices, faces, process=False)
    original = mf.Manifold(mf.Mesh64(vertices, faces))
    assert original.status() == mf.Error.NoError
    # Local axes: X projects forward; Y is installed height; Z runs across the holder.
    # Front support tips have an asymmetric original opening; retain its center.
    front_vertices = vertices[vertices[:, 0] > 7.00001]
    old_left = float(front_vertices[front_vertices[:, 2] < 0, 2].max())
    old_right = float(front_vertices[front_vertices[:, 2] > 0, 2].min())
    center = (old_left + old_right) / 2
    gap = 32.0
    left, right = center - gap / 2, center + gap / 2
    cutter = mf.Manifold.cube((10, 100, gap)).translate((7, -50, left))
    result = (original - cutter).simplify(1e-8)
    mesh = mesh_of(result)
    assert result.status() == mf.Error.NoError and len(result.decompose()) == 1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    assert np.allclose(mesh.bounds, original_mesh.bounds, rtol=0, atol=1e-6)
    assert abs((result - original).volume()) < 1e-6
    removed = original - result
    assert abs((removed - cutter).volume()) < 1e-6
    assert np.asarray(removed.bounding_box())[0] >= 7 - 1e-6

    obj.remove(obj.find('m:mesh', NS))
    xmesh = ET.SubElement(obj, f'{{{CORE}}}mesh')
    xv = ET.SubElement(xmesh, f'{{{CORE}}}vertices')
    xf = ET.SubElement(xmesh, f'{{{CORE}}}triangles')
    for v in mesh.vertices:
        ET.SubElement(xv, f'{{{CORE}}}vertex', **dict(zip('xyz', ('%.12g' % n for n in v))))
    for f in mesh.faces:
        ET.SubElement(xf, f'{{{CORE}}}triangle', **dict(zip(('v1', 'v2', 'v3'), map(str, f))))
    ET.register_namespace('', CORE)
    ET.register_namespace('p', PRODUCTION)
    archive[object_path] = ET.tostring(object_root, encoding='utf-8', xml_declaration=True)
    root = ET.fromstring(archive['3D/3dmodel.model'])
    metadata = {e.get('name'): e.text for e in root.findall('m:metadata', NS)}
    (ROOT / 'Source/Original_Metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    for key, value in {
        'Title': NAME, 'Origin': 'remix', 'ModificationDate': '2026-10-14',
        'Description': 'Local modification of the Caliper Holder for French Cleat by 3D-Therapy (CC0). Central clearance widened from 28.92079 mm to 32 mm for an approximately 30 mm digital-caliper body. Backplate, rear French cleat, outside dimensions, print orientation and slicer settings retained. Physical fit of this revision is untested.'
    }.items():
        node = root.find(f'm:metadata[@name="{key}"]', NS)
        if node is None:
            node = ET.SubElement(root, f'{{{CORE}}}metadata', name=key)
        node.text = value
    archive['3D/3dmodel.model'] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    config = ET.fromstring(archive['Metadata/model_settings.config'])
    for node in config.findall('.//metadata[@key="name"]'):
        node.set('value', NAME + '.stl')
    for node in config.findall('.//metadata[@face_count]') + config.findall('.//mesh_stat'):
        node.set('face_count', str(len(mesh.faces)))
    config.find('.//plate/metadata[@key="plater_name"]').set('value', NAME)
    archive['Metadata/model_settings.config'] = ET.tostring(config, encoding='utf-8', xml_declaration=True)
    with ZipFile(OUT / (NAME + '.3mf'), 'w', ZIP_DEFLATED) as z:
        for name, data in archive.items(): z.writestr(name, data)

    a = np.array([float(v) for v in root.find('m:build/m:item', NS).get('transform').split()])
    transform = np.eye(4)
    transform[:3, :3] = a[:9].reshape(3, 3).T
    transform[:3, 3] = a[9:]
    placed = mesh.copy(); placed.apply_transform(transform)
    placed.export(OUT / (NAME + '.stl'), file_type='stl_ascii')
    original_mesh.export(validation / 'original_local.stl', file_type='stl_ascii')
    mesh.export(validation / 'widened_local.stl', file_type='stl_ascii')
    mesh_of(removed).export(validation / 'removed_material.stl', file_type='stl_ascii')
    report = dict(status='Digital geometry checked; physical fit untested.',
        designer=metadata.get('Designer'), license=metadata.get('License'),
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        user_caliper_body_width_approx_mm=30, original_gap_mm=old_right-old_left,
        new_gap_mm=gap, nominal_clearance_per_side_mm=1,
        original_inner_edges_z_mm=[old_left,old_right], new_inner_edges_z_mm=[left,right],
        opening_center_z_mm=center, trim_per_side_mm=(gap-(old_right-old_left))/2,
        removed_volume_mm3=removed.volume(), original_volume_mm3=original.volume(),
        final_volume_mm3=result.volume(), bounds_local_mm=mesh.bounds.tolist(),
        bounds_print_mm=placed.bounds.tolist(), print_transform=transform.tolist(),
        watertight=bool(mesh.is_watertight), bodies=mesh.body_count, triangles=len(mesh.faces),
        preserved=['backplate', 'French cleat', 'outer dimensions', 'original print placement', 'printer and filament settings', 'source attribution and license'])
    (validation / 'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
