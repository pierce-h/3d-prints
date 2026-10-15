"""Original French-cleat storage prototype for the TSO PTR-18 PLUS.

Installed axes: X along wall, Y up, Z toward user. Millimetres.
Only published tool dimensions are treated as facts; roomy storage clearances
are design capacities. The small samples are for physical fitting before use.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import uuid
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as mf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions' / 'v01-test-fit'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P = dict(width=260., back_web=4., back_reinforced=6., ymin=-55., ymax=68., cleat_projection=17.5,
         cleat_front_bevel_y=42., cleat_top_y=58., cleat_segment_width=70., peg_y=-35., peg_pitch=192.,
         shaft_d=16., head_d=19.2, peg_root_z=10., keeper_start_z=34., peg_end_z=38.,
         shelf_bottom_y=47., shelf_top_y=51., fence_back_z=9., fence_front_z=49.,
         fence_lip_top_y=68., shelf_front_z=114.)


def box(lo, hi):
    return mf.Manifold.cube(tuple(np.subtract(hi, lo))).translate(tuple(lo))


def prism_x(points_yz, width, x_center=0):
    sec = mf.CrossSection([np.asarray(points_yz)], mf.FillRule.EvenOdd)
    return sec.extrude(width).transform(np.array(
        [[0, 0, 1, x_center-width/2], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def union(parts):
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add).simplify(1e-7)


def mesh_of(s):
    v = s.to_mesh64()
    return trimesh.Trimesh(np.asarray(v.vert_properties)[:, :3],
                          np.asarray(v.tri_verts), process=False)


def cylinder_y(x, z, diameter, ylo, yhi):
    return mf.Manifold.cylinder(yhi-ylo, diameter/2, circular_segments=72).rotate(
        (-90, 0, 0)).translate((x, ylo, z))


def cleat(width):
    return prism_x([(24.5, -17.5), (42, 0), (58, 0), (58, -17.5)], width)


def peg(x=0, y=-35):
    # 24 mm clear axial space between the root face and the retaining shoulder.
    # Heads remain below nominal 20 mm tool-hole diameter for insertion.
    return union([
        mf.Manifold.cylinder(5, 14, 8, circular_segments=96).translate((x, y, 5)),
        mf.Manifold.cylinder(24.2, 8, circular_segments=96).translate((x, y, 9.9)),
        mf.Manifold.cylinder(3, 9.6, circular_segments=96).translate((x, y, 34)),
        mf.Manifold.cylinder(1, 9.6, 8.7, circular_segments=96).translate((x, y, 37)),
    ])


def fence_channel(width):
    half = width/2
    return union([
        box((-half, 47, 5.8), (half, 51, 53)),
        box((-half, 50.9, 6), (half, 68, 9)),
        box((-half, 50.9, 49), (half, 68, 53)),
    ])


def main_holder():
    rack = box((-130, 45, 52.9), (130, 51, 114))
    holes = []
    positions = []
    for x in (-114, -90, -66, -42):
        for z in (64, 90):
            positions.append(dict(type='M6 clearance', x=x, z=z, diameter=6.6))
    for x in (-17, 1, 19):
        for z in (61, 76):
            positions.append(dict(type='M4 clearance', x=x, z=z, diameter=4.6))
    for x in (54, 101):
        positions.append(dict(type='M8 clearance', x=x, z=90, diameter=8.8))
    positions.append(dict(type='3 mm hex key', x=19, z=98, diameter=3.8))
    for p in positions:
        holes.append(cylinder_y(p['x'], p['z'], p['diameter'], 38, 52))
    rack = rack - union(holes)
    # Slim open-top tray, separate from the fence channel and pin holes.
    tray = union([
        box((31, 50.9, 53), (34, 62, 69)),
        box((126, 50.9, 53), (129, 62, 69)),
        box((31, 50.9, 66), (129, 62, 69)),
    ])
    # Raised shelf webs leave at least 66 mm above peg centres before a tool
    # can touch their underside. Actual hole-to-edge offset remains unverified.
    webs = [prism_x([(31, 5.8), (45.1, 78), (47.1, 78), (47.1, 5.8)], 6, x)
            for x in (-126, -26, 26, 126)]
    # The 45-degree notch removes unused backing while its returning edge
    # builds progressively in the side-print orientation.
    outline=[(-130,68),(130,68),(130,-55),(95,-55),(19,21),(-19,21),(-95,-55),(-130,-55)]
    back=mf.CrossSection([outline],mf.FillRule.EvenOdd).extrude(4)
    reinforced=[box((-130,21,3.9),(130,68,6))]
    reinforced += [mf.Manifold.cylinder(2.2,15,circular_segments=96).translate((x,-35,3.8))
                   for x in (-96,96)]
    body = union([back,*reinforced,cleat(70).translate((-85,0,0)),cleat(70).translate((85,0,0)),
                  fence_channel(260), rack, tray, *webs, peg(-96), peg(96)])
    return body, positions


def samples():
    c = union([box((-17.5, 10, 0), (17.5, 58, 6)), cleat(35)])
    p = union([box((-16, -51, 0), (16, -19, 6)), peg()])
    f = fence_channel(20)
    h = box((-10, 45, -42), (10, 51, 42))
    # Same 6 mm bank thickness and horizontal print-hole axes as the full rack.
    for z, d in zip((-30, -10, 10, 30), (4.6, 6.6, 8.8, 3.8)):
        h = h - cylinder_y(0, z, d, 44, 52)
    return [('Cleat_Fit', c), ('Peg_Fit', p), ('Fence_Channel_Fit', f), ('Hardware_Holes_Fit', h)]


def side_transform(mesh, center=(175, 155)):
    # X becomes print height; peg bending plane is within the printed layers.
    r = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float)
    v = mesh.vertices @ r.T
    t = np.array([center[0], center[1], 0.])
    t[:2] -= (v.min(axis=0)[:2] + v.max(axis=0)[:2])/2
    t[2] -= v.min(axis=0)[2]
    m = np.eye(4); m[:3, :3] = r; m[:3, 3] = t
    return m


def write_project(path, objects, settings, description):
    ET.register_namespace('', CORE)
    root = ET.Element(f'{{{CORE}}}model', {'unit':'millimeter',
                      '{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    meta = {'Application':'BambuStudio-02.08.02.61', 'BambuStudio:3mfVersion':'1',
            'CreationDate':'2026-10-14', 'Title':path.stem, 'Origin':'original',
            'Description':description, 'ProfileTitle':'TEST FIT — 0.20 mm, 6 walls, 30% gyroid'}
    for k,v in meta.items():
        ET.SubElement(root, f'{{{CORE}}}metadata', name=k).text = v
    resources = ET.SubElement(root, f'{{{CORE}}}resources')
    build = ET.SubElement(root, f'{{{CORE}}}build')
    config = ET.Element('config'); plate = ET.Element('plate')
    for k,v in [('plater_id','1'),('plater_name',path.stem),('locked','false'),
                ('filament_map_mode','Auto For Flush'), ('thumbnail_file','Metadata/plate_1.png'),
                ('thumbnail_no_light_file','Metadata/plate_no_light_1.png')]:
        ET.SubElement(plate,'metadata',key=k,value=v)
    for i,(name,mesh,mat) in enumerate(objects,1):
        obj = ET.SubElement(resources,f'{{{CORE}}}object',id=str(i),type='model',name=name)
        xm = ET.SubElement(obj,f'{{{CORE}}}mesh')
        vs=ET.SubElement(xm,f'{{{CORE}}}vertices'); fs=ET.SubElement(xm,f'{{{CORE}}}triangles')
        for v in mesh.vertices:
            ET.SubElement(vs,f'{{{CORE}}}vertex',**dict(zip('xyz',('%.12g'%a for a in v))))
        for f in mesh.faces:
            ET.SubElement(fs,f'{{{CORE}}}triangle',**dict(zip(('v1','v2','v3'),map(str,f))))
        transform=' '.join('%.12g'%a for a in np.r_[mat[:3,:3].T.ravel(),mat[:3,3]])
        ET.SubElement(build,f'{{{CORE}}}item',objectid=str(i),transform=transform,printable='1')
        ob=ET.SubElement(config,'object',id=str(i))
        ET.SubElement(ob,'metadata',key='name',value=name)
        ET.SubElement(ob,'metadata',key='extruder',value='1')
        ET.SubElement(ob,'metadata',face_count=str(len(mesh.faces)))
        part=ET.SubElement(ob,'part',id=str(i),subtype='normal_part',uuid=str(uuid.uuid4()))
        ET.SubElement(part,'metadata',key='name',value=name)
        ET.SubElement(part,'metadata',key='matrix',value='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        ET.SubElement(part,'mesh_stat',face_count=str(len(mesh.faces)),edges_fixed='0',
            degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        inst=ET.SubElement(plate,'model_instance')
        for k,v in [('object_id',str(i)),('instance_id','0'),('identify_id',str(5000+i))]:
            ET.SubElement(inst,'metadata',key=k,value=v)
    config.append(plate)
    content=b'''<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/></Types>'''
    rel=b'''<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/><Relationship Target="/Metadata/plate_1.png" Id="thumb" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/></Relationships>'''
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content); z.writestr('_rels/.rels',rel)
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/model_settings.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/project_settings.config',json.dumps(settings,indent=2))


def main():
    validation=OUT/'Validation'; validation.mkdir(parents=True,exist_ok=True)
    settings=json.loads((ROOT/'Source/H2D_Profile_Base.json').read_text())
    changes=dict(wall_loops='6',sparse_infill_density='30%',sparse_infill_pattern='gyroid',
        top_shell_layers='6',bottom_shell_layers='6',enable_support='1',support_type='tree(auto)',
        support_style='default',support_threshold_angle='30',support_on_build_plate_only='0',
        support_critical_regions_only='1',brim_type='outer_only',brim_width='6',brim_object_gap='0.1')
    settings.update(changes)
    diff=list(settings['different_settings_to_system'])
    diff[0]=';'.join(sorted(set(filter(None,diff[0].split(';')))|set(changes)))
    settings['different_settings_to_system']=diff
    solid,positions=main_holder()
    pieces=[('PTR18_Hanger_v01_TEST_FIT',solid)]+samples()
    report=dict(status='PROTOTYPE — dimensions not published by TSO remain unverified; print fit samples first.',
        parameters_mm=P, hardware_positions=positions, parts={}, known_dimensions=dict(
            tool_hole_diameter=20, tool_hole_pitch=96, triangle_nominal_leg=457.2,
            standard_pin_threads='M6',standard_screw_threads='M4x0.7'),
        design_capacities=dict(fence_channel_clear_width_mm=40, fence_channel_lip_height_mm=17,
            fence_length='Open-ended; longer fences overhang', peg_plate_clearance_mm=24,
            storage='8 M6, 6 M4, 2 M8 clearance holes; hex key hole; 92 x 13 mm tray'),
        unknowns=['triangle thickness','fence dimensions','triangle hole-to-edge offsets',
            'types and dimensions of extra attachments','actual wall cleat thickness and height',
            'physical fit, strength and long-term loaded performance'])
    sample_objects=[]
    centers=[(125,105),(220,105),(125,180),(220,185)]
    for index,(name,s) in enumerate(pieces):
        mesh=mesh_of(s)
        assert s.status()==mf.Error.NoError and len(s.decompose())==1
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
        mesh.export(validation/(name+'_installed.stl'),file_type='stl_ascii')
        if index==0:
            transform=side_transform(mesh)
            write_project(OUT/(name+'.3mf'),[(name,mesh,transform)],settings,
                'Original prototype for PTR-18 PLUS storage with detached fence, hardware rack and nominal 3/4-inch 45-degree French cleat. Published 20 mm holes and 96 mm pitch determine two 192 mm-spaced pegs. Fence cradle is a design capacity, not a measured TSO fit. Print fit samples before the full holder.')
        else:
            transform=side_transform(mesh,centers[index-1])
            sample_objects.append((name,mesh,transform))
        placed=mesh.copy();placed.apply_transform(transform)
        assert np.all(placed.bounds[0]>=np.array([25,5,-1e-6]))
        assert np.all(placed.bounds[1]<=np.array([325,305,350]))
        placed.export(OUT/(name+'.stl'),file_type='stl_ascii')
        report['parts'][name]=dict(bounds_installed=mesh.bounds.tolist(),bounds_print=placed.bounds.tolist(),
            transform=transform.tolist(),volume_mm3=mesh.volume,triangles=len(mesh.faces),
            watertight=bool(mesh.is_watertight),bodies=mesh.body_count)
    write_project(OUT/'PTR18_Fit_Check_Plate_v01.3mf',sample_objects,settings,
        'Print first. Four separate samples: French-cleat mating profile, hanging peg, open-ended 40 mm fence channel, and M4/M6/M8/hex-key clearance-hole gauge. These samples do not establish a load rating.')
    (validation/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
