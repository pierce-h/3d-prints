"""One cabinet backplate with two preserved PowerDetect receivers.

Receiver: jverlenich, CC BY-NC-SA 4.0. This derivative uses the same license.
See ../Original/Attribution.txt. Installed X across, Y up, Z away from cabinet.
"""
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
import build_mount_v01 as previous

ROOT=previous.ROOT
OUT=ROOT/'Revisions/v02-single-piece'
STEM='Shark_Accessory_Mount_v02_One_Piece_PLA_Left_TEST_FIT'
common=previous.common
mf=previous.mf
SOCKET_SPACING=100.0


def make_mount():
    # The exact same 100 mm spacing used in the v01 pair arrangement/preview.
    source=previous.load_reference()
    cropped=source ^ common.box((-100,-100,0),(100,100,100))
    pieces=[p for p in cropped.decompose() if p.volume()>1e-4]
    assert len(pieces)==1
    receiver=pieces[0]
    receivers=common.union([receiver,receiver.translate((SOCKET_SPACING,0,0))])
    bottom=common.mesh_of(receiver).bounds[0,1]
    x0,x1,y0,y1,z0,z1,r=-12.,159.,bottom,34.,-6.,0.5,4.
    plate_parts=[common.box((x0+r,y0,z0),(x1-r,y1,z1)),
                 common.box((x0,y0+r,z0),(x1,y1-r,z1))]
    for x in (x0+r,x1-r):
        for y in (y0+r,y1-r):
            plate_parts.append(mf.Manifold.cylinder(z1-z0,r,circular_segments=64).translate((x,y,z0)))
    screw_centers=[(-3.,27.),(150.,27.)]
    cutters=[]
    for x,y in screw_centers:
        cutters.append(mf.Manifold.cylinder(10,2.4,circular_segments=96).translate((x,y,-7)))
        cutters.append(mf.Manifold.cylinder(2.35,2.4,4.75,circular_segments=96).translate((x,y,-1.85)))
    solid=common.union([receivers,common.union(plate_parts)])-common.union(cutters)
    assert solid.status()==mf.Error.NoError and len(solid.decompose())==1
    mesh=common.mesh_of(solid)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
    region=common.box((-100,-100,0.501),(250,100,100))
    assert abs(((solid^region)-(receivers^region)).volume())<1e-5
    assert abs(((receivers^region)-(solid^region)).volume())<1e-5
    # A solid full-height center section connects the two receiver areas.
    middle=common.box((60,y0+4,-5.5),(87,y1-4,0))
    assert abs((middle-solid).volume())<1e-5
    report=dict(installed_bounds_mm=mesh.bounds.tolist(),dimensions_mm=mesh.extents.tolist(),
        socket_count=2,socket_center_spacing_mm=SOCKET_SPACING,
        spacing_basis='Unchanged 100 mm arrangement from v01 preview and pair. Full accessory-body clearance not physically verified.',
        backing_width_mm=x1-x0,backing_height_mm=y1-y0,backing_thickness_mm=z1-z0,
        screw_centers_xy_mm=screw_centers,screw_spacing_mm=153.,
        screw_clearance_diameter_mm=4.8,countersink_diameter_mm=9.5,countersink_angle_degrees=90,
        socket_bore_nominal_diameter_mm=33.6,
        socket_source='Source mesh measurements, not manufacturer dimensions.',
        receiver_geometry_preserved_ahead_of_z_mm=0.501,
        source_units='meter; multiplied by 1000',source_url=previous.SOURCE_URL,
        source_sha256=hashlib.sha256(previous.SOURCE.read_bytes()).hexdigest(),
        source_license=previous.LICENSE,material='black PLA / left nozzle',
        physical_fit='IP1251 fit report; IP3251 inferred from shared accessory parts. Socket fit and fixed-spacing accessory clearance untested.',
        print_status='Prepared only; no print sent.',watertight=True,connected_bodies=1,
        volume_mm3=mesh.volume)
    return mesh,receivers,report


def update_metadata(path):
    with ZipFile(path) as z:entries={n:z.read(n) for n in z.namelist()}
    root=ET.fromstring(entries['3D/3dmodel.model'])
    metadata={'CreationDate':'2026-11-18','Origin':'remix',
        'Description':'One continuous cabinet backplate with two accessory sockets at 100 mm centers. Receivers from jverlenich IP1251 holder, Printables 1421739. New shared backing and countersinks. CC BY-NC-SA 4.0. IP3251 fit and accessory spacing untested.',
        'Designer':'jverlenich (receivers); Pierce project (cabinet remix)',
        'License':previous.LICENSE,'Source':previous.SOURCE_URL,
        'ProfileTitle':'H2D PLA left | 0.20 mm | 5 walls | 25% gyroid | one-piece mount'}
    for key,value in metadata.items():
        node=root.find(f"{{{common.CORE}}}metadata[@name='{key}']")
        if node is None:node=ET.SubElement(root,f'{{{common.CORE}}}metadata',name=key)
        node.text=value
    entries['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for n,b in entries.items():z.writestr(n,b)


def main():
    val=OUT/'Validation';val.mkdir(parents=True,exist_ok=True)
    mesh,receivers,report=make_mount()
    mesh.export(val/'Mount_Installed.stl')
    common.mesh_of(receivers).export(val/'Receivers_Installed.stl')
    pose=previous.print_pose(mesh,(170,155))
    placed=mesh.copy();placed.apply_transform(pose)
    assert np.all(placed.bounds[0]>=[5,5,-1e-5]) and np.all(placed.bounds[1]<=[320,305,320])
    assert placed.body_count==1
    placed.export(OUT/(STEM+'.stl'))
    path=OUT/(STEM+'.3mf')
    common.write_project(path,[('Shark two-accessory cabinet mount — one piece',mesh,pose)],previous.profile())
    update_metadata(path)
    report.update(print_transform=pose.tolist(),print_bounds_mm=placed.bounds.tolist())
    (val/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
