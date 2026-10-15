"""v06: only the ten measured attachments and one Allen-key through-hole."""
from pathlib import Path
from zipfile import ZipFile
import json
import numpy as np
import manifold3d as mf
from build_holder import box,union,prism_x,mesh_of,side_transform,write_project,cylinder_y,cleat
from build_holder_v04 import hook,fence_channel,key_void,main_holder as previous_holder

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'Revisions/v05-no-top-tray'
OUT=ROOT/'Revisions/v06-essential-storage'
MAIN='PTR18_Hanger_v06_Essential_Storage_TEST_FIT'

def hardware_positions():
    positions=[]
    for x in (-98,-66):
        positions.append(dict(type='measured short pin pocket',x=x,z=40,diameter=9.8,depth=8,body_diameter=9,body_height=12))
        positions.append(dict(type='measured tall pin pocket',x=x,z=64,diameter=9.8,depth=16,body_diameter=9,body_height=25))
    for x in (22,58,94):
        for z in (40,64):
            positions.append(dict(type='measured screw head pocket',x=x,z=z,diameter=6.8,depth=2.5,body_diameter=6,body_height=4))
    return positions


def main_holder():
    outline=[(-130,78),(130,78),(130,32),(46,-57),(-46,-57),(-130,32)]
    back=mf.CrossSection([outline],mf.FillRule.EvenOdd).extrude(4)
    parts=[back,box((-130,21,3.9),(130,78,6)),box((-44,-57,3.9),(44,21.1,6)),
           cleat(70).translate((-85,0,0)),cleat(70).translate((85,0,0)),
           hook(),fence_channel(260),box((-130,59,24.9),(130,65,82))]
    parts += [prism_x([(49,5.8),(59.1,53),(61.1,53),(61.1,5.8)],6,x)
              for x in (-126,-26,26,126)]
    positions=hardware_positions()
    for p in positions:
        if p['depth']>4:
            parts.append(cylinder_y(p['x'],p['z'],p['diameter']+6,65-p['depth']-3,65))
    cavities=[cylinder_y(p['x'],p['z'],p['diameter'],65-p['depth'],66) for p in positions]
    return union(parts)-union(cavities+[key_void()]),positions


def main():
    v=OUT/'Validation';v.mkdir(parents=True,exist_ok=True)
    solid,positions=main_holder()
    before,_=previous_holder();before=before-box((31,65,25),(129,76.1,41))
    mesh=mesh_of(solid)
    assert solid.status()==mf.Error.NoError and len(solid.decompose())==1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
    transform=side_transform(mesh)
    placed=mesh.copy();placed.apply_transform(transform)
    assert np.all(placed.bounds[0]>=np.array([25,5,-1e-6]))
    assert np.all(placed.bounds[1]<=np.array([325,305,350]))
    mesh.export(v/(MAIN+'_installed.stl'),file_type='stl_ascii')
    placed.export(OUT/(MAIN+'.stl'),file_type='stl_ascii')
    with ZipFile(OLD/'PTR18_Hanger_v05_No_Top_Tray_TEST_FIT.3mf') as z:
        settings=json.loads(z.read('Metadata/project_settings.config'))
    write_project(OUT/(MAIN+'.3mf'),[(MAIN,mesh,transform)],settings,
        'PTR-18 PLUS cutout-hook prototype with only two tall-pin pockets, two short-pin pockets, six screw-head pockets and one Allen-key through-hole. Detached-fence channel retained; no spare pockets or short tray. Functional fit samples remain v04.')
    report=json.loads((OLD/'Validation/geometry.json').read_text())
    report['revision']='v06 — only the measured attachments and Allen key'
    report['hardware_pockets']=positions
    report['change']=dict(removed_feature='Four spare pin pockets and two larger spare pockets, including their underside bosses',
        layout='Four measured pin pockets grouped left; six measured screw-head pockets grouped right',
        attachment_pocket_count=10,allen_key_hole_count=1,total_top_openings=11,
        removed_volume_mm3=float((before-solid).volume()),added_volume_mm3=float((solid-before).volume()),
        unchanged_fit_projects='../v04-round-key-hole/',same_printer_and_process_settings_as='v05')
    report['design_capacities']['storage']='2 measured tall-pin pockets,2 measured short-pin pockets,6 measured screw-head pockets; one round Allen-key through-hole'
    report['unknowns']=['triangle exact thickness and cutout dimensions','printed clearances for attachments and Allen key',
                        'actual wall cleat thickness, height and bevel','physical fit and loaded performance']
    report['parts']={MAIN:dict(bounds_installed=mesh.bounds.tolist(),bounds_print=placed.bounds.tolist(),
        transform=transform.tolist(),volume_mm3=float(mesh.volume),triangles=len(mesh.faces),
        watertight=bool(mesh.is_watertight),bodies=int(mesh.body_count))}
    (v/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['change'],indent=2))

if __name__=='__main__':main()
