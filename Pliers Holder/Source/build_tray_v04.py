"""Upright divider tray inspired by the user's reference, with French cleats.

Original geometry. Installed axes X along wall, Y up, Z forward; millimetres.
v04 is one continuous sixteen-bay body, placed diagonally on the H2D left nozzle area.
Earlier revisions remain archived unchanged.
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
OUT=ROOT/'Revisions/v04-monolithic-diagonal'
P=dict(bay_widths=[16,16,16,16,18,18,18,18,20,20,20,20,22,22,24,24],floor_thickness=3.2,
       back_thickness=3.2,divider_thickness=2.8,outer_wall_thickness=3.2,
       height=177.8,depth=63.5,front_lip_height=18.,front_lip_thickness=4.,
       cleat_projection=17.5,cleat_segment_width=60.,cleat_pad_thickness=6.,
       print_angle_degrees=45.,sample_height=35.,max_bay_width=24.)
STEMS={'full':'Pliers_Tray_v04_Monolithic_16_Slots_PLA_Left_TEST_FIT'}

BED=dict(plate_xy=[[0,0],[350,320]], left_nozzle_xy=[[0,0],[325,320]],
         left_nozzle_height=320, wrapping_exclusion_xy=[[145,310],[256,326]])


def make_tray(widths,sample=False):
    assert all(0 < w <= P['max_bay_width'] for w in widths)
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
    profile=[(0,3),(height,3),(height,10),(height-2,14),
             (65,22),(61,24),(28,depth-4),(24,depth),(0,depth)]
    for lo,hi in walls:
        parts.append(base.prism_x(profile,hi-lo,(lo+hi)/2))
    cleat_centers=[]
    if not sample:
        cleat_centers=[45.,width/2,width-45.]
        for center in cleat_centers:
            # Reinforce the entire cleat attachment, not merely its top.
            # A 45-degree lower ramp avoids a small support ledge inside bays.
            parts.append(base.prism_x([(height-41,3),(height-38,6),
                                       (height,6),(height,3)],68,center))
            parts.append(base.prism_x([(height-33.5,-17.5),(height-16,0),
                                      (height,0),(height,-17.5)],
                                      P['cleat_segment_width'],center))
    solid=base.union(parts)
    if sample:
        solid=solid ^ base.box((-1,0,-1),(width+1,P['sample_height'],depth+1))
    mesh=base.mesh_of(solid)
    # Remove tiny coplanar slivers before STL precision rounding.
    mesh.process(validate=True)
    assert solid.status()==mf.Error.NoError and len(solid.decompose())==1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
    return mesh,dict(width=width,bay_widths=widths,bays=positions,divider_intervals=walls,
                     height=P['sample_height'] if sample else height,
                     depth_including_cleat=depth if sample else depth+P['cleat_projection'],
                     cleat_centers=cleat_centers)


def pose(mesh,center=(162.5,155.)):
    # Floor down, then rotate in the build plane. Preserve this saved pose.
    upright=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)
    theta=np.deg2rad(P['print_angle_degrees'])
    spin=np.array([[np.cos(theta),-np.sin(theta),0],
                   [np.sin(theta),np.cos(theta),0],[0,0,1]],float)
    r=spin@upright
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
            meta.text=('One continuous 16-slot pliers tray with 16–24 mm clear bays, a closed floor and divider fins. '
                       'PLA Basic left nozzle, floor-down printing rotated 45 degrees on the H2D. '+
                       ('Three shallow bays for fit checks; no wall mount.' if is_sample else
                        'Integrated French cleat for nominal 19.05 mm plywood / 45 degree bevel; rear supports enabled.')+
                       ' Physical tool fit and loaded use untested.')
        if meta.get('name')=='ProfileTitle':
            meta.text='H2D PLA left | one piece | diagonal 45 degrees | 0.20 mm | 4 walls'
    data['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for name,value in data.items():z.writestr(name,value)


def main():
    validation=OUT/'Validation';validation.mkdir(parents=True,exist_ok=True)
    tray,layout=make_tray(P['bay_widths'])
    tray.export(validation/'Tray_Installed.stl')
    transform=pose(tray)
    objects=[('Monolithic 16-slot pliers tray',tray,transform)]
    stem=STEMS['full']
    write_project(OUT/(stem+'.3mf'),objects,settings())
    placed=tray.copy();placed.apply_transform(transform)
    assert np.all(placed.bounds[0]>=np.array([0,0,-1e-6]))
    assert np.all(placed.bounds[1]<=np.array([325,320,320]))
    placed.export(OUT/(stem+'.stl'))
    report=dict(status='PROTOTYPE — physical fit and loaded use untested',
                parameters_mm=P,module=layout,bed=BED,
                projects={'full':dict(stem=stem,bays=16,objects=[dict(
                    name=objects[0][0],bounds=placed.bounds.tolist(),transform=transform.tolist(),
                    volume_mm3=tray.volume,watertight=True,components=tray.body_count,
                    triangles=len(tray.faces))])},
                reference='User reference height 177.8 mm and tray depth 63.5 mm; user maximum clear slot 24 mm.',
                requested_max_clear_bay_mm=24,
                supersedes='v03 two independent trays; v04 is one continuous body with a middle divider and three rear cleats.',
                fit_sample='../v03-24mm-max-slots/Pliers_Tray_v03_3_Bay_Fit_Sample_PLA_Left.3mf',
                usage='Tools rest on the solid floor between upright dividers. Choose stable seating for each tool.',
                unknowns=['Actual tool fit and stable seating','Actual wooden rail height and mating fit','Loaded performance'])
    (validation/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(width_mm=layout['width'],bays=layout['bay_widths'],
                         angle_degrees=P['print_angle_degrees'],bounds=placed.bounds.tolist(),
                         components=placed.body_count),indent=2))


if __name__=='__main__':main()
