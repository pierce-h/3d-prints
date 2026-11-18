"""Single-edge drawer knob drilling jig; millimetres.

X is across the drawer, Y down from its top edge, and Z into the drawer.
The exposed drill face is Z=0, drawer contact is Z=10, and the top datum Y=0.
Print the broad drill face on the bed, with the single edge stop pointing up.
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

OUT = ROOT / 'Revisions/v01-single-edge'
STEM = 'Drawer_Knob_Jig_v01_Single_Edge_Clear_PETG_Right_TEST_FIT'
BASE = LIBRARY / 'Cabinet Knob Jig/Revisions/v03-clear-petg-right/Cabinet_Knob_Jig_v03_Claybourne_Pair_Clear_PETG_Right_TEST_FIT.3mf'
P = dict(rail_height=63.5, guide_offset=31.75, plate_width=80.,
         plate_length=55., plate_thickness=10., fence_thickness=4.,
         stop_depth=10., printed_guide_diameter=5.05, drill_bit_diameter=4.7625,
         entry_chamfer=0.5, centerline_width=0.6, centerline_depth=0.5,
         sight_notch_width=3., sight_notch_depth=3.)


def make_jig():
    mf = common.mf
    w, h, t = P['plate_width'], P['plate_length'], P['plate_thickness']
    f, d = P['fence_thickness'], P['stop_depth']
    solid = common.union([
        common.box((0, -f, 0), (w, h, t)),
        common.box((0, -f, t-0.2), (w, 0, t+d)),
    ])
    x, y, r = w/2, P['guide_offset'], P['printed_guide_diameter']/2
    cuts = [mf.Manifold.cylinder(t+2, r, circular_segments=128).translate((x,y,-1)),
            mf.Manifold.cylinder(P['entry_chamfer'], r+P['entry_chamfer'], r,
                                 circular_segments=128).translate((x,y,0))]
    # A narrow engraved line, interrupted around the guide to preserve its rim.
    for lo, hi in [(4., 27.), (36.5, 52.)]:
        cuts.append(common.box((x-P['centerline_width']/2, lo, -0.1),
                               (x+P['centerline_width']/2, hi, P['centerline_depth'])))
    # The open V reveals a pencil centerline on the drawer face. Its apex is
    # exactly on the bore's X centerline; no side stop constrains horizontal use.
    half = P['sight_notch_width']/2
    poly = [(x-half,h+1), (x-half,h), (x,h-P['sight_notch_depth']),
            (x+half,h), (x+half,h+1)]
    cuts.append(mf.CrossSection([np.array(poly)], mf.FillRule.EvenOdd)
                .extrude(t+2).translate((0,0,-1)))
    solid = solid - common.union(cuts)
    assert solid.status() == mf.Error.NoError and len(solid.decompose()) == 1
    mesh = common.mesh_of(solid)
    mesh.process(validate=True)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    return mesh


def main():
    val = OUT/'Validation'; val.mkdir(parents=True, exist_ok=True)
    mesh = make_jig()
    mesh.export(val/'Jig_Local.stl')
    pose = np.eye(4)
    pose[:2,3] = np.array([170.,160.]) - mesh.bounds[:,:2].mean(axis=0)
    placed = mesh.copy(); placed.apply_transform(pose)
    assert np.all(placed.bounds[0] >= [5,5,-1e-6])
    assert np.all(placed.bounds[1] <= [320,305,320])
    placed.export(OUT/(STEM+'.stl'))
    with ZipFile(BASE) as z:
        settings = json.loads(z.read('Metadata/project_settings.config'))
    assert settings['filament_type'] == ['PETG'] and settings['filament_map'] == ['2']
    path = OUT/(STEM+'.3mf')
    common.write_project(path, [('Drawer knob jig - single top stop',mesh,pose)], settings)
    with ZipFile(path) as z:
        entries = {name:z.read(name) for name in z.namelist()}
    model = ET.fromstring(entries['3D/3dmodel.model'])
    metadata = {
        'CreationDate':'2026-11-18',
        'Description':'Single-edge drawer knob drilling jig. One top-edge stop, horizontally free. '
                      'Guide center 31.75 mm below top edge, centered on a 63.5 mm rail. '
                      'V sight notch and engraved centerline align to a user-marked drawer midpoint. '
                      'Printed 5.05 mm guide for 3/16 in drill. Clear PETG, H2D right nozzle.',
        'ProfileTitle':'H2D clear PETG right | 0.20 mm | 6 walls | 25% gyroid | no supports',
    }
    for node in model.findall(f'{{{common.CORE}}}metadata'):
        if node.get('name') in metadata: node.text = metadata[node.get('name')]
    entries['3D/3dmodel.model'] = ET.tostring(model,encoding='utf-8',xml_declaration=True)
    config = ET.fromstring(entries['Metadata/model_settings.config'])
    config.find("plate/metadata[@key='filament_maps']").set('value','2')
    entries['Metadata/model_settings.config'] = ET.tostring(config,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,data in entries.items(): z.writestr(name,data)
    report = dict(
        status='New drawer geometry; not yet physically tested. Cabinet-jig guide size was user-tested successfully.',
        parameters_mm=P, guide_center_local=[40.,31.75], top_edge_datum_y=0.,
        drawer_contact_z=10., exposed_drill_face_z=0.,
        bounds_local=mesh.bounds.tolist(), print_transform=pose.tolist(),
        print_bounds=placed.bounds.tolist(), volume_mm3=mesh.volume,
        watertight=bool(mesh.is_watertight), connected_bodies=mesh.body_count,
        user_confirmed='2.5 inch drawer top rail; knob hole centered 1.25 inch below top edge.',
        horizontal_alignment='User marks drawer midpoint; align engraved line/V-notch apex with pencil centerline.',
        side_stops=0, top_stops=1, material='Bambu PETG Translucent, clear',
        physical_nozzle='right / 2', profile_source=str(BASE.relative_to(LIBRARY)),
        print_status='Prepared only; no print sent.', project=path.name)
    (val/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
