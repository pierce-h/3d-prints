"""Prepare the checked v10 holder for the device's left external PLA feed.

Run normally to create the project, or with --slice to also slice and archive
the isolated CLI validation. Geometry and material calibration stay unchanged.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Revisions/v10-pla-right-nozzle'
OUT = ROOT / 'Revisions/v11-pla-left-external'
OLD = 'PTR18_Hanger_v10_PLA_Basic_Right_TEST_FIT'
MAIN = 'PTR18_Hanger_v11_PLA_Basic_Left_TEST_FIT'
TEMP = Path('/tmp/ptr18-v11')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare():
    (OUT / 'Validation').mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE / (OLD + '.3mf')) as z:
        original = {n: z.read(n) for n in z.namelist()}
    data = dict(original)
    settings = json.loads(data['Metadata/project_settings.config'])
    assert settings['filament_type'][0] == 'PLA'
    assert settings['filament_settings_id'][0] == 'Bambu PLA Basic @BBL H2D'
    settings['filament_map'] = ['1', '1', '1', '1']
    # Auto For Flush can regroup a single filament onto the default right
    # extruder during slicing. Manual keeps the chosen left assignment.
    settings['filament_map_mode'] = 'Manual'
    data['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    model = ET.fromstring(data['Metadata/model_settings.config'])
    for element in model.iter('metadata'):
        if element.get('key') in ('name', 'plater_name'):
            element.set('value', MAIN)
        elif element.get('key') == 'extruder':
            assert element.get('value') == '1'
        elif element.get('key') == 'filament_maps':
            element.set('value', '1 1 1 1')
        elif element.get('key') == 'filament_map_mode':
            element.set('value', 'Manual')
    data['Metadata/model_settings.config'] = ET.tostring(model, encoding='utf-8', xml_declaration=True)
    core = data['3D/3dmodel.model'].decode()
    start = core.index('<metadata name="Description">')
    end = core.index('</metadata>', start)
    description = ('<metadata name="Description">PTR-18 PLUS full holder, v09 geometry unchanged: '
                   '11.8 mm pin pockets; six 8.8 mm screw pockets, 6 mm deep. '
                   'v11 selects the saved Bambu PLA Basic profile on the LEFT nozzle for '
                   'the black external PLA spool confirmed in the device UI on 2026-10-15. '
                   'All geometry, placement, process and filament calibration values are '
                   'unchanged from v10. Full PLA print and deeper-pocket fit remain untested.')
    core = core[:start] + description + core[end:]
    data['3D/3dmodel.model'] = core.replace(OLD, MAIN).encode()
    ns = {'c': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    before = ET.fromstring(original['3D/3dmodel.model'])
    after = ET.fromstring(data['3D/3dmodel.model'])
    assert [ET.tostring(m) for m in before.findall('c:resources/c:object/c:mesh', ns)] == [ET.tostring(m) for m in after.findall('c:resources/c:object/c:mesh', ns)]
    assert ET.tostring(before.find('c:build', ns)) == ET.tostring(after.find('c:build', ns))
    reference_settings = json.loads(original['Metadata/project_settings.config'])
    changed = [k for k in settings if settings[k] != reference_settings[k]]
    assert set(changed) == {'filament_map', 'filament_map_mode'}
    project = OUT / (MAIN + '.3mf')
    with ZipFile(project, 'w', ZIP_DEFLATED) as z:
        for name, value in data.items():
            z.writestr(name, value)
    shutil.copyfile(SOURCE / (OLD + '.stl'), OUT / (MAIN + '.stl'))
    shutil.copyfile(SOURCE / 'Print_Preview.png', OUT / 'Print_Preview.png')
    report = {
        'revision': 'v11 PLA Basic left external feed',
        'status': 'Prepared for an authorized print; complete PLA holder and deeper-pocket fit remain untested.',
        'device_confirmation': 'Bambu Studio device UI showed black Bambu PLA Basic on the left external feed, 2026-10-15.',
        'geometry_reference': str((SOURCE / (OLD + '.3mf')).relative_to(ROOT)),
        'reference_sha256': digest((SOURCE / (OLD + '.3mf')).read_bytes()),
        'geometry_and_placement_unchanged': True,
        'process_and_filament_calibration_unchanged': True,
        'stl_identical_to_v10': digest((OUT / (MAIN + '.stl')).read_bytes()) == digest((SOURCE / (OLD + '.stl')).read_bytes()),
        'changed_project_setting_keys': changed,
        'active_filament_slot': 1,
        'profile': settings['filament_settings_id'][0],
        'filament_type': settings['filament_type'][0],
        'color': settings['filament_colour'][0],
        'extruder': 'left / 1',
        'feed': 'external',
        'nozzle_temperature_C_standard': settings['nozzle_temperature'][0],
        'bed_temperature_C_textured': settings['textured_plate_temp'][0],
        'part_fan_min_max_percent': [settings['fan_min_speed'][0], settings['fan_max_speed'][0]],
        'overhang_fan_percent': settings['overhang_fan_speed'][0],
        'existing_PLA_flow_ratio_standard': settings['filament_flow_ratio'][0],
        'existing_PLA_pressure_advance': settings['pressure_advance'][0],
        'project_sha256': digest(project.read_bytes()),
    }
    (OUT / 'Validation/settings.json').write_text(json.dumps(report, indent=2) + '\n')
    write_hashes()
    print(project)
    return project


def write_hashes():
    hashes = {p.name: digest(p.read_bytes()) for p in OUT.iterdir()
              if p.suffix in ('.3mf', '.stl', '.png')}
    (OUT / 'Validation/archive_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')


def validate_slice(project):
    (TEMP / 'main').mkdir(parents=True, exist_ok=True)
    with (TEMP / 'main.log').open('w') as log:
        run = subprocess.run([
            '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio',
            '--datadir', str(TEMP / 'main-profile'), '--debug', '1',
            '--arrange', '0', '--orient', '0', '--slice', '1',
            '--export-3mf', 'sliced.3mf', '--outputdir', str(TEMP / 'main'),
            str(project),
        ], stdout=log, stderr=subprocess.STDOUT)
    assert run.returncode == 0, f'Slicer exited {run.returncode}; see {TEMP / "main.log"}'
    result = json.loads((TEMP / 'main/result.json').read_text())
    assert result['return_code'] == 0
    plate = result['sliced_plates'][0]
    assert not plate['warning_message']
    assert len(plate['filaments']) == 1 and plate['filaments'][0]['id'] == 1
    with ZipFile(TEMP / 'main/sliced.3mf') as z:
        info = z.read('Metadata/slice_info.config')
        root = ET.fromstring(info)
        nozzles = root.findall('plate/nozzle')
        assert len(nozzles) == 1 and nozzles[0].get('extruder_id') == '1'
        filaments = root.findall('plate/filament')
        assert len(filaments) == 1 and filaments[0].get('type') == 'PLA' and filaments[0].get('id') == '1'
        gcode_name = next(n for n in z.namelist() if n.endswith('.gcode'))
        gcode = z.read(gcode_name).decode()
    assert '; filament_type = PLA' in gcode
    for src, dest in [('main/result.json', 'slicing.json'), ('main.log', 'slicing.log')]:
        shutil.copyfile(TEMP / src, OUT / 'Validation' / dest)
    (OUT / 'Validation/slice_info.config').write_bytes(info)
    settings = json.loads((OUT / 'Validation/settings.json').read_text())
    settings['slicing'] = {
        'return_code': result['return_code'], 'plate_warnings': plate['warning_message'],
        'active_filament_ids': [p['id'] for p in plate['filaments']], 'extruder_id': '1',
        'gcode_filament_type_verified': 'PLA', 'total_seconds': plate['total_predication'],
        'total_used_g': plate['filaments'][0]['total_used_g'],
    }
    (OUT / 'Validation/settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    write_hashes()
    print(json.dumps(settings['slicing'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--slice', action='store_true')
    args = parser.parse_args()
    project = prepare()
    if args.slice:
        validate_slice(project)
