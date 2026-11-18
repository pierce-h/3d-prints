"""Two independent cabinet accessory sockets, millimetres.

Receiver remixed from jverlenich's IP1251 holder, CC BY-NC-SA 4.0.
See ../Original/Attribution.txt. Installed axes: X across, Y up, Z away
from the cabinet. The original 3MF uses METERS; convert explicitly.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT.parent
sys.path.insert(0, str(LIBRARY / 'Pliers Holder/Source'))
import build_holder as common
mf = common.mf
OUT = ROOT / 'Revisions/v01-cabinet-sockets'
SOURCE = ROOT / 'Original/vacuumattach_r.3mf'
PROFILE = LIBRARY / 'Cabinet Knob Jig/Revisions/v02-claybourne-rail-aligned/Cabinet_Knob_Jig_v02_Claybourne_Pair_3-16in_PLA_Left_TEST_FIT.3mf'
STEM = 'Shark_Accessory_Mount_v01_Pair_PLA_Left_TEST_FIT'
LICENSE = 'https://creativecommons.org/licenses/by-nc-sa/4.0/'
SOURCE_URL = 'https://www.printables.com/model/1421739-shark-powerdetect-vacuum-ip1251-attachment-holder'


def load_reference():
    with ZipFile(SOURCE) as archive:
        root = ET.fromstring(archive.read('3D/3dmodel.model'))
    assert root.get('unit') == 'meter'
    ns = {'m': common.CORE}
    meshes = root.findall('m:resources/m:object/m:mesh', ns)
    assert len(meshes) == 1
    mesh = meshes[0]
    vertices = np.array([[float(e.get(k))*1000 for k in ('x','y','z')]
                         for e in mesh.find('m:vertices', ns)])
    faces = np.array([[int(e.get(k)) for k in ('v1','v2','v3')]
                      for e in mesh.find('m:triangles', ns)], dtype=np.uint64)
    solid = mf.Manifold(mf.Mesh64(vertices, faces))
    assert solid.status() == mf.Error.NoError
    return solid


def make_mount():
    source = load_reference()
    cropped = source ^ common.box((-100,-100,0), (100,100,100))
    pieces = [piece for piece in cropped.decompose() if piece.volume() > 1e-4]
    assert len(pieces) == 1  # Discard only a zero-volume clamp face at Z=0.
    receiver = pieces[0]
    bottom = common.mesh_of(receiver).bounds[0,1]
    # Rounded backing, with its bottom at the same print-bed height as the
    # receiver. The 0.5 mm overlap joins the shell without reaching its bore.
    x0,x1,y0,y1,z0,z1,r = -12.,59.,bottom,34.,-6.,0.5,4.
    bits = [common.box((x0+r,y0,z0),(x1-r,y1,z1)),
            common.box((x0,y0+r,z0),(x1,y1-r,z1))]
    for x in (x0+r,x1-r):
        for y in (y0+r,y1-r):
            bits.append(mf.Manifold.cylinder(z1-z0,r,circular_segments=64).translate((x,y,z0)))
    plate = common.union(bits)
    screw_centers = [(-3.,27.),(50.,27.)]
    holes=[]
    for x,y in screw_centers:
        holes.append(mf.Manifold.cylinder(10,2.4,circular_segments=96).translate((x,y,-7)))
        holes.append(mf.Manifold.cylinder(2.35,2.4,4.75,circular_segments=96).translate((x,y,-1.85)))
    solid = common.union([receiver,plate]) - common.union(holes)
    assert solid.status() == mf.Error.NoError and len(solid.decompose()) == 1
    mesh = common.mesh_of(solid)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    # Preserve ALL inherited receiver material and the complete keyed interface
    # forward of the backing overlap; additions are limited to the backing.
    interface = common.box((-100,-100,0.501),(100,100,100))
    assert abs(((solid ^ interface) - (receiver ^ interface)).volume()) < 1e-5
    assert abs(((receiver ^ interface) - (solid ^ interface)).volume()) < 1e-5
    return mesh, receiver, dict(
        installed_bounds_mm=mesh.bounds.tolist(), dimensions_mm=mesh.extents.tolist(),
        backing_width_mm=71, backing_height_mm=y1-y0, backing_thickness_mm=6.5,
        screw_centers_xy_mm=screw_centers, screw_spacing_mm=53.,
        screw_clearance_diameter_mm=4.8, countersink_diameter_mm=9.5,
        countersink_angle_degrees=90, socket_bore_nominal_diameter_mm=33.6,
        socket_source='Measured mesh; not a manufacturer specification.',
        receiver_geometry_preserved_ahead_of_z_mm=0.501,
        source_units='meter; multiplied by 1000', source_url=SOURCE_URL,
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        source_license=LICENSE, material='black PLA / left nozzle',
        physical_fit='IP1251 creator and make report; IP3251 inferred from shared accessory part numbers, not yet tested by user.',
        print_status='Prepared only; no print sent.', watertight=True, connected_bodies=1)


def print_pose(mesh,center):
    # Original +Y (insertion axis/up) becomes print +Z. Both receiver and
    # backing begin on the bed, keeping the functional bore support-free.
    rot=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)
    vertices=mesh.vertices@rot.T
    translation=np.array([*center,0.])-np.r_[(vertices.min(0)[:2]+vertices.max(0)[:2])/2,vertices.min(0)[2]]
    pose=np.eye(4);pose[:3,:3]=rot;pose[:3,3]=translation
    return pose


def profile():
    with ZipFile(PROFILE) as archive:
        settings=json.loads(archive.read('Metadata/project_settings.config'))
    changes=dict(layer_height='0.2',initial_layer_print_height='0.2',wall_loops='5',
        sparse_infill_density='25%',sparse_infill_pattern='gyroid',
        top_shell_layers='5',bottom_shell_layers='5',enable_support='0',
        enable_prime_tower='0',brim_type='outer_only',brim_width='3',brim_object_gap='0.1',
        filament_map=['1'],filament_map_mode='Manual',master_extruder_id='1')
    settings.update(changes)
    settings['different_settings_to_system'][0]=';'.join(sorted(set(filter(None,settings['different_settings_to_system'][0].split(';')))|set(changes)))
    assert settings['filament_type']==['PLA']
    return settings


def update_metadata(path):
    with ZipFile(path) as archive: entries={n:archive.read(n) for n in archive.namelist()}
    root=ET.fromstring(entries['3D/3dmodel.model'])
    quantity='One screw-mounted cabinet accessory socket.' if 'Single' in path.name else 'Two separate screw-mounted cabinet accessory sockets.'
    metadata={'CreationDate':'2026-11-18','Origin':'remix',
        'Description':quantity+' Receiver from jverlenich IP1251 holder, Printables 1421739. New backing and countersinks. CC BY-NC-SA 4.0. Shared IP3251 accessories; physical fit pending.',
        'Designer':'jverlenich (receiver); Pierce project (cabinet backing/remix)',
        'License':LICENSE,'Source':SOURCE_URL,
        'ProfileTitle':'H2D PLA left | 0.20 mm | 5 walls | 25% gyroid | upright sockets'}
    for key,value in metadata.items():
        node=root.find(f"{{{common.CORE}}}metadata[@name='{key}']")
        if node is None: node=ET.SubElement(root,f'{{{common.CORE}}}metadata',name=key)
        node.text=value
    entries['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as archive:
        for name,data in entries.items():archive.writestr(name,data)


def main():
    val=OUT/'Validation';val.mkdir(parents=True,exist_ok=True)
    mesh,receiver,report=make_mount()
    mesh.export(val/'Mount_Installed.stl')
    common.mesh_of(receiver).export(val/'Source_Receiver_Installed.stl')
    poses=[print_pose(mesh,(125,155)),print_pose(mesh,(225,155))]
    objects=[(f'Shark accessory cabinet socket {i+1}',mesh,p) for i,p in enumerate(poses)]
    common.write_project(OUT/(STEM+'.3mf'),objects,profile());update_metadata(OUT/(STEM+'.3mf'))
    placed=[]
    for pose in poses:
        item=mesh.copy();item.apply_transform(pose);placed.append(item)
        assert np.all(item.bounds[0]>=[5,5,-1e-5]) and np.all(item.bounds[1]<=[320,305,320])
    trimesh.util.concatenate(placed).export(OUT/(STEM+'.stl'))
    single=mesh.copy();single.apply_transform(print_pose(mesh,(170,160)))
    single.export(OUT/'Shark_Accessory_Mount_v01_Single_TEST_FIT.stl')
    single_path=OUT/'Shark_Accessory_Mount_v01_Single_PLA_Left_TEST_FIT.3mf'
    common.write_project(single_path,[('Shark accessory cabinet socket fit sample',mesh,print_pose(mesh,(170,160)))],profile())
    update_metadata(single_path)
    report.update(print_transforms=[p.tolist() for p in poses],print_bounds=[m.bounds.tolist() for m in placed],volume_mm3=mesh.volume)
    (val/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
