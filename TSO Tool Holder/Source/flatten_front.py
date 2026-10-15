"""Fill the 0.5 mm recessed maker emblem, retaining the original front plane.

Original TSO Square Holder by dave3ddiy; BY-NC-SA. No scaling, tool-slot,
cleat, print-placement, or slicer-setting changes. Coordinates are millimetres.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Original' / 'TSO_Square_Holder.3mf'
OUT = ROOT / 'Revisions' / 'v01-plain-front'
NAME = 'TSO_Tool_Holder_v01_Plain_Front'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PRODUCTION = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
NS = {'m': CORE}


def mesh_of(solid):
    data = solid.to_mesh64()
    return trimesh.Trimesh(np.asarray(data.vert_properties)[:, :3],
                          np.asarray(data.tri_verts), process=False)


def main():
    validation = OUT / 'Validation'
    validation.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as z:
        archive = {n: z.read(n) for n in z.namelist()}
    object_path = '3D/Objects/object_1.model'
    object_root = ET.fromstring(archive[object_path])
    obj = object_root.find('.//m:object[@id="1"]', NS)
    vertices = np.array([[float(e.get(a)) for a in 'xyz']
                        for e in obj.findall('.//m:vertex', NS)])
    faces = np.array([[int(e.get(a)) for a in ('v1', 'v2', 'v3')]
                     for e in obj.findall('.//m:triangle', NS)], dtype=np.uint64)
    source_mesh = trimesh.Trimesh(vertices, faces, process=False)
    original = mf.Manifold(mf.Mesh64(vertices, faces))
    assert original.status() == mf.Error.NoError

    front = 6.27499962
    patch = mf.Manifold.cube((86, 86, front - 5.70)).translate((-43, -54, 5.70))
    # The entire patch footprint has existing solid material beneath it.
    foundation = mf.Manifold.cube((86, 86, 0.04)).translate((-43, -54, 5.70))
    assert abs((foundation - original).volume()) < 1e-6
    flat = (original + patch).simplify(1e-7)
    mesh = mesh_of(flat)
    assert flat.status() == mf.Error.NoError and len(flat.decompose()) == 1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    assert np.allclose(mesh.bounds, source_mesh.bounds, rtol=0, atol=1e-6)
    removed = abs((original - flat).volume())
    assert removed < 1e-6
    added_all = flat - original
    added = mf.Manifold.batch_boolean([s for s in added_all.decompose()
                                       if abs(s.volume()) > 1e-6], mf.OpType.Add)
    assert abs(added.volume() - added_all.volume()) < 1e-6
    added_bounds = np.array(added.bounding_box()).reshape(2, 3)
    assert np.all(added_bounds[0] >= [-43, -54, 5.77499])
    assert np.all(added_bounds[1] <= [43, 32, 6.27501])
    assert abs(added.volume() - 2183.1378474708) < 1e-4

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
    (ROOT / 'Source' / 'Original_Metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    changes = {'Title': NAME, 'Origin': 'remix', 'ModificationDate': '2026-10-13',
               'Description': 'Plain-front local modification of the TSO Square French Cleat Holder by dave3ddiy (BY-NC-SA). The recessed 0.5 mm maker emblem is filled flush with the original front face. Tool slot, French cleat, outside dimensions, print orientation and slicer settings are unchanged.'}
    for key, value in changes.items():
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
        for name, data in archive.items():
            z.writestr(name, data)

    item = root.find('m:build/m:item', NS)
    a = np.array([float(v) for v in item.get('transform').split()])
    transform = np.eye(4)
    transform[:3, :3] = a[:9].reshape(3, 3).T
    transform[:3, 3] = a[9:]
    printable = mesh.copy()
    printable.apply_transform(transform)
    printable.export(OUT / (NAME + '.stl'), file_type='stl_ascii')
    source_mesh.export(validation / 'original_local.stl', file_type='stl_ascii')
    mesh.export(validation / 'plain_local.stl', file_type='stl_ascii')
    mesh_of(added).export(validation / 'filled_emblem.stl', file_type='stl_ascii')
    reread = trimesh.load(OUT / (NAME + '.stl'), force='mesh')
    assert reread.is_watertight and reread.is_winding_consistent and reread.body_count == 1
    with ZipFile(OUT / (NAME + '.3mf')) as z, ZipFile(SOURCE) as original_zip:
        assert z.read('Metadata/project_settings.config') == original_zip.read('Metadata/project_settings.config')
    report = dict(status='Geometry checked; physical print and fit untested.',
        original_designer=metadata['Designer'], original_license=metadata['License'],
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        feature='Recessed circular maker emblem filled flush', recess_depth_mm=0.5,
        original_front_plane_z_mm=front, local_bounds_mm=mesh.bounds.tolist(),
        print_bounds_mm=printable.bounds.tolist(), print_transform=transform.tolist(),
        source_volume_mm3=original.volume(), final_volume_mm3=flat.volume(),
        added_volume_mm3=added.volume(), removed_volume_mm3=removed,
        added_bounds_mm=added_bounds.tolist(), triangle_count=len(mesh.faces),
        watertight=bool(mesh.is_watertight), consistent_winding=bool(mesh.is_winding_consistent),
        connected_bodies=mesh.body_count, preserved=['tool slot', 'French cleat', 'external dimensions',
            'original placement', 'printer and filament settings', 'source attribution and license'])
    (validation / 'geometry.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
