"""Weld the matching Bench Cookie holder and accessory extension by alejepa.

Millimetres; source CAD axes: X towards user, Y across wall, Z up.
The supplied models' locating joint seats after raising the accessory 1 mm.
Fill only the obsolete assembly clearance, then export one connected solid.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import copy
import hashlib
import json
import uuid
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions' / 'v01-welded'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
NS = {'m': CORE}
TOP = ROOT / 'Original' / 'Bench_Cookie_Plus_8_French_Cleat_Holder.3mf'
ACC = ROOT / 'Original' / 'Bench_Cookie_Accesory_Extension_French_Cleat_Holder.3mf'
NAME = 'Bench_Cookie_Organizer_v01_Welded'


def source_solid(path, member, object_id):
    with ZipFile(path) as z:
        root = ET.fromstring(z.read(member))
    obj = root.find(f'.//m:object[@id="{object_id}"]', NS)
    vertices = np.array([[float(e.get(a)) for a in 'xyz']
                         for e in obj.findall('.//m:vertex', NS)])
    faces = np.array([[int(e.get(a)) for a in ('v1', 'v2', 'v3')]
                      for e in obj.findall('.//m:triangle', NS)], dtype=np.uint64)
    solid = mf.Manifold(mf.Mesh64(vertices, faces))
    assert solid.status() == mf.Error.NoError
    return solid


def mesh_of(solid):
    data = solid.to_mesh64()
    return trimesh.Trimesh(np.asarray(data.vert_properties)[:, :3],
                          np.asarray(data.tri_verts), process=False)


def transform_text(matrix):
    return ' '.join('%.12g' % x for x in np.r_[matrix[:3, :3].T.ravel(), matrix[:3, 3]])


def xml_bytes(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def write_project(path, objects, settings, description, original_meta):
    """Create a clean Bambu 3MF without old support modifiers/assembly state."""
    ET.register_namespace('', CORE)
    root = ET.Element(f'{{{CORE}}}model', {'unit': 'millimeter',
                      '{http://www.w3.org/XML/1998/namespace}lang': 'en-US'})
    meta = {k: original_meta[k] for k in ('Designer', 'License', 'CopyRight', 'Copyright')
            if k in original_meta}
    meta.update(Application='BambuStudio-02.08.02.61',
                **{'BambuStudio:3mfVersion': '1'}, CreationDate='2026-10-13',
                Title=path.stem, Origin='remix', Description=description,
                ProfileTitle='Welded organizer — PLA, 0.20 mm, 3 walls, 12% gyroid')
    for key, val in meta.items():
        ET.SubElement(root, f'{{{CORE}}}metadata', name=key).text = val
    resources = ET.SubElement(root, f'{{{CORE}}}resources')
    build = ET.SubElement(root, f'{{{CORE}}}build')
    config = ET.Element('config')
    plate = ET.Element('plate')
    for k, v in [('plater_id', '1'), ('plater_name', path.stem), ('locked', 'false'),
                 ('filament_map_mode', 'Auto For Flush'),
                 ('thumbnail_file', 'Metadata/plate_1.png'),
                 ('thumbnail_no_light_file', 'Metadata/plate_no_light_1.png'),
                 ('top_file', 'Metadata/top_1.png'), ('pick_file', 'Metadata/pick_1.png')]:
        ET.SubElement(plate, 'metadata', key=k, value=v)
    for i, (name, mesh, matrix) in enumerate(objects, 1):
        obj = ET.SubElement(resources, f'{{{CORE}}}object', id=str(i), type='model', name=name)
        xmesh = ET.SubElement(obj, f'{{{CORE}}}mesh')
        vertices = ET.SubElement(xmesh, f'{{{CORE}}}vertices')
        triangles = ET.SubElement(xmesh, f'{{{CORE}}}triangles')
        for v in mesh.vertices:
            ET.SubElement(vertices, f'{{{CORE}}}vertex', **dict(zip('xyz', ('%.12g' % x for x in v))))
        for f in mesh.faces:
            ET.SubElement(triangles, f'{{{CORE}}}triangle', **dict(zip(('v1','v2','v3'), (str(x) for x in f))))
        ET.SubElement(build, f'{{{CORE}}}item', objectid=str(i),
                      transform=transform_text(matrix), printable='1')
        ob = ET.SubElement(config, 'object', id=str(i))
        ET.SubElement(ob, 'metadata', key='name', value=name)
        ET.SubElement(ob, 'metadata', key='extruder', value='1')
        ET.SubElement(ob, 'metadata', face_count=str(len(mesh.faces)))
        part = ET.SubElement(ob, 'part', id=str(i), subtype='normal_part', uuid=str(uuid.uuid4()))
        ET.SubElement(part, 'metadata', key='name', value=name)
        ET.SubElement(part, 'metadata', key='matrix', value='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        ET.SubElement(part, 'mesh_stat', face_count=str(len(mesh.faces)), edges_fixed='0',
                      degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
        inst = ET.SubElement(plate, 'model_instance')
        for k, v in [('object_id', str(i)), ('instance_id', '0'), ('identify_id', str(3000+i))]:
            ET.SubElement(inst, 'metadata', key=k, value=v)
    config.append(plate)
    content_types = b'''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/></Types>'''
    rels = b'''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'''
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', xml_bytes(root))
        z.writestr('Metadata/model_settings.config', xml_bytes(config))
        z.writestr('Metadata/project_settings.config', json.dumps(settings, indent=2))


def main():
    validation = OUT / 'Validation'
    validation.mkdir(parents=True, exist_ok=True)
    top = source_solid(TOP, '3D/Objects/object_13.model', '1').translate((40, 111, 37.5))
    accessory = source_solid(ACC, '3D/Objects/object_25.model', '6').translate((49, 111, -62.5))
    placed = top + accessory
    # The roof lands at Z=0 after seating. Extend its footprint just through
    # the 1.2 mm-deep tongue/groove clearance; functional cookie bowls start higher.
    seam = accessory.slice(-0.05).extrude(1.35).translate((0, 0, -0.05))
    nominal = placed + seam
    added_raw = nominal - placed
    # Ignore only numerical subtraction fragments below one millionth mm³
    # when reporting the extent of the material intentionally added.
    added = mf.Manifold.batch_boolean([s for s in added_raw.decompose()
                                       if abs(s.volume()) > 1e-6], mf.OpType.Add)
    assert abs(added_raw.volume()-added.volume()) < 1e-5
    welded = nominal.simplify(1e-7)
    assert welded.status() == mf.Error.NoError and len(welded.decompose()) == 1
    mesh = mesh_of(welded)
    # Boolean intersections can retain nanometre-scale duplicate vertices at
    # the old joint. Collapse these before STL/3MF decimal serialization.
    mesh.merge_vertices(digits_vertex=8)
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-12))
    mesh.remove_unreferenced_vertices()
    welded = mf.Manifold(mf.Mesh64(mesh.vertices, mesh.faces.astype(np.uint64)))
    assert welded.status() == mf.Error.NoError and len(welded.decompose()) == 1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    assert mesh.volume > 0 and mesh.area_faces.min() > 1e-10
    removed = placed - welded
    assert abs(removed.volume()) < 1e-5
    cleanup_change = abs((nominal-welded).volume()) + abs((welded-nominal).volume())
    assert cleanup_change < 1e-5
    assert 0 < added.volume() < 250
    assert added.bounding_box()[2] >= -1e-5 and added.bounding_box()[5] <= 1.201
    # Upright print, front towards the front of the bed; same scale as sources.
    # Centre in the two nozzles' shared X=25..325 mm region. Tree supports
    # spread beyond the model, so centring only in the left nozzle's region
    # would allow a support to cross the right nozzle's X=25 mm boundary.
    matrix = np.array([[0,1,0,64],[-1,0,0,195],[0,0,1,126],[0,0,0,1]], dtype=float)
    printable = mesh.copy()
    printable.apply_transform(matrix)
    assert np.all(printable.bounds[0] >= [25,5,0])
    assert np.all(printable.bounds[1] <= [325,305,350])
    with ZipFile(TOP) as z:
        settings = json.loads(z.read('Metadata/project_settings.config'))
        meta_root = ET.fromstring(z.read('3D/3dmodel.model'))
    meta = {e.get('name'): e.text or '' for e in meta_root.findall('m:metadata', NS)}
    desc = ('One-piece organizer: eight Bench Cookie Plus positions above the matching accessory '
            'holder, in the source design assembled arrangement. Original models by alejepa. '
            'The accessory seats 1 mm into the matching joint; only internal assembly clearance '
            'is filled. Original French cleat and storage features retained. Optional rear spacers '
            'remain separate. Geometry and slicing checks do not establish physical fit or load capacity.')
    write_project(OUT / (NAME+'.3mf'), [(NAME+'.stl', mesh, matrix)], settings, desc, meta)
    # ASCII STL retains precision at the original finely tessellated joint;
    # float32 binary STL collapses several nearby vertices into degenerate faces.
    printable.export(OUT / (NAME+'.stl'), file_type='stl_ascii')
    mesh.export(validation / 'holder_installed.stl', file_type='stl_ascii')
    mesh_of(seam).export(validation / 'joint_filler.stl', file_type='stl_ascii')
    mesh_of(added).export(validation / 'added_material.stl', file_type='stl_ascii')
    # Preserve the original four loose rear stand-offs in their own print project.
    block = mesh_of(source_solid(ACC, '3D/Objects/object_14.model', '1'))
    blocks = []
    for i in range(4):
        mat = np.array([[0,1,0,125+25*i],[0,0,1,155],[1,0,0,9.44999981],[0,0,0,1]], float)
        blocks.append((f'Original rear spacer {i+1}', block, mat))
    write_project(OUT / 'Rear_Spacers_4x_v01.3mf', blocks, copy.deepcopy(settings),
                  'Four unmodified optional rear distance blocks from alejepa accessory holder. '
                  'Attach only where they bear against the intended wall surface; positions depend on rail spacing.', meta)
    block_oriented = block.copy()
    block_oriented.apply_transform(np.array([[0,1,0,0],[0,0,1,0],[1,0,0,9.44999981],[0,0,0,1]], float))
    block_oriented.export(OUT / 'Rear_Spacer_v01.stl', file_type='stl_ascii')
    report = dict(status='Geometry checked; physical print, fit and load untested.',
        original_designer=meta.get('Designer'), original_license=meta.get('License'),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (TOP,ACC)},
        source_translations_mm=dict(cookie=[40,111,37.5], accessory=[49,111,-62.5]),
        accessory_joint_insertion_mm=1.0,
        seam=dict(slice_z_mm=-0.05, extrusion_mm=1.35, top_z_mm=1.3),
        installed_axes='X front/depth; Y width; Z up',
        installed_bounds_mm=mesh.bounds.tolist(), dimensions_width_depth_height_mm=[222,116,201],
        print_transform=matrix.tolist(), print_bounds_mm=printable.bounds.tolist(),
        volume_mm3=mesh.volume, added_volume_mm3=added.volume(), removed_volume_mm3=removed.volume(),
        numerical_cleanup_difference_mm3=cleanup_change,
        added_bounds_mm=list(added.bounding_box()), triangle_count=len(mesh.faces),
        watertight=bool(mesh.is_watertight), consistent_winding=bool(mesh.is_winding_consistent),
        connected_bodies=mesh.body_count, manifold_components=len(welded.decompose()),
        settings={k:settings[k] for k in ('printer_model','filament_type','filament_settings_id',
           'layer_height','wall_loops','sparse_infill_density','sparse_infill_pattern',
           'enable_support','support_type','support_on_build_plate_only','brim_type')},
        preserved_features=['cookie slots','accessory holes and shaped storage bays','original French cleat'],
        separate_parts='Four optional original rear spacers in Rear_Spacers_4x_v01.3mf',
        excluded='Original support-enforcer modifier and stale per-object print overrides; not model geometry.')
    (validation / 'geometry.json').write_text(json.dumps(report, indent=2)+'\n')
    source_metadata = {}
    for p in (TOP, ACC):
        with ZipFile(p) as z:
            r = ET.fromstring(z.read('3D/3dmodel.model'))
        source_metadata[p.name] = {e.get('name'):e.text for e in r.findall('m:metadata', NS)}
    (ROOT / 'Source' / 'Original_Metadata.json').write_text(json.dumps(source_metadata, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
