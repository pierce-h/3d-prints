"""v03: measured attachment bodies, cutout hook, fence cradle and Allen-key pockets.
Installed coordinates: X along wall, Y up, Z toward user; millimetres.
"""
from pathlib import Path
import json
import numpy as np
import manifold3d as mf
from build_holder import box, prism_x, union, mesh_of, cylinder_y, cleat, side_transform, write_project

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'Revisions/v03-measured-attachments'
MAIN = 'PTR18_Hanger_v03_Measured_Attachments_TEST_FIT'
P = dict(width=260., hook_width=80., hook_plate_gap=8., hook_bearing_y=-40.,
         hook_lip_height=10., hook_floor_thickness=8., fence_clear_width=12.,
         fence_lip_height=13., shelf_top_y=65., shelf_front_z=82.,
         key_slot_length=40., key_slot_width=8., key_pocket_depth=35.)


def prism_y(points_xz, ylo, yhi):
    return mf.CrossSection([np.asarray(points_xz)],mf.FillRule.EvenOdd).extrude(yhi-ylo).transform(
        np.array([[1,0,0,0],[0,0,-1,yhi],[0,1,0,0]],float))


def key_void():
    # Pointed 45-degree ends avoid a broad internal roof in the side print pose.
    return prism_y([(-21,72),(-17,68),(15,68),(19,72),(15,76),(-17,76)],30,66)


def key_pocket():
    return box((-24,27,65),(22,65,79)) - key_void()


def hook(width=80):
    # 8 mm plate gap between back Z6 and front lip Z14; load bearing top Y-40.
    return union([box((-width/2,-48,4),(width/2,-40,18)),
                  box((-width/2,-40.1,14),(width/2,-30,18))])


def fence_channel(width):
    return union([box((-width/2,61,5.8),(width/2,65,25)),
                  box((-width/2,64.9,6),(width/2,78,9)),
                  box((-width/2,64.9,21),(width/2,78,25))])


def hardware_positions():
    out=[]
    for x in (-112,-88):
        out.append(dict(type='measured short pin pocket',x=x,z=40,diameter=9.8,depth=8,body_diameter=9,body_height=12))
        out.append(dict(type='measured tall pin pocket',x=x,z=64,diameter=9.8,depth=16,body_diameter=9,body_height=25))
    for x in (-64,-40):
        for z,depth in ((40,6),(64,13)):
            out.append(dict(type='spare pin pocket',x=x,z=z,diameter=12.,depth=depth))
    for x in (-17,1,19):
        for z in (37,52):
            out.append(dict(type='measured screw head pocket',x=x,z=z,diameter=6.8,depth=2.5,body_diameter=6,body_height=4))
    for x in (54,101):
        out.append(dict(type='extra attachment pocket',x=x,z=64,diameter=16.,depth=13))
    return out


def pocket_solid(diameter, depth, x=0,z=0):
    return cylinder_y(x,z,diameter+6,65-depth-3,65) - cylinder_y(x,z,diameter,65-depth,66)


def main_holder():
    outline=[(-130,78),(130,78),(130,32),(46,-57),(-46,-57),(-130,32)]
    back=mf.CrossSection([outline],mf.FillRule.EvenOdd).extrude(4)
    parts=[back,box((-130,21,3.9),(130,78,6)),box((-44,-57,3.9),(44,21.1,6)),
           cleat(70).translate((-85,0,0)),cleat(70).translate((85,0,0)),
           hook(),fence_channel(260),box((-130,59,24.9),(130,65,82)),key_pocket()]
    # Loose-parts tray shares the fence channel's front wall.
    parts += [box((31,64.9,25),(34,76,41)),box((126,64.9,25),(129,76,41)),
              box((31,64.9,38),(129,76,41))]
    # Minimum web underside Y49 permits 77 mm top-bar height plus 12 mm lift.
    parts += [prism_x([(49,5.8),(59.1,53),(61.1,53),(61.1,5.8)],6,x)
              for x in (-126,-26,26,126)]
    positions=hardware_positions()
    # Add closed floors first, then cut all cavities through the entire union.
    for p in positions:
        if p['depth']>4:
            parts.append(cylinder_y(p['x'],p['z'],p['diameter']+6,65-p['depth']-3,65))
    body=union(parts)
    cavities=[cylinder_y(p['x'],p['z'],p['diameter'],65-p['depth'],66) for p in positions]
    body=body-union(cavities+[key_void()])
    return body,positions


def samples():
    c=union([box((-17.5,10,0),(17.5,58,6)),cleat(35)])
    h=union([box((-40,-57,0),(40,-20,6)),hook()])
    f=fence_channel(20)
    # Connected test bank uses the actual depths and diameters of the storage.
    test_positions=[(0,9.8,8),(24,9.8,16),(48,6.8,2.5)]
    p=box((-12,59,-12),(60,65,12))
    for x,d,depth in test_positions:
        if depth>4:p=p+cylinder_y(x,0,d+6,65-depth-3,65)
    p=p-union([cylinder_y(x,0,d,65-depth,66) for x,d,depth in test_positions])
    return [('Cleat_Fit',c),('Cutout_Hook_Fit',h),('Fence_Channel_Fit',f),
            ('Attachment_Pockets_Fit',p),('Allen_Key_Pocket_Fit',key_pocket())]


