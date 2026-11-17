"""Single-hole corner jigs, mirrored for all four cabinet-door corners.

Units: mm. A's edge datums are X=0 and Y=0; the door face seats at Z=10.
Print the broad exposed face (Z=0) on the bed, with stops pointing up.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import sys
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT.parent
sys.path.insert(0, str(LIBRARY / 'Pliers Holder/Source'))
import build_holder as common

OUT = ROOT / 'Revisions/v02-claybourne-rail-aligned'
STEM = 'Cabinet_Knob_Jig_v02_Claybourne_Pair_3-16in_PLA_Left_TEST_FIT'
# Rejuvenation Claybourne spec: 0.63 in base, 1.25 in face.
# Align the base edge with the nominal rail's inner edge.
P = dict(side_offset=31.75, end_offset=63.5 + (0.63 * 25.4 / 2),
         knob_base_diameter=0.63 * 25.4, knob_face_diameter=31.75,
         knob_projection=25.4, plate_width=70., plate_length=90.,
         plate_thickness=10., stop_depth=10., fence_thickness=4.,
         corner_relief_radius=1.5, drill_bit_diameter=4.7625,
         printed_guide_diameter=5.05, entry_chamfer=0.5,
         door_thickness_min=19.05, door_thickness_max=20.6375,
         nominal_stile_rail_width=63.5)


def make_jig(kind):
    w, h, t = P['plate_width'], P['plate_length'], P['plate_thickness']
    f, d = P['fence_thickness'], P['stop_depth']
    solid = common.union([
        common.box((-f, -f, 0), (w, h, t)),
        common.box((-f, -f, t-0.2), (0, h, t+d)),
        common.box((-f, -f, t-0.2), (w, 0, t+d)),
    ])
    x, y, r = P['side_offset'], P['end_offset'], P['printed_guide_diameter']/2
    mf = common.mf
    holes = [mf.Manifold.cylinder(t+2, r, circular_segments=128).translate((x,y,-1)),
             mf.Manifold.cylinder(P['entry_chamfer'], r+P['entry_chamfer'], r,
                                  circular_segments=128).translate((x,y,0)),
             mf.Manifold.cylinder(d+0.3, P['corner_relief_radius'],
                                  circular_segments=64).translate((0,0,t-0.2))]
    # Identification grooves are recessed in the exposed face, away from the
    # guide and registration surfaces. One groove=A; two grooves=B.
    for gx in ([54.] if kind == 'A' else [54.,50.]):
        holes.append(common.box((gx,10,-0.1),(gx+2,18,0.6)))
    solid = solid - common.union(holes)
    assert solid.status() == mf.Error.NoError and len(solid.decompose()) == 1
    mesh = common.mesh_of(solid)
    mesh.process(validate=True)
    if kind == 'B':
        mirror = np.eye(4); mirror[0,0] = -1; mirror[0,3] = w
        mesh.apply_transform(mirror)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    hole_x = x if kind == 'A' else w-x
    return mesh, dict(name=kind, guide_center=[hole_x,y], guide_axis='Z',
                     side_datum_x=0 if kind == 'A' else w, end_datum_y=0,
                     door_contact_z=t, groove_count=1 if kind == 'A' else 2,
                     door_corners=['bottom-right','top-left'] if kind=='A'
                         else ['bottom-left','top-right'])


def settings():
    result = common.project_settings()
    changes = dict(wall_loops='6', sparse_infill_density='25%', brim_width='3',
                   enable_support='0', initial_layer_line_width='0.5')
    result.update(changes)
    diff = list(result['different_settings_to_system'])
    diff[0] = ';'.join(sorted(set(filter(None,diff[0].split(';'))) | set(changes)))
    result['different_settings_to_system'] = diff
    return result


def main():
    import trimesh
    val = OUT/'Validation'; val.mkdir(parents=True, exist_ok=True)
    report = dict(status='PROTOTYPE; verify guide fit and location on scrap before finished doors',
                  parameters_mm=P, placement_basis='Claybourne mounting-base edge aligned with inner rail edge: 63.5 mm nominal rail + 8.001 mm base radius = 71.501 mm end offset; stile centered at 31.75 mm',
                  knob='Rejuvenation Claybourne, polished nickel; manufacturer nominal dimensions',
                  hardware_thread='#8-32 per manufacturer instructions',
                  placement_limits='Stile and rail widths remain user-reported approximate 2.5 in; verify actual door before drilling. Larger knob face overlaps rail reference line.',
                  references=dict(knob_spec='https://www.rejuvenation.com/netstorage/images/pdfs/instructions/Claybourne_Cabinet_Hardware-Tear-Sheet.pdf',
                                  assembly='https://www.rejuvenation.com/netstorage/images/pdfs/instructions/AI-Claybourne_cabinet_-_01DEC21-A.pdf',
                                  alignment='https://www.amerock.com/set-it-and-forget-it-spikes-help-keep-knobs-in-place'),
                  material='PLA Basic; left extruder', guide_material='Printed plastic, no metal bushing',
                  coordinate_notes='Drill face Z=0 faces the operator, door seats at Z=10: A bottom-right/top-left; B bottom-left/top-right. Looking at the opposite contact face reverses handedness.',
                  project=STEM+'.3mf', parts=[])
    objects=[]; placed=[]
    for kind, center in [('A',(110,160)),('B',(230,160))]:
        mesh, detail = make_jig(kind)
        mesh.export(val/f'Jig_{kind}_Installed.stl')
        pose=np.eye(4)
        pose[:2,3]=np.array(center)-mesh.bounds[:,:2].mean(axis=0)
        pm=mesh.copy(); pm.apply_transform(pose)
        pm.export(OUT/f'Cabinet_Knob_Jig_v02_Claybourne_{kind}.stl')
        assert np.all(pm.bounds[0] >= [5,5,-1e-6])
        assert np.all(pm.bounds[1] <= [320,305,320])
        detail.update(bounds_installed=mesh.bounds.tolist(), print_transform=pose.tolist(),
                      print_bounds=pm.bounds.tolist(), volume_mm3=mesh.volume,
                      watertight=True, connected_bodies=1)
        report['parts'].append(detail)
        objects.append((f'Jig {kind} - {detail["groove_count"]} groove',mesh,pose)); placed.append(pm)
    trimesh.util.concatenate(placed).export(OUT/(STEM+'.stl'))
    path=OUT/(STEM+'.3mf'); common.write_project(path,objects,settings())
    with ZipFile(path) as z: data={n:z.read(n) for n in z.namelist()}
    model=ET.fromstring(data['3D/3dmodel.model'])
    updates={'CreationDate':'2026-11-17',
             'Description':'Mirrored single-hole cabinet knob corner jigs. 31.75 mm side / 71.501 mm end offset. Rejuvenation Claybourne mounting-base edge aligned to a nominal 63.5 mm rail. Printed plastic 5.05 mm guide for a 3/16 in drill bit; test actual fit on scrap. No metal bushing. H2D PLA left.',
             'ProfileTitle':'H2D PLA left | 0.20 mm | 6 walls | 25% gyroid | no supports'}
    for meta in model.findall(f'{{{common.CORE}}}metadata'):
        if meta.get('name') in updates: meta.text=updates[meta.get('name')]
    data['3D/3dmodel.model']=ET.tostring(model,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,value in data.items(): z.writestr(name,value)
    (val/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(project=str(path),parts=report['parts']),indent=2))


if __name__=='__main__': main()
