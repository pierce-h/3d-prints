"""Apply the physically preferred v08 clearance to the full PTR-18 holder.

The six screw pockets also become 6 mm deep so the 4 mm heads sit 2 mm
below the shelf. New underside bosses retain their 3.5 mm closed floors.
Installed coordinates: X along the wall, Y up, Z toward the user, in mm.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import xml.etree.ElementTree as ET

import manifold3d as mf
import numpy as np

from build_holder import box, cylinder_y, mesh_of, prism_x, side_transform, union, write_project
from build_holder_v06 import main_holder as original_holder
from build_clearance_test_v08 import patch_project


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v09-enlarged-deeper-pockets'
MAIN = 'PTR18_Hanger_v09_Enlarged_Deeper_Pockets_PETG_Right_TEST_FIT'
BASE_SETTINGS = ROOT / 'Revisions/v08-clearance-test/PTR18_Attachment_Clearance_Test_v08_PETG_Right.3mf'
BASE_GEOMETRY = ROOT / 'Revisions/v06-essential-storage/PTR18_Hanger_v06_Essential_Storage_TEST_FIT.3mf'
TOL_VOLUME = 1e-5


def main_holder():
    original, positions_before = original_holder()
    positions = []
    bosses = []
    for old in positions_before:
        p = dict(old)
        p['diameter'] = old['diameter'] + 2.
        p['depth'] = 6. if old['body_diameter'] == 6 else old['depth']
        p['floor_thickness'] = 3.5 if old['body_diameter'] == 6 else 3.
        p['nominal_wall_thickness'] = 3.
        p['boss_diameter'] = p['diameter'] + 6.
        p['floor_y'] = 65. - p['depth']
        p['boss_base_y'] = p['floor_y'] - p['floor_thickness']
        positions.append(p)
        # Union complete bosses before cutting. This refills the old cavities
        # and ensures the deeper screw cavities also cut the existing gusset.
        bosses.append(cylinder_y(p['x'], p['z'], p['boss_diameter'], p['boss_base_y'], 65.))
    cavities = [cylinder_y(p['x'], p['z'], p['diameter'], p['floor_y'], 66.)
                for p in positions]
    solid = union([original] + bosses) - union(cavities)
    return solid, positions, original, bosses


def verify(solid, positions, original, bosses):
    mesh = mesh_of(solid)
    assert solid.status() == mf.Error.NoError
    assert len(solid.decompose()) == 1
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count == 1
    assert np.allclose(mesh.bounds, mesh_of(original).bounds, atol=1e-6)

    # Read the resulting mesh section, independently of the Boolean cutters.
    section = mesh.section(plane_normal=[0, 1, 0], plane_origin=[0, 64.5, 0])
    openings = []
    for points in section.discrete:
        bounds = np.array([points.min(axis=0), points.max(axis=0)])
        size = np.ptp(bounds, axis=0)
        if size[0] < 14 and size[2] < 14:
            openings.append(dict(center_XZ_mm=bounds.mean(axis=0)[[0, 2]].tolist(),
                                 diameter_XZ_mm=size[[0, 2]].tolist()))
    assert len(openings) == 11
    probes = []
    for p in positions:
        found = [o for o in openings
                 if np.allclose(o['center_XZ_mm'], [p['x'], p['z']], atol=1e-6)]
        assert len(found) == 1 and np.allclose(found[0]['diameter_XZ_mm'], p['diameter'], atol=1e-6)
        cavity = cylinder_y(p['x'], p['z'], p['diameter'] - .002,
                            p['floor_y'] + .001, 65.1)
        floor = cylinder_y(p['x'], p['z'], p['boss_diameter'] - .002,
                           p['boss_base_y'] + .001, p['floor_y'] - .001)
        outer = cylinder_y(p['x'], p['z'], p['boss_diameter'] - .002,
                           p['floor_y'] + .001, 65. - .001)
        inner = cylinder_y(p['x'], p['z'], p['diameter'] + .002,
                           p['floor_y'], 65.)
        wall = outer - inner
        blocked = float((solid ^ cavity).volume())
        missing_floor = float((floor - solid).volume())
        missing_wall = float((wall - solid).volume())
        assert abs(blocked) < TOL_VOLUME
        assert abs(missing_floor) < TOL_VOLUME
        assert abs(missing_wall) < TOL_VOLUME
        probes.append(dict(**p, cavity_obstruction_mm3=blocked,
                           missing_full_floor_probe_mm3=missing_floor,
                           missing_full_wall_probe_mm3=missing_wall,
                           probe_boundary_inset_mm=.001,
                           minimum_faceted_wall_mm=3. * float(np.cos(np.pi / 72)),
                           body_top_relative_to_shelf_mm=p['body_height'] - p['depth']))

    added = solid - original
    removed = original - solid
    envelopes = union([cylinder_y(p['x'], p['z'], p['boss_diameter'] + .02,
                                  p['boss_base_y'] - .01, 66.) for p in positions])
    added_outside = float((added - envelopes).volume())
    removed_outside = float((removed - envelopes).volume())
    assert abs(added_outside) < TOL_VOLUME and abs(removed_outside) < TOL_VOLUME
    preserved = {}
    for name, region in {
        'cutout_hook': box((-45, -57, 0), (45, -25, 20)),
        'fence_channel': box((-130, 61, 5.8), (130, 78, 25)),
        'wall_cleats': box((-130, 20, -18), (130, 59, .01)),
        'allen_key_hole': box((-5, 58, 68), (3, 66, 76)),
    }.items():
        a, r = float((added ^ region).volume()), float((removed ^ region).volume())
        assert abs(a) < TOL_VOLUME and abs(r) < TOL_VOLUME
        preserved[name] = dict(added_mm3=a, removed_mm3=r)
    key_probe = cylinder_y(-1, 72, 4.198, 58.001, 65.999)
    key_blockage = float((solid ^ key_probe).volume())
    assert abs(key_blockage) < TOL_VOLUME

    # The leftmost rear screw cup overlaps one existing shelf gusset. Its
    # cavity is deliberately cut through the union; the gusset stays connected.
    web = prism_x([(49, 5.8), (59.1, 53), (61.1, 53), (61.1, 5.8)], 6, 26)
    screw_cut = cylinder_y(22, 40, 8.8, 59, 66)
    assert len((web - screw_cut).decompose()) == 1
    return mesh, dict(
        section_Y_mm=64.5, section_openings=openings, attachment_pockets=probes,
        delta_from_v06=dict(added_volume_mm3=float(added.volume()),
                           removed_volume_mm3=float(removed.volume()),
                           added_outside_pocket_envelopes_mm3=added_outside,
                           removed_outside_pocket_envelopes_mm3=removed_outside,
                           unchanged_geometry_outside_pocket_envelopes=True),
        preserved_features=preserved, allen_key_path_obstruction_mm3=key_blockage,
        intersecting_shelf_gusset=dict(center_X_mm=26,
            screw_pocket_XZ_mm=[22, 40], original_volume_mm3=float(web.volume()),
            cavity_removes_mm3=float((web ^ screw_cut).volume()),
            boss_web_overlap_mm3=float((bosses[4] ^ web).volume()),
            remaining_gusset_components=1),
        clearance_checks_mm=dict(pin_boss_rear_to_fence_front=40-17.8/2-25,
                                 screw_boss_rear_to_fence_front=40-14.8/2-25,
                                 tall_pin_boss_to_gusset_front=64-17.8/2-53,
                                 pin_boss_row_gap=24-17.8,
                                 screw_boss_row_gap=24-14.8,
                                 pin_boss_front_to_shelf_front=82-(64+17.8/2)))


def main():
    validation = OUT / 'Validation'
    validation.mkdir(parents=True, exist_ok=True)
    with ZipFile(BASE_SETTINGS) as z:
        settings = json.loads(z.read('Metadata/project_settings.config'))
        extras = {n: z.read(n) for n in z.namelist()
                  if n.startswith('Metadata/filament_settings_') and n.endswith('.config')}
    assert settings['filament_settings_id'][3] == 'Bambu PETG Matte @BBL H2D 0.4 nozzle'
    assert settings['filament_colour'][3] == '#000000'
    assert all(float(v) == 100 for v in settings['outer_wall_speed'])
    assert float(settings['layer_height']) == .2
    solid, positions, original, bosses = main_holder()
    mesh, verification = verify(solid, positions, original, bosses)
    transform = side_transform(mesh)
    placed = mesh.copy()
    placed.apply_transform(transform)
    assert np.allclose(placed.extents, [135., 99.5, 260.])
    assert np.all(placed.bounds[0] >= [25, 5, -1e-6])
    assert np.all(placed.bounds[1] <= [325, 305, 350])
    installed_path = validation / (MAIN + '_installed.stl')
    stl_path = OUT / (MAIN + '.stl')
    mesh.export(installed_path, file_type='stl_ascii')
    placed.export(stl_path, file_type='stl_ascii')
    project_path = OUT / (MAIN + '.3mf')
    write_project(project_path, [(MAIN, mesh, transform)], settings,
        'PTR-18 PLUS hanger: selected +2 mm attachment clearance from the physically tested '
        'one-notch v08 sample. Four pin pockets: diameter 11.8 mm, depths 8/16 mm. '
        'Six screw pockets: diameter 8.8 mm, depth 6 mm, closed 3.5 mm floors. '
        'Fence channel, cutout hook, cleats and Allen-key through-hole unchanged. '
        'Black PETG Matte, right nozzle, 0.20 mm layers, 100 mm/s outer walls. '
        'The deeper screw recesses have not yet been physically tested.')
    patch_project(project_path, extras)
    with ZipFile(project_path) as z:
        assert z.testzip() is None
        assert json.loads(z.read('Metadata/project_settings.config')) == settings
        assert all(z.read(n) == data for n, data in extras.items())
        config = ET.fromstring(z.read('Metadata/model_settings.config'))
        assert all(o.find("metadata[@key='extruder']").get('value') == '4'
                   for o in config.findall('object'))
        assert config.find("plate/metadata[@key='filament_maps']").get('value') == '1 1 1 2'
    report = dict(
        revision='v09 enlarged and deeper pockets',
        status='UNPRINTED FULL REVISION: diameter selected from user-tested v08 sample; new depth untested.',
        user_feedback=dict(selected_sample='v08 A_Plus2mm, one notch, labeled 2',
            fit='More than enough space; a touch loose, acceptable to the user.',
            shallow_pocket_request='Two to three times the former 2.5 mm depth.',
            retrieval_preference='Recess the heads; grab the threads.',
            finish='Test smoother than the previous full build, but rough lines and edge waviness near holes.',
            finish_cause='Not established by the physical feedback alone.'),
        design_decisions=dict(pin_pocket_diameter_mm=11.8, pin_depths_mm=[8, 16],
            screw_pocket_diameter_mm=8.8, screw_pocket_depth_mm=6,
            depth_multiple=2.4, screw_head_height_mm=4, screw_head_recess_mm=2,
            thread_grip_note='Exposed thread height is the actual thread length minus the 2 mm head recess; thread length has not been measured.',
            pin_floor_mm=3, screw_floor_mm=3.5, nominal_radial_walls_mm=3,
            faceting_note='72-sided cylinders retain 3 mm nominal radial walls; minimum parallel-facet separation is approximately 2.997 mm.'),
        reference_geometry=str(BASE_GEOMETRY.relative_to(ROOT)),
        reference_geometry_sha256=hashlib.sha256(BASE_GEOMETRY.read_bytes()).hexdigest(),
        reference_settings=str(BASE_SETTINGS.relative_to(ROOT)),
        reference_settings_sha256=hashlib.sha256(BASE_SETTINGS.read_bytes()).hexdigest(),
        settings_identical_to_v08=True, filament_extras_identical_to_v08=True,
        filament=dict(slot=4, material=settings['filament_settings_id'][3],
            color=settings['filament_colour'][3], plate_mapping='1 1 1 2',
            physical_extruder_map=settings['physical_extruder_map'], nozzle='right'),
        print_orientation='Original full-holder side pose; pocket axes are horizontal during printing.',
        hole_axis_installed=[0, 1, 0], hole_axis_print=[1, 0, 0],
        geometry=dict(bounds_installed=mesh.bounds.tolist(), bounds_print=placed.bounds.tolist(),
            transform=transform.tolist(), volume_mm3=float(mesh.volume),
            triangles=len(mesh.faces), watertight=bool(mesh.is_watertight),
            winding_consistent=bool(mesh.is_winding_consistent), bodies=int(mesh.body_count)),
        verification=verification, project=project_path.name,
        project_sha256=hashlib.sha256(project_path.read_bytes()).hexdigest(),
        limitations=['New 6 mm screw pocket depth has not been physically tested.',
                     'Thread length and exposed grip are not measured.',
                     'Geometry checks and prior print feedback do not establish a load rating.'])
    (validation / 'geometry.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(project=str(project_path), watertight=mesh.is_watertight,
                         bodies=mesh.body_count, print_dimensions_mm=placed.extents.tolist(),
                         pocket_diameters_mm=[p['diameter'] for p in positions],
                         pocket_depths_mm=[p['depth'] for p in positions],
                         change=verification['delta_from_v06']), indent=2))


if __name__ == '__main__':
    main()
