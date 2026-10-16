"""Original 16-slot pliers rack. Installed axes: X along wall, Y up, Z forward.

Two identical independently mounted eight-slot sections; millimetres.
Slot widths are design capacities, not measured fits for the user's tools.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import uuid
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT.parent
OUT = ROOT / 'Revisions/v01-16-slot'
BASE = LIBRARY / 'Caliper Holder/Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P = dict(slot_widths=[12,14,16,18,20,22,24,26], pitch=34., end_margin=24.,
         back_thickness=4., back_reinforced_thickness=6., back_reinforcement_bottom=24.,
         height=58., shelf_thickness=6., shelf_front=91.,
         slot_rear=22., entrance_flare_each_side=1., flare_length=5.,
         rib_width=5., rib_bottom=14., rib_front=83., cleat_projection=17.5,
         cleat_segment_width=60., cleat_angle_degrees=45., wall_gap_between_modules=6.)


def box(lo, hi):
    return mf.Manifold.cube(tuple(np.subtract(hi,lo))).translate(tuple(lo))


def prism_x(points_yz, width, center):
    section = mf.CrossSection([np.array(points_yz)], mf.FillRule.EvenOdd)
    return section.extrude(width).transform(np.array(
        [[0,0,1,center-width/2],[1,0,0,0],[0,1,0,0]],float))


def polygon_y(points_xz, lo, hi):
    # Right-handed transform: extruded +Z becomes installed -Y.
    return mf.CrossSection([np.array(points_xz)],mf.FillRule.EvenOdd).extrude(hi-lo).transform(
        np.array([[1,0,0,0],[0,0,-1,hi],[0,1,0,0]],float))


def union(parts):
    return mf.Manifold.batch_boolean(parts,mf.OpType.Add).simplify(1e-7)


def mesh_of(solid):
    data=solid.to_mesh64()
    return trimesh.Trimesh(np.asarray(data.vert_properties)[:,:3],np.asarray(data.tri_verts),process=False)


def make_module(widths, fit_sample=False):
    centers=np.arange(len(widths))*P['pitch']+P['end_margin']
    width=float(centers[-1]+P['end_margin'])
    shelf_bottom=P['height']-P['shelf_thickness']
    parts=[box((0,0,0),(width,P['height'],P['back_thickness'])),
           box((0,P['back_reinforcement_bottom'],3.8),(width,P['height'],P['back_reinforced_thickness'])),
           box((0,shelf_bottom,3.8),(width,P['height'],P['shelf_front']))]
    # Same 45-degree mating profile as the existing PTR-18 holder. The
    # backing bears against the front of the wooden rail below its bevel.
    cleat_centers=[width/2] if len(widths)<=3 else [55.,width-55.]
    cleat_width=min(P['cleat_segment_width'],width-24)
    for center in cleat_centers:
        parts.append(prism_x([(24.5,-17.5),(42,0),(58,0),(58,-17.5)],cleat_width,center))
    # One rib under each finger, entirely outside every tool opening.
    left_edges=[x-w/2 for x,w in zip(centers,widths)]
    right_edges=[x+w/2 for x,w in zip(centers,widths)]
    finger_gaps=list(zip([0.]+right_edges,left_edges+[width]))
    ribs=[]
    for left,right in finger_gaps:
        assert right-left>=P['rib_width']+2*P['entrance_flare_each_side']
        center=(left+right)/2
        parts.append(prism_x([(P['rib_bottom'],3.8),(shelf_bottom+.2,3.8),
                              (shelf_bottom+.2,P['rib_front'])],P['rib_width'],center))
        ribs.append(dict(center_x=float(center),width=P['rib_width'],finger_width=right-left))
    solid=union(parts)
    cuts=[]
    for x,w in zip(centers,widths):
        # A round closed end spreads stress; the front remains open.
        r=w/2; z=P['slot_rear']+r
        cuts.append(mf.Manifold.cylinder(80,r,circular_segments=96).rotate((-90,0,0)).translate((x,-10,z)))
        cuts.append(box((x-r,-10,z),(x+r,70,P['shelf_front']+2)))
        e=P['entrance_flare_each_side']; front=P['shelf_front']
        cuts.append(polygon_y([(x-r,front-P['flare_length']),(x+r,front-P['flare_length']),
                               (x+r+e,front),(x+r+e,front+2),
                               (x-r-e,front+2),(x-r-e,front)],-10,70))
    solid=solid-union(cuts)
    if fit_sample:
        solid=solid ^ box((-1,48,0),(width+1,60,92))
    mesh=mesh_of(solid)
    assert solid.status()==mf.Error.NoError and len(solid.decompose())==1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
    return mesh,dict(width=width,slot_widths=list(widths),slot_centers_x=centers.tolist(),
                     ribs=ribs,cleat_centers_x=cleat_centers,cleat_segment_width=cleat_width)


def print_pose(mesh,center=(175,160)):
    # Shelf/top lies on the bed; all braces and cleats taper as layers rise.
    r=np.array([[1,0,0],[0,0,1],[0,-1,0]],float)
    v=mesh.vertices@r.T
    t=np.array([center[0],center[1],0.])-np.r_[(v.min(0)[:2]+v.max(0)[:2])/2,v.min(0)[2]]
    transform=np.eye(4); transform[:3,:3]=r; transform[:3,3]=t
    return transform


def project_settings():
    with ZipFile(BASE) as z:
        settings=json.loads(z.read('Metadata/project_settings.config'))
    changes=dict(layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',
                 sparse_infill_density='25%',sparse_infill_pattern='gyroid',
                 top_shell_layers='5',bottom_shell_layers='5',enable_support='0',
                 brim_type='outer_only',brim_width='3',brim_object_gap='0.1',
                 outer_wall_speed='100',top_surface_speed='80',
                 filament_map=['1'],filament_map_mode='Manual',master_extruder_id='1')
    settings.update(changes)
    diff=list(settings['different_settings_to_system'])
    diff[0]=';'.join(sorted(set(filter(None,diff[0].split(';')))|set(changes)))
    settings['different_settings_to_system']=diff
    return settings


def write_project(path,objects,settings):
    ET.register_namespace('',CORE)
    root=ET.Element(f'{{{CORE}}}model',unit='millimeter')
    for key,value in {'Application':'BambuStudio-02.08.02.61','BambuStudio:3mfVersion':'1',
                      'CreationDate':'2026-10-16','Title':path.stem,'Origin':'original',
                      'Description':'Original open-front pliers rack, 19.05 mm plywood / 45 degree French cleat. '
                      'PLA Basic, left nozzle, shelf face down. Tool and wall fit untested.',
                      'ProfileTitle':'PLA left | 0.20 mm | 4 walls | 25% gyroid | no supports'}.items():
        ET.SubElement(root,f'{{{CORE}}}metadata',name=key).text=value
    resources=ET.SubElement(root,f'{{{CORE}}}resources'); build=ET.SubElement(root,f'{{{CORE}}}build')
    config=ET.Element('config'); plate=ET.Element('plate')
    for key,value in [('plater_id','1'),('plater_name',path.stem),('locked','false'),
                      ('filament_map_mode','Manual'),('filament_maps','1'),
                      ('thumbnail_file','Metadata/plate_1.png'),('thumbnail_no_light_file','Metadata/plate_no_light_1.png')]:
        ET.SubElement(plate,'metadata',key=key,value=value)
    for i,(name,mesh,pose) in enumerate(objects,1):
        obj=ET.SubElement(resources,f'{{{CORE}}}object',id=str(i),type='model',name=name)
        xm=ET.SubElement(obj,f'{{{CORE}}}mesh'); vertices=ET.SubElement(xm,f'{{{CORE}}}vertices'); faces=ET.SubElement(xm,f'{{{CORE}}}triangles')
        for v in mesh.vertices:
            ET.SubElement(vertices,f'{{{CORE}}}vertex',**dict(zip('xyz',(f'{a:.10g}' for a in v))))
        for f in mesh.faces:
            ET.SubElement(faces,f'{{{CORE}}}triangle',**dict(zip(('v1','v2','v3'),map(str,f))))
        value=' '.join(f'{a:.10g}' for a in np.r_[pose[:3,:3].T.ravel(),pose[:3,3]])
        ET.SubElement(build,f'{{{CORE}}}item',objectid=str(i),transform=value,printable='1')
        ob=ET.SubElement(config,'object',id=str(i))
        for key,val in [('name',name),('extruder','1')]: ET.SubElement(ob,'metadata',key=key,value=val)
        ET.SubElement(ob,'metadata',face_count=str(len(mesh.faces)))
        part=ET.SubElement(ob,'part',id=str(i),subtype='normal_part',uuid=str(uuid.uuid4()))
        ET.SubElement(part,'metadata',key='name',value=name)
        ET.SubElement(part,'metadata',key='matrix',value='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        ET.SubElement(part,'mesh_stat',face_count=str(len(mesh.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        inst=ET.SubElement(plate,'model_instance')
        for key,val in [('object_id',str(i)),('instance_id','0'),('identify_id',str(6100+i))]:
            ET.SubElement(inst,'metadata',key=key,value=val)
    config.append(plate)
    types=b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/></Types>'
    rels=b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/><Relationship Target="/Metadata/plate_1.png" Id="thumb" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/></Relationships>'
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',types); z.writestr('_rels/.rels',rels)
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/model_settings.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/project_settings.config',json.dumps(settings,indent=2))


def main():
    validation=OUT/'Validation'; validation.mkdir(parents=True,exist_ok=True)
    settings=project_settings()
    module,layout=make_module(P['slot_widths'])
    sample,sample_layout=make_module([12,20,26],fit_sample=True)
    sample_layout['purpose']='Handheld slot-fit gauge only; cropped to top 10 mm, no wall cleat.'
    module.export(validation/'Module_Installed.stl')
    sample.export(validation/'Fit_Sample_Installed.stl')
    projects={
        'Pliers_Rack_v01_16_Slots_PLA_Left_TEST_FIT':[(f'8-slot section {i+1}',module,print_pose(module,(175,y))) for i,y in enumerate([95,220])],
        'Pliers_Rack_v01_8_Slot_Section_PLA_Left_TEST_FIT':[('8-slot section',module,print_pose(module))],
        'Pliers_Rack_v01_3_Slot_Fit_Sample_PLA_Left':[('12 / 20 / 26 mm fit sample',sample,print_pose(sample))],
    }
    report=dict(status='PROTOTYPE — physical tool fit, cleat fit and loaded use untested',
                parameters_mm=P,module=layout,fit_sample=sample_layout,projects={},
                usage='Jaws up, handles down, tool broad faces toward neighboring tools; handles spread front-to-back. '
                      'Joint/head must be wider than chosen slot. Push fully back. Leave neighboring slots empty for very bulky tools if needed.',
                assumptions=['Actual plier dimensions unavailable; mixed-size design capacities only.',
                             'Wall cleat nominal 19.05 mm plywood, 45 degree bevel; height unknown.',
                             'No fixed rear lower spacer, because unknown rail height could make it interfere.'])
    for stem,objects in projects.items():
        write_project(OUT/(stem+'.3mf'),objects,settings)
        placed=[]; object_info=[]
        for name,mesh,pose in objects:
            m=mesh.copy();m.apply_transform(pose); placed.append(m)
            # Conservatively keep the 3 mm brim inside the left nozzle region.
            assert np.all(m.bounds[0]>=np.array([28,5,-1e-6]))
            assert np.all(m.bounds[1]<=np.array([322,305,325]))
            object_info.append(dict(name=name,transform=pose.tolist(),bounds=m.bounds.tolist(),
                                    volume_mm3=mesh.volume,watertight=bool(mesh.is_watertight),
                                    components=mesh.body_count,triangles=len(mesh.faces)))
        trimesh.util.concatenate(placed).export(OUT/(stem+'.stl'))
        report['projects'][stem]=dict(objects=object_info,total_slots=16 if len(objects)==2 else (3 if 'Sample' in stem else 8))
    (validation/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:dict(slots=v['total_slots'],volume_mm3=sum(o['volume_mm3'] for o in v['objects'])) for k,v in report['projects'].items()},indent=2))


if __name__=='__main__':
    main()
