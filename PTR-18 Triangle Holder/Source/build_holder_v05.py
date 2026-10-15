"""v05 removes the small top tray; functional fit samples remain v04."""
from pathlib import Path
from zipfile import ZipFile
import json
import numpy as np
from build_holder import box,mesh_of,side_transform,write_project
from build_holder_v04 import main_holder

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'Revisions/v04-round-key-hole'
OUT=ROOT/'Revisions/v05-no-top-tray'
MAIN='PTR18_Hanger_v05_No_Top_Tray_TEST_FIT'

def main():
    v=OUT/'Validation';v.mkdir(parents=True,exist_ok=True)
    before,positions=main_holder()
    # Clip only above the shelf. The fence wall ends at Z25 and is preserved.
    removed_region=box((31,65,25),(129,76.1,41))
    solid=before-removed_region
    mesh=mesh_of(solid)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
    transform=side_transform(mesh)
    placed=mesh.copy();placed.apply_transform(transform)
    assert np.all(placed.bounds[0]>=np.array([25,5,-1e-6]))
    assert np.all(placed.bounds[1]<=np.array([325,305,350]))
    mesh.export(v/(MAIN+'_installed.stl'),file_type='stl_ascii')
    placed.export(OUT/(MAIN+'.stl'),file_type='stl_ascii')
    with ZipFile(OLD/'PTR18_Hanger_v04_Round_Key_Hole_TEST_FIT.3mf') as z:
        settings=json.loads(z.read('Metadata/project_settings.config'))
    write_project(OUT/(MAIN+'.3mf'),[(MAIN,mesh,transform)],settings,
        'PTR-18 PLUS cutout-hook prototype with measured attachment pockets, detached-fence channel and round Allen-key through-hole. Small top tray removed; shelf flat there. Functional fit samples remain v04.')
    report=json.loads((OLD/'Validation/geometry.json').read_text())
    report['revision']='v05 — small top tray removed'
    report['change']=dict(removed_feature='Three raised walls of the short loose-parts tray',
        removal_bounds_installed=[[31,65,25],[129,76.1,41]],
        removed_volume_mm3=float((before-solid).volume()),
        added_volume_mm3=float((solid-before).volume()),
        unchanged_fit_projects='../v04-round-key-hole/',
        same_printer_and_process_settings_as='v04')
    report['design_capacities']['storage']=report['design_capacities']['storage'].replace('; small tray','')
    report['parts']={MAIN:dict(bounds_installed=mesh.bounds.tolist(),bounds_print=placed.bounds.tolist(),
        transform=transform.tolist(),volume_mm3=float(mesh.volume),triangles=len(mesh.faces),
        watertight=bool(mesh.is_watertight),bodies=int(mesh.body_count))}
    (v/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['change'],indent=2))

if __name__=='__main__':main()
