"""Upright divider tray inspired by the user's reference, with French cleats.

Original geometry. Installed axes X along wall, Y up, Z forward; millimetres.
The preceding v01 hanging-comb geometry remains archived and is superseded.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as mf
import build_holder as base

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Revisions/v02-upright-divider-tray'
P=dict(bay_widths=[24,24,28,28,32,32,36,36],floor_thickness=3.2,
       back_thickness=3.2,divider_thickness=2.8,outer_wall_thickness=3.2,
       height=130.,depth=105.,front_lip_height=18.,front_lip_thickness=4.,
       cleat_projection=17.5,cleat_segment_width=60.,cleat_pad_thickness=6.,
       module_gap=6.,sample_height=35.)
STEMS={
 'full':'Pliers_Tray_v02_16_Bays_PLA_Left_TEST_FIT',
 'section':'Pliers_Tray_v02_8_Bay_Section_PLA_Left_TEST_FIT',
 'sample':'Pliers_Tray_v02_3_Bay_Fit_Sample_PLA_Left',
}


def make_tray(widths,sample=False):
    outside=P['outer_wall_thickness']; divider=P['divider_thickness']
    width=sum(widths)+2*outside+(len(widths)-1)*divider
    positions=[]; walls=[(0,outside)]; x=outside
    for i,w in enumerate(widths):
        positions.append(dict(left=x,right=x+w,width=w,center=x+w/2))
        x+=w
        thickness=outside if i==len(widths)-1 else divider
        walls.append((x,x+thickness)); x+=thickness
    assert abs(x-width)<1e-7
    height=P['height']; depth=P['depth']
    parts=[base.box((0,0,0),(width,P['floor_thickness'],depth)),
           base.box((0,0,0),(width,height,P['back_thickness'])),
           base.box((0,0,depth-P['front_lip_thickness']),
                    (width,P['front_lip_height'],depth))]
    # Tall at the back, low at the front for access. Small bevels soften the
    # exposed change in direction without increasing print overhangs.
    profile=[(0,3),(130,3),(130,12),(128,16),(54,28),(50,30),
             (28,101),(24,105),(0,105)]
    for lo,hi in walls:
        parts.append(base.prism_x(profile,hi-lo,(lo+hi)/2))
    cleat_centers=[]
    if not sample:
        cleat_centers=[45.,width-45.]
        for center in cleat_centers:
            # Reinforce the entire cleat attachment, not merely its top.
            # A 45-degree lower ramp avoids a small support ledge inside bays.
            parts.append(base.prism_x([(89,3),(92,6),(130,6),(130,3)],68,center))
            parts.append(base.prism_x([(96.5,-17.5),(114,0),(130,0),(130,-17.5)],
                                      P['cleat_segment_width'],center))
    solid=base.union(parts)
    if sample:
        solid=solid ^ base.box((-1,0,-1),(width+1,P['sample_height'],depth+1))
    mesh=base.mesh_of(solid)
    assert solid.status()==mf.Error.NoError and len(solid.decompose())==1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
    return mesh,dict(width=width,bay_widths=widths,bays=positions,divider_intervals=walls,
                     height=P['sample_height'] if sample else height,
                     depth_including_cleat=depth if sample else depth+P['cleat_projection'],
                     cleat_centers=cleat_centers)


def pose(mesh,center=(175,160)):
    # Installed upright: floor on bed. Right-handed mapping to print Z-up.
    r=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)
    v=mesh.vertices@r.T
    t=np.r_[center,0.]-np.r_[(v.min(0)[:2]+v.max(0)[:2])/2,v.min(0)[2]]
    m=np.eye(4);m[:3,:3]=r;m[:3,3]=t
    return m


def settings():
    s=base.project_settings()
    changes=dict(enable_support='1',support_type='tree(auto)',support_style='default',
                 support_threshold_angle='30',support_on_build_plate_only='1',
                 support_critical_regions_only='1',brim_width='4',
                 support_filament='0',support_interface_filament='0')
    s.update(changes)
    diff=list(s['different_settings_to_system'])
    diff[0]=';'.join(sorted(set(filter(None,diff[0].split(';')))|set(changes)))
    s['different_settings_to_system']=diff
    return s


def write_project(path,objects,s,is_sample=False):
    base.write_project(path,objects,s)
    with ZipFile(path) as z:data={n:z.read(n) for n in z.namelist()}
    root=ET.fromstring(data['3D/3dmodel.model'])
    for meta in root.findall(f'{{{base.CORE}}}metadata'):
        if meta.get('name')=='Description':
            meta.text=('Original upright pliers tray with closed floor and divider fins, matching the user reference direction. '
                       'PLA Basic left nozzle, floor-down printing. '+
                       ('Three shallow bays for fit checks; no wall mount.' if is_sample else
                        'Integrated French cleat for nominal 19.05 mm plywood / 45 degree bevel; rear supports enabled.')+
                       ' Physical tool fit and loaded use untested.')
        if meta.get('name')=='ProfileTitle':
            meta.text='PLA left | 0.20 mm | 4 walls | 25% gyroid | upright tray'
    data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,value in data.items():z.writestr(name,value)


def main():
    validation=OUT/'Validation';validation.mkdir(parents=True,exist_ok=True)
    module,layout=make_tray(P['bay_widths'])
    sample,sample_layout=make_tray([24,30,36],sample=True)
    module.export(validation/'Module_Installed.stl')
    sample.export(validation/'Fit_Sample_Installed.stl')
    config=settings()
    projects={
        'full':[(f'8-bay upright tray {i+1}',module,pose(module,(175,y))) for i,y in enumerate([89,226])],
        'section':[('8-bay upright tray',module,pose(module))],
        'sample':[('24 / 30 / 36 mm shallow fit tray',sample,pose(sample))],
    }
    report=dict(status='PROTOTYPE — physical fit and loaded use untested',parameters_mm=P,
                module=layout,fit_sample=sample_layout,projects={},
                reference='User screenshot of red Pliersrack, 2026-10-16; functional layout reference, original CAD dimensions.',
                supersedes='v01 hanging comb: wrong design direction for the user.',
                usage='Place tools between dividers, supported by the closed floor; choose the end/orientation that sits stably. '
                      'No minimum tool-head width is required. Tall or bulky tools may need extra adjacent clearance.',
                unknowns=['Actual tool widths, lengths and stable seating','Actual wooden rail height and mating fit','Loaded performance'])
    for label,objects in projects.items():
        s=dict(config)
        if label=='sample':s['enable_support']='0'
        stem=STEMS[label];write_project(OUT/(stem+'.3mf'),objects,s,label=='sample')
        placed=[];details=[]
        for name,mesh,transform in objects:
            m=mesh.copy();m.apply_transform(transform);placed.append(m)
            assert np.all(m.bounds[0]>=np.array([25,10,-1e-6]))
            assert np.all(m.bounds[1]<=np.array([325,310,325]))
            details.append(dict(name=name,bounds=m.bounds.tolist(),transform=transform.tolist(),
                                volume_mm3=mesh.volume,watertight=True,components=mesh.body_count,
                                triangles=len(mesh.faces)))
        trimesh.util.concatenate(placed).export(OUT/(stem+'.stl'))
        report['projects'][label]=dict(stem=stem,bays=16 if label=='full' else 8 if label=='section' else 3,objects=details)
    (validation/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(module=layout,sample=sample_layout),indent=2))


if __name__=='__main__':main()
