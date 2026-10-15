"""Create a PLA print setup while preserving the checked v09 geometry."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Revisions/v09-enlarged-deeper-pockets'
OUT = ROOT / 'Revisions/v10-pla-right-nozzle'
OLD = 'PTR18_Hanger_v09_Enlarged_Deeper_Pockets_PETG_Right_TEST_FIT'
MAIN = 'PTR18_Hanger_v10_PLA_Basic_Right_TEST_FIT'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    (OUT / 'Validation').mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE / (OLD + '.3mf')) as z:
        original = {n: z.read(n) for n in z.namelist()}
    data = dict(original)
    settings = json.loads(data['Metadata/project_settings.config'])
    assert settings['filament_type'][0] == 'PLA'
    assert settings['filament_settings_id'][0] == 'Bambu PLA Basic @BBL H2D'
    # Existing PLA temperatures, cooling, flow and pressure-advance settings
    # are preserved. Select that filament and map it to the right extruder.
    settings['filament_map'] = ['2', '1', '1', '1']
    data['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    model = ET.fromstring(data['Metadata/model_settings.config'])
    for element in model.iter('metadata'):
        if element.get('key') in ('name', 'plater_name'):
            element.set('value', MAIN)
        elif element.get('key') == 'extruder':
            element.set('value', '1')
        elif element.get('key') == 'filament_maps':
            element.set('value', '2 1 1 1')
    data['Metadata/model_settings.config'] = ET.tostring(model, encoding='utf-8', xml_declaration=True)
    # Preserve geometry bytes exactly; change only descriptive core metadata.
    core = data['3D/3dmodel.model'].decode()
    start = core.index('<metadata name="Description">')
    end = core.index('</metadata>', start)
    description = ('<metadata name="Description">PTR-18 PLUS full holder, v09 geometry unchanged: '
                   '11.8 mm pin pockets; six 8.8 mm screw pockets, 6 mm deep. '
                   'v10 selects the saved Bambu PLA Basic profile on the RIGHT nozzle, '
                   'with 0.20 mm layers, 6 walls, 30% gyroid and 100 mm/s outer walls. '
                   'Confirm actual PLA spool/profile before printing. New depth and PLA full print untested.')
    core = core[:start] + description + core[end:]
    core = core.replace(OLD, MAIN)
    data['3D/3dmodel.model'] = core.encode()
    project = OUT / (MAIN + '.3mf')
    with ZipFile(project, 'w', ZIP_DEFLATED) as z:
        for name, value in data.items():
            z.writestr(name, value)
    shutil.copyfile(SOURCE / (OLD + '.stl'), OUT / (MAIN + '.stl'))
    shutil.copyfile(SOURCE / 'Print_Preview.png', OUT / 'Print_Preview.png')
    ns = {'c': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    before = ET.fromstring(original['3D/3dmodel.model'])
    after = ET.fromstring(data['3D/3dmodel.model'])
    assert [ET.tostring(m) for m in before.findall('c:resources/c:object/c:mesh', ns)] == [ET.tostring(m) for m in after.findall('c:resources/c:object/c:mesh', ns)]
    assert ET.tostring(before.find('c:build', ns)) == ET.tostring(after.find('c:build', ns))
    reference_settings = json.loads(original['Metadata/project_settings.config'])
    changed = [k for k in settings if settings[k] != reference_settings[k]]
    assert changed == ['filament_map']
    report = {
        'revision': 'v10 PLA Basic right nozzle',
        'status': 'Unprinted; PLA Basic is the existing profile, actual spool type not yet confirmed.',
        'geometry_reference': str((SOURCE / (OLD + '.3mf')).relative_to(ROOT)),
        'reference_sha256': digest((SOURCE / (OLD + '.3mf')).read_bytes()),
        'geometry_and_placement_unchanged': True,
        'stl_identical_to_v09': digest((OUT / (MAIN + '.stl')).read_bytes()) == digest((SOURCE / (OLD + '.stl')).read_bytes()),
        'changed_project_setting_keys': changed,
        'active_filament_slot': 1,
        'profile': settings['filament_settings_id'][0],
        'filament_type': settings['filament_type'][0],
        'color': settings['filament_colour'][0],
        'extruder': 'right / 2',
        'nozzle_temperature_C_standard': settings['nozzle_temperature'][0],
        'bed_temperature_C_textured': settings['textured_plate_temp'][0],
        'part_fan_min_max_percent': [settings['fan_min_speed'][0], settings['fan_max_speed'][0]],
        'overhang_fan_percent': settings['overhang_fan_speed'][0],
        'existing_PLA_flow_ratio_standard': settings['filament_flow_ratio'][0],
        'existing_PLA_pressure_advance': settings['pressure_advance'][0],
        'project_sha256': digest(project.read_bytes()),
        'notes': ['Original PLA flow/calibration values preserved; no new calibration performed.',
                  'Inactive filament slots remain in the project; only slot 1 is assigned to this model and its supports.',
                  'New screw depth and whole-holder PLA performance require physical evaluation.']
    }
    (OUT / 'Validation/settings.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
