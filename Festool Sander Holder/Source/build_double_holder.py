"""Build a double cradle and an integrated French cleat from the original 3MF.

All dimensions are millimetres. Installed coordinates: X across the wall,
Y upwards, Z towards the user. The 3MF and STL are oriented top edge down
for printing. This revision is a physical-test prototype, not load rated.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Original' / 'Festool_RO150_Holder_3MF.3mf'
NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
MEMBER = '3D/Objects/object_2.model'


def mesh_of(solid):
    data = solid.to_mesh64()
    return trimesh.Trimesh(np.asarray(data.vert_properties)[:, :3],
                          np.asarray(data.tri_verts), process=False)


def box(lo, hi):
    return mf.Manifold.cube(tuple(np.subtract(hi, lo))).translate(tuple(lo))


def prism_x(points_yz, width):
    # Extrude a YZ polygon along +X. This cyclic permutation is right handed.
    section = mf.CrossSection([np.asarray(points_yz)], mf.FillRule.EvenOdd)
    return mf.Manifold.extrude(section, width).transform(
        np.array([[0, 0, 1, -width / 2], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def printable_transform(mesh, angle=43.):
    # Top edge on bed: x' = x, y' = z, z' = -y, then turn about bed Z.
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    rotation = np.array([[c, 0, -s], [s, 0, c], [0, -1, 0]])
    rotated = mesh.vertices @ rotation.T
    midpoint = (rotated.min(axis=0) + rotated.max(axis=0)) / 2
    translation = np.array([162.5-midpoint[0], 155-midpoint[1], -rotated[:, 2].min()])
    matrix = np.eye(4)
    matrix[:3, :3], matrix[:3, 3] = rotation, translation
    return matrix


def mesh_xml(mesh):
    vertices = '\n'.join('     <vertex x="%.10g" y="%.10g" z="%.10g"/>' % tuple(v)
                         for v in mesh.vertices)
    triangles = '\n'.join('     <triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f)
                          for f in mesh.faces)
    return '<mesh>\n    <vertices>\n'+vertices+'\n    </vertices>\n    <triangles>\n'+triangles+'\n    </triangles>\n   </mesh>'


def write_project(original, entries, mesh, matrix, dest, settings):
    changed = dict(original)
    name = dest.stem
    changed[MEMBER] = re.sub(r'<mesh>.*?</mesh>', mesh_xml(mesh),
                            original[MEMBER].decode(), flags=re.S).encode()
    transform = ' '.join('%.10g' % v for v in np.r_[matrix[:3, :3].T.ravel(), matrix[:3, 3]])
    model = original['3D/3dmodel.model'].decode()
    model = re.sub(r'(<item\b[^>]*\btransform=")[^"]*', lambda m: m[1]+transform, model)
    updates = {
        'Title': name,
        'Origin': 'remix',
        'Description': 'Two side-by-side sander cradles on a shared rear plate with an integrated French cleat. Based on the original RO150 cradle by FortuneAU; original designer and license metadata retained. Prototype: verify wall fit, tool clearance and loaded performance before use. The original screw holes are filled; the wall cleat is the mounting interface.',
        'ProfileTitle': 'TEST FIT — double holder, 0.20 mm, 6 walls, 40% gyroid',
        'ProfileDescription': 'Prototype for two sanders and a nominal 3/4-inch 45-degree wall cleat. Physical fit and load not yet tested. Print cleat sample first. Original cradle by FortuneAU.',
    }
    for key, value in updates.items():
        model = re.sub(r'(<metadata name="'+key+r'">).*?(</metadata>)',
                       lambda m: m[1]+value+m[2], model, flags=re.S)
    changed['3D/3dmodel.model'] = model.encode()
    config = original['Metadata/model_settings.config'].decode()
    config = re.sub(r'face_count="\d+"', f'face_count="{len(mesh.faces)}"', config)
    config = re.sub(r'(<metadata key="name" value=")[^"]*', lambda m: m[1]+name+'.stl', config)
    config = re.sub(r'(<metadata key="plater_name" value=")[^"]*', lambda m: m[1]+'TEST FIT', config)
    # Remove stale source offsets and saved exploded-assembly placement.
    for axis in 'xyz':
        config = re.sub(r'(<metadata key="source_offset_'+axis+r'" value=")[^"]*', lambda m: m[1]+'0', config)
    config = re.sub(r'\s*<assemble>.*?</assemble>', '', config, flags=re.S)
    changed['Metadata/model_settings.config'] = config.encode()
    changed['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    with ZipFile(dest, 'w') as archive:
        for entry in entries:
            archive.writestr(entry, changed[entry.filename])
    oriented = mesh.copy()
    oriented.apply_transform(matrix)
    oriented.export(dest.with_suffix('.stl'))
    return oriented


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--gap', type=float, default=20., help='Gap between cradle outer bounds')
    ap.add_argument('--back-thickness', type=float, default=6.)
    ap.add_argument('--cleat-projection', type=float, default=17.5)
    ap.add_argument('--cleat-angle', type=float, default=45.)
    ap.add_argument('--back-style', choices=['rectangular','frame'], default='rectangular',
                    help='Frame follows the original rim/spokes below the continuous cleat backing')
    ap.add_argument('--revision', default='v01-double-holder-test-fit')
    args = ap.parse_args()
    if args.gap < 0 or args.back_thickness < 4 or not 0 < args.cleat_projection < 19.05:
        raise ValueError('Invalid gap, backing thickness, or cleat projection')
    if not 30 <= args.cleat_angle <= 60:
        raise ValueError('Cleat angle outside supported prototype range')
    out = ROOT / 'Revisions' / args.revision
    validation = out / 'Validation'
    validation.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with ZipFile(SOURCE) as archive:
        entries = archive.infolist()
        original = {e.filename: archive.read(e.filename) for e in entries}
    tree = ET.fromstring(original[MEMBER])
    vertices = np.array([[float(e.get(k)) for k in ('x', 'y', 'z')]
                         for e in tree.findall('.//m:vertex', NS)])
    faces = np.array([[int(e.get(k)) for k in ('v1', 'v2', 'v3')]
                      for e in tree.findall('.//m:triangle', NS)])
    source = mf.Manifold(mf.Mesh64(vertices, faces.astype(np.uint64)))
    assert source.status() == mf.Error.NoError
    bounds = np.array(source.bounding_box()).reshape(2, 3)
    # Fill the obsolete screw holes/countersinks without altering the cradle rim.
    holes = [(-62.753,34.992), (0,34.992), (62.753,34.992), (0,-22.008)]
    caps = [mf.Manifold.cylinder(4., 3., circular_segments=96).translate((x,y,-10.))
            for x,y in holes]
    cradle = mf.Manifold.batch_boolean([source]+caps, mf.OpType.Add)
    pitch = 164. + args.gap
    width = 328. + args.gap
    ymin, ymax = float(bounds[0,1]), float(bounds[1,1])
    zface = -10. - args.back_thickness
    zrear = zface - args.cleat_projection
    bevel_front_y = 8.
    bevel_rear_y = bevel_front_y - args.cleat_projection * math.tan(math.radians(args.cleat_angle))
    cleat_width = width - 34.
    profile = [(bevel_rear_y,zrear),(bevel_front_y,zface),(ymax,zface),(ymax,zrear)]
    cleat = prism_x(profile, cleat_width)
    rectangular_back = box((-width/2,ymin,zface),(width/2,ymax,-9.99))
    if args.back_style == 'frame':
        # Thicken the original rear rim and center spoke by six millimetres.
        # Keep a continuous bridge behind the full cleat attachment area, from
        # bevel_front_y upwards. Nothing in the rear cleat is removed.
        # A 1 mm rear-only margin widens the ribs and avoids coincident edges
        # where the extruded footprint meets the original tessellated mesh.
        cradle_back = cradle.slice(-8.).offset(1., mf.JoinType.Miter).extrude(
            args.back_thickness+.01).translate((0,0,zface))
        back = mf.Manifold.batch_boolean([
            cradle_back.translate((-pitch/2,0,0)),
            cradle_back.translate((pitch/2,0,0)),
            box((-cleat_width/2,bevel_front_y,zface),(cleat_width/2,ymax,-9.99)),
        ], mf.OpType.Add)
        back = (back ^ rectangular_back).simplify(1e-6)
    else:
        back = rectangular_back
    left = cradle.translate((-pitch/2,0,0))
    right = cradle.translate((pitch/2,0,0))
    double = mf.Manifold.batch_boolean([left,right,back,cleat], mf.OpType.Add).simplify(1e-6)
    # Coupon reproduces the full-height backing and EXACT mating-cleat profile.
    coupon_width = 35.
    coupon = mf.Manifold.batch_boolean([
        box((-coupon_width/2,ymin,zface),(coupon_width/2,ymax,-10.)),
        prism_x(profile,coupon_width)], mf.OpType.Add).simplify(1e-6)
    settings = json.loads(original['Metadata/project_settings.config'])
    settings.update(layer_height='0.2', wall_loops='6', top_shell_layers='6',
                    bottom_shell_layers='6', sparse_infill_density='40%',
                    enable_support='1', support_type='normal(auto)', support_style='default',
                    support_threshold_angle='30', support_top_z_distance='0.2',
                    support_bottom_z_distance='0.2', support_on_build_plate_only='0',
                    brim_type='outer_only', brim_width='5', brim_object_gap='0.1')
    # Desktop Bambu Studio reconciles against its installed system preset and
    # retains only keys listed here as deliberate project overrides. The CLI
    # reads raw values, so writing values alone would produce a GUI/CLI mismatch.
    source_settings = json.loads(original['Metadata/project_settings.config'])
    overridden = {k for k in settings if settings[k] != source_settings.get(k)}
    differences = list(settings.get('different_settings_to_system', ['', '', '', '']))
    differences[0] = ';'.join(sorted(set(filter(None,differences[0].split(';'))) | overridden))
    settings['different_settings_to_system'] = differences
    report = {
        'status':'PROTOTYPE — physical cleat fit, tool clearance and load untested',
        'source_sha256':source_hash, 'source_designer':'FortuneAU',
        'models_requested':['Festool RO 150 ROTEX','Festool ETS EC 150/5'],
        'parameters_mm': dict(cradle_gap=args.gap, cradle_center_spacing=pitch,
            overall_width=width, backing_thickness=args.back_thickness,
            cleat_width=cleat_width, cleat_projection=args.cleat_projection,
            nominal_wall_plywood_thickness=19.05, nominal_wall_clearance=19.05-args.cleat_projection),
        'cleat_angle_degrees':args.cleat_angle,
        'back_style':args.back_style,
        'rear_backing_volume_mm3':back.volume(),
        'rectangular_backing_volume_mm3':rectangular_back.volume(),
        'backing_removed_vs_rectangle_mm3':(rectangular_back-back).volume(),
        'cleat_profile_yz_mm':profile,
        'installation':'Backing below the bevel rests against the FRONT of the wall cleat. No full-depth lower wall spacer; actual wall-cleat height remains unmeasured.',
        'print_orientation':'Original top edge on bed, rotated 43 degrees in XY; automatic support for cradle overhangs.',
        'settings_changes':{k:settings[k] for k in settings if settings[k]!=json.loads(original['Metadata/project_settings.config']).get(k)},
        'parts':{},
    }
    revision = args.revision.split('-')[0]
    for key, solid, name in [
        ('holder',double,f'Festool_Double_Holder_{revision}_TEST_FIT'),
        ('coupon',coupon,f'French_Cleat_Fit_Sample_{revision}')]:
        assert solid.status() == mf.Error.NoError
        mesh = mesh_of(solid)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
        assert mesh.volume > 0 and mesh.area_faces.min() > 1e-10
        matrix = printable_transform(mesh, 43. if key=='holder' else 0.)
        part_settings = dict(settings)
        if key=='coupon':
            part_settings['enable_support']='0'
        placed = write_project(original, entries, mesh, matrix, out/(name+'.3mf'), part_settings)
        # Leave room for 5 mm brim within the left extruder's safe 325x310 region.
        assert np.all(placed.bounds[0,:2] >= 5.)
        assert np.all(placed.bounds[1,:2] <= [320.,305.])
        assert abs(placed.bounds[0,2]) < 1e-7 and placed.bounds[1,2]<320.
        # Installed-coordinate meshes are for independent validation/rendering.
        mesh.export(validation/(key+'_installed.stl'))
        report['parts'][key] = dict(file=name+'.3mf', watertight=bool(mesh.is_watertight),
            winding_consistent=bool(mesh.is_winding_consistent), connected_bodies=int(mesh.body_count),
            volume_mm3=float(mesh.volume), triangles=len(mesh.faces), bounds_installed_mm=mesh.bounds.tolist(),
            bounds_print_mm=placed.bounds.tolist(), transform=matrix.tolist())
    # The original cradles are contained in the result; all added material is behind
    # the tool-facing web apart from the four original mounting-hole fills per cup.
    missing = (source.translate((-pitch/2,0,0)) - double).volume()
    missing += (source.translate((pitch/2,0,0)) - double).volume()
    assert missing < 1e-5
    report['original_cradle_material_missing_mm3'] = missing
    report['original_holes_filled_per_cradle'] = 4
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
    (validation/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