def main():
    v=OUT/'Validation';v.mkdir(parents=True,exist_ok=True)
    settings=json.loads((ROOT/'Source/H2D_Profile_Base.json').read_text())
    changes=dict(wall_loops='6',sparse_infill_density='30%',sparse_infill_pattern='gyroid',
        top_shell_layers='6',bottom_shell_layers='6',enable_support='1',support_type='tree(auto)',
        support_style='default',support_threshold_angle='30',support_on_build_plate_only='0',
        support_critical_regions_only='1',brim_type='outer_only',brim_width='6',brim_object_gap='0.1')
    settings.update(changes)
    diff=list(settings['different_settings_to_system'])
    diff[0]=';'.join(sorted(set(filter(None,diff[0].split(';')))|set(changes)))
    settings['different_settings_to_system']=diff
    body,positions=main_holder()
    report=dict(status='FIRST-FIT PROTOTYPE; physical fit and loaded strength unverified.',
        parameters_mm=P,hardware_pockets=positions,parts={},
        user_measurements=dict(attachment_bodies_excluding_threads=[dict(count=2,diameter_mm=9,height_mm=25),dict(count=2,diameter_mm=9,height_mm=12),dict(count=6,diameter_mm=6,height_mm=4)],fence_mm=[430,20,10],triangle_thickness='Roughly the same as the prior TSO tool; not measured numerically.'),
        design_capacities=dict(hook_plate_gap_mm=8,hook_width_mm=80,hook_lip_height_mm=10,
            outer_top_edge_to_cutout_bearing_edge_max_mm=77,assumed_removal_lift_mm=12,
            fence_clear_width_mm=12,fence_lip_height_mm=13,
            key_pocket_clear_envelope_mm=[40,8,35],key_pocket_shape='45-degree pointed ends; 32 mm of full-width opening',
            storage='2 measured tall-pin pockets,2 measured short-pin pockets,6 measured screw-head pockets,4 spare pin pockets,2 larger spare pockets; closed Allen-key pocket; small tray',
            measured_pocket_diametral_clearance_mm=0.8,exposed_body_height_mm=dict(tall_pin=9,short_pin=4,screw_head=1.5)),
        unknowns=['triangle exact thickness and cutout dimensions','thread lengths (not needed for body-first storage)',
                  'extra attachment and Allen-key dimensions','actual wall cleat thickness, height and bevel','physical fit and loaded performance'])
    small=[]
    centers=[(110,100),(195,100),(265,100),(130,190),(235,190)]
    for i,(name,solid) in enumerate([(MAIN,body)]+samples()):
        mesh=mesh_of(solid)
        assert solid.status()==mf.Error.NoError and len(solid.decompose())==1,name
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1,name
        mesh.export(v/(name+'_installed.stl'),file_type='stl_ascii')
        transform=side_transform(mesh,(175,155) if i==0 else centers[i-1])
        placed=mesh.copy();placed.apply_transform(transform)
        assert np.all(placed.bounds[0]>=np.array([25,5,-1e-6]))
        assert np.all(placed.bounds[1]<=np.array([325,305,350]))
        placed.export(OUT/(name+'.stl'),file_type='stl_ascii')
        if i==0:
            write_project(OUT/(name+'.3mf'),[(name,mesh,transform)],settings,
                'PTR-18 PLUS prototype: cutout hook, cradle for user-measured430x20x10mm detached fence, closed pockets fitted to measured 9x25,9x12,6x4mm attachment bodies and Allen-key pocket. Print fit checks first.')
        else:
            small.append((name,mesh,transform))
            if name=='Attachment_Pockets_Fit':
                write_project(OUT/'Attachment_Pockets_Fit_v03.3mf',[(name,mesh,side_transform(mesh))],settings,
                    'Quick fit check for the three user-measured attachment bodies. Closed pockets: diameter9.8 x depth8; diameter9.8 x depth16; diameter6.8 x depth2.5 mm. Body-first, threads up.')
        report['parts'][name]=dict(bounds_installed=mesh.bounds.tolist(),bounds_print=placed.bounds.tolist(),
            transform=transform.tolist(),volume_mm3=float(mesh.volume),triangles=len(mesh.faces),
            watertight=bool(mesh.is_watertight),bodies=int(mesh.body_count))
    write_project(OUT/'PTR18_Fit_Check_Plate_v03.3mf',small,settings,
        'Print first: wall cleat, full-width cutout hook, measured-fence channel, attachment pockets and closed Allen-key pocket. These fit checks do not establish a load rating.')
    (v/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
